"""LAB 5 - Session memory and thread isolation.

    python labs/lab5_memory.py

Goal: make the agent remember within one conversation, and prove that a
DIFFERENT conversation remembers nothing.

That second check is the one students skip, and it is the one that matters:
history leaking between users is an incident, not a bug.
"""

import _path  # noqa: F401
from agentcore import Agent, ConversationStore
from agentcore.demo_tools import campus_registry, CAMPUS_INSTRUCTIONS

agent = Agent(
    name="Campus Assistant",
    instructions=CAMPUS_INSTRUCTIONS,
    registry=campus_registry(),
)
store = ConversationStore(keep_last=20)


def chat(thread_id: str, message: str) -> str:
    """Load history, run, save. The agent itself stays stateless."""
    history = store.load(thread_id)
    result = agent.run(message, history=history)
    store.save(thread_id, result.messages)
    return result.output


print("\n=== Thread A: two turns, second depends on the first ===\n")
print("A1 >", "Look up 21CS045 for me.")
print("   <", chat("thread-A", "Look up 21CS045 for me."))
print()
print("A2 >", "And what about her attendance?")          # 'her' only resolves with history
print("   <", chat("thread-A", "And what about her attendance?"))

print("\n\n=== Thread B: a different conversation. No carryover. ===\n")
print("B1 >", "And what about her attendance?")
print("   <", chat("thread-B", "And what about her attendance?"))

print(f"""

  Thread A resolved "her" because the history was re-sent.
  Thread B could not, because it has its own empty history.

  threads in the store: {store.threads()}
  messages in thread-A: {len(store.load('thread-A'))}
  messages in thread-B: {len(store.load('thread-B'))}

  The Agent object is shared between both. It holds no state.
  That is what lets one agent serve many users at once.
""")

print("\n=== Pair-safe trimming ===\n")

# Build an oversized history alternating assistant(tool_calls) and tool results.
fake = [{"role": "system", "content": "s"}]
for i in range(15):
    fake.append({"role": "assistant", "tool_calls": [{"id": f"t{i}"}]})
    fake.append({"role": "tool", "tool_call_id": f"t{i}", "content": "r"})

trimmed = ConversationStore(keep_last=6).trim(fake)
print(f"  before: {len(fake)} messages")
print(f"  after : {len(trimmed)} messages")
print(f"  roles : {[m['role'] for m in trimmed]}")
print("""
  The first message after 'system' is never a bare 'tool'. If it were, its
  matching assistant tool_call would have been trimmed away and the next API
  call would fail with a hard error.
""")
