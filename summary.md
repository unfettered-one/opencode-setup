# Compact Summary

## What This Repo Is

This repo is a local-first multi-agent workflow around `workflow/workflow.py`.

The current execution model is:

- `architect` plans
- `developer` implements
- `tester` validates
- `reviewer` approves or rejects
- `conductor` runs before each phase and decides `PROCEED`, `RETRY_SAME`, `RETRY_FRESH`, `ESCALATE`, or `STOP`

Artifacts live under `.ai/` and act as the workflow state, handoff, and audit surface.

## What Is Implemented

### Runner foundations

- Deterministic phase loop with transition validation
- Retry budgets per phase
- Operating modes: `standard`, `high-accuracy`, `hands-off`
- Summary artifact: `.ai/summary.md`
- Hybrid continuity metadata in `.ai/resume.json`
- Blank known JSON recovery for key workflow artifacts

### Observability

- Runner-owned `.ai/activity.log` events for:
  - engine start and stop
  - conductor start and end
  - conductor decisions
  - phase start and end
  - phase heartbeats
  - phase timeouts
- Parent agents now own canonical delegation telemetry
- `librarian` is back to read-only and no longer writes workflow telemetry

### Planning and control

- Architect must delegate research to `librarian`
- Architect performs pre-plan gap analysis
- Conductor is wired into the runner before every phase
- Plan schema is now enforced before downstream phases run

### Plan validation now enforced

`plan.json` is now validated for:

- object shape
- required top-level fields
- `task_breakdown` list shape
- required per-task fields
- non-empty acceptance criteria
- unique task IDs
- valid `depends_on` references
- valid `estimated_complexity` values

## Current Strengths

- Better unattended visibility than before
- Better startup resilience
- Better separation between runner-owned state and agent-owned outputs
- Better planning discipline before Developer starts

## Current Gaps

The system is improved, but not yet a fully trustworthy unattended builder.

### 1. Delegated task control is still prompt-driven

The runner owns phases, but not a true delegated task queue.
Child-task execution, retry behavior, and completion semantics still depend too much on parent-agent obedience.

### 2. Resume is metadata, not full orchestration

`resume.json` records child-session metadata, but the runner does not directly resume subagent work by `session_id`.

### 3. Verification evidence is still soft

Tester and Reviewer rely heavily on markdown summaries and prompt discipline.
There is not yet a strict criterion-to-evidence mapping enforced by the runner.

### 4. No delegated work ledger or wave executor

There is no runner-owned queue for task waves, child-task statuses, or automatic defect-to-task rerouting.

### 5. No rollback/checkpoint model

Bad unattended edits can still accumulate before a later rejection.

### 6. Artifact validation is still incomplete

Some important artifacts recover from blank files, but there is not yet full schema validation and repair across all workflow state.

### 7. Permission hardening is still partial

Prompt contracts are cleaner now, but not all least-privilege expectations are runtime-enforced.

## Recommended Next Build Order

1. Add a runner-owned delegated task ledger and child-task lifecycle model.
2. Add structured verification evidence per acceptance criterion.
3. Add artifact schema validation and repair for all critical `.ai` files.
4. Add checkpoints and rollback before risky implementation waves.
5. Tighten permission boundaries only after the runner owns more of the control plane.

## Practical Status

Current status: strong prototype with real orchestration improvements, but not yet ready to be trusted as a fully autonomous unattended builder.

Best short description:

"The workflow now has a real runner, conductor, activity logging, retry budgets, hybrid continuity metadata, and enforced plan structure, but it still needs runner-owned delegated task control and stronger evidence enforcement before it becomes reliably hands-off."
