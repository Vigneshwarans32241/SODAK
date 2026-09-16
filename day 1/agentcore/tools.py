"""Tools: turning a Python function into something the model can call.

Two pieces live here:

    @tool          - reads a function's type hints and docstring and builds
                     the JSON schema the model needs
    ToolRegistry   - holds the tools, exports their schemas, and dispatches
                     the model's requests to the real callables

Design rule that runs through the whole file: dispatch NEVER raises.
Every failure becomes a structured result the model can read and react to.
That is what makes self-healing possible (see labs/lab4_self_healing.py).
"""

from __future__ import annotations

import inspect
import re
import traceback
import typing
from dataclasses import dataclass, field
from typing import Any, Callable

from .config import STRICT_SCHEMA

# How many times in a row one tool may fail before we take it off the table.
# Without this, a permanently broken tool is just an expensive infinite loop.
MAX_CONSECUTIVE_TOOL_FAILURES = 3

# Tracebacks go into the model's context, so they must be capped.
# Forty lines of trace re-sent every turn will exhaust the context window.
TRACEBACK_CHAR_LIMIT = 800


# --------------------------------------------------------------------------
# Schema generation
# --------------------------------------------------------------------------
_JSON_TYPES: dict[Any, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _json_type(annotation: Any) -> str:
    """Map a Python annotation onto a JSON Schema type name.

    Anything unrecognised becomes "string", which is the safe default:
    the model sends text and the function decides how to parse it.
    """
    origin = typing.get_origin(annotation)
    if origin is not None:                       # list[str], dict[str, int], Optional[x]
        if origin in (list, tuple, set):
            return "array"
        if origin is dict:
            return "object"
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if args:
            return _json_type(args[0])
    return _JSON_TYPES.get(annotation, "string")


def _parse_docstring(doc: str | None) -> tuple[str, dict[str, str]]:
    """Split a docstring into a summary and per-parameter descriptions.

    Supports the common Args: convention:

        Look up a fee balance.

        Args:
            roll_number: The roll number, e.g. 21CS045.
    """
    if not doc:
        return "", {}

    doc = inspect.cleandoc(doc)
    parts = re.split(r"\n\s*(?:Args|Arguments|Parameters)\s*:\s*\n", doc, maxsplit=1)
    summary = parts[0].strip()

    params: dict[str, str] = {}
    if len(parts) > 1:
        for line in parts[1].splitlines():
            match = re.match(r"\s*(\w+)\s*(?:\([^)]*\))?\s*:\s*(.+)", line)
            if match:
                params[match.group(1)] = match.group(2).strip()
    return summary, params


@dataclass
class Tool:
    """A model-callable tool: a JSON schema plus the Python callable behind it."""

    name: str
    description: str
    fn: Callable[..., Any]
    schema: dict[str, Any] = field(default_factory=dict)

    def to_openai(self) -> dict[str, Any]:
        """Render in the shape the chat completions API expects."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema,
            },
        }


def tool(fn: Callable[..., Any]) -> Tool:
    """Decorator: convert a typed, documented Python function into a Tool.

    The signature becomes the parameter schema and the docstring becomes the
    description the model reads when deciding whether to call it.

    IMPORTANT: the description is a PROMPT, not documentation. Write it as an
    instruction about WHEN to call the tool, not merely what it does.
    """
    hints = typing.get_type_hints(fn)
    signature = inspect.signature(fn)
    summary, param_docs = _parse_docstring(fn.__doc__)

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in signature.parameters.items():
        if param_name in ("self", "cls"):
            continue

        entry: dict[str, Any] = {"type": _json_type(hints.get(param_name, str))}
        if param_name in param_docs:
            entry["description"] = param_docs[param_name]
        properties[param_name] = entry

        # No default value means the model MUST supply it.
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "required": required,
    }

    # Some OpenAI-compatible endpoints (Gemini, Groq) reject schema keys they
    # do not recognise with a 400. OpenAI itself wants this one. STRICT_SCHEMA
    # comes from the provider table in config.py.
    if STRICT_SCHEMA:
        schema["additionalProperties"] = False

    return Tool(
        name=fn.__name__,
        description=summary or f"Call {fn.__name__}.",
        fn=fn,
        schema=schema,
    )


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------
class ToolRegistry:
    """Holds every tool available to an agent and routes the model's calls."""

    def __init__(self, tools: list[Tool] | None = None) -> None:
        self._tools: dict[str, Tool] = {}
        self._failures: dict[str, int] = {}
        for t in tools or []:
            self.register(t)

    def register(self, t: Tool) -> None:
        """Add a tool. Re-registering the same name replaces it."""
        self._tools[t.name] = t
        self._failures[t.name] = 0

    def names(self) -> list[str]:
        return sorted(self._tools)

    def schemas(self) -> list[dict[str, Any]]:
        """Every tool rendered for the API. Pass this as the tools= argument."""
        return [t.to_openai() for t in self._tools.values()]

    def reset_failures(self) -> None:
        """Called at the start of each run so counts do not leak between runs."""
        self._failures = {name: 0 for name in self._tools}

    def dispatch(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool by name. ALWAYS returns a dict. NEVER raises.

        Every failure mode becomes a structured observation that goes back to
        the model, so it can correct itself instead of the run dying.
        """
        # --- unknown tool ---------------------------------------------------
        if name not in self._tools:
            return {
                "error": "UnknownTool",
                "message": f"No tool named '{name}'.",
                "available_tools": self.names(),
                "hint": "Choose one of the available tools, or answer without a tool.",
            }

        # --- circuit breaker ------------------------------------------------
        if self._failures[name] >= MAX_CONSECUTIVE_TOOL_FAILURES:
            return {
                "error": "ToolDisabled",
                "message": (
                    f"'{name}' has failed {MAX_CONSECUTIVE_TOOL_FAILURES} times in a "
                    "row and is no longer available for this run."
                ),
                "hint": "Do not call this tool again. Report the problem to the user.",
            }

        # --- execution ------------------------------------------------------
        try:
            result = self._tools[name].fn(**arguments)
            self._failures[name] = 0                 # success resets the counter
            return result if isinstance(result, dict) else {"result": result}

        except TypeError as exc:
            # Wrong or missing arguments. Highly recoverable by the model,
            # so we hand back the schema it should have matched.
            self._failures[name] += 1
            return {
                "error": "InvalidArguments",
                "message": str(exc),
                "expected_schema": self._tools[name].schema,
                "hint": "Correct the arguments to match the schema and call it again.",
            }

        except Exception as exc:
            # Everything else. The traceback is truncated from the END because
            # the final frames identify the actual failure.
            self._failures[name] += 1
            return {
                "error": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc()[-TRACEBACK_CHAR_LIMIT:],
                "hint": "Read the error, adjust your approach, and try once more.",
            }
