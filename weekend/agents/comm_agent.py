"""
Specialist Agent 3: Behavioral & Communication Coach Agent
Evaluates candidate interview responses, STAR method alignment, articulation, and tone.
"""

import re
from typing import Dict, Any, List
from agents.base import BaseAgent, AgentResult


class CommunicationCoachAgent(BaseAgent):
    """
    Evaluates behavioral and HR interview responses.
    Verifies adherence to the STAR framework (Situation, Task, Action, Result),
    detects filler words, measures clarity, and provides communication coaching.
    """

    def __init__(self):
        super().__init__(
            name="CommunicationCoachAgent",
            role_description="Evaluates behavioral interview responses using the STAR method and communication metrics."
        )
        self.task_type = "COMMUNICATION_COACHING"

    def run_task(self, session_id: str, context: Dict[str, Any]) -> AgentResult:
        response_text = context.get("interview_response", "")
        question_asked = context.get("question_asked", "Behavioral Interview Question")

        resp_lower = response_text.lower()
        word_count = len(response_text.split())

        # 1. STAR Framework Validation
        star_markers = {
            "Situation": [r"\bwhen i was\b", r"\bin my previous\b", r"\bat that time\b", r"\bduring the\b", r"\bcontext\b", r"\bproblem\b"],
            "Task": [r"\bmy goal was\b", r"\bi needed to\b", r"\btasked with\b", r"\bresponsibility was\b", r"\bobjective\b"],
            "Action": [r"\bi implemented\b", r"\bi initiated\b", r"\bi collaborated\b", r"\bi researched\b", r"\bi took the lead\b", r"\bi decided\b"],
            "Result": [r"\bas a result\b", r"\bwhich resulted in\b", r"\bconsequently\b", r"\bthe outcome\b", r"\bimproved by\b", r"\bleading to\b"]
        }

        detected_star = {}
        for stage, patterns in star_markers.items():
            detected_star[stage] = any(re.search(p, resp_lower) for p in patterns)

        star_score = (sum(detected_star.values()) / 4.0) * 100.0

        # 2. Filler Word Detection
        filler_words = ["um", "uh", "like", "basically", "actually", "literally", "sort of", "kind of"]
        detected_fillers = []
        for filler in filler_words:
            matches = re.findall(rf"\b{re.escape(filler)}\b", resp_lower)
            if matches:
                detected_fillers.extend(matches)

        filler_penalty = min(len(detected_fillers) * 8.0, 40.0)
        clarity_score = max(100.0 - filler_penalty, 30.0)

        # 3. Conciseness & Structure
        # Optimal answer length for behavioral response: 80 to 250 words
        if 80 <= word_count <= 250:
            length_score = 100.0
        elif 40 <= word_count < 80:
            length_score = 70.0
        else:
            length_score = 60.0

        # Composite communication score
        composite_score = round(
            (0.50 * star_score) + (0.30 * clarity_score) + (0.20 * length_score), 2
        )

        strengths = []
        growth_areas = []

        present_stages = [k for k, v in detected_star.items() if v]
        missing_stages = [k for k, v in detected_star.items() if not v]

        if len(present_stages) >= 3:
            strengths.append(f"Strong structured communication covering STAR pillars: {', '.join(present_stages)}.")
        if missing_stages:
            growth_areas.append(f"Incorporate missing STAR components: {', '.join(missing_stages)} to complete your narrative.")

        if len(detected_fillers) == 0:
            strengths.append("Crisp articulation with zero conversational fillers detected.")
        else:
            growth_areas.append(f"Reduce reliance on filler phrases ({len(detected_fillers)} instances detected).")

        if word_count < 60:
            growth_areas.append("Response is overly brief; elaborate on specific technical actions and outcomes.")
        elif word_count > 260:
            growth_areas.append("Response is slightly verbose; practice delivering within 90-120 seconds.")
        else:
            strengths.append(f"Ideal response pacing ({word_count} words).")

        summary = (
            f"Communication Score: {composite_score}/100. STAR coverage: {len(present_stages)}/4 stages. "
            f"Clarity index: {round(clarity_score, 1)}%, Pacing score: {round(length_score, 1)}%."
        )

        return AgentResult(
            agent_name=self.name,
            dimension="BEHAVIORAL_COMM",
            score=composite_score,
            strengths=strengths,
            growth_areas=growth_areas,
            detailed_metrics={
                "star_coverage": detected_star,
                "filler_count": len(detected_fillers),
                "word_count": word_count,
                "clarity_index": round(clarity_score, 2)
            },
            summary=summary
        )
