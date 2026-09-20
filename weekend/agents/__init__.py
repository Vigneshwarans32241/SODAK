"""Multi-Agent System Module Initialization."""
from agents.base import BaseAgent, AgentResult
from agents.resume_agent import ResumeIntelligenceAgent
from agents.tech_agent import TechnicalEvaluationAgent
from agents.comm_agent import CommunicationCoachAgent
from agents.orchestrator import OrchestratorAgent

__all__ = [
    "BaseAgent",
    "AgentResult",
    "ResumeIntelligenceAgent",
    "TechnicalEvaluationAgent",
    "CommunicationCoachAgent",
    "OrchestratorAgent",
]
