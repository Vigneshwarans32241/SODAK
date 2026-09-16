# Agentic AI — Day 1
## Local setup and hands-on programs

**SoDak EduTech** · Agent Foundations & Building an Agent from Scratch

Everything runs on your own machine. No Colab, no cloud notebook.

**This course costs nothing to run.** The default provider is Google's Gemini
free tier — no credit card, no billing account, no trial that expires. The only
third-party package is `openai`, and that package is not tied to OpenAI: point
it at a different base URL and it talks to any provider with an OpenAI-compatible
endpoint. Everything else is the Python standard library.

---

# Part A — Setting up your environment

Do this **once**, before Day 1. Budget 30 minutes. If you get stuck, jump to
[Troubleshooting](#troubleshooting) at the end — the five most common failures
are listed there with fixes.

---

## Step 1 — Check your Python version

You need **Python 3.10 or newer**. Open a terminal and run:

```bash
python --version
```

On macOS and most Linux systems, use `python3` instead of `python`:

```bash
python3 --version
```

**If the command is not found, or the version is below 3.10:**

| System | What to do |
|---|---|
| **Windows** | Download from python.org. **Tick "Add python.exe to PATH"** on the first installer screen — this is the single most common setup failure. |
| **macOS** | `brew install python@3.12` — or download from python.org. |
| **Ubuntu / Debian** | `sudo apt update && sudo apt install python3.12 python3.12-venv` |

> **Windows note:** throughout this guide, wherever you see `python3`, use
> `python` instead. Wherever you see `pip3`, use `pip`.

---

## Step 2 — Get the project folder

Put the `sodak-day1` folder somewhere you can find it — Desktop or Documents is
fine. Avoid paths with spaces or special characters if you can.

Open a terminal **inside that folder**:

- **Windows:** open the folder in File Explorer, click the address bar, type `cmd`, press Enter
- **macOS:** right-click the folder → Services → New Terminal at Folder
- **Linux:** right-click inside the folder → Open in Terminal

Confirm you are in the right place:

```bash
# Windows
dir

# macOS / Linux
ls
```

You should see `agentcore`, `labs`, `exercises`, `requirements.txt`, `setup_check.py`.

---

## Step 3 — Create a virtual environment

A virtual environment is a private box of packages for one project. Without it,
installing something for this course can break a different project on your
machine — and Linux systems will simply refuse the install.

```bash
# Windows
python -m venv .venv

# macOS / Linux
python3 -m venv .venv
```

This creates a `.venv` folder. It takes a few seconds. You will not need to edit
anything inside it.

---

## Step 4 — Activate it

**This is the step people forget.** You must activate the environment **every
time you open a new terminal**.

| System | Command |
|---|---|
| **Windows — Command Prompt** | `.venv\Scripts\activate` |
| **Windows — PowerShell** | `.venv\Scripts\Activate.ps1` |
| **macOS / Linux** | `source .venv/bin/activate` |

You will know it worked because your prompt gains a `(.venv)` prefix:

```
(.venv) C:\Users\priya\sodak-day1>
```

**If PowerShell refuses with a "running scripts is disabled" error**, run this
once, then activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**To leave the environment later:** type `deactivate`.

---

## Step 5 — Install the dependency

With `(.venv)` showing in your prompt:

```bash
pip install -r requirements.txt
```

That installs `openai` and its dependencies. It takes under a minute.

> **Behind a college proxy?** If the install hangs or fails with a connection
> error, ask your lab administrator for the proxy address and use:
> `pip install --proxy http://PROXY:PORT -r requirements.txt`

---

## Step 6 — Get a free API key

We use **Google Gemini's free tier**. It needs no credit card and no billing
account, and it does not expire.

1. Go to **https://aistudio.google.com/apikey**
2. Sign in with any Google account
3. Click **Create API key** — accept the default project if asked
4. Copy the key. It starts with `AIza`

Now put it in the project:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` in any text editor and replace the placeholder:

```
PROVIDER=gemini
GEMINI_API_KEY=AIza...your-real-key-here
```

Save the file.

### Two things to know about the free tier

**Rate limits, not spend limits.** Gemini 2.5 Flash allows roughly **15 requests
per minute**; Flash-Lite allows about **30**. Both have a daily cap in the
low thousands of requests. One agent run can make five calls, so a whole class
running the same lab at the same moment will occasionally hit a limit. The code
handles this — it retries with backoff and prints `[rate limited - waiting 4s]`.
That message is normal, not an error.

**Your prompts may be used to improve Google's models.** That is the trade for a
free tier. The sample data in this project is invented, so nothing sensitive is
at risk — but **do not put real student records, real roll numbers, or anyone's
personal details into these labs.**

### If you prefer a different provider

Change one line in `.env`. Nothing in `agentcore/` needs editing.

| `PROVIDER=` | Cost | Key from | Notes |
|---|---|---|---|
| `gemini` | **Free** | aistudio.google.com/apikey | Default. Best tool calling of the free options. |
| `groq` | **Free** | console.groq.com/keys | Very fast. Open-weight models. Check current model names. |
| `ollama` | **Free, offline** | ollama.com/download | No key, no internet, no limits. Needs ~16GB RAM. Weaker tool calling. |
| `openai` | **Paid** | platform.openai.com/api-keys | No general free tier. Most reliable, but every call is billed. |

**Ollama is the fallback if your lab has no internet.** Install it, run
`ollama pull llama3.1`, set `PROVIDER=ollama`, and no key is needed at all.
Expect the agent to need more retries — smaller models are less precise about
tool arguments, which is itself a useful thing for students to observe.

---

## Step 7 — Verify everything

```bash
python setup_check.py
```

This runs six checks and stops at the first failure, telling you what to fix. The
last check makes one real API call — free on the default provider. Expected output:

```
SoDak EduTech - Agentic AI Day 1 - environment check
============================================================
  [ok] Python 3.12.3
  [ok] running inside a virtual environment
  [ok] openai package 1.51.0
  [ok] .env file exists
  [ok] provider: Google Gemini (free tier)
  [ok] key loaded (AIzaSy...4f2a)
         Google Gemini (free tier) | main=gemini-2.5-flash |
         cheap=gemini-2.5-flash-lite | FREE tier

  making one live API call (free)...
  [ok] model responded: 'SETUP OK'
         tokens used: 24

============================================================
  All checks passed. You are ready.
```

**Do not proceed until every line reads `[ok]`.**

---

## Coming back tomorrow

You only create the environment once. To resume work:

```bash
cd sodak-day1
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
python labs/lab3_agent.py
```

That is the whole routine: navigate, activate, run.

---
---

# Part B — The hands-on programs

Run them **in order**. Each builds on the one before it, and each prints an
explanation of what you just saw.

Run every command from the **project root** (the folder containing `README.md`),
not from inside `labs/`.

| # | Command | Time | What you build |
|---|---|---|---|
| 1 | `python labs/lab1_first_call.py` | 15 min | Your first model call. Roles, tokens, statelessness. |
| 2 | `python labs/lab2_tools.py` | 25 min | Tool schemas, dispatch, the four failure modes. |
| 3 | `python labs/lab3_agent.py` | 30 min | A complete agent loop with three tools. |
| 4 | `python labs/lab4_self_healing.py` | 25 min | The agent reads its own traceback and recovers. |
| 5 | `python labs/lab5_memory.py` | 25 min | Session memory and thread isolation. |
| 6 | `python labs/lab6_patterns.py` | 40 min | Evaluator–Optimizer and Orchestrator–Worker. |

---

## Lab 1 — Your first model call

```bash
python labs/lab1_first_call.py
```

Makes three calls and shows you the token counts side by side. The second half
proves the model has **no memory**: the same follow-up question is asked with and
without history attached, and only one of them can answer it.

**Look for:** the prompt-token difference between the two calls. That gap is why
long conversations cost more.

---

## Lab 2 — Tools

```bash
python labs/lab2_tools.py
```

Three parts. The first prints a JSON schema that **nobody typed** — it was
generated from the function's type hints and docstring. The second runs all four
dispatch outcomes (success, tool raises, wrong arguments, unknown tool). The
third shows what the model actually sends back when it wants a tool.

**Look for:** in part 3, the `arguments` field is a **string**, not a dictionary.
Forgetting `json.loads` on it is the classic Day 1 bug.

---

## Lab 3 — Your first agent

```bash
python labs/lab3_agent.py
```

Three questions of increasing complexity, each printing the answer followed by a
full run trace.

**Look for three things in the traces:**

1. **How many model calls happened.** It is not a fixed number — the loop ends
   when the model stops asking for tools.
2. **Did it use `list_students_below_attendance`,** or three separate
   `get_student` calls? If the latter, the tool *description* is the bug.
3. **Did it invent a comparison tool?** It should not. The model can compare
   three numbers itself. Never build a tool for something the model already does.

---

## Lab 4 — Self-healing

```bash
python labs/lab4_self_healing.py
```

**This is the highlight of Day 1.**

Part 1 shows the naive case: the exception escapes and the run dies. Part 2 sends
the same bad input through the real agent, where dispatch converts the failure
into a structured observation.

**Look for:** in the part 2 trace, a failed tool step followed by a **corrected**
call with the right roll number. Nobody wrote that correction. The model read its
own error and fixed its own mistake.

Then open `agentcore/tools.py` and find the three details that make it work: the
error names the valid options, the traceback is truncated to 800 characters, and
the circuit breaker stops the tool after three consecutive failures.

---

## Lab 5 — Memory

```bash
python labs/lab5_memory.py
```

Two threads. Thread A asks a follow-up using the word "her" and resolves it
correctly. Thread B asks the identical question and cannot, because it has its own
empty history.

**Look for:** the same `Agent` object serves both threads. It holds no state at
all — history is passed in and returned out. That is what lets one agent serve
hundreds of users at once.

The last section demonstrates pair-safe trimming: the first message after
`system` is never a bare `tool`, because an orphaned tool result is rejected by
the API.

---

## Lab 6 — Design patterns

```bash
python labs/lab6_patterns.py
```

The most expensive lab — roughly 10–14 model calls. Part 1 runs an
Evaluator–Optimizer loop against four explicit criteria. Part 2 runs an
Orchestrator–Worker system that invents its own sub-tasks.

**Look for:** in part 2, the printed worker roles. Run it again with a different
goal and **the roles change** — those strings are not in the source code. That is
what separates orchestrator–worker from parallelisation.

Two experiments are printed at the end of part 1. Do both — especially the vague
criteria one, which demonstrates the pattern's most common production failure.

---
---

# Part C — Exercises

The labs are read-and-run. These are write-your-own. Each file has a
`YOUR CODE` block and a checkpoint list.

| # | Command | Time | Task |
|---|---|---|---|
| 1 | `python exercises/ex1_side_effect_tool.py` | 20 min | Write a tool with a side effect and a docstring that controls when it fires. |
| 2 | `python exercises/ex2_session_memory.py` | 20 min | Implement the `chat()` helper with load / run / save. |
| 3 | `python exercises/ex3_circuit_breaker.py` | 15 min | Write a tool that always fails; prove the breaker works. |
| 4 | `python exercises/ex4_evaluator_own_task.py` | 25 min | Evaluator–Optimizer on a task from your own life. |

Exercises 2, 3 and 4 will raise `NotImplementedError` until you complete them.
That is intentional.

**Exercise 1 is the one to spend time on.** The Python is trivial; the docstring
is the actual work. It must make the agent send a notice for *"Inform Priya about
her fee balance"* but **not** for *"What is Priya's fee balance?"* — using the same
code, changing only the words the model reads.

---
---

# Project structure

```
sodak-day1/
├─ README.md                  this file
├─ requirements.txt           one dependency: openai
├─ .env.example               copy to .env and add your key
├─ .gitignore                 keeps .env and .venv out of git
├─ setup_check.py             run this first
│
├─ agentcore/                 the framework you are building
│  ├─ config.py               env loading, client, cost constants
│  ├─ tools.py                @tool decorator + ToolRegistry + dispatch
│  ├─ tracing.py              Step, RunTrace, cost estimation
│  ├─ memory.py               ConversationStore, output capping
│  ├─ agent.py                the execution loop
│  ├─ patterns.py             Evaluator-Optimizer, Orchestrator-Worker
│  └─ demo_tools.py           three campus tools to experiment with
│
├─ labs/                      run these in order
└─ exercises/                 write these yourself
```

Read the modules in this order — each is heavily commented and roughly 150 lines:

`tools.py` → `tracing.py` → `memory.py` → `agent.py` → `patterns.py`

---

# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `'python' is not recognized` | Python not on PATH (Windows) | Reinstall, **tick "Add python.exe to PATH"**. Or use the full path. |
| `No module named 'openai'` | Environment not activated, or install skipped | Activate (`.venv\Scripts\activate`), then `pip install -r requirements.txt` |
| `No module named 'agentcore'` | Running from inside `labs/` | `cd` back to the project root and run `python labs/lab1_first_call.py` |
| `GEMINI_API_KEY is missing` | No `.env`, or placeholder still in it | Copy `.env.example` to `.env` and paste your free key |
| `PROVIDER='x' is not recognised` | Typo in `.env` | Use one of: `gemini`, `groq`, `ollama`, `openai` |
| `running scripts is disabled` | PowerShell execution policy | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |
| `externally-managed-environment` | Installing outside a venv on Linux | Create and activate `.venv` first — do not use `--break-system-packages` |
| `401` / `API key not valid` | Key wrong, or has a stray space | Regenerate at aistudio.google.com/apikey; check for quotes around it |
| `[rate limited - waiting 4s]` | Free-tier requests-per-minute cap | **Normal.** It retries automatically. Wait. |
| `429` after all retries | Whole class calling at once | Wait 60s. Or set `MODEL_MAIN=gemini-2.5-flash-lite` in `.env` (higher limit) |
| `APIConnectionError` | No internet, or a proxy is blocking | Check connectivity; ask the lab admin for proxy settings |
| `404` / model not found | Model renamed or retired | Set `MODEL_MAIN=` in `.env` to a current model name |
| `Connection refused` on Ollama | Ollama not running | Start the Ollama app, then `ollama pull llama3.1` |
| `tool message must follow tool_calls` | Append order wrong | The assistant message goes in **before** any tool messages |
| `not JSON serializable` | Tool returned a date or custom object | `json.dumps(..., default=str)` — see `memory.cap_tool_output` |
| Run never ends | No iteration cap, or a tool always failing | Check `max_iterations`; look at the trace for a repeating tool |

---

# Cost and rate limits

**On the default provider this course costs nothing.** No card, no credits, no
expiry. The trace still prints a cost line so you learn to read it — it will say
`cost: free tier` until you switch to a paid provider.

What you manage instead is **rate limits**. Four habits:

1. **Keep `MODEL_CHEAP` on the lighter model.** Evaluators, planners and routers
   do easy work, and the lighter model usually has a higher request limit.
2. **Never remove `max_iterations`.** A failing tool with no cap will burn your
   daily request quota in about ninety seconds.
3. **Stagger the class.** If thirty students launch Lab 6 simultaneously, some
   will hit limits. Start in two halves a minute apart.
4. **Read the token counts anyway.** They are the habit that matters when a real
   project moves to a paid provider — where the same run costs real money.

If you later move to a paid provider, set `PRICE_PER_1K_INPUT` and
`PRICE_PER_1K_OUTPUT` in `.env` and the trace will compute rupee costs for you.

---

# End of Day 1 — what to submit

- Your completed `exercises/` folder, pushed to your own GitHub repository
- One trace from a successful multi-tool run (Lab 3)
- One trace showing self-healing recovery (Lab 4)
- Your largest run by token count, and one thing you would change to reduce it

**Tomorrow:** the OpenAI Agents SDK. Every feature in it is something in
`agentcore/` that you built by hand today. Keep this folder — you will map them
one to one.

---

*SoDak EduTech · Agentic AI Track · sodakedutech.in*
