import subprocess
import json
import time
import sys
import socket
import signal
from pathlib import Path
from typing import Dict, Any

# =====================================================
# CONFIGURATION
# =====================================================

AI_DIR = Path(".ai")
STATUS_FILE = AI_DIR / "status.json"
CONTEXT_FILE = AI_DIR / "context.md"
TASK_FILE = AI_DIR / "task.md"
DECISIONS_FILE = AI_DIR / "decisions.md"

SRCLIGHT_PORT = 8742

ALLOWED_PHASES = {
    "architect",
    "developer",
    "tester",
    "reviewer",
    "devops"
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
    "history": []
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

OPENCODE_PATH = r"C:\Users\z004xm0r\AppData\Roaming\npm\opencode.CMD"

INDEX_FILE = Path(".srclight") / "index.db"

# Track subprocesses
SRCLIGHT_PROCESS = None

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

def read_status() -> Dict[str, Any]:
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to read status.json: {e}")

    validate_status_structure(data)
    return data


def write_json(path: Path, data: Dict[str, Any]):
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


# =====================================================
# EXECUTION
# =====================================================

def run_phase(phase: str):
    print(f"\n=== Running phase: {phase.upper()} ===")

    message = f"Start the {phase} task. Follow workflow rules strictly."

    result = subprocess.run(
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

    if result.returncode != 0:
        raise RuntimeError(
            f"Phase {phase} exited with code {result.returncode}")


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

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    try:
        ensure_ai_structure()
        prompt_for_task_if_empty()

        ensure_code_index()
        ensure_srclight_server()

        iterations = 0

        while iterations < MAX_ITERATIONS:

            old_status = read_status()

            if old_status.get("completed"):
                print("\nWorkflow completed successfully.")
                return

            phase = old_status["phase"]

            if phase not in ALLOWED_PHASES:
                raise RuntimeError(f"Unknown phase: {phase}")

            run_phase(phase)

            time.sleep(1)

            new_status = read_status()
            validate_transition(old_status, new_status)

            iterations += 1

        raise RuntimeError(
            "Max iterations reached. Possible infinite loop detected.")

    finally:
        cleanup()


if __name__ == "__main__":
    main()
