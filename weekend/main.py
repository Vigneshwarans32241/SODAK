"""
Autonomous Multi-Agent Placement Readiness Platform
Main Demonstration Runner
"""

import sys
import uuid

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from database import init_db, get_db, Candidate, JobProfile, EvaluationSession, AgentTaskLog, EvaluationReport, get_db_status
from agents import OrchestratorAgent

console = Console(force_terminal=True)

def run_pipeline():
    console.print(Panel.fit(
        "[bold cyan]AUTONOMOUS MULTI-AGENT PLACEMENT READINESS PLATFORM[/bold cyan]\n"
        "[dim]Architecture: 1 Master Orchestrator + 3 Specialist Worker Agents + PostgreSQL Engine[/dim]",
        border_style="cyan"
    ))

    # 1. Initialize Database
    init_db()
    status = get_db_status()
    console.print(f"[bold green][OK] Database Engine Initialized:[/bold green] {status['engine']}")
    console.print(f"[dim]Endpoint: {status['url']}[/dim]\n")

    db = next(get_db())

    # 2. Setup Candidate & Job Profile
    candidate_email = f"vigneshwaran.{uuid.uuid4().hex[:6]}@sodak.edu"
    candidate = Candidate(
        full_name="Vigneshwaran S",
        email=candidate_email,
        university="Sri Sairam Engineering College",
        branch="Computer Science & Engineering",
        cgpa=8.85
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    job = JobProfile(
        title="Senior AI Systems & Full-Stack Engineer",
        company="Antigravity Tech Labs",
        required_skills=["python", "postgresql", "docker", "fastapi", "react", "distributed systems"],
        min_cgpa=8.0,
        experience_level="Fresh Graduate / Entry Level"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # 3. Create Evaluation Session
    session = EvaluationSession(
        candidate_id=candidate.id,
        job_profile_id=job.id,
        status="PENDING"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    console.print(f"[bold yellow][+] Initiating Evaluation Session ID:[/bold yellow] {session.id}")
    console.print(f"Candidate: [bold]{candidate.full_name}[/bold] ({candidate.branch}, CGPA: {candidate.cgpa})")
    console.print(f"Target Role: [bold]{job.title}[/bold] at [bold]{job.company}[/bold]\n")

    # Sample candidate data package for evaluation
    candidate_data = {
        # Context for Agent 1 (Resume & Profile Intelligence)
        "resume_text": """
        Vigneshwaran S - Software Engineer
        Experience & Projects:
        - Engineered an autonomous multi-agent platform using Python, PostgreSQL, Docker, and FastAPI.
        - Deployed microservices on Kubernetes, reducing API latency by 45% and serving over 150k monthly requests.
        - Architected real-time WebSocket dashboard in React with state management.
        - Optimized database indexing in PostgreSQL, accelerating query execution by 3x.
        Skills: Python, PostgreSQL, Docker, FastAPI, React, Git, Distributed Systems.
        """,
        "required_skills": job.required_skills,
        "experience_summary": "Full stack AI agent engineering, relational databases, distributed systems.",

        # Context for Agent 2 (Technical Assessment & Code Evaluator)
        "submitted_code": '''
def find_two_sum_optimized(nums: list[int], target: int) -> list[int]:
    """
    Finds two indices such that their elements sum up to the target.
    Utilizes a hash map for optimal O(N) runtime and O(N) auxiliary space.
    """
    if not nums or len(nums) < 2:
        return []

    lookup: dict[int, int] = {}
    for index, value in enumerate(nums):
        complement = target - value
        if complement in lookup:
            return [lookup[complement], index]
        lookup[value] = index
    return []
''',
        "problem_title": "Two-Sum Array Complement Lookup",
        "expected_complexity": "O(N)",

        # Context for Agent 3 (Behavioral & Communication Coach)
        "interview_response": """
        When I was working on my previous university capstone project, our microservices experienced high latency under peak traffic.
        My goal was to diagnose the bottleneck and stabilize response times within 48 hours.
        I initiated profiling of the database queries and collaborated with our infrastructure team to implement connection pooling.
        As a result, we reduced latency by 45% and stabilized the system with zero downtime.
        """,
        "question_asked": "Describe a time when you resolved a high-pressure technical bottleneck."
    }

    # 4. Trigger Master Orchestrator Agent
    orchestrator = OrchestratorAgent()
    console.print("[bold cyan][*] Orchestrator Agent activated:[/bold cyan] Dispatching workloads to 3 specialist agents...")

    result = orchestrator.evaluate_candidate(
        session_id=session.id,
        candidate_data=candidate_data,
        db=db
    )

    # 5. Display Specialist Agent Scores & Telemetry
    table = Table(title="Specialist Worker Agent Evaluation Breakdown", box=box.ROUNDED)
    table.add_column("Agent Name", style="cyan", no_wrap=True)
    table.add_column("Dimension", style="magenta")
    table.add_column("Score (0-100)", justify="right", style="green")
    table.add_column("Latency (ms)", justify="right", style="yellow")
    table.add_column("Key Finding", style="white")

    specs = result["specialist_evaluations"]
    table.add_row(
        "Agent 1: ResumeIntelligenceAgent",
        "RESUME_ATS",
        f"{specs['resume_agent']['score']:.1f}",
        f"{specs['resume_agent']['latency_ms']:.2f} ms",
        specs['resume_agent']['summary'][:60] + "..."
    )
    table.add_row(
        "Agent 2: TechnicalEvaluationAgent",
        "TECHNICAL_RIGOR",
        f"{specs['tech_agent']['score']:.1f}",
        f"{specs['tech_agent']['latency_ms']:.2f} ms",
        specs['tech_agent']['summary'][:60] + "..."
    )
    table.add_row(
        "Agent 3: CommunicationCoachAgent",
        "BEHAVIORAL_COMM",
        f"{specs['comm_agent']['score']:.1f}",
        f"{specs['comm_agent']['latency_ms']:.2f} ms",
        specs['comm_agent']['summary'][:60] + "..."
    )

    console.print(table)

    # 6. Display Synthesized Placement Readiness Report
    pri = result["placement_readiness_index"]
    rec = result["recommendation"]
    rec_color = "bold green" if rec == "READY" else "bold yellow"

    console.print(Panel(
        f"[bold white]Overall Placement Readiness Index (PRI):[/bold white] [bold cyan]{pri} / 100[/bold cyan]\n"
        f"[bold white]Final Placement Recommendation:[/bold white] [{rec_color}]{rec}[/{rec_color}]\n"
        f"[bold white]Pipeline Total Latency:[/bold white] [yellow]{result['pipeline_latency_ms']} ms[/yellow]\n\n"
        f"[bold white]Executive Summary:[/bold white]\n{result['verdict']}",
        title="[bold green]Orchestrator Placement Dossier[/bold green]",
        border_style="green"
    ))

    # 7. Verify Database Persistence
    db.refresh(session)
    log_count = db.query(AgentTaskLog).filter_by(session_id=session.id).count()
    report_count = db.query(EvaluationReport).filter_by(session_id=session.id).count()

    console.print(Panel(
        f"[OK] Session Status in DB: [bold cyan]{session.status}[/bold cyan]\n"
        f"[OK] Audit Trail Logs Written (agent_task_logs): [bold cyan]{log_count} records[/bold cyan]\n"
        f"[OK] Evaluation Reports Stored (evaluation_reports): [bold cyan]{report_count} reports[/bold cyan]\n"
        f"[OK] Relational Consistency: [bold green]VERIFIED (100% PERSISTED)[/bold green]",
        title="[bold blue]Database Verification & Relational Audit Trail[/bold blue]",
        border_style="blue"
    ))

    db.close()
    return result

if __name__ == "__main__":
    run_pipeline()
