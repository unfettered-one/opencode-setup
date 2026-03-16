# opencode-setup

This repository uses `workflow/workflow.py` as the canonical workflow runner.

## Workflow model

- Top-level phases run sequentially: `architect` -> `developer` -> `tester` -> `reviewer` with the existing loop-back rules.
- Each phase agent may delegate work to subagents through OpenCode.
- If OpenCode supports background subagent execution, those subagents may run in parallel inside the active phase.
- The Python workflow runner does not run multiple top-level phases in parallel.
- Phase boundaries stay artifact-driven and fresh. The runner now supports a hybrid continuity model where only an exact delegated subtask retry may reuse saved child-session metadata from `.ai/resume.json`.

## Startup sequence

The workflow runner preserves this startup order:

1. `ensure_ai_structure()`
2. `prompt_for_task_if_empty()`
3. `ensure_code_index()`
4. `ensure_srclight_server()`

This ensures `.ai` files exist, task input is optionally collected, the Srclight index is available, and the Srclight MCP server is running before phase execution.

## Active runtime

Run the workflow with `python workflow/workflow.py`.

The runner validates `.ai/status.json` before and after every phase and keeps the existing Srclight startup and shutdown behavior.

## Hybrid continuity

- `.ai/resume.json` remains workflow-runner owned.
- The runner records top-level phase checkpoints plus delegated-run continuity metadata.
- Top-level phases do not share one long-lived primary-agent session.
- A saved child session is only eligible for reuse when the retry target is the exact same delegated subtask.
- If scope, blocker class, or delegated agent changes, a fresh child session should be used instead.
