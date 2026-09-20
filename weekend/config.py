"""
System Configuration & Environment Loader
Autonomous Multi-Agent Placement Readiness Platform
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root if it exists
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/placement_platform"
)

APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# AI Provider configurations (Optional fallback to intelligent local evaluators)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/"
)
