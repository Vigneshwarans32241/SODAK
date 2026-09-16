"""Two of the five agent design patterns, implemented.

    EvaluatorOptimizer   - pattern 5: generate, critique, revise
    OrchestratorWorker   - pattern 4: plan at runtime, delegate, synthesise

Chaining, routing and parallelisation are left as exercises, because all
three are simple once you have these two.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable

from .agent import Agent
from .config import MODEL_CHEAP


def _strip_fences(raw: str) -> str:
    """Remove markdown code fences the model sometimes adds around JSON."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned)
    return cleaned.strip()


# ==========================================================================
# Pattern 5 - Evaluator / Optimizer
# ==========================================================================
@dataclass
class Critique:
    """The evaluator's verdict. This is the contract between the two agents.

    Note what is being asked for: a DECISION plus EVIDENCE, not an opinion.
    A field that can be filled with "it depends" is a badly designed field.
    """

    passed: bool
    failed_criteria: list[str]
    evidence: list[str]
    fix: str

    @classmethod
    def parse(cls, raw: str) -> "Critique":
        data = json.loads(_strip_fences(raw))
        return cls(
            passed=bool(data["passed"]),
            failed_criteria=list(data.get("failed_criteria", [])),
            evidence=list(data.get("evidence", [])),
            fix=str(data.get("fix", "")),
        )


class EvaluatorOptimizer:
    """Generate -> critique -> revise, bounded by a maximum number of rounds.

    The rule that decides whether this works at all: the evaluator must return
    SPECIFIC, STRUCTURED feedback. "Not good enough" produces no improvement,
    from a project guide or from an evaluator agent.
    """

    def __init__(
        self,
        generator: Agent,
        criteria: list[str],
        max_rounds: int = 3,
        evaluator_model: str = MODEL_CHEAP,
    ) -> None:
        self.generator = generator
        self.criteria = criteria
        self.max_rounds = max_rounds

        criteria_block = "\n".join(f"- {c}" for c in criteria)
        self.evaluator = Agent(
            name="Evaluator",
            model=evaluator_model,
            temperature=0.0,                       # judgement should be repeatable
            instructions=(
                "You are a strict reviewer. Judge the draft against these criteria:\n"
                f"{criteria_block}\n\n"
                "Respond with JSON ONLY, no prose and no code fences:\n"
                '{"passed": bool, "failed_criteria": [str], '
                '"evidence": [str], "fix": str}\n\n'
                "Quote exact phrases from the draft in `evidence`. "
                "If every criterion is met, set passed to true and leave the lists empty."
            ),
        )

    def run(self, task: str, verbose: bool = True) -> dict[str, Any]:
        """Produce a draft satisfying the criteria, or the best attempt at the cap."""
        history: list[dict[str, Any]] = []
        draft = self.generator.run(task).output

        for round_number in range(1, self.max_rounds + 1):
            verdict_text = self.evaluator.run(f"TASK:\n{task}\n\nDRAFT:\n{draft}").output

            # A malformed verdict is FEEDBACK, not a crash - the same principle
            # as tool error recovery in tools.ToolRegistry.dispatch.
            try:
                critique = Critique.parse(verdict_text)
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                critique = Critique(
                    passed=False,
                    failed_criteria=[f"evaluator returned malformed JSON: {exc}"],
                    evidence=[],
                    fix="Return valid JSON matching the required shape.",
                )

            history.append({
                "round": round_number,
                "passed": critique.passed,
                "failed_criteria": critique.failed_criteria,
                "fix": critique.fix,
            })

            if verbose:
                status = "PASS" if critique.passed else "revise"
                print(f"  round {round_number}: {status}"
                      + ("" if critique.passed else f" - {'; '.join(critique.failed_criteria)}"))

            if critique.passed:
                return {"output": draft, "rounds": round_number,
                        "passed": True, "history": history}

            # Feedback re-enters the GENERATOR as input, with the previous draft.
            draft = self.generator.run(
                f"TASK:\n{task}\n\n"
                f"YOUR PREVIOUS DRAFT:\n{draft}\n\n"
                "REVIEW - problems found:\n"
                + "\n".join(f"- {c}" for c in critique.failed_criteria)
                + f"\n\nREQUIRED FIX: {critique.fix}\n\n"
                "Produce a corrected version. Output the corrected text only."
            ).output

        # Cap reached: return the best attempt, flagged. Never raise.
        return {"output": draft, "rounds": self.max_rounds,
                "passed": False, "history": history}


