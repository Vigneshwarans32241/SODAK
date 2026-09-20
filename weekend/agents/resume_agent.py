"""
Specialist Agent 1: Resume & Profile Intelligence Agent
Evaluates candidate profiles, ATS compatibility, skill alignment, and project depth.
"""

import re
from typing import Dict, Any, List
from agents.base import BaseAgent, AgentResult


class ResumeIntelligenceAgent(BaseAgent):
    """
    Analyzes resumes against target job profiles.
    Performs keyword extraction, ATS alignment scoring, quantified impact checks, and gap analysis.
    """

    def __init__(self):
        super().__init__(
            name="ResumeIntelligenceAgent",
            role_description="Evaluates applicant resumes for ATS compliance, skill alignment, and project rigor."
        )
        self.task_type = "RESUME_ANALYSIS"

    def run_task(self, session_id: str, context: Dict[str, Any]) -> AgentResult:
        resume_text = context.get("resume_text", "")
        required_skills = [s.lower() for s in context.get("required_skills", [])]
        experience_summary = context.get("experience_summary", "")

        # 1. Skill Alignment Analysis
        found_skills = []
        missing_skills = []
        resume_lower = resume_text.lower()

        for skill in required_skills:
            # Word boundary regex search
            if re.search(rf"\b{re.escape(skill)}\b", resume_lower):
                found_skills.append(skill)
            else:
                missing_skills.append(skill)

        skill_match_ratio = len(found_skills) / max(len(required_skills), 1)
        skill_score = skill_match_ratio * 100.0

        # 2. Impact & Action-Verb Density
        action_verbs = [
            "engineered", "architected", "optimized", "implemented", "deployed",
            "scaled", "reduced", "spearheaded", "accelerated", "designed"
        ]
        action_matches = [v for v in action_verbs if re.search(rf"\b{v}\b", resume_lower)]
        action_score = min(len(action_matches) * 15.0, 100.0)

        # 3. Quantifiable Impact Analysis (numbers, %, ms, $, etc.)
        quantifiable_metrics = re.findall(r"\b\d+%\b|\b\d+x\b|\b\d+\s*ms\b|\b\d+\s*k\b", resume_lower)
        metric_score = min(len(quantifiable_metrics) * 20.0, 100.0)

        # Weighted composite score
        composite_score = round(
            (0.50 * skill_score) + (0.25 * action_score) + (0.25 * metric_score), 2
        )

        strengths = []
        growth_areas = []

        if skill_match_ratio >= 0.75:
            strengths.append(f"Strong tech stack match ({len(found_skills)}/{len(required_skills)} required skills matched: {', '.join(found_skills[:5])}).")
        else:
            growth_areas.append(f"Missing key job requirements: {', '.join(missing_skills[:5])}.")

        if action_matches:
            strengths.append(f"Uses strong engineering action verbs ({', '.join(action_matches[:4])}).")
        else:
            growth_areas.append("Lacks strong action verbs; rephrase responsibilities into active achievements.")

        if quantifiable_metrics:
            strengths.append(f"Features {len(quantifiable_metrics)} quantifiable achievements demonstrating business impact.")
        else:
            growth_areas.append("Add measurable metrics (e.g. latency reduced by 40%, throughput increased 3x) to validate claims.")

        summary = (
            f"Resume ATS Score: {composite_score}/100. Matches {len(found_skills)} of {len(required_skills)} required competencies. "
            f"Skill match: {round(skill_score, 1)}%, Impact density: {round(action_score, 1)}%."
        )

        return AgentResult(
            agent_name=self.name,
            dimension="RESUME_ATS",
            score=composite_score,
            strengths=strengths,
            growth_areas=growth_areas,
            detailed_metrics={
                "matched_skills": found_skills,
                "missing_skills": missing_skills,
                "skill_match_percentage": round(skill_score, 2),
                "action_verb_count": len(action_matches),
                "quantifiable_metric_count": len(quantifiable_metrics)
            },
            summary=summary
        )
