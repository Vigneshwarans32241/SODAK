"""agentcore - the Day 1 agent framework, built from scratch.

Import order matters: config.py validates your API key and exits with a
readable message if it is missing, so import it first.
"""

from .config import (client, MODEL_MAIN, MODEL_CHEAP, masked_key, describe,
                     PROVIDER, PROVIDER_LABEL, IS_FREE)
from .tools import tool, Tool, ToolRegistry
from .tracing import Step, RunTrace
from .memory import ConversationStore, cap_tool_output
from .agent import Agent, RunResult
from .patterns import EvaluatorOptimizer, OrchestratorWorker

__all__ = [
    "client", "MODEL_MAIN", "MODEL_CHEAP", "masked_key", "describe",
    "PROVIDER", "PROVIDER_LABEL", "IS_FREE",
    "tool", "Tool", "ToolRegistry",
    "Step", "RunTrace",
    "ConversationStore", "cap_tool_output",
    "Agent", "RunResult",
    "EvaluatorOptimizer", "OrchestratorWorker",
]
