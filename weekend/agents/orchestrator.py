"""
Master Orchestrator Agent
Autonomous Multi-Agent Placement Readiness Platform
Coordinates 3 specialist agents, aggregates telemetry, synthesizes scores, and persists to DB.
"""

from datetime import datetime, timezone
import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from agents.base import BaseAgent, AgentResult
from agents.resume_agent import ResumeIntelligenceAgent
from agents.tech_agent import TechnicalEvaluationAgent
from agents.comm_agent import CommunicationCoachAgent
from database.models import EvaluationSession, EvaluationReport


class OrchestratorAgent(BaseAgent):
    """
    Central Controller and Workflow Coordinator.
    - Manages session state machine.
    - Dispatches workloads to Resume, Tech, and Communication specialist agents.
    - Synthesizes findings into a unified Placement Readiness Index (PRI).
    - Writes immutable evaluation reports to the database.
    """

    def __init__(self):
        super().__init__(
            name="OrchestratorAgent",
            role_description="Coordinates candidate assessment across specialist agents and synthesizes the Placement Readiness Index."
        )
        self.task_type = "ORCHESTRATION"
        self.resume_agent = ResumeIntelligenceAgent()
        self.tech_agent = TechnicalEvaluationAgent()
        self.comm_agent = CommunicationCoachAgent()

    def run_task(self, session_id: str, context: Dict[str, Any]) -> AgentResult:
        """Internal execution method required by BaseAgent."""
        # This is invoked when the orchestrator itself logs its synthesis step
        return AgentResult(
            agent_name=self.name,
            dimension="FINAL_SYNTHESIS",
            score=context.get("overall_score", 0.0),
            strengths=context.get("all_strengths", []),
            growth_areas=context.get("all_growth_areas", []),
            detailed_metrics=context.get("metrics_summary", {}),
            summary=context.get("final_verdict", "Evaluation Complete.")
        )

    def evaluate_candidate(
        self,
        session_id: str,
        candidate_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        End-to-End Orchestrated Pipeline:
        1. Updates session status to IN_PROGRESS.
        2. Dispatches task to Agent 1 (ResumeIntelligenceAgent).
        3. Dispatches task to Agent 2 (TechnicalEvaluationAgent).
        4. Dispatches task to Agent 3 (CommunicationCoachAgent).
        5. Computes weighted Placement Readiness Index (PRI).
        6. Persists reports and updates session to COMPLETED.
        """
        start_time = time.perf_counter()

        # Update Session state in DB
        session_record = db.query(EvaluationSession).filter_by(id=session_id).first()
        if session_record:
            session_record.status = "IN_PROGRESS"
            db.commit()

        # Step 1: Agent 1 - Resume & Profile Intelligence
        resume_context = {
            "resume_text": candidate_data.get("resume_text", ""),
            "required_skills": candidate_data.get("required_skills", []),
            "experience_summary": candidate_data.get("experience_summary", "")
        }
        resume_res = self.resume_agent.execute(session_id, resume_context, db=db)

        # Step 2: Agent 2 - Technical Assessment & Code Evaluator
        tech_context = {
            "submitted_code": candidate_data.get("submitted_code", ""),
            "problem_title": candidate_data.get("problem_title", "Algorithmic Challenge"),
            "expected_complexity": candidate_data.get("expected_complexity", "O(N)")
        }
        tech_res = self.tech_agent.execute(session_id, tech_context, db=db)

        # Step 3: Agent 3 - Behavioral & Communication Coach
        comm_context = {
            "interview_response": candidate_data.get("interview_response", ""),
            "question_asked": candidate_data.get("question_asked", "Behavioral Leadership")
        }
        comm_res = self.comm_agent.execute(session_id, comm_context, db=db)

        # Step 4: Synthesize Placement Readiness Index (PRI)
        # Weights: 35% Technical Rigor, 35% Resume/Fit, 30% Communication
        weights = {"tech": 0.35, "resume": 0.35, "comm": 0.30}
        pri_score = round(
            (weights["resume"] * resume_res.score) +
            (weights["tech"] * tech_res.score) +
            (weights["comm"] * comm_res.score),
            2
        )

        if pri_score >= 80.0:
            recommendation = "READY"
            verdict = "Strong candidate profile. Highly recommended for placement interviews."
        elif pri_score >= 65.0:
            recommendation = "NEEDS_INTERVENTION"
            verdict = "Candidate shows solid baseline but requires targeted intervention before tier-1 interviews."
        else:
            recommendation = "NOT_READY"
            verdict = "Candidate requires foundational coaching in technical rigor and communication."

        # Step 5: Persist Evaluation Reports for all agents
        agent_results = [
            (self.resume_agent.name, "RESUME_ATS", resume_res),
            (self.tech_agent.name, "TECHNICAL_RIGOR", tech_res),
            (self.comm_agent.name, "BEHAVIORAL_COMM", comm_res)
        ]

        for agent_name, dimension, res in agent_results:
            rep = EvaluationReport(
                session_id=session_id,
                agent_name=agent_name,
                dimension=dimension,
                score=res.score,
                strengths=res.strengths,
                growth_areas=res.growth_areas,
                raw_analysis=res.summary
            )
            db.add(rep)

        # Record Orchestrator's master synthesis report
        all_strengths = resume_res.strengths + tech_res.strengths + comm_res.strengths
        all_growth = resume_res.growth_areas + tech_res.growth_areas + comm_res.growth_areas

        master_rep = EvaluationReport(
            session_id=session_id,
            agent_name=self.name,
            dimension="FINAL_SYNTHESIS",
            score=pri_score,
            strengths=all_strengths,
            growth_areas=all_growth,
            raw_analysis=verdict
        )
        db.add(master_rep)

        # Step 6: Finalize Session Record
        total_pipeline_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if session_record:
            session_record.status = "COMPLETED"
            session_record.overall_readiness_score = pri_score
            session_record.placement_recommendation = recommendation
            session_record.completed_at = datetime.now(timezone.utc)
            db.commit()

        # Also log Orchestrator task execution
        self.execute(
            session_id=session_id,
            context={
                "overall_score": pri_score,
                "all_strengths": all_strengths,
                "all_growth_areas": all_growth,
                "metrics_summary": {
                    "resume_score": resume_res.score,
                    "tech_score": tech_res.score,
                    "comm_score": comm_res.score,
                    "pipeline_latency_ms": total_pipeline_time_ms
                },
                "final_verdict": verdict
            },
            db=db
        )

        return {
            "session_id": session_id,
            "placement_readiness_index": pri_score,
            "recommendation": recommendation,
            "verdict": verdict,
            "pipeline_latency_ms": total_pipeline_time_ms,
            "specialist_evaluations": {
                "resume_agent": resume_res.model_dump(),
                "tech_agent": tech_res.model_dump(),
                "comm_agent": comm_res.model_dump()
            },
            "strengths": all_strengths,
            "growth_areas": all_growth
        }
