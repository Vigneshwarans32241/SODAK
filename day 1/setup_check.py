"""Run this FIRST. It verifies your environment before you write any agent code.

    python setup_check.py

Six checks, in order, stopping at the first failure with the fix named.
The last check makes one real API call - free on the default provider.
"""

from __future__ import annotations

import sys
from pathlib import Path

OK, BAD = "  [ok] ", "  [--] "
failures = 0


def check(label: str, condition: bool, fix: str = "") -> bool:
    global failures
    print((OK if condition else BAD) + label)
    if not condition:
        failures += 1
        if fix:
            print(f"         fix: {fix}")
    return condition


print("\nSoDak EduTech - Agentic AI Day 1 - environment check")
print("=" * 60)

# 1 - Python version -------------------------------------------------------
v = sys.version_info
check(f"Python {v.major}.{v.minor}.{v.micro}", v >= (3, 10),
      "install Python 3.10 or newer, then recreate the virtual environment")

# 2 - virtual environment --------------------------------------------------
check("running inside a virtual environment", sys.prefix != sys.base_prefix,
      "activate it:  Windows -> .venv\\Scripts\\activate   "
      "macOS/Linux -> source .venv/bin/activate")

# 3 - openai package -------------------------------------------------------
try:
    import openai
    check(f"openai package {openai.__version__}", True)
except ImportError:
    check("openai package", False, "pip install -r requirements.txt")

# 4 - .env file ------------------------------------------------------------
env_path = Path(__file__).resolve().parent / ".env"
check(".env file exists", env_path.exists(),
      "copy .env.example to .env, then paste your free key into it")

if failures:
    print("\n" + "=" * 60)
    print(f"  {failures} check(s) failed. Fix them and run this again.\n")
    sys.exit(1)

# 5 - provider and key -----------------------------------------------------
# Imported here, not at the top: config.py exits with its own message if the
# key is missing, and we want checks 1-4 to report first.
from agentcore.config import (  # noqa: E402
    client, describe, masked_key, IS_FREE, MODEL_MAIN,
    PROVIDER, PROVIDER_LABEL, PROVIDER_NOTES,
)

check(f"provider: {PROVIDER_LABEL}", True)
check(f"key loaded ({masked_key()})", True)
print(f"         {describe()}")

if not IS_FREE:
    print("\n  WARNING: you are on a PAID provider. Every call costs money.")
    print("  Set PROVIDER=gemini in .env for the free tier.\n")

# 6 - one real API call ----------------------------------------------------
print(f"\n  making one live API call ({'free' if IS_FREE else 'this one costs money'})...")
try:
    reply = client.chat.completions.create(
        model=MODEL_MAIN,
        messages=[{"role": "user", "content": "Reply with exactly: SETUP OK"}],
        max_tokens=20,
    )
    text = (reply.choices[0].message.content or "").strip()
    check(f"model responded: {text[:40]!r}", "SETUP OK" in text.upper(),
          "the call worked but the reply was unexpected - not a problem")
    if reply.usage:
        print(f"         tokens used: {reply.usage.total_tokens}")

except Exception as exc:
    name = type(exc).__name__
    text = str(exc).lower()

    if "429" in text or "rate" in text or "resource_exhausted" in text:
        hint = "rate limited - wait 60 seconds and run this again"
    elif "api key" in text or "unauthenticated" in text or "401" in text:
        hint = f"the key is wrong - get a fresh one and re-paste it into .env"
    elif "not found" in text or "404" in text:
        hint = f"model {MODEL_MAIN!r} is unavailable - set MODEL_MAIN in .env"
    elif "connect" in text or "timeout" in text:
        hint = ("no internet, or a proxy is blocking the call"
                + (" - is Ollama running?" if PROVIDER == "ollama" else ""))
    else:
        hint = str(exc)[:140]

    check(f"live API call ({name})", False, hint)

print("\n" + "=" * 60)
if failures:
    print(f"  {failures} check(s) failed.\n")
    sys.exit(1)

print("  All checks passed. You are ready.")
print(f"\n  Note: {PROVIDER_NOTES}")
print("\n  Next:  python labs/lab1_first_call.py\n")
