# Canonical workflow engine.
import subprocess
import json
import time
import sys
import os
import socket
import signal
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, TypeAlias

JSONDocument: TypeAlias = Dict[str, Any] | List[Any]

# =====================================================
# CONFIGURATION
# =====================================================

AI_DIR = Path(".ai")
STATUS_FILE = AI_DIR / "status.json"
CONTEXT_FILE = AI_DIR / "context.md"
TASK_FILE = AI_DIR / "task.md"
DECISIONS_FILE = AI_DIR / "decisions.md"
PLAN_FILE = AI_DIR / "plan.json"
DEFECTS_FILE = AI_DIR / "defects.json"
LEARNINGS_FILE = AI_DIR / "learnings.md"
ISSUES_FILE = AI_DIR / "issues.md"
VERIFICATION_FILE = AI_DIR / "verification.md"
RESUME_FILE = AI_DIR / "resume.json"
ACTIVITY_LOG = AI_DIR / "activity.log"

SRCLIGHT_PORT = 8742

ALLOWED_PHASES = {
    "architect",
    "developer",
    "tester",
    "reviewer",
    "devops"
}

INTENT_CATEGORIES = {
    "implement",
    "refactor",
    "debug",
    "investigate",
    "verify",
}

PHASE_RETRY_BUDGETS = {
    "architect": 2,
    "developer": 3,
    "tester": 3,
    "reviewer": 2,
    "devops": 2,
}

# Per-phase timeout in seconds. Prevents indefinite hangs when a phase agent
# stalls or a subagent never returns a terminal state.
PHASE_TIMEOUTS = {
    "architect": 900,    # 15 min
    "developer": 2700,   # 45 min
    "tester": 2700,      # 45 min
    "reviewer": 1200,    # 20 min
    "devops": 1200,      # 20 min
}

# Artifact sections that must exist in context.md before a phase may start
PHASE_REQUIRED_CONTEXT_SECTIONS = {
    "tester": "## Developer Phase",
    "reviewer": "## Tester Phase",
}

VALID_TRANSITIONS = {
    "architect": {"developer"},
    "developer": {"tester"},
    "tester": {"developer", "reviewer"},
    "devops": {"reviewer"},
    "reviewer": {"developer", "devops", "tester"},
}

MAX_ITERATIONS = 25

DEFAULT_STATUS = {
    "task_id": "TASK-001",
    "phase": "architect",
    "completed": False,
    "history": [],
    "retry_counts": {}
}

DEFAULT_CONTEXT = """# Task Working Context

## Architect Phase
---

## Developer Phase
---

## Tester Phase
---

## Reviewer Phase
---

## DevOps Phase
---
"""

DEFAULT_TASK = """# TASK-001

"""

DEFAULT_DECISIONS = """# Architectural Decisions Log

"""

DEFAULT_PLAN = {
    "intent": "",
    "scope_summary": "",
    "task_breakdown": [],
    "dependencies": [],
    "risks": [],
    "security_assumptions": [],
    "created_at": ""
}

DEFAULT_DEFECTS: List[Dict[str, Any]] = []

DEFAULT_LEARNINGS = """# Workflow Learnings

## Patterns Discovered
---

## Successful Approaches
---

## Failures & Gotchas
---

## Commands & Tools
---
"""

DEFAULT_ISSUES = """# Active Issues

<!-- Blocker classes: auto-fixable | needs-replan | needs-human | environmental -->
<!-- Severity: CRITICAL | HIGH | MEDIUM | LOW -->

---
"""

DEFAULT_VERIFICATION = """# Verification Results

---
"""

DEFAULT_RESUME = {
    "active_phase": "",
    "active_plan_item": "",
    "retry_counts": {},
    "last_checkpoint": "",
    "delegated_runs": [],
    "stop_reason": "",
    "phase_mode": "fresh",
    "last_result_summary": "",
    "conductor_decision": {
        "verdict": "PROCEED",
        "target_phase": "",
        "reason": "Initial state — no conductor run yet.",
        "decided_at": ""
    }
}

DEFAULT_DELEGATED_RUN = {
    "task_id": "",
    "delegated_agent": "",
    "session_id": "",
    "status": "pending",
    "retry_count": 0,
    "last_error": "",
    "last_result_summary": "",
    "updated_at": ""
}

OPENCODE_PATH = r"C:\Users\z004xm0r\AppData\Roaming\npm\opencode.CMD"
CONDUCTOR_AGENT = "conductor"

INDEX_FILE = Path(".srclight") / "index.db"

