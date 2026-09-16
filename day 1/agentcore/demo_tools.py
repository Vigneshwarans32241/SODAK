"""A small campus-records tool set, chosen because you can verify it by eye.

Read the docstrings carefully. Each one states WHEN the model should call the
tool, not merely what it does. Compare "Looks up fees" with what is written
below and watch how differently the agent behaves.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .tools import tool, ToolRegistry

# A stand-in for a real records system.
STUDENTS: dict[str, dict[str, Any]] = {
    "21CS045": {"name": "Priya R",     "programme": "B.E. CSE",  "semester": 6,
                "fee_balance": 18500, "attendance_pct": 81},
    "21IT012": {"name": "Karthik S",   "programme": "B.Tech IT", "semester": 6,
                "fee_balance": 0,     "attendance_pct": 68},
    "22EC101": {"name": "Aishwarya M", "programme": "B.E. ECE",  "semester": 4,
                "fee_balance": 42000, "attendance_pct": 92},
}

REMINDERS: list[dict[str, Any]] = []


@tool
def get_student(roll_number: str) -> dict:
    """Look up a student's record: name, programme, semester, fee balance, attendance.

    Call this whenever a roll number is mentioned and you need any detail about
    that student. Never guess a student's details.

    Args:
        roll_number: The roll number, for example 21CS045.
    """
    record = STUDENTS.get(roll_number.strip().upper())
    if record is None:
        # The error NAMES the valid options. "KeyError: 'x'" alone gives the
        # model nothing to correct towards.
        raise KeyError(
            f"No student with roll number {roll_number!r}. "
            f"Known roll numbers: {sorted(STUDENTS)}"
        )
    return {"roll_number": roll_number.strip().upper(), **record}


@tool
def list_students_below_attendance(threshold_pct: int) -> dict:
    """List students whose attendance is below a percentage threshold.

    Call this for questions about attendance shortfall across students, rather
    than looking up each student individually.

    Args:
        threshold_pct: Attendance percentage cut-off, for example 75.
    """
    flagged = [
        {"roll_number": roll, "name": rec["name"], "attendance_pct": rec["attendance_pct"]}
        for roll, rec in STUDENTS.items()
        if rec["attendance_pct"] < threshold_pct
    ]
    return {"threshold_pct": threshold_pct, "count": len(flagged), "students": flagged}


@tool
def create_reminder(title: str, days_from_now: int, note: str = "") -> dict:
    """Create a dated reminder.

    Call this when the user asks to be reminded, to schedule a follow-up, or to
    flag something for later action.

    Args:
        title: Short reminder title.
        days_from_now: How many days ahead the reminder should fire.
        note: Optional additional detail.
    """
    due = date.today() + timedelta(days=int(days_from_now))
    REMINDERS.append({"title": title, "due": due, "note": note})
    # `due` is a date object, not a string. cap_tool_output's default=str
    # handles it - remove that and this tool breaks the run.
    return {"created": True, "title": title, "due": due}


def campus_registry() -> ToolRegistry:
    """A fresh registry with the three campus tools registered."""
    return ToolRegistry([get_student, list_students_below_attendance, create_reminder])


CAMPUS_INSTRUCTIONS = (
    "You are a campus records assistant for SoDak EduTech. "
    "Answer only from tool results - never invent student data. "
    "If a tool returns an error, read it, correct your approach, and try again. "
    "Be concise: two or three sentences unless asked for detail."
)
