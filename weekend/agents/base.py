"""
Base Agent Abstract Class & Execution Framework
Autonomous Multi-Agent Placement Readiness Platform
"""

from abc import ABC, abstractmethod
import time
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.models import AgentTaskLog


class AgentResult(BaseModel):
    """Standardized output structure across all specialist agents."""
    agent_name: str
    dimension: str
    score: float = Field(ge=0.0, le=100.0, description="Normalized score between 0 and 100")
    strengths: List[str] = Field(default_factory=list)
    growth_areas: List[str] = Field(default_factory=list)
    detailed_metrics: Dict[str, Any] = Field(default_factory=dict)
    summary: str
    latency_ms: float = 0.0
    status: str = "SUCCESS"


class BaseAgent(ABC):
    """Abstract Base Agent providing telemetry, DB audit logging, and uniform execution interface."""

    def __init__(self, name: str, role_description: str):
        self.name = name
        self.role_description = role_description

    @abstractmethod
    def run_task(self, session_id: str, context: Dict[str, Any]) -> AgentResult:
        """Core specialist agent logic implemented by subclasses."""
        pass

    def execute(self, session_id: str, context: Dict[str, Any], db: Optional[Session] = None) -> AgentResult:
        """Executes the agent task, captures latency, and persists an immutable audit trace to DB."""
        start_time = time.perf_counter()
        status = "SUCCESS"
        error_msg = None
        result: Optional[AgentResult] = None

        try:
            result = self.run_task(session_id, context)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            result.latency_ms = latency_ms
        except Exception as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            status = "FAILED"
            error_msg = str(e)
            result = AgentResult(
                agent_name=self.name,
                dimension="UNKNOWN",
                score=0.0,
                strengths=[],
                growth_areas=["Agent execution error: " + str(e)],
                summary=f"Failed with exception: {e}",
                latency_ms=latency_ms,
                status=status
            )

        # Persist audit trace to database
        if db is not None:
            try:
                task_log = AgentTaskLog(
                    session_id=session_id,
                    agent_name=self.name,
                    task_type=getattr(self, "task_type", "EVALUATION"),
                    input_payload={k: str(v)[:500] for k, v in context.items()},
                    output_payload=result.model_dump(),
                    latency_ms=latency_ms,
                    status=status,
                    error_message=error_msg
                )
                db.add(task_log)
                db.commit()
            except Exception as db_err:
                db.rollback()
                print(f"[{self.name} DB Trace Warning] Failed to log telemetry: {db_err}")

        return result
