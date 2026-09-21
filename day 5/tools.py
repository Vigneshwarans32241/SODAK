"""
LangChain Tools for Day 5 Student Intelligence Agent.
Implements the 4 required tools using LangChain's @tool decorator.
"""

import sqlite3
import os
import re
from typing import Dict, Any
from langchain_core.tools import tool

DB_PATH = os.path.join(os.path.dirname(__file__), "students.db")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

@tool
def get_student_info(student_id: str) -> Dict[str, Any]:
    """
    Retrieves the name and department of a student given their student ID.
    
    Args:
        student_id: The unique identifier of the student (e.g., '22CS045').
        
    Returns:
        A dictionary containing the student's name and department, or an error if not found.
    """
    student_id = student_id.strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, department FROM students WHERE student_id = ?;", (student_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "student_id": student_id,
            "name": row[0],
            "department": row[1]
        }
    return {"error": f"Student with ID '{student_id}' not found in database."}


@tool
def get_student_marks(student_id: str) -> Dict[str, Any]:
    """
    Retrieves individual subject marks (Python, Database, AI, Web) for a student given their student ID.
    
    Args:
        student_id: The unique identifier of the student (e.g., '22CS045').
        
    Returns:
        A dictionary with individual subject scores in Python, Database, AI, and Web.
    """
    student_id = student_id.strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT python, database, ai, web FROM students WHERE student_id = ?;", (student_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "student_id": student_id,
            "python": row[0],
            "database": row[1],
            "ai": row[2],
            "web": row[3]
        }
    return {"error": f"Marks for student ID '{student_id}' not found."}


@tool
def calculator(expression: str) -> str:
    """
    Safely calculates mathematical expressions.
    Use this tool whenever you need to compute total marks, average marks, or percentages.
    
    Args:
        expression: A mathematical expression string, such as '85 + 72 + 90 + 78' or '(85 + 72 + 90 + 78) / 4'.
        
    Returns:
        The evaluated numerical result as a string.
    """
    # Sanitize expression: allow only numbers, operators, spaces, parentheses, decimal points
    clean_expr = expression.strip()
    if not re.match(r"^[0-9+\-*/().\s]+$", clean_expr):
        return "Error: Invalid characters in mathematical expression. Only basic arithmetic operations are allowed."
    
    try:
        # Safe evaluation of basic arithmetic
        result = eval(clean_expr, {"__builtins__": None}, {})
        if isinstance(result, float):
            return f"{result:.2f}"
        return str(result)
    except Exception as e:
        return f"Calculation Error: {str(e)}"


@tool
def get_passing_rules() -> str:
    """
    Retrieves the official university academic passing rules and eligibility criteria.
    Call this tool whenever asked if a student passes, qualifies, or satisfies graduation requirements.
    
    Returns:
        A string containing the university minimum passing criteria.
    """
    return (
        "University Passing Rules:\n"
        "1. Minimum overall average mark: 40%\n"
        "2. Minimum mark in each individual subject: 35%\n"
        "A student must satisfy BOTH rules to be eligible to pass."
    )
