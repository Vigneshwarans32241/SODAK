"""LAB 2 - Tools: schema generation and dispatch.

    python labs/lab2_tools.py

Goal: understand that a tool is a JSON schema plus a Python callable, and that
the model NEVER executes anything - it only emits a request.

No API calls are made in parts 1 and 2. Part 3 makes one.
"""

import json

import _path  # noqa: F401
from agentcore.demo_tools import campus_registry, get_student
from agentcore.config import client, MODEL_MAIN

registry = campus_registry()

print("\n=== 1. The schema was generated, not written ===\n")
print(json.dumps(get_student.to_openai(), indent=2))

print("""
  Nobody typed that JSON. It came from:
    - the function name          -> "name"
    - the docstring summary      -> "description"
    - the type hint (roll: str)  -> "type": "string"
    - the Args: line             -> the parameter description
    - no default value           -> "required"

  Change the function and the schema follows. They cannot drift apart.
""")

print("\n=== 2. Dispatch: the four things that can happen ===\n")

for label, name, args in [
    ("success        ", "get_student", {"roll_number": "21cs045"}),
    ("tool raises    ", "get_student", {"roll_number": "twenty one CS"}),
    ("wrong arguments", "get_student", {"wrong_name": "x"}),
    ("unknown tool   ", "does_not_exist", {}),
]:
    result = registry.dispatch(name, args)
    status = "ok   " if "error" not in result else result["error"]
    print(f"  {label} -> {status}")
    print(f"      {json.dumps(result, default=str)[:150]}")

print("""
  Look at what dispatch returned for the failures. Not an exception -
  a dictionary the model can READ. That is the entire basis of the
  self-healing loop in lab 4.
""")

print("\n=== 3. What the model actually sends back ===\n")

response = client.chat.completions.create(
    model=MODEL_MAIN,
    messages=[{"role": "user", "content": "What is the fee balance for 21CS045?"}],
    tools=registry.schemas(),
    tool_choice="auto",
)
message = response.choices[0].message

if message.tool_calls:
    call = message.tool_calls[0]
    print(f"  content    : {message.content!r}   <- usually None when a tool is wanted")
    print(f"  tool name  : {call.function.name}")
    print(f"  arguments  : {call.function.arguments!r}")
    print(f"  type       : {type(call.function.arguments).__name__}   <- a STRING, not a dict")
    print(f"  call id    : {call.id}")
    print("""
  The model did not look anything up. It produced a request.
  Your code decides whether to honour it - and must json.loads()
  those arguments before use.
""")
else:
    print("  The model answered without a tool. Re-run - or check your tool descriptions.")
