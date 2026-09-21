"""
SQLite Database Initialization for Day 5 LangChain Agent Assignment.
Creates students.db with required student records and subject marks.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "students.db")

def init_students_db(db_path: str = DB_PATH) -> str:
    """Initializes students.db with table schema and seed data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        python INTEGER NOT NULL,
        database INTEGER NOT NULL,
        ai INTEGER NOT NULL,
        web INTEGER NOT NULL
    );
    """)

    students_data = [
        ("22CS045", "Dhanushya", "Computer Science", 85, 72, 90, 78),
        ("22CS046", "Rahul", "Computer Science", 65, 70, 68, 72),
        ("22CS047", "Priya", "Information Technology", 92, 88, 95, 90),
        ("22CS048", "Arun", "Information Technology", 55, 60, 58, 62),
        ("22CS049", "Meena", "Computer Science", 78, 85, 80, 88)
    ]

    cursor.executemany("""
    INSERT OR REPLACE INTO students (student_id, name, department, python, database, ai, web)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, students_data)

    conn.commit()
    conn.close()
    return db_path

if __name__ == "__main__":
    path = init_students_db()
    print(f"[OK] Database successfully initialized at: {path}")
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM students;")
    rows = cur.fetchall()
    print(f"[OK] Total students inserted: {len(rows)}")
    for r in rows:
        print("  ", r)
    conn.close()
