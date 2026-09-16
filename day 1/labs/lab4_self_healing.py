"""LAB 4 - The agent reads its own error and recovers.

    python labs/lab4_self_healing.py

This is the highlight of Day 1.

Part 1 shows what a naive implementation does: the exception escapes and
kills the run. Part 2 runs the same bad input through the real agent, where
dispatch converts the failure into an observation the model can act on.

Watch the trace in part 2: a failed tool step, then a CORRECTED call.
Nobody wrote that correction.
"""

import _path  # noqa: F401
from agentcore import Agent
from agentcore.demo_tools import campus_registry, get_student, CAMPUS_INSTRUCTIONS

BAD_INPUT = "twenty one CS zero four five"

print("\n=== 1. Without error handling: the run dies ===\n")
try:
    get_student.fn(roll_number=BAD_INPUT)
except KeyError as exc:
    print(f"  KeyError escaped: {exc}")
    print("  In a naive agent loop this ends the run. The user gets nothing.")

print("\n\n=== 2. With error handling: the model corrects itself ===\n")

agent = Agent(
    name="Campus Assistant",
    instructions=CAMPUS_INSTRUCTIONS,
    registry=campus_registry(),
)
result = agent.run(f"What is the fee balance for roll number '{BAD_INPUT}'?")

print(result.output)
print()
print(result.trace.render())

failed = [s for s in result.trace.steps if s.kind == "tool" and not s.ok]
passed = [s for s in result.trace.steps if s.kind == "tool" and s.ok]

print(f"""
  tool failures : {len(failed)}
  tool successes: {len(passed)}

  Three design details make this work, and all three are easy to get wrong:

    1. The error NAMES the valid roll numbers. "KeyError: 'x'" alone gives
       the model nothing to correct towards.
    2. The traceback is truncated to 800 characters. Forty lines re-sent
       every turn would exhaust the context window.
    3. The circuit breaker stops the tool after 3 consecutive failures.
       Self-healing without a limit is an expensive infinite loop.

  Open agentcore/tools.py and find all three.
""")
