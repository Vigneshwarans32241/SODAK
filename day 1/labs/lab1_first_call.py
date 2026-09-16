"""LAB 1 - Your first model call.

    python labs/lab1_first_call.py

Goal: see the four message roles, the request/response shape, and the token
count with your own eyes, before any agent machinery is involved.

Concepts: prompt, completion, tokens, system vs user, statelessness.
"""

import _path  # noqa: F401
from agentcore.config import client, MODEL_MAIN, describe

print(f"\n  using: {describe()}\n")
print("=== 1. A single call ===\n")

response = client.chat.completions.create(
    model=MODEL_MAIN,
    messages=[
        # SYSTEM: standing instructions. True for every visitor. Set once.
        {"role": "system", "content": "You are a concise campus assistant. Two sentences maximum."},
        # USER: what the person actually asked.
        {"role": "user", "content": "What is a semester backlog?"},
    ],
    temperature=0.3,
)

print(response.choices[0].message.content)
print(f"\n  prompt tokens     : {response.usage.prompt_tokens}")
print(f"  completion tokens : {response.usage.completion_tokens}")
print(f"  total             : {response.usage.total_tokens}")


print("\n\n=== 2. Proving the model has no memory ===\n")

# Ask a follow-up WITHOUT sending the previous exchange.
forgetful = client.chat.completions.create(
    model=MODEL_MAIN,
    messages=[{"role": "user", "content": "How many did I just ask about?"}],
    temperature=0.3,
)
print("Without history:")
print("  " + (forgetful.choices[0].message.content or "").strip()[:200])

# Now send the same follow-up WITH the history attached.
remembering = client.chat.completions.create(
    model=MODEL_MAIN,
    messages=[
        {"role": "system", "content": "You are a concise campus assistant."},
        {"role": "user", "content": "What is a semester backlog?"},
        {"role": "assistant", "content": response.choices[0].message.content},
        {"role": "user", "content": "Summarise what you just told me in one line."},
    ],
    temperature=0.3,
)
print("\nWith history:")
print("  " + (remembering.choices[0].message.content or "").strip()[:200])

print(f"""
  Notice the token counts:
    call 1 (no history)   : {forgetful.usage.prompt_tokens} prompt tokens
    call 2 (with history) : {remembering.usage.prompt_tokens} prompt tokens

  The model did not "remember" anything. You re-sent the transcript.
  That is the whole mechanism - and the reason longer conversations
  cost more.
""")
