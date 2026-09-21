"""
LangChain Gemini Agent for Day 5 Student Advisory System.
Coordinates the 4 tools dynamically based on user questions.
"""

import os
import sys
from dotenv import load_dotenv

# Ensure UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
try:
    from langchain.agents import create_tool_calling_agent, AgentExecutor
except ImportError:
    from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from database import init_students_db
from tools import get_student_info, get_student_marks, calculator, get_passing_rules

def create_student_agent(api_key: str = None, model_name: str = None):
    """
    Creates and returns a LangChain AgentExecutor powered by Gemini and the 4 student tools.
    """
    # Ensure database exists
    init_students_db()

    gemini_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_key:
        raise ValueError(
            "Gemini API key not found. Set GEMINI_API_KEY environment variable or pass api_key to create_student_agent()."
        )

    # Initialize Gemini LLM with zero temperature for deterministic reasoning
    target_model = model_name or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    llm = ChatGoogleGenerativeAI(
        model=target_model,
        google_api_key=gemini_key
    )

    tools = [get_student_info, get_student_marks, calculator, get_passing_rules]

    system_prompt = (
        "You are an intelligent academic advisor assistant for SJIT University.\n"
        "You have access to specialized tools to look up student info, subject marks, university passing rules, "
        "and perform arithmetic calculations.\n\n"
        "IMPORTANT RULES:\n"
        "1. Decide which tools to invoke dynamically based on what the user asks.\n"
        "2. Do NOT invent student marks, names, or rules; always query the respective tool.\n"
        "3. When asked for total or average marks, fetch the marks using get_student_marks and then compute total and average using the calculator tool.\n"
        "4. When asked if a student passes or is eligible, fetch the marks, check the university rules via get_passing_rules, calculate the average, and verify if each subject is >= 35% and average >= 40%.\n"
        "5. Provide clear, well-structured, professional final answers."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True
    )

    return agent_executor


def ask_agent(agent_executor, question: str):
    """Executes a user question against the agent and prints intermediate steps."""
    print("=" * 75)
    print(f"[User Query]: {question}")
    print("-" * 75)
    
    response = agent_executor.invoke({"input": question})
    
    print("\n[Tools Invoked in Workflow]:")
    steps = response.get("intermediate_steps", [])
    if steps:
        for i, (action, observation) in enumerate(steps, 1):
            print(f"  Step {i}: Tool '{action.tool}' called with args: {action.tool_input}")
            print(f"          Result: {observation}")
    else:
        print("  (No tools required)")
        
    out = response.get("output", "")
    if isinstance(out, list) and len(out) > 0 and isinstance(out[0], dict) and "text" in out[0]:
        out = out[0]["text"]
    print(f"\n[Final Answer]:\n{out}")
    print("=" * 75 + "\n")
    return response


if __name__ == "__main__":
    try:
        agent = create_student_agent()
        print("[OK] Agent initialized successfully!")
        
        # Test Sample
        sample_q = "What is the name and department of student 22CS045?"
        ask_agent(agent, sample_q)
    except Exception as e:
        print(f"Setup Notice: {e}")
        print("Ensure GEMINI_API_KEY is configured in your environment or Google Colab secrets.")
