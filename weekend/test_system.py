"""
Automated Test Suite for Multi-Agent Placement Readiness Platform
Verifies:
1. Database schema, tables, and session lifecycle.
2. Specialist Agent 1 (ResumeIntelligenceAgent) execution and ATS scoring.
3. Specialist Agent 2 (TechnicalEvaluationAgent) execution and complexity evaluation.
4. Specialist Agent 3 (CommunicationCoachAgent) execution and STAR framework scoring.
5. Master Orchestrator Agent end-to-end pipeline, PRI calculation, and DB persistence.
"""

import pytest
import uuid
from database import init_db, get_db, Candidate, JobProfile, EvaluationSession, AgentTaskLog, EvaluationReport
from agents import (
    ResumeIntelligenceAgent,
    TechnicalEvaluationAgent,
    CommunicationCoachAgent,
    OrchestratorAgent,
    AgentResult
)

@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = next(get_db())
    yield db
    db.close()


def test_database_initialization(db_session):
    """Verifies candidate and job profile persistence."""
    candidate = Candidate(
        full_name="Test Student",
        email=f"test.{uuid.uuid4().hex[:6]}@sodak.edu",
        university="Engineering Institute",
        branch="CSE",
        cgpa=9.1
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    assert candidate.id is not None
    assert candidate.full_name == "Test Student"

    job = JobProfile(
        title="AI Engineer",
        company="Tech Corp",
        required_skills=["python", "docker", "postgresql"]
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    assert job.id is not None
    assert len(job.required_skills) == 3


def test_resume_intelligence_agent(db_session):
    """Verifies Specialist Agent 1 logic and output structure."""
    agent = ResumeIntelligenceAgent()
    context = {
        "resume_text": "Engineered an AI microservice with Python, PostgreSQL, and Docker. Reduced latency by 35%.",
        "required_skills": ["python", "docker", "postgresql", "kubernetes"],
        "experience_summary": "Backend and AI systems"
    }
    result = agent.execute("test-session-1", context, db=db_session)

    assert isinstance(result, AgentResult)
    assert result.agent_name == "ResumeIntelligenceAgent"
    assert result.dimension == "RESUME_ATS"
    assert 0.0 <= result.score <= 100.0
    assert len(result.strengths) > 0
    assert result.status == "SUCCESS"


def test_technical_evaluation_agent(db_session):
    """Verifies Specialist Agent 2 code AST analysis and complexity scoring."""
    agent = TechnicalEvaluationAgent()
    code_submission = """
def two_sum(nums: list[int], target: int) -> list[int]:
    '''Finds two indices matching target.'''
    if not nums or len(nums) < 2:
        return []
    seen = {}
    for i, n in enumerate(nums):
        diff = target - n
        if diff in seen:
            return [seen[diff], i]
        seen[n] = i
    return []
"""
    context = {
        "submitted_code": code_submission,
        "problem_title": "Two-Sum Problem",
        "expected_complexity": "O(N)"
    }
    result = agent.execute("test-session-2", context, db=db_session)

    assert isinstance(result, AgentResult)
    assert result.agent_name == "TechnicalEvaluationAgent"
    assert result.dimension == "TECHNICAL_RIGOR"
    assert result.score >= 70.0
    assert result.detailed_metrics["syntax_valid"] is True
    assert result.detailed_metrics["has_type_hints"] is True


def test_communication_coach_agent(db_session):
    """Verifies Specialist Agent 3 STAR behavioral evaluation."""
    agent = CommunicationCoachAgent()
    interview_text = (
        "When I was in my final year project, our team faced high database latency. "
        "My goal was to optimize the queries. I implemented index partitioning and connection pooling. "
        "As a result, we improved query response time by 50% with zero downtime."
    )
    context = {
        "interview_response": interview_text,
        "question_asked": "Tell me about a difficult problem you solved."
    }
    result = agent.execute("test-session-3", context, db=db_session)

    assert isinstance(result, AgentResult)
    assert result.agent_name == "CommunicationCoachAgent"
    assert result.dimension == "BEHAVIORAL_COMM"
    assert result.score >= 80.0
    assert result.detailed_metrics["star_coverage"]["Situation"] is True
    assert result.detailed_metrics["star_coverage"]["Result"] is True


def test_master_orchestrator_pipeline(db_session):
    """Verifies end-to-end coordination of all 3 agents and database persistence."""
    candidate = Candidate(
        full_name="Orchestrator Test Candidate",
        email=f"orchestrator.{uuid.uuid4().hex[:6]}@sodak.edu",
        cgpa=8.5
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    session = EvaluationSession(candidate_id=candidate.id)
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    orchestrator = OrchestratorAgent()
    candidate_data = {
        "resume_text": "Architected distributed systems in Python and PostgreSQL. Optimized latency by 40%.",
        "required_skills": ["python", "postgresql"],
        "submitted_code": "def solve(x: int) -> int:\n    '''Calculates square.'''\n    if x < 0: return 0\n    return x * x",
        "interview_response": "When I was leading the team, my goal was to deliver on time. I initiated daily standups. As a result, we delivered 2 days early."
    }

    result = orchestrator.evaluate_candidate(
        session_id=session.id,
        candidate_data=candidate_data,
        db=db_session
    )

    assert result["placement_readiness_index"] > 0
    assert result["recommendation"] in ["READY", "NEEDS_INTERVENTION", "NOT_READY"]

    # Verify Database Persistence
    db_session.refresh(session)
    assert session.status == "COMPLETED"
    assert float(session.overall_readiness_score) == pytest.approx(result["placement_readiness_index"])

    logs = db_session.query(AgentTaskLog).filter_by(session_id=session.id).all()
    assert len(logs) >= 4  # 3 specialist agents + 1 orchestrator trace

    reports = db_session.query(EvaluationReport).filter_by(session_id=session.id).all()
    assert len(reports) == 4  # 3 specialist reports + 1 final synthesis
