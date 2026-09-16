"""LAB 3 - Your first full agent.

    python labs/lab3_agent.py

Goal: run the complete loop - model, tools, model, answer - and read the trace.

Watch for three things:
  1. How many model calls happened. It is not a fixed number.
  2. Whether it used list_students_below_attendance or three get_student calls.
     If the latter, the tool DESCRIPTION is the bug, not the code.
  3. That it did NOT invent a compare tool. The model can compare numbers.
"""

import _path  # noqa: F401
from agentcore import Agent
from agentcore.demo_tools import campus_registry, CAMPUS_INSTRUCTIONS

agent = Agent(
    name="Campus Assistant",
    instructions=CAMPUS_INSTRUCTIONS,
    registry=campus_registry(),
    max_iterations=8,
)

QUESTIONS = [
    "What is the fee balance for 21CS045?",
    "Which students are below 75% attendance, and what is Priya's fee balance?",
    "Remind me in 3 days to follow up with the students who have attendance shortfall.",
]

for question in QUESTIONS:
    print("\n" + "=" * 74)
    print(f"Q: {question}")
    print("=" * 74)

    result = agent.run(question)

    print(f"\n{result.output}\n")
    print(result.trace.render())