SUMMARY_FILE = AI_DIR / "summary.md"
VALID_VERDICTS = {"PROCEED", "RETRY_SAME", "RETRY_FRESH", "ESCALATE", "STOP"}
VALID_TASK_COMPLEXITIES = {"low", "medium", "high"}

# Operating mode: standard | high-accuracy | hands-off
# Set via WORKFLOW_MODE environment variable; defaults to standard.
_raw_mode = os.environ.get("WORKFLOW_MODE", "standard").lower()
WORKFLOW_MODE: str = _raw_mode if _raw_mode in {
    "standard", "high-accuracy", "hands-off"} else "standard"
if _raw_mode not in {"standard", "high-accuracy", "hands-off"}:
    print(
        f"WARNING: Unknown WORKFLOW_MODE '{_raw_mode}', defaulting to 'standard'.")

# Blocker classes injected into agent messages for consistent triage vocabulary
BLOCKER_CLASSES = ("auto-fixable", "needs-replan",
                   "needs-human", "environmental")

# Track subprocesses
SRCLIGHT_PROCESS = None

JSON_DEFAULTS_BY_PATH = {
    STATUS_FILE: DEFAULT_STATUS,
    PLAN_FILE: DEFAULT_PLAN,
    DEFECTS_FILE: DEFAULT_DEFECTS,
    RESUME_FILE: DEFAULT_RESUME,
}

# =====================================================
# CLEANUP
# =====================================================


def cleanup():
    """
    Ensure all subprocesses are terminated safely.
    """
    global SRCLIGHT_PROCESS

    print("\nCleaning up subprocesses...")

    if SRCLIGHT_PROCESS is not None:
        try:
            SRCLIGHT_PROCESS.terminate()
            SRCLIGHT_PROCESS.wait(timeout=5)
            print("Srclight server stopped.")
        except Exception:
            try:
                SRCLIGHT_PROCESS.kill()
                print("Srclight server force killed.")
            except Exception:
                pass


def handle_exit(signum, frame):
    print(f"\nReceived signal {signum}. Shutting down.")
    cleanup()
    sys.exit(0)


# =====================================================
# BOOTSTRAP
# =====================================================

def ensure_ai_structure():
    AI_DIR.mkdir(exist_ok=True)

    if not STATUS_FILE.exists():
        print("Creating default status.json")
        write_json(STATUS_FILE, DEFAULT_STATUS)

    if not CONTEXT_FILE.exists():
        print("Creating default context.md")
        CONTEXT_FILE.write_text(DEFAULT_CONTEXT)

    if not TASK_FILE.exists():
        print("Creating default task.md")
        TASK_FILE.write_text(DEFAULT_TASK)

    if not DECISIONS_FILE.exists():
        print("Creating default decisions.md")
        DECISIONS_FILE.write_text(DEFAULT_DECISIONS)

    if not PLAN_FILE.exists():
        print("Creating default plan.json")
        write_json(PLAN_FILE, DEFAULT_PLAN)

    if not DEFECTS_FILE.exists():
        print("Creating default defects.json")
        write_json(DEFECTS_FILE, DEFAULT_DEFECTS)

    if not LEARNINGS_FILE.exists():
        print("Creating default learnings.md")
        LEARNINGS_FILE.write_text(DEFAULT_LEARNINGS)

    if not ISSUES_FILE.exists():
        print("Creating default issues.md")
        ISSUES_FILE.write_text(DEFAULT_ISSUES)

    if not VERIFICATION_FILE.exists():
        print("Creating default verification.md")
        VERIFICATION_FILE.write_text(DEFAULT_VERIFICATION)

    if not RESUME_FILE.exists():
        print("Creating default resume.json")
        write_json(RESUME_FILE, DEFAULT_RESUME)

    if not ACTIVITY_LOG.exists():
        print("Creating activity.log")
        ACTIVITY_LOG.write_text("", encoding="utf-8")


