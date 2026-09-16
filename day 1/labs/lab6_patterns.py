"""LAB 6 - Two design patterns, running.

    python labs/lab6_patterns.py

Part 1: Evaluator-Optimizer - generate, critique, revise.
Part 2: Orchestrator-Worker - plan at runtime, delegate, synthesise.

Both make far more calls than a single request. On a free tier that means
rate limits, not money - if you see "[rate limited - waiting 4s]" the code is
retrying for you. Wait; do not stop it.
"""

import _path  # noqa: F401
from agentcore import Agent, EvaluatorOptimizer, OrchestratorWorker

# ==========================================================================
print("\n" + "=" * 74)
print("PART 1 - Evaluator / Optimizer")
print("=" * 74 + "\n")

writer = Agent(
    name="Writer",
    instructions="You write short, professional English for an Indian academic audience.",
    temperature=0.7,
)

loop = EvaluatorOptimizer(
    generator=writer,
    criteria=[
        "Under 90 words.",
        "Names at least one specific, concrete benefit to the student.",
        "Contains no exclamation marks and no marketing superlatives.",
        "Ends with a clear single call to action.",
    ],
    max_rounds=3,
)

outcome = loop.run(
    "Write an announcement inviting final-year students to a 9-day Agentic AI "
    "training track run by SoDak EduTech."
)

print(f"\n  passed: {outcome['passed']}   rounds: {outcome['rounds']}\n")
print(outcome["output"])

print("""

  TRY THIS before moving on:

    a) Make one criterion impossible, e.g. "under 5 words AND over 200 words".
       Confirm it stops at 3 rounds and returns passed=False. Students skip
       this negative test, and it is the one that catches a broken cap.

    b) Replace all four criteria with "Make it good." Watch the evaluator
       approve the first draft every time. VAGUE CRITERIA PRODUCE A USELESS
       EVALUATOR - this is the pattern's most common production failure.
""")

# ==========================================================================
print("\n" + "=" * 74)
print("PART 2 - Orchestrator / Worker")
print("=" * 74 + "\n")


def make_worker(role: str) -> Agent:
    """Build a specialist for a role the PLANNER invented at runtime."""
    return Agent(
        name=role,
        instructions=(
            f"You are a {role}. Address ONLY the sub-task you are given. "
            "You do not know the wider goal, so do not speculate about it. "
            "Be specific and concise: at most 120 words."
        ),
        temperature=0.4,
    )


orchestrator = OrchestratorWorker(worker_factory=make_worker, max_subtasks=4)

campaign = orchestrator.run(
    "Prepare a final-year engineering student in Chennai for placement "
    "interviews in agentic AI engineering roles."
)

print(f"\n--- SYNTHESIS ({campaign['total_tokens']:,} worker tokens) ---\n")
print(campaign["output"])

print(f"""

  Run this again with a different goal. THE ROLES WILL CHANGE:

    this run: {[s['role'] for s in campaign['plan']]}

  Those strings are not in the source code. The planner invented them.
  That is what separates orchestrator-worker from parallelisation, where
  you write the branches yourself.

  Cost: 1 plan + {len(campaign['plan'])} workers + 1 synthesis = {len(campaign['plan']) + 2} model calls
  for one question. Decide deliberately whether the answer justified it.
""")
