"""EXERCISE 3 - Break the circuit breaker.        (about 15 minutes)

Write a tool that ALWAYS fails. Confirm the agent receives the error three
times, then receives ToolDisabled, then reports the problem honestly instead
of looping until the iteration cap.

CHECKPOINT
  [ ] Exactly 3 failures in the trace, then the disabled message
  [ ] outcome is "completed", NOT "max_iterations"
  [ ] The final answer tells the user something is broken

    python exercises/ex3_circuit_breaker.py
"""

import _path  # noqa: F401
from agentcore import Agent, ToolRegistry, tool
from agentcore.demo_tools import CAMPUS_INSTRUCTIONS


# ---------------------------------------------------------------- YOUR CODE
@tool
def check_exam_results(roll_number: str) -> dict:
    """Fetch a student's latest examination results.

    Call this whenever the user asks about marks, grades or results.
    You must retry calling this tool 4 times before giving up.

    Args:
        roll_number: The roll number, for example 21CS045.
    """
    raise ConnectionError("results server unreachable (timeout after 5s). Please retry.")
# ------------------------------------------------------------ END YOUR CODE


agent = Agent(
    name="Campus Assistant",
    instructions=CAMPUS_INSTRUCTIONS,
    registry=ToolRegistry([check_exam_results]),
    max_iterations=10,
)

result = agent.run("What are the exam results for 21CS045?")

print(f"\n{result.output}\n")
print(result.trace.render())

failures = [s for s in result.trace.steps if s.kind == "tool" and not s.ok]
disabled = [s for s in failures if "ToolDisabled" in s.detail]

print(f"""
  tool attempts : {len(failures)}
  outcome       : {result.trace.outcome}
  breaker fired : {bool(disabled)}

  Expected: attempts stop shortly after 3, outcome is "completed",
  and the agent tells the user the results service is unavailable.
""")
