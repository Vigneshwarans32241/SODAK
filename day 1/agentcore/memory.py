"""Memory: session storage and output capping.

Two rules drive this file.

1. The agent stays STATELESS. History is passed in and returned out, never
   held on the Agent instance. One agent must be able to serve many users
   at once, and state on `self` makes that impossible.

2. Trimming must be PAIR-SAFE. An assistant message carrying tool_calls and
   its matching tool messages are one unit. Cut between them and the next
   API call fails with a hard error.
"""

from __future__ import annotations

import json
from typing import Any

Message = dict[str, Any]

# Oversized tool output is the usual cause of context exhaustion.
# Cap it at the boundary rather than hoping tools behave.
TOOL_RESULT_CHAR_LIMIT = 2000


def cap_tool_output(payload: dict[str, Any]) -> str:
    """Serialise a tool result to JSON, truncating if it is oversized.

    default=str rescues values that are not natively JSON-serialisable
    (datetime, Decimal, custom objects) instead of raising mid-run. Forgetting
    it is one of the four classic Day 1 errors.
    """
    text = json.dumps(payload, default=str)
    if len(text) <= TOOL_RESULT_CHAR_LIMIT:
        return text

    return json.dumps({
        "truncated": True,
        "original_length": len(text),
        "preview": text[:TOOL_RESULT_CHAR_LIMIT],
        "hint": "Output was truncated. Narrow your query if you need the rest.",
    })


class ConversationStore:
    """In-memory session store keyed by thread id.

    On Day 6 this becomes a SQLite checkpointer; on Day 2 the SDK's
    SQLiteSession does the same job. The interface is the same shape as both.
    """

    def __init__(self, keep_last: int = 20) -> None:
        self._threads: dict[str, list[Message]] = {}
        self.keep_last = keep_last

    def load(self, thread_id: str) -> list[Message]:
        """Return a COPY so callers cannot mutate stored history by accident."""
        return list(self._threads.get(thread_id, []))

    def save(self, thread_id: str, messages: list[Message]) -> None:
        self._threads[thread_id] = self.trim(messages)

    def clear(self, thread_id: str) -> None:
        self._threads.pop(thread_id, None)

    def threads(self) -> list[str]:
        return sorted(self._threads)

    def trim(self, messages: list[Message]) -> list[Message]:
        """Keep the system message plus recent turns, without orphaning tools.

        Walks forward from the intended cut point and skips past any leading
        tool message, because a tool result whose assistant tool_call was
        trimmed away is rejected by the API.
        """
        if len(messages) <= self.keep_last + 1:
            return list(messages)

        system = [m for m in messages[:1] if m.get("role") == "system"]
        body = messages[len(system):]

        cut = max(0, len(body) - self.keep_last)
        while cut < len(body) and body[cut].get("role") == "tool":
            cut += 1

        return system + body[cut:]
