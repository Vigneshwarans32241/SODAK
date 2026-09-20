"""
SQLAlchemy 2.0 ORM Models for Placement Readiness Platform
Engineered for full relational capability and cross-engine portability.
"""

from datetime import datetime, timezone
import uuid
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column,
    String,
    Numeric,
    DateTime,
    Text,
    JSON
)
from sqlalchemy.orm import declarative_base, relationship, foreign

Base = declarative_base()

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    university = Column(String(255), nullable=True)
    branch = Column(String(100), nullable=True)
    cgpa = Column(Numeric(4, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    sessions = relationship(
        "EvaluationSession",
        back_populates="candidate",
        primaryjoin=lambda: foreign(EvaluationSession.candidate_id) == Candidate.id,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Candidate id={self.id} name={self.full_name}>"


class JobProfile(Base):
    __tablename__ = "job_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(150), nullable=False)
    company = Column(String(150), nullable=False)
    required_skills = Column(JSON, nullable=False)  # List of skill keywords
    min_cgpa = Column(Numeric(4, 2), default=7.0)
    experience_level = Column(String(50), default="Fresh Graduate")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    sessions = relationship(
        "EvaluationSession",
        back_populates="job_profile",
        primaryjoin=lambda: foreign(EvaluationSession.job_profile_id) == JobProfile.id
    )

    def __repr__(self) -> str:
        return f"<JobProfile id={self.id} title={self.title} company={self.company}>"


class EvaluationSession(Base):
    __tablename__ = "evaluation_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), nullable=False, index=True)
    job_profile_id = Column(String(36), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="PENDING", index=True)  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    overall_readiness_score = Column(Numeric(5, 2), nullable=True)
    placement_recommendation = Column(String(50), nullable=True)  # READY, NEEDS_INTERVENTION, NOT_READY
    started_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    candidate = relationship(
        "Candidate",
        back_populates="sessions",
        primaryjoin=lambda: Candidate.id == foreign(EvaluationSession.candidate_id)
    )
    job_profile = relationship(
        "JobProfile",
        back_populates="sessions",
        primaryjoin=lambda: JobProfile.id == foreign(EvaluationSession.job_profile_id)
    )
    task_logs = relationship(
        "AgentTaskLog",
        back_populates="session",
        primaryjoin=lambda: foreign(AgentTaskLog.session_id) == EvaluationSession.id,
        cascade="all, delete-orphan"
    )
    reports = relationship(
        "EvaluationReport",
        back_populates="session",
        primaryjoin=lambda: foreign(EvaluationReport.session_id) == EvaluationSession.id,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<EvaluationSession id={self.id} status={self.status} score={self.overall_readiness_score}>"


class AgentTaskLog(Base):
    __tablename__ = "agent_task_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    task_type = Column(String(100), nullable=False)
    input_payload = Column(JSON, nullable=True)
    output_payload = Column(JSON, nullable=True)
    latency_ms = Column(Numeric(10, 2), nullable=True)
    status = Column(String(30), nullable=False, default="SUCCESS")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    session = relationship(
        "EvaluationSession",
        back_populates="task_logs",
        primaryjoin=lambda: EvaluationSession.id == foreign(AgentTaskLog.session_id)
    )

    def __repr__(self) -> str:
        return f"<AgentTaskLog agent={self.agent_name} task={self.task_type} status={self.status}>"


class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    dimension = Column(String(100), nullable=False)  # RESUME_ATS, TECHNICAL_RIGOR, BEHAVIORAL_COMM, FINAL_SYNTHESIS
    score = Column(Numeric(5, 2), nullable=False)
    strengths = Column(JSON, nullable=True)
    growth_areas = Column(JSON, nullable=True)
    raw_analysis = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    session = relationship(
        "EvaluationSession",
        back_populates="reports",
        primaryjoin=lambda: EvaluationSession.id == foreign(EvaluationReport.session_id)
    )

    def __repr__(self) -> str:
        return f"<EvaluationReport agent={self.agent_name} dimension={self.dimension} score={self.score}>"
