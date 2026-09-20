-- ====================================================================
-- Production PostgreSQL Database DDL
-- Autonomous Multi-Agent Candidate Evaluation & Placement Readiness Platform
-- ====================================================================

-- Enable UUID extension if available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table 1: Candidates
CREATE TABLE IF NOT EXISTS candidates (
    id VARCHAR(36) PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    university VARCHAR(255),
    branch VARCHAR(100),
    cgpa NUMERIC(4, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Job Profiles / Benchmarks
CREATE TABLE IF NOT EXISTS job_profiles (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    company VARCHAR(150) NOT NULL,
    required_skills JSONB NOT NULL,
    min_cgpa NUMERIC(4, 2) DEFAULT 7.0,
    experience_level VARCHAR(50) DEFAULT 'Fresh Graduate',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table 3: Evaluation Sessions (Managed by Orchestrator Agent)
CREATE TABLE IF NOT EXISTS evaluation_sessions (
    id VARCHAR(36) PRIMARY KEY,
    candidate_id VARCHAR(36) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_profile_id VARCHAR(36) REFERENCES job_profiles(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING', -- PENDING, IN_PROGRESS, COMPLETED, FAILED
    overall_readiness_score NUMERIC(5, 2),
    placement_recommendation VARCHAR(50), -- READY, NEEDS_INTERVENTION, NOT_READY
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Table 4: Agent Task Logs (Full Audit Trail of all 3 Specialist Agents + Orchestrator)
CREATE TABLE IF NOT EXISTS agent_task_logs (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL, -- OrchestratorAgent, ResumeIntelligenceAgent, TechnicalEvaluationAgent, CommunicationCoachAgent
    task_type VARCHAR(100) NOT NULL,
    input_payload JSONB,
    output_payload JSONB,
    latency_ms NUMERIC(10, 2),
    status VARCHAR(30) NOT NULL DEFAULT 'SUCCESS', -- SUCCESS, RETRY, FAILED
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table 5: Evaluation Reports (Detailed per-agent synthesized scores & qualitative feedback)
CREATE TABLE IF NOT EXISTS evaluation_reports (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    dimension VARCHAR(100) NOT NULL, -- RESUME_ATS, TECHNICAL_RIGOR, BEHAVIORAL_COMM, FINAL_SYNTHESIS
    score NUMERIC(5, 2) NOT NULL,
    strengths JSONB,
    growth_areas JSONB,
    raw_analysis TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_sessions_candidate ON evaluation_sessions(candidate_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON evaluation_sessions(status);
CREATE INDEX IF NOT EXISTS idx_task_logs_session ON agent_task_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_task_logs_agent ON agent_task_logs(agent_name);
CREATE INDEX IF NOT EXISTS idx_reports_session ON evaluation_reports(session_id);

-- Documentation Comments
COMMENT ON TABLE candidates IS 'Master candidate profiles undergoing placement readiness evaluation';
COMMENT ON TABLE evaluation_sessions IS 'Orchestrator-driven assessment sessions linking candidates to evaluations';
COMMENT ON TABLE agent_task_logs IS 'Immutable telemetry and execution trace for multi-agent workflows';
COMMENT ON TABLE evaluation_reports IS 'Per-agent evaluation outputs, scores, strengths, and recommendations';
