"""EXERCISE 2 - Session memory.                   (about 20 minutes)

Complete the chat() helper so a conversation remembers itself, and prove that
a different thread does not.

CHECKPOINT
  [ ] Turn 2 on the same thread resolves "her" correctly
  [ ] A different thread_id has no carryover
  [ ] After 25 turns, trim() has not orphaned a tool message (no API error)

    python exercises/ex2_session_memory.py
"""

import _path  # noqa: F401
from agentcore import Agent, ConversationStore
from agentcore.demo_tools import campus_registry, CAMPUS_INSTRUCTIONS

agent = Agent(name="Campus Assistant", instructions=CAMPUS_INSTRUCTIONS,
              registry=campus_registry())
store = ConversationStore(keep_last=20)


# ---------------------------------------------------------------- YOUR CODE
def chat(thread_id: str, message: str) -> str:
    """Execute a chat turn with session memory load and save."""
    history = store.load(thread_id)
    result = agent.run(message, history=history)
    store.save(thread_id, result.messages)
    return result.output
# ------------------------------------------------------------ END YOUR CODE


print("\n--- thread A ---")
print(chat("A", "Look up 21CS045 for me."))
print(chat("A", "And what about her attendance?"))

print("\n--- thread B (should NOT know who 'her' is) ---")
print(chat("B", "And what about her attendance?"))

print(f"\n  threads: {store.threads()}")
print(f"  A has {len(store.load('A'))} messages, B has {len(store.load('B'))}")
