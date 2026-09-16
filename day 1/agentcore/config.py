"""Configuration: provider selection, environment loading, and the client.

This course runs on a FREE API tier by default (Google Gemini).
Nothing here requires a credit card.

Why this file is shaped like this: the `openai` Python package is not tied to
OpenAI. Point it at a different `base_url` and it speaks to any provider with
an OpenAI-compatible endpoint. So one client library covers Gemini, Groq,
OpenAI and a local Ollama install - and nothing else in agentcore/ changes.

To switch providers, set PROVIDER in your .env file. That is the only edit.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def load_env(path: Path = ENV_FILE) -> dict[str, str]:
    """Read a .env file into os.environ without overwriting real env vars.

    Supported format:
        KEY=value
        KEY = value          # spaces around = are fine
        # comments and blank lines are ignored
        KEY="quoted value"   # surrounding quotes are stripped

    Real environment variables win, so a key exported in your shell overrides
    the file. That is the behaviour you want on a shared lab machine.
    """
    found: dict[str, str] = {}
    if not path.exists():
        return found

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        found[key] = value
        os.environ.setdefault(key, value)

    return found


load_env()


# ==========================================================================
# Provider table
# ==========================================================================
# strict_schema: whether the provider accepts "additionalProperties": false
# inside a tool's parameter schema. OpenAI wants it; some OpenAI-compatible
# layers reject unknown schema keys with a 400. Used by tools.py.
PROVIDERS: dict[str, dict] = {
    "gemini": {
        "label": "Google Gemini (free tier)",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "main": "gemini-2.5-flash",
        "cheap": "gemini-2.5-flash-lite",
        "strict_schema": False,
        "free": True,
        "get_key_at": "https://aistudio.google.com/apikey",
        "notes": "No credit card required. Free-tier prompts may be used by "
                 "Google to improve its models - never send real personal data.",
    },
    "groq": {
        "label": "Groq (free tier)",
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        # Groq retires model names often. Check your console and override
        # MODEL_MAIN / MODEL_CHEAP in .env if these no longer exist.
        "main": "llama-3.3-70b-versatile",
        "cheap": "llama-3.1-8b-instant",
        "strict_schema": False,
        "free": True,
        "get_key_at": "https://console.groq.com/keys",
        "notes": "Very fast, open-weight models only. Tool calling is good but "
                 "a little less reliable than Gemini on complex schemas.",
    },
    "ollama": {
        "label": "Ollama (local, fully offline)",
        "base_url": "http://localhost:11434/v1",
        "key_env": "OLLAMA_API_KEY",     # Ollama ignores it; any string works
        "main": "llama3.1",
        "cheap": "llama3.1",
        "strict_schema": False,
        "free": True,
        "get_key_at": "https://ollama.com/download",
        "notes": "No key, no internet, no rate limits. Needs about 16GB RAM. "
                 "Tool calling is noticeably weaker - expect more retries.",
    },
    "openai": {
        "label": "OpenAI (PAID)",
        "base_url": None,                # use the client's own default
        "key_env": "OPENAI_API_KEY",
        "main": "gpt-4o-mini",           # verify this is still offered
        "cheap": "gpt-4o-mini",
        "strict_schema": True,
        "free": False,
        "get_key_at": "https://platform.openai.com/api-keys",
        "notes": "Pay per token. There is no general free tier. Most reliable "
                 "tool calling of the four.",
    },
}

PROVIDER = os.environ.get("PROVIDER", "gemini").strip().lower()

if PROVIDER not in PROVIDERS:
    sys.exit(
        f"\n  PROVIDER='{PROVIDER}' is not recognised.\n"
        f"  Valid options: {', '.join(PROVIDERS)}\n"
        f"  Set it in {ENV_FILE}\n"
    )

_P = PROVIDERS[PROVIDER]

PROVIDER_LABEL: str = _P["label"]
BASE_URL = _P["base_url"]
STRICT_SCHEMA: bool = _P["strict_schema"]
IS_FREE: bool = _P["free"]
PROVIDER_NOTES: str = _P["notes"]
GET_KEY_AT: str = _P["get_key_at"]


# ==========================================================================
# API key
# ==========================================================================
KEY_ENV: str = _P["key_env"]
API_KEY = os.environ.get(KEY_ENV, "").strip()

if PROVIDER == "ollama" and not API_KEY:
    API_KEY = "ollama-local"             # Ollama needs a value, not a real key

if not API_KEY or API_KEY.lower().startswith(("paste", "your", "replace", "sk-replace")):
    sys.exit(
        "\n"
        f"  {KEY_ENV} is missing or still set to the placeholder.\n"
        f"  Provider: {PROVIDER_LABEL}\n"
        "\n"
        "  Fix it in four steps:\n"
        "    1. Copy .env.example to .env\n"
        f"    2. Get a free key at: {GET_KEY_AT}\n"
        f"    3. Paste it into .env after {KEY_ENV}=\n"
        "    4. Save the file and run this again\n"
        "\n"
        f"  Looking for the file at: {ENV_FILE}\n"
    )


# ==========================================================================
# Models
# ==========================================================================
# MAIN  - the agent doing the actual work
# CHEAP - evaluators, routers, planners. Judging is easier than generating,
#         and on a free tier the cheaper model usually has a HIGHER rate limit.
MODEL_MAIN = os.environ.get("MODEL_MAIN", _P["main"])
MODEL_CHEAP = os.environ.get("MODEL_CHEAP", _P["cheap"])


# ==========================================================================
# Rate limiting
# ==========================================================================
# Free tiers cap requests per minute. Gemini Flash allows roughly 15 per
# minute and one agent run can easily make five. Without backoff, a whole
# class running lab 6 at once produces a wall of 429 errors.
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "4"))
RETRY_BASE_DELAY = float(os.environ.get("RETRY_BASE_DELAY", "2.0"))   # seconds


# ==========================================================================
# Cost estimation
# ==========================================================================
# Zero on a free tier. The trace still prints a cost line so you learn to read
# it, and so the numbers are real if you later move to a paid provider.
PRICE_PER_1K_INPUT = float(os.environ.get("PRICE_PER_1K_INPUT", "0.0"))
PRICE_PER_1K_OUTPUT = float(os.environ.get("PRICE_PER_1K_OUTPUT", "0.0"))
USD_TO_INR = float(os.environ.get("USD_TO_INR", "88.0"))


# ==========================================================================
# Client
# ==========================================================================
from openai import OpenAI  # noqa: E402  (imported after the key check on purpose)

_kwargs: dict = {"api_key": API_KEY}
if BASE_URL:
    _kwargs["base_url"] = BASE_URL

client = OpenAI(**_kwargs)


def masked_key() -> str:
    """A safe-to-print form of the key, for setup checks and logs."""
    return f"{API_KEY[:6]}...{API_KEY[-4:]}" if len(API_KEY) > 12 else "****"


def describe() -> str:
    """One line describing the active configuration."""
    cost = "FREE tier" if IS_FREE else "PAID - every call costs money"
    return f"{PROVIDER_LABEL} | main={MODEL_MAIN} | cheap={MODEL_CHEAP} | {cost}"
