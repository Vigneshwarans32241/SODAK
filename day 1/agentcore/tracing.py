"""Tracing: the only practical way to debug an agent.

Print statements do not work here. One run makes several model calls with
state that changes between them. You need an ordered record with timings and
token counts. On Day 2 the SDK gives you a hosted dashboard that does exactly
this - it is useful to know what is inside it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .config import PRICE_PER_1K_INPUT, PRICE_PER_1K_OUTPUT, USD_TO_INR


@dataclass
class Step:
    """One observable event inside a run: a model call or a tool execution."""

    index: int
    kind: str                      # "model" | "tool"
    label: str                     # model name, or tool name
    duration_s: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    detail: str = ""               # arguments, or a short result summary
    ok: bool = True


@dataclass
class RunTrace:
    """The full record of one agent run."""

    goal: str
    steps: list[Step] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    outcome: str = "incomplete"    # "completed" | "max_iterations"

    @property
    def prompt_tokens(self) -> int:
        return sum(s.prompt_tokens for s in self.steps)

    @property
    def completion_tokens(self) -> int:
        return sum(s.completion_tokens for s in self.steps)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def duration_s(self) -> float:
        return (self.finished_at or time.time()) - self.started_at

    @property
    def cost_inr(self) -> float:
        usd = (self.prompt_tokens / 1000) * PRICE_PER_1K_INPUT \
            + (self.completion_tokens / 1000) * PRICE_PER_1K_OUTPUT
        return usd * USD_TO_INR

    def add(self, step: Step) -> Step:
        self.steps.append(step)
        return step

    def render(self) -> str:
        """Human-readable trace. Print this after EVERY run while developing."""
        width = 74
        lines = ["-" * width, f"RUN TRACE  |  {self.goal[:58]}", "-" * width]

        for s in self.steps:
            mark = " " if s.ok else "x"
            tokens = f"{s.prompt_tokens + s.completion_tokens:>6} tok" if s.kind == "model" else " " * 10
            lines.append(f" {mark} #{s.index:<2} {s.kind:<6} {s.duration_s:>5.2f}s {tokens}  {s.label}")
            if s.detail:
                lines.append(f"        {s.detail[:96]}")

        lines += [
            "-" * width,
            f" outcome: {self.outcome}   steps: {len(self.steps)}   "
            f"tokens: {self.total_tokens:,}   time: {self.duration_s:.1f}s   "
            + (f"est. cost: Rs {self.cost_inr:.3f}" if self.cost_inr > 0
               else "cost: free tier"),
            "-" * width,
        ]
        return "\n".join(lines)