# ==========================================================================
# Pattern 4 - Orchestrator / Worker
# ==========================================================================
class OrchestratorWorker:
    """Plan sub-tasks at RUNTIME, delegate them, then synthesise the findings.

    The test that distinguishes this from parallelisation:
    could you have written the sub-task list BEFORE seeing the input?
    Yes -> parallelisation. No -> orchestrator/worker.
    """

    def __init__(
        self,
        worker_factory: Callable[[str], Agent],
        planner_model: str = MODEL_CHEAP,
        max_subtasks: int = 4,
    ) -> None:
        self.worker_factory = worker_factory
        self.max_subtasks = max_subtasks

        self.planner = Agent(
            name="Planner",
            model=planner_model,
            temperature=0.2,
            instructions=(
                "You break a goal into independent sub-tasks that separate "
                "specialists can work on in parallel.\n"
                f"Produce between 2 and {max_subtasks} sub-tasks.\n"
                "Each sub-task must be self-contained: a worker sees ONLY its own "
                "sub-task, not the original goal or the other sub-tasks.\n\n"
                "Respond with JSON ONLY, no prose and no code fences:\n"
                '{"subtasks": [{"role": str, "instruction": str, "reason": str}]}'
            ),
        )

        self.synthesiser = Agent(
            name="Synthesiser",
            temperature=0.3,
            instructions=(
                "You combine several specialists' findings into one coherent answer "
                "for the original goal. Do not repeat the sub-task structure. "
                "If a finding is missing or failed, say so plainly rather than "
                "filling the gap yourself."
            ),
        )

    def _plan(self, goal: str) -> list[dict[str, str]]:
        """Ask the planner for sub-tasks; degrade gracefully on malformed JSON."""
        raw = self.planner.run(f"GOAL:\n{goal}").output

        try:
            subtasks = json.loads(_strip_fences(raw))["subtasks"][: self.max_subtasks]
        except (json.JSONDecodeError, KeyError, TypeError):
            # Treat the whole goal as one sub-task rather than failing the run.
            # Partial capability beats no capability.
            return [{"role": "Generalist", "instruction": goal,
                     "reason": "planner output could not be parsed"}]

        return [s for s in subtasks if s.get("instruction")]

    def run(self, goal: str, verbose: bool = True) -> dict[str, Any]:
        """Plan, delegate, collect, synthesise."""
        plan = self._plan(goal)
        findings: list[dict[str, Any]] = []

        # Workers run sequentially so the classroom trace stays readable.
        # Making this concurrent is Exercise 5.
        for index, subtask in enumerate(plan, start=1):
            if verbose:
                print(f"  worker {index}: [{subtask['role']}] {subtask['instruction'][:60]}")

            worker = self.worker_factory(subtask["role"])
            result = worker.run(subtask["instruction"])

            findings.append({
                "index": index,
                "role": subtask["role"],
                "instruction": subtask["instruction"],
                "ok": result.ok,
                "finding": result.output,
                "tokens": result.trace.total_tokens,
            })

        digest = "\n\n".join(
            f"[{f['index']}] {f['role']} ({'ok' if f['ok'] else 'INCOMPLETE'})\n"
            f"Sub-task: {f['instruction']}\nFinding: {f['finding']}"
            for f in findings
        )
        final = self.synthesiser.run(
            f"ORIGINAL GOAL:\n{goal}\n\nSPECIALIST FINDINGS:\n{digest}"
        ).output

        return {
            "output": final,
            "plan": plan,
            "findings": findings,
            "total_tokens": sum(f["tokens"] for f in findings),
        }
