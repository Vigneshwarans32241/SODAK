"""
Automated Test & Demonstration Script for Day 5 LangChain Assignment.
Executes all required questions and the challenge question.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from database import init_students_db
from tools import get_student_info, get_student_marks, calculator, get_passing_rules

def test_tools_offline():
    """Validates all 4 tools independently without requiring API calls."""
    print("[*] Testing Tool 1: get_student_info('22CS045')...")
    info = get_student_info.invoke({"student_id": "22CS045"})
    assert info["name"] == "Dhanushya"
    assert info["department"] == "Computer Science"
    print("    [PASS] Result:", info)

    print("[*] Testing Tool 2: get_student_marks('22CS047')...")
    marks = get_student_marks.invoke({"student_id": "22CS047"})
    assert marks["python"] == 92
    assert marks["database"] == 88
    assert marks["ai"] == 95
    assert marks["web"] == 90
    print("    [PASS] Result:", marks)

    print("[*] Testing Tool 3: calculator('(85 + 72 + 90 + 78) / 4')...")
    avg = calculator.invoke({"expression": "(85 + 72 + 90 + 78) / 4"})
    assert float(avg) == 81.25
    print("    [PASS] Result:", avg)

    print("[*] Testing Tool 4: get_passing_rules()...")
    rules = get_passing_rules.invoke({})
    assert "40%" in rules and "35%" in rules
    print("    [PASS] Result: University Rules Verified")
    print("\n[SUCCESS] All 4 LangChain Tools passed local verification!\n")

def run_all_questions():
    """Runs all 4 required questions + challenge question through the agent."""
    from agent import create_student_agent, ask_agent

    try:
        agent_executor = create_student_agent()
    except ValueError as e:
        print(f"[Notice] {e}")
        print("Skipping online LLM inference. To test live, export GEMINI_API_KEY='your-key'")
        return

    questions = [
        "What is the name and department of student 22CS045?",
        "What are the marks of 22CS047?",
        "What is the total and average mark of 22CS045?",
        "Is 22CS045 eligible to pass according to the university rules?",
        "I am 22CS045. Tell me my name, department, total marks, average marks, and whether I satisfy the university passing requirements."
    ]

    for q in questions:
        ask_agent(agent_executor, q)

if __name__ == "__main__":
    init_students_db()
    test_tools_offline()
    run_all_questions()
