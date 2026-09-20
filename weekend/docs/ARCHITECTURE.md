# System Architecture Specification
## Autonomous Multi-Agent Placement Readiness Platform

**Author:** Vigneshwaran S  
**Email:** vigneshwarans3224@gmail.com  
**Course:** SoDak EduTech — Agentic AI & Full-Stack Engineering  
**Repository:** [https://github.com/Vigneshwarans32241/SODAK/tree/main/weekend](https://github.com/Vigneshwarans32241/SODAK/tree/main/weekend)  

---

## 1. High-Level Architecture Overview

The system implements a **Hierarchical Orchestrator-Worker Multi-Agent Architecture** coupled with a production **PostgreSQL** persistence and telemetry layer.

```mermaid
graph TD
    User([Candidate / Recruiter / API Client]) -->|Candidate Dossier & JD| Orchestrator[Master Orchestrator Agent]
    
    subgraph MultiAgentEngine [Multi-Agent Intelligence Core]
        Orchestrator -->|1. Dispatch Profile & JD| ResumeAgent[Agent 1: ResumeIntelligenceAgent]
        Orchestrator -->|2. Dispatch Code Submission| TechAgent[Agent 2: TechnicalEvaluationAgent]
        Orchestrator -->|3. Dispatch Interview Transcript| CommAgent[Agent 3: CommunicationCoachAgent]
        
        ResumeAgent -->|ATS Score, Gaps, Match %| Orchestrator
        TechAgent -->|Complexity, Edge Cases, Code Score| Orchestrator
        CommAgent -->|STAR Adherence, Clarity, Fillers| Orchestrator
    end
    
    subgraph DataStorage [Enterprise Database Tier - PostgreSQL]
        Orchestrator -->|1. Create/Update Session| DB_Sessions[(evaluation_sessions)]
        Orchestrator -->|2. Persist Final Dossier & Scores| DB_Reports[(evaluation_reports)]
        ResumeAgent -.->|Audit Telemetry Trace| DB_Logs[(agent_task_logs)]
        TechAgent -.->|Audit Telemetry Trace| DB_Logs
        CommAgent -.->|Audit Telemetry Trace| DB_Logs
        Orchestrator -.->|Orchestrator Execution Trace| DB_Logs
        
        DB_Candidates[(candidates)] --- DB_Sessions
        DB_Jobs[(job_profiles)] --- DB_Sessions
    end
    
    Orchestrator -->|Placement Readiness Index + Verdict| ReportOutput([Placement Readiness Dossier])
```

---

## 2. Multi-Agent System Roles & Responsibilities

| Agent Identifier | Pattern / Role | Core Responsibilities & Evaluation Criteria | Output Dimension |
| :--- | :--- | :--- | :--- |
| **`OrchestratorAgent`** | Master Controller / Workflow Synthesizer | Manages lifecycle, distributes evaluation workloads, aggregates telemetry, calculates weighted **Placement Readiness Index (PRI)**, and determines placement recommendation (`READY`, `NEEDS_INTERVENTION`, `NOT_READY`). | `FINAL_SYNTHESIS` |
| **`ResumeIntelligenceAgent`** | Specialist Worker 1 | Evaluates ATS keyword alignment against target Job Description, measures action-verb density, verifies quantified business impact metrics, and flags skill gaps. | `RESUME_ATS` |
| **`TechnicalEvaluationAgent`** | Specialist Worker 2 | Inspects code submissions via AST parsing, estimates time & space complexity ($O(N)$, $O(N^2)$), audits edge-case handling (nulls, empty bounds), and scores clean code practices. | `TECHNICAL_RIGOR` |
| **`CommunicationCoachAgent`** | Specialist Worker 3 | Evaluates behavioral/HR responses against the **STAR** framework (Situation, Task, Action, Result), penalizes conversational fillers, and evaluates response pacing and articulation. | `BEHAVIORAL_COMM` |

---

## 3. End-to-End Execution Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Client as Candidate / Client
    participant Orch as Master Orchestrator Agent
    participant Resume as ResumeIntelligenceAgent
    participant Tech as TechnicalEvaluationAgent
    participant Comm as CommunicationCoachAgent
    participant DB as PostgreSQL Database

    Client->>Orch: Submit Candidate Data (Resume, Code, HR Response, Target JD)
    Orch->>DB: INSERT / UPDATE evaluation_sessions (Status: IN_PROGRESS)
    
    par Parallel / Sequential Specialist Dispatch
        Orch->>Resume: run_task(resume_text, required_skills)
        Resume->>Resume: Calculate ATS Match, Verbs, Metrics
        Resume->>DB: INSERT agent_task_logs (Resume Telemetry)
        Resume-->>Orch: Return AgentResult (Score, Strengths, Gaps)
    and
        Orch->>Tech: run_task(submitted_code, expected_complexity)
        Tech->>Tech: AST Parse, Complexity Heuristic, Edge Checks
        Tech->>DB: INSERT agent_task_logs (Tech Telemetry)
        Tech-->>Orch: Return AgentResult (Score, Complexity, Hygiene)
    and
        Orch->>Comm: run_task(interview_response, question)
        Comm->>Comm: STAR Analysis, Filler Detection, Articulation
        Comm->>DB: INSERT agent_task_logs (Comm Telemetry)
        Comm-->>Orch: Return AgentResult (Score, STAR Coverage, Fillers)
    end

    Orch->>Orch: Compute Placement Readiness Index (PRI) = (0.35 * Tech) + (0.35 * Resume) + (0.30 * Comm)
    Orch->>DB: INSERT evaluation_reports (4 records: 3 specialist + 1 master synthesis)
    Orch->>DB: UPDATE evaluation_sessions (Status: COMPLETED, score: PRI, rec: READY)
    Orch->>DB: INSERT agent_task_logs (Orchestrator Telemetry)
    Orch-->>Client: Return Comprehensive Placement Dossier
```

---

## 4. Scoring Algorithm & Decision Matrix

The **Placement Readiness Index (PRI)** is formulated as:

$$\text{PRI} = 0.35 \times S_{\text{Tech}} + 0.35 \times S_{\text{Resume}} + 0.30 \times S_{\text{Comm}}$$

### Placement Decision Matrix:
- **$\text{PRI} \ge 80.0$**: **`READY`**  
  Direct institutional recommendation for tier-1 product and technical placements.
- **$65.0 \le \text{PRI} < 80.0$**: **`NEEDS_INTERVENTION`**  
  Solid fundamentals with specific deficiencies flagged by specialist agents (e.g., missing required framework skills or sub-optimal algorithmic complexity). Targeted mentorship module assigned.
- **$\text{PRI} < 65.0$**: **`NOT_READY`**  
  Fundamental training required across core algorithmic problem-solving or communication structuring.

---

## 5. Fault Tolerance & Reliability
- **Connection Health Checks:** The system includes real-time connection pinging (`SELECT 1;`) with connection pooling (`pool_size=10, max_overflow=20, pool_pre_ping=True`).
- **Telemetry Isolation:** If an agent encounters a runtime failure during task execution, the error is isolated, logged into `agent_task_logs`, and default penalty fallbacks are applied without crashing the entire orchestration pipeline.
- **Multi-Engine Portability:** Standard PostgreSQL dialect with graceful local analytical fallback engine.
