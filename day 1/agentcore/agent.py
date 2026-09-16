"""The agent: the execution loop itself.

The loop, restated:

    1. Send the whole message list to the model, with tool schemas attached.
    2. No tool calls in the reply? That is the final answer. Stop.
    3. Otherwise run every requested tool, appending each result.
    4. Go back to step 1.

THE APPEND ORDER RULE (this breaks everyone at least once):

    assistant (with tool_calls)  ->  tool (id=A)  ->  tool (id=B)  ->  next call

A tool message with no preceding tool_calls is a hard API error, and every
tool message must carry the matching tool_call_id.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from .config import client, MODEL_MAIN, MAX_RETRIES, RETRY_BASE_DELAY
from .memory import Message, cap_tool_output
from .tools import ToolRegistry
from .tracing import RunTrace, Step


@dataclass
class RunResult:
    """What a run returns: the answer, the full message list, and the trace."""

    output: str
    messages: list[Message]
    trace: RunTrace

    @property
    def ok(self) -> bool:
        return self.trace.outcome == "completed"


class Agent:
    """A tool-using agent built on the raw chat completions API.

    Deliberately stateless. Conversation history is passed in and returned
    out, never stored on the instance.
    """

    def __init__(
        self,
        name: str,
        instructions: str,
        registry: ToolRegistry | None = None,
        model: str = MODEL_MAIN,
        max_iterations: int = 8,
        temperature: float = 0.3,
    ) -> None:
        self.name = name
        self.instructions = instructions
        self.registry = registry or ToolRegistry()
        self.model = model
        self.max_iterations = max_iterations
        self.temperature = temperature

    # ---------------------------------------------------------------- internals

    def _call_model(self, messages: list[Message], trace: RunTrace, index: int):
        """One model call, timed and recorded into the trace."""
        started = time.time()

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        # Only attach tools if there are any - an empty list is rejected.
        if self.registry.names():
            kwargs["tools"] = self.registry.schemas()
            kwargs["tool_choice"] = "auto"

        # Free tiers are rate-limited per minute, and one run makes several
        # calls. Retry with exponential backoff rather than dying on a 429.
        response = None
        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(**kwargs)
                break
            except Exception as exc:
                message = str(exc).lower()
                transient = (
                    "429" in message
                    or "rate limit" in message
                    or "resource_exhausted" in message
                    or "overloaded" in message
                    or "503" in message
                )
                if not transient or attempt == MAX_RETRIES - 1:
                    raise
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"    [rate limited - waiting {delay:.0f}s, "
                      f"attempt {attempt + 2}/{MAX_RETRIES}]")
                time.sleep(delay)

        usage = response.usage

        trace.add(Step(
            index=index,
            kind="model",
            label=self.model,
            duration_s=time.time() - started,
            prompt_tokens=getattr(usage, "prompt_tokens", 0),
            completion_tokens=getattr(usage, "completion_tokens", 0),
        ))
        return response.choices[0].message

    @staticmethod
    def _as_message(model_message) -> Message:
        """Convert the SDK response object into a plain dict for the history.

        Built by hand rather than with model_dump() so you can see exactly
        what the API expects to receive back.
        """
        message: Message = {"role": "assistant", "content": model_message.content}

        if model_message.tool_calls:
            message["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in model_message.tool_calls
            ]
        return message

    # ------------------------------------------------------------------- public

    def run(self, goal: str, history: list[Message] | None = None) -> RunResult:
        """Execute the loop until the model answers or the cap is reached."""
        trace = RunTrace(goal=goal)
        self.registry.reset_failures()

        # Build the working message list: system prompt, prior history, new goal.
        messages: list[Message] = []
        if history:
            messages = list(history)
            if not messages or messages[0].get("role") != "system":
                messages.insert(0, {"role": "system", "content": self.instructions})
        else:
            messages.append({"role": "system", "content": self.instructions})

        messages.append({"role": "user", "content": goal})

        step_index = 0

        for _ in range(self.max_iterations):
            step_index += 1
            model_message = self._call_model(messages, trace, step_index)

            # RULE: append the assistant message BEFORE any tool results.
            messages.append(self._as_message(model_message))

            # No tool requested -> this is the answer. The loop ends naturally.
            if not model_message.tool_calls:
                trace.outcome = "completed"
                trace.finished_at = time.time()
                return RunResult(model_message.content or "", messages, trace)

            # Otherwise: run every requested tool.
            for tool_call in model_message.tool_calls:
                step_index += 1
                started = time.time()

                # Arguments arrive as a JSON *string*, never a dict.
                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError as exc:
                    arguments = {}
                    result: dict[str, Any] = {
                        "error": "MalformedArguments",
                        "message": str(exc),
                        "hint": "Emit valid JSON for the arguments and retry.",
                    }
                else:
                    result = self.registry.dispatch(tool_call.function.name, arguments)

                succeeded = "error" not in result
                trace.add(Step(
                    index=step_index,
                    kind="tool",
                    label=tool_call.function.name,
                    duration_s=time.time() - started,
                    detail=(str(arguments) if succeeded
                            else f"{result.get('error')}: {result.get('message', '')}"),
                    ok=succeeded,
                ))

                # RULE: tool_call_id must match the id from the request.
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": cap_tool_output(result),
                })

        # Iteration cap reached. Escalate - never silently return a partial answer.
        trace.outcome = "max_iterations"
        trace.finished_at = time.time()
        return RunResult(
            output=(
                f"[escalation] '{self.name}' reached its iteration limit of "
                f"{self.max_iterations} without completing the task. "
                "A human should review the trace."
            ),
            messages=messages,
            trace=trace,
        )