def append_activity_log(event: str, **fields: str):
    """Append a single structured line to .ai/activity.log.
    This file is runner-owned and should remain append-only.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts = [f"[{timestamp}]", event]
    for key, value in fields.items():
        if value:
            sanitized = str(value).replace("\n", " ").strip()
            parts.append(f"{key}={sanitized}")
    with open(ACTIVITY_LOG, "a", encoding="utf-8") as f:
        f.write(" ".join(parts) + "\n")


def ensure_code_index():
    """
    Ensure Srclight index exists. Build if missing.
    """

    print("\nBuilding Srclight code index...")

    result = subprocess.run(
        ["srclight", "index", "."],
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=False
    )

    if result.returncode != 0:
        raise RuntimeError("Srclight indexing failed")

    print("Srclight index created successfully.\n")


def is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def ensure_srclight_server():
    """
    Ensure Srclight MCP server is running.
    """

    global SRCLIGHT_PROCESS

    if is_port_open(SRCLIGHT_PORT):
        print("Srclight MCP server already running.")
        return

    print("Starting Srclight MCP server...")

    SRCLIGHT_PROCESS = subprocess.Popen(
        ["srclight", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(3)

    if not is_port_open(SRCLIGHT_PORT):
        raise RuntimeError("Failed to start Srclight MCP server")

    print("Srclight MCP server started.")


def prompt_for_task_if_empty():
    content = TASK_FILE.read_text(encoding="utf-8").strip()

    stripped = content.replace("# TASK-001", "").strip()

    if stripped:
        return

    print("\nTask file is empty.")
    choice = input(
        "Do you want to enter task details now? (y/n): ").strip().lower()

    if choice == "y":
        print("\nEnter task description (finish with empty line):\n")
        lines = []

        while True:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)

        task_body = "\n".join(lines)

        if task_body.strip():
            TASK_FILE.write_text(f"# TASK-001\n\n{task_body}\n")
            print("Task updated.\n")
        else:
            print("No task entered. Starting with empty task.\n")

    else:
        print("Starting workflow with empty task.\n")


# =====================================================
# JSON SAFETY
# =====================================================

def read_json(path: Path) -> Any:
    try:
        if not path.exists():
            raise RuntimeError(f"Missing JSON artifact: {path}")

        raw = path.read_text(encoding="utf-8")
        if raw.strip() == "":
            default_value = JSON_DEFAULTS_BY_PATH.get(path)
            if default_value is None:
                raise RuntimeError(f"Failed to read {path}: file is empty")

            recovered = json.loads(json.dumps(default_value))
            write_json(path, recovered)
            append_activity_log(
                "JSON_RECOVERED",
                file=str(path),
                reason="blank-file",
            )
            return recovered

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except RuntimeError:
        raise
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to read {path}: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to read {path}: {e}")


def current_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_status() -> Dict[str, Any]:
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to read status.json: {e}")

    validate_status_structure(data)
    return data


def read_resume() -> Dict[str, Any]:
    data = read_json(RESUME_FILE)
    validate_resume_structure(data)
    return data


def write_json(path: Path, data: JSONDocument):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def validate_status_structure(data: Dict[str, Any]):
    required_keys = {"task_id", "phase", "completed", "history"}

    if not required_keys.issubset(set(data.keys())):
        raise RuntimeError("status.json missing required keys")

    if not isinstance(data["history"], list):
        raise RuntimeError("status.json history must be a list")

    if data["phase"] not in ALLOWED_PHASES:
        raise RuntimeError(f"Invalid phase detected: {data['phase']}")

    # Migrate: add retry_counts if absent (backwards compatibility)
    if "retry_counts" not in data:
        data["retry_counts"] = {}


def validate_resume_structure(data: Dict[str, Any]):
    if not isinstance(data, dict):
        raise RuntimeError("resume.json must be a JSON object")

    for key, value in DEFAULT_RESUME.items():
        if key not in data:
            data[key] = [] if isinstance(value, list) else value

    if not isinstance(data["delegated_runs"], list):
        raise RuntimeError("resume.json delegated_runs must be a list")

    normalized_runs: List[Dict[str, Any]] = []
    for run in data["delegated_runs"]:
        if not isinstance(run, dict):
            continue

        normalized = dict(DEFAULT_DELEGATED_RUN)
        normalized.update(run)
        normalized_runs.append(normalized)

    data["delegated_runs"] = normalized_runs

    decision = data.get("conductor_decision", {})
    if not isinstance(decision, dict):
        decision = {}
    normalized_decision = dict(DEFAULT_RESUME["conductor_decision"])
    normalized_decision.update(decision)
    data["conductor_decision"] = normalized_decision


def validate_plan_structure(data: Dict[str, Any]):
    if not isinstance(data, dict):
        raise RuntimeError("plan.json must be a JSON object")

    for key, value in DEFAULT_PLAN.items():
        if key not in data:
            data[key] = [] if isinstance(value, list) else value

    if not isinstance(data["task_breakdown"], list):
        raise RuntimeError("plan.json task_breakdown must be a list")
    if not isinstance(data["dependencies"], list):
        raise RuntimeError("plan.json dependencies must be a list")
    if not isinstance(data["risks"], list):
        raise RuntimeError("plan.json risks must be a list")
    if not isinstance(data["security_assumptions"], list):
        raise RuntimeError("plan.json security_assumptions must be a list")

    seen_ids = set()
    normalized_tasks: List[Dict[str, Any]] = []
    required_task_keys = {
        "id",
        "title",
        "description",
        "affected_files",
        "depends_on",
        "acceptance_criteria",
        "estimated_complexity",
    }

    for index, task in enumerate(data["task_breakdown"]):
        label = f"plan.json task_breakdown[{index}]"
        if not isinstance(task, dict):
            raise RuntimeError(f"{label} must be an object")

        missing_keys = required_task_keys - set(task.keys())
        if missing_keys:
            missing_list = ", ".join(sorted(missing_keys))
            raise RuntimeError(
                f"{label} missing required keys: {missing_list}")

        task_id = task.get("id", "")
        title = task.get("title", "")
        description = task.get("description", "")
        affected_files = task.get("affected_files")
        depends_on = task.get("depends_on")
        acceptance_criteria = task.get("acceptance_criteria")
        complexity = task.get("estimated_complexity", "")

        if not isinstance(task_id, str) or not task_id.strip():
            raise RuntimeError(f"{label} id must be a non-empty string")
        if task_id in seen_ids:
            raise RuntimeError(
                f"plan.json task ids must be unique; duplicate id '{task_id}'")
        seen_ids.add(task_id)

        if not isinstance(title, str) or not title.strip():
            raise RuntimeError(f"{label} title must be a non-empty string")
        if not isinstance(description, str) or not description.strip():
            raise RuntimeError(
                f"{label} description must be a non-empty string")
        if not isinstance(affected_files, list) or not all(isinstance(item, str) and item.strip() for item in affected_files):
            raise RuntimeError(
                f"{label} affected_files must be a list of non-empty strings")
        if not isinstance(depends_on, list) or not all(isinstance(item, str) and item.strip() for item in depends_on):
            raise RuntimeError(
                f"{label} depends_on must be a list of non-empty strings")
        if not isinstance(acceptance_criteria, list) or not acceptance_criteria:
            raise RuntimeError(
                f"{label} acceptance_criteria must be a non-empty list")
        if not all(isinstance(item, str) and item.strip() for item in acceptance_criteria):
            raise RuntimeError(
                f"{label} acceptance_criteria must contain only non-empty strings")
        if complexity not in VALID_TASK_COMPLEXITIES:
            allowed = ", ".join(sorted(VALID_TASK_COMPLEXITIES))
            raise RuntimeError(
                f"{label} estimated_complexity must be one of: {allowed}")

        normalized_tasks.append(task)

    task_ids = {task["id"] for task in normalized_tasks}
    for task in normalized_tasks:
        unknown_dependencies = [
            item for item in task["depends_on"] if item not in task_ids]
        if unknown_dependencies:
            unknown_list = ", ".join(unknown_dependencies)
            raise RuntimeError(
                f"plan.json task '{task['id']}' depends_on unknown task ids: {unknown_list}"
            )

    data["task_breakdown"] = normalized_tasks


def read_plan() -> Dict[str, Any]:
    data = read_json(PLAN_FILE)
    validate_plan_structure(data)
    return data


def get_latest_delegated_run(resume: Dict[str, Any], phase: str) -> Optional[Dict[str, Any]]:
    candidates = []
    for run in resume.get("delegated_runs", []):
        task_id = run.get("task_id", "")
        if task_id.startswith(f"{phase}:"):
            candidates.append(run)

    if not candidates:
        return None

    return max(candidates, key=lambda item: item.get("updated_at", ""))


def get_resume_mode_for_phase(phase: str, resume: Dict[str, Any]) -> str:
    latest_run = get_latest_delegated_run(resume, phase)
    if latest_run is None:
        return "fresh"

    if latest_run.get("status") in {"blocked", "failed", "retryable"}:
        return "resume-eligible"

    return "fresh"


def prune_stale_delegated_runs(resume: Dict[str, Any], phase: str, status: Dict[str, Any]):
    budget = PHASE_RETRY_BUDGETS.get(phase, 2)
    for run in resume.get("delegated_runs", []):
        task_id = run.get("task_id", "")
        if not task_id.startswith(f"{phase}:"):
            continue

        if run.get("retry_count", 0) >= budget and run.get("status") not in {"completed", "abandoned"}:
            run["status"] = "abandoned"
            run["last_error"] = (
                "Abandoned by workflow runner after exceeding the phase retry budget. "
                "Start a fresh delegated subtask if work continues."
            )
            run["updated_at"] = current_timestamp()

    resume["retry_counts"] = status.get("retry_counts", {})


def build_resume_guidance(phase: str) -> str:
    resume = read_resume()
    latest_run = get_latest_delegated_run(resume, phase)
    conductor_decision = resume.get("conductor_decision", {})
    guidance_lines = [
        f"Resume mode: {resume.get('phase_mode', 'fresh')}.",
        (
            "Conductor verdict: "
            f"{conductor_decision.get('verdict', 'PROCEED')} "
            f"for target_phase={conductor_decision.get('target_phase', phase) or phase}."
        ),
        "Treat the conductor verdict as authoritative for retry behavior.",
        "Use artifact handoff first.",
        "Only reuse child-session continuity for the exact same delegated subtask retry.",
        "If scope, blocker class, or delegated agent changed, start a fresh child session and record why in context.",
    ]

    if latest_run:
        guidance_lines.append(
            "Latest delegated retry candidate: "
            f"task_id={latest_run.get('task_id', '')}, "
            f"agent={latest_run.get('delegated_agent', '')}, "
            f"session_id={latest_run.get('session_id', '') or 'none'}, "
            f"status={latest_run.get('status', '')}, "
            f"retry_count={latest_run.get('retry_count', 0)}."
        )
        if latest_run.get("last_error"):
            guidance_lines.append(
                f"Last delegated error: {latest_run['last_error']}")
        if latest_run.get("last_result_summary"):
            guidance_lines.append(
                f"Last delegated result summary: {latest_run['last_result_summary']}"
            )
    else:
        guidance_lines.append(
            "No delegated retry candidate recorded for this phase. Start fresh delegated work if needed."
        )

    return " ".join(guidance_lines)


# =====================================================
# EXECUTION
# =====================================================

def classify_task_intent() -> str:
    """
    Classify the task intent by scanning task.md for keywords.
    Returns one of: implement, refactor, debug, investigate, verify
    """
    content = TASK_FILE.read_text(encoding="utf-8").lower()

    if any(k in content for k in ["refactor", "restructure", "reorganize", "clean up", "modernize"]):
        return "refactor"
    if any(k in content for k in ["debug", "fix", "bug", "error", "broken", "failing", "crash"]):
        return "debug"
    if any(k in content for k in ["investigate", "analyse", "analyze", "understand", "research", "explore"]):
        return "investigate"
    if any(k in content for k in ["verify", "validate", "test", "check", "confirm"]):
        return "verify"
    return "implement"


def inject_intent_into_context(intent: str):
    """
    Injects the task intent into context.md under a dedicated section
    so all agents can read it without re-classifying.
    """
    context = CONTEXT_FILE.read_text(encoding="utf-8")
    marker = "## Task Intent"
    if marker not in context:
        intent_block = (
            f"\n## Task Intent\n\n"
            f"Classified as: **{intent}**\n\n"
            f"---\n"
        )
        context = context.replace(
            "# Task Working Context\n",
            f"# Task Working Context\n{intent_block}",
            1
        )
        CONTEXT_FILE.write_text(context, encoding="utf-8")
        print(f"Task intent injected: {intent}")


def validate_phase_preconditions(phase: str):
    """
    Enforce that required artifacts exist before a phase may start.
    Prevents phases from running in an uninformed state.
    """
    if phase == "developer":
        plan = read_plan()
        if not plan.get("task_breakdown"):
            raise RuntimeError(
                "PHASE GATE VIOLATION: plan.json has no task_breakdown. "
                "Architect must produce a structured plan before Developer starts."
            )
        if WORKFLOW_MODE == "high-accuracy":
            context = CONTEXT_FILE.read_text(encoding="utf-8")
            if "## Pre-Plan Gap Analysis" not in context:
                raise RuntimeError(
                    "PHASE GATE VIOLATION (high-accuracy mode): '## Pre-Plan Gap Analysis' not found in "
                    "context.md. Architect gap analysis is required before Developer starts."
                )

    if phase in {"tester", "reviewer"}:
        read_plan()

    required_section = PHASE_REQUIRED_CONTEXT_SECTIONS.get(phase)
    if required_section:
        context = CONTEXT_FILE.read_text(encoding="utf-8")
        if required_section not in context:
            raise RuntimeError(
                f"PHASE GATE VIOLATION: '{required_section}' not found in context.md. "
                f"Phase '{phase}' cannot start without this prerequisite section."
            )


def enforce_retry_budget(phase: str, status: Dict[str, Any]):
    """
    Enforce per-phase retry budgets.
    A re-entry (phase already in history) costs one retry credit.
    Raises if the budget is exhausted.
    """
    retry_counts = status.get("retry_counts", {})
    history = status.get("history", [])

    if phase not in history:
        return  # First visit is free

    count = retry_counts.get(phase, 0)
    budget = PHASE_RETRY_BUDGETS.get(phase, 2)

    if count >= budget:
        raise RuntimeError(
            f"RETRY BUDGET EXCEEDED: Phase '{phase}' has been retried {count}/{budget} times. "
            "Inspect .ai/defects.json, .ai/issues.md, and .ai/learnings.md then restart manually."
        )

    retry_counts[phase] = count + 1
    status["retry_counts"] = retry_counts
    write_json(STATUS_FILE, status)
    print(f"Phase '{phase}' re-entry #{count + 1} of {budget}")


def update_resume_checkpoint(phase: str):
    """
    Persist current workflow position so interrupted runs can resume.
    Hybrid continuity rule:
    - top-level phases remain artifact-driven and fresh
    - exact delegated subtask retries may reuse saved child session metadata
    """
    status = read_status()
    resume = read_resume()
    prune_stale_delegated_runs(resume, phase, status)
    resume["active_phase"] = phase
    resume["retry_counts"] = status.get("retry_counts", {})
    resume["last_checkpoint"] = current_timestamp()
    resume["phase_mode"] = get_resume_mode_for_phase(phase, resume)
    resume["last_result_summary"] = (
        f"Phase {phase} ready in {resume['phase_mode']} mode. "
        "Use artifact handoff first. Only reuse delegated child-session state for the exact same retry target."
    )
    write_json(RESUME_FILE, resume)


def run_conductor(phase: str):
    """Run conductor agent as a pre-flight check before every phase.
    Fail-open: if conductor crashes or exits non-zero, log a warning and continue.
    """
    print(f"\n--- Conductor pre-flight for phase: {phase} ---")
    append_activity_log("CONDUCTOR_START", phase=phase, mode=WORKFLOW_MODE)
    blocker_taxonomy = ", ".join(BLOCKER_CLASSES)
    message = (
        f"[WORKFLOW_MODE={WORKFLOW_MODE}] "
        f"Run pre-flight decision check for the '{phase}' phase. "
        f"Read .ai/status.json, .ai/resume.json, .ai/context.md, .ai/issues.md, and .ai/defects.json. "
        f"Blocker classes in use: {blocker_taxonomy}. "
        f"Emit a verdict and write conductor_decision to .ai/resume.json."
    )
    result = subprocess.run(
        [OPENCODE_PATH, "run", "--agent", CONDUCTOR_AGENT, message],
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=False
    )
    if result.returncode != 0:
        append_activity_log(
            "CONDUCTOR_END",
            phase=phase,
            status="failed",
            code=str(result.returncode),
        )
        print(
            f"WARNING: Conductor exited with code {result.returncode}. Falling back to PROCEED.")
        return

    append_activity_log("CONDUCTOR_END", phase=phase, status="completed")


def read_conductor_decision() -> Dict[str, Any]:
    """Read the conductor_decision written by the conductor agent.
    Returns a safe PROCEED default if the field is missing or malformed.
    """
    try:
        resume = read_resume()
        decision = resume.get("conductor_decision", {})
        if not isinstance(decision, dict):
            raise ValueError("conductor_decision is not a dict")
        verdict = decision.get("verdict", "PROCEED")
        if verdict not in VALID_VERDICTS:
            print(
                f"WARNING: Unknown conductor verdict '{verdict}'. Falling back to PROCEED.")
            verdict = "PROCEED"
        target_phase = decision.get("target_phase", "")
        if target_phase and target_phase not in ALLOWED_PHASES:
            print(
                f"WARNING: Unknown conductor target phase '{target_phase}'. Falling back to current phase.")
            target_phase = ""
        return {
            "verdict": verdict,
            "target_phase": target_phase,
            "reason": decision.get("reason", ""),
            "decided_at": decision.get("decided_at", ""),
        }
    except Exception as e:
        print(
            f"WARNING: Could not read conductor decision ({e}). Falling back to PROCEED.")
        return {"verdict": "PROCEED", "target_phase": "", "reason": "Fallback", "decided_at": ""}


def write_return_summary(phase: str, verdict: str, reason: str, iterations: int):
    """Write .ai/summary.md — the 'come back and check' file."""
    try:
        status = read_status()
        resume = read_resume()
        retry_info = ", ".join(
            f"{k}={v}" for k, v in status.get("retry_counts", {}).items()
        ) or "none"
        overall = "COMPLETED" if status.get("completed") else (
            "NEEDS_HUMAN" if verdict == "ESCALATE" else (
                "BLOCKED" if verdict in {
                    "RETRY_SAME", "RETRY_FRESH"} else "RUNNING"
            )
        )
        lines = [
            "# Workflow Return Summary",
            "",
            f"Last updated : {current_timestamp()}",
            f"Workflow mode: {WORKFLOW_MODE}",
            f"Current phase: {phase}",
            f"Iterations   : {iterations}",
            f"Retry counts : {retry_info}",
            f"Overall      : {overall}",
            "",
            "## Conductor Last Verdict",
            "",
            f"Verdict : {verdict}",
            f"Reason  : {reason}",
            "",
            "## Phase History",
            "",
        ]
        for h in status.get("history", []):
            lines.append(f"- {h}")
        lines.append("")
        lines.append("## Last Result Summary")
        lines.append("")
        lines.append(resume.get("last_result_summary", "(none)"))
        lines.append("")
        SUMMARY_FILE.write_text("\n".join(lines), encoding="utf-8")
    except Exception as e:
        print(f"WARNING: Could not write summary.md ({e}).")


def apply_conductor_decision(phase: str, decision: Dict[str, Any]) -> Dict[str, Any]:
    """Apply conductor-owned retry semantics to resume.json and return the execution phase.
    The conductor currently owns retry mode decisions. Cross-phase reroutes are recorded,
    but execution stays on the current phase unless the target matches the active phase.
    """
    resume = read_resume()
    verdict = decision.get("verdict", "PROCEED")
    target_phase = decision.get("target_phase") or phase
    reason = decision.get("reason", "")

    if verdict == "RETRY_SAME":
        resume["phase_mode"] = "resume-eligible"
    else:
        resume["phase_mode"] = "fresh"

    resume["active_phase"] = phase
    resume["last_result_summary"] = f"Conductor verdict {verdict}: {reason}".strip(
    )
    if verdict in {"ESCALATE", "STOP"}:
        resume["stop_reason"] = reason
    elif resume.get("stop_reason") == reason:
        resume["stop_reason"] = ""
    write_json(RESUME_FILE, resume)

    if target_phase != phase:
        print(
            "WARNING: Conductor requested cross-phase reroute "
            f"{phase} -> {target_phase}, but runner currently applies conductor authority "
            "only to retry mode within the active phase."
        )
        target_phase = phase

    return {"phase_to_run": target_phase, "verdict": verdict, "reason": reason}


def run_phase(phase: str):
    print(f"\n=== Running phase: {phase.upper()} ===")
    append_activity_log("PHASE_START", phase=phase, mode=WORKFLOW_MODE)

    # Read intent from context.md so the agent message is pre-scoped
    intent = "unknown"
    context = CONTEXT_FILE.read_text(encoding="utf-8")
    for line in context.splitlines():
        if "Classified as:" in line:
            intent = line.replace("Classified as:", "").strip().strip("**")
            break

    hands_off_hint = (
        " You are running in hands-off mode: do not stop to ask clarifying questions. "
        f"Record blockers in .ai/issues.md with a blocker class ({', '.join(BLOCKER_CLASSES)}) and continue or stop cleanly."
        if WORKFLOW_MODE == "hands-off" else ""
    )
    message = (
        f"[WORKFLOW_MODE={WORKFLOW_MODE}] "
        f"Start the {phase} task (intent: {intent}). "
        f"Read .ai/plan.json for the implementation plan and "
        f".ai/learnings.md for prior workflow knowledge and .ai/resume.json for hybrid continuity metadata. "
        f"{build_resume_guidance(phase)}"
        f"{hands_off_hint} "
        f"Follow workflow rules strictly."
    )

    timeout_secs = PHASE_TIMEOUTS.get(phase, 1800)
    heartbeat_interval = 30
    process = subprocess.Popen(
        [
            OPENCODE_PATH,
            "run",
            "--agent",
            phase,
            message
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=False
    )

    started_at = time.monotonic()
    next_heartbeat = started_at + heartbeat_interval
    while True:
        result_code = process.poll()
        now = time.monotonic()

        if result_code is not None:
            break

        if now >= next_heartbeat:
            elapsed = int(now - started_at)
            append_activity_log(
                "PHASE_HEARTBEAT",
                phase=phase,
                elapsed_seconds=str(elapsed),
                mode=WORKFLOW_MODE,
            )
            next_heartbeat += heartbeat_interval

        if now - started_at > timeout_secs:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            timeout_msg = (
                f"Phase {phase} exceeded {timeout_secs}s timeout and was killed. "
                f"This is typically caused by a subagent stalling or waiting for input. "
                f"Check .ai/issues.md for blocker details."
            )
            print(f"\n[TIMEOUT] {timeout_msg}", file=sys.stderr)
            append_activity_log(
                "PHASE_TIMEOUT",
                phase=phase,
                limit_seconds=str(timeout_secs),
            )
            # Append a blocker entry so the next run can diagnose the cause
            if ISSUES_FILE.exists():
                existing = ISSUES_FILE.read_text(encoding="utf-8")
            else:
                existing = ""
            ISSUES_FILE.write_text(
                existing +
                f"\n## Phase Timeout\n"
                f"- Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
                f"- Phase: {phase}\n"
                f"- Limit: {timeout_secs}s\n"
                f"- Action: Runner killed the process. Re-run after resolving the stall.\n",
                encoding="utf-8"
            )
            raise RuntimeError(timeout_msg)

        time.sleep(1)

    append_activity_log(
        "PHASE_END",
        phase=phase,
        status="completed" if result_code == 0 else "failed",
        code=str(result_code),
    )

    if result_code != 0:
        raise RuntimeError(
            f"Phase {phase} exited with code {result_code}")


# =====================================================
# STATE MACHINE VALIDATION
# =====================================================

def validate_transition(old_status: Dict[str, Any], new_status: Dict[str, Any]):
    old_phase = old_status["phase"]
    new_phase = new_status["phase"]

    if new_status.get("completed"):
        if old_phase != "reviewer":
            raise RuntimeError("Only reviewer can mark workflow as completed.")
        return

    if new_phase == old_phase:
        raise RuntimeError(
            f"Lifecycle violation: phase did not advance from {old_phase}")

    if new_phase not in VALID_TRANSITIONS.get(old_phase, set()):
        raise RuntimeError(
            f"Invalid phase transition: {old_phase} → {new_phase}")

    if old_phase not in new_status["history"]:
        raise RuntimeError(
            f"Lifecycle violation: '{old_phase}' not appended to history")


# =====================================================
# MAIN ORCHESTRATOR
# =====================================================

def main():
    print("=== AI WORKFLOW ENGINE STARTED ===")
    append_activity_log("ENGINE_START", mode=WORKFLOW_MODE)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    try:
        ensure_ai_structure()
        prompt_for_task_if_empty()

        ensure_code_index()
        ensure_srclight_server()

        # Classify and inject task intent once before the first phase runs
        intent = classify_task_intent()
        inject_intent_into_context(intent)
        print(f"Task intent: {intent}")
        print(f"Workflow mode: {WORKFLOW_MODE}")

        iterations = 0

        while iterations < MAX_ITERATIONS:

            old_status = read_status()

            if old_status.get("completed"):
                print("\nWorkflow completed successfully.")
                return

            phase = old_status["phase"]

            if phase not in ALLOWED_PHASES:
                raise RuntimeError(f"Unknown phase: {phase}")

            # Enforce retry budgets before re-entering any phase
            enforce_retry_budget(phase, old_status)

            # Gate: ensure required artifacts exist before phase runs
            validate_phase_preconditions(phase)

            # Save resume checkpoint so interrupted runs can continue
            update_resume_checkpoint(phase)

            # Conductor pre-flight: read state and emit routing verdict
            run_conductor(phase)
            decision = read_conductor_decision()
            applied_decision = apply_conductor_decision(phase, decision)
            verdict = applied_decision["verdict"]
            reason = applied_decision["reason"]
            phase_to_run = applied_decision["phase_to_run"]
            print(f"Conductor verdict: {verdict} — {reason}")
            append_activity_log(
                "CONDUCTOR_DECISION",
                phase=phase,
                verdict=verdict,
                target_phase=phase_to_run,
                reason=reason,
            )

            write_return_summary(phase, verdict, reason, iterations)

            if verdict == "STOP":
                print("Conductor: STOP verdict — workflow marked complete.")
                return
            elif verdict == "ESCALATE":
                raise RuntimeError(f"Conductor escalation: {reason}")
            # PROCEED, RETRY_SAME, RETRY_FRESH all fall through to run_phase
            # apply_conductor_decision has already set the authoritative phase_mode in resume.json.

            run_phase(phase_to_run)

            time.sleep(1)

            new_status = read_status()
            validate_transition(old_status, new_status)

            iterations += 1

        raise RuntimeError(
            "Max iterations reached. Possible infinite loop detected.")

    finally:
        append_activity_log("ENGINE_STOP")
        write_return_summary(
            read_status().get("phase", "unknown"),
            "STOP",
            "Workflow engine exited.",
            iterations if 'iterations' in dir() else 0
        )
        cleanup()


if __name__ == "__main__":
    main()
