# Workflow Safety Rules

These rules enforce stable tool usage and prevent infinite loops.

---

## Avoid Repeated File Reads

Do not repeatedly read the same file without new reasoning.

Examples of incorrect behavior:

- reading `.ai/status.json` multiple times in a row
- reading `.ai/context.md` repeatedly
- re-reading a file immediately after reading it unless required for verification

Correct behavior:

1. Read the file once
2. Extract required information
3. Continue reasoning using the extracted information

Only re-read a file if:

- it was modified
- new information must be confirmed

---

## Status File Handling

`.ai/status.json` should normally be read **once at the beginning of the phase**.

Re-reading the status file should only happen when:

- performing lifecycle commit
- verifying workflow state

Repeated reads are unnecessary and should be avoided.

---

## Context File Handling

`.ai/context.md` may be read to inspect previous phase output.

However:

- Do not repeatedly read the file.
- Extract the required section once.
- Continue reasoning.

---

## Prefer Structured Tools Over Bash

Use structured tools whenever possible:

- `read` → file contents
- `glob` / `list` → file discovery
- `grep` → search inside files

Do NOT use bash commands such as:

- `cat`
- `ls`
- `find`

These operations must use built-in tools instead.

---

## Bash Usage Restrictions

The `bash` tool should only be used for:

- running test commands
- executing build tools
- interacting with running services

Bash must NOT be used for:

- reading files
- listing directories
- searching files

---

## Workflow File Safety

The following files are controlled by the workflow system:

- `.ai/status.json`
- `.ai/context.md`
- `.ai/decisions.md`
- `.ai/plan.json`
- `.ai/defects.json`
- `.ai/learnings.md`
- `.ai/issues.md`
- `.ai/verification.md`
- `.ai/resume.json`

Rules:

- Never delete these files
- Never overwrite previous sections
- `.ai/task.md` is read-only for all agents — only the human modifies it
- `.ai/resume.json` runner-owned fields (`conductor_decision`, `mode`, top-level metadata) must not be edited by agents
- Phase agents (developer) **may** upsert entries in the `delegated_runs[]` array to persist coder and pretester run records — this is the only permitted write to `resume.json` by an agent

---

## Workflow Artifact Ownership

| Artifact              | Written by                                                                    | Read by                     | Rules                                                                                                         |
| --------------------- | ----------------------------------------------------------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `.ai/status.json`     | All phases (lifecycle commit only)                                            | All phases, runner          | Never skip the lifecycle commit                                                                               |
| `.ai/task.md`         | Human only                                                                    | Architect                   | Read-only for all agents                                                                                      |
| `.ai/context.md`      | All phases (append-only)                                                      | All phases                  | Never overwrite or delete existing sections                                                                   |
| `.ai/plan.json`       | Architect                                                                     | Developer, Tester, Reviewer | Written once; Developer sets task status only                                                                 |
| `.ai/decisions.md`    | Architect, Reviewer (append)                                                  | Reviewer                    | Architectural decisions log                                                                                   |
| `.ai/defects.json`    | Tester (append)                                                               | Developer, Reviewer         | Developer updates status to "resolved" only                                                                   |
| `.ai/learnings.md`    | All phases (append)                                                           | All phases                  | Accumulate knowledge; never delete entries                                                                    |
| `.ai/issues.md`       | Developer, Tester (append)                                                    | All phases                  | Open blockers and known limitations                                                                           |
| `.ai/verification.md` | Tester (append)                                                               | Reviewer                    | Full validation evidence log                                                                                  |
| `.ai/resume.json`     | Workflow runner (top-level fields); Developer (delegated_runs[] upserts only) | Workflow runner, all phases | Agents must not modify conductor_decision or runner-owned fields; only delegated_runs[] upserts are permitted |
| `.ai/activity.log`    | All phases (append-only)                                                      | Human observer              | Append-only log for live delegation visibility; never delete or overwrite                                     |

---

## Escalation Protocol

### Tester → Developer

**Trigger**: Any test failure, any open defect (any severity)
**Required**:

1. Write structured defect(s) to `.ai/defects.json`
2. Append `## Tester Phase: DEFECT REPORT` summary to `.ai/context.md`
3. Set `phase` to `"developer"`, append `"tester"` to `history`

### Reviewer → Developer

**Trigger**: Quality gates not met, plan adherence gaps, unresolved defects, or missing evidence
**Required**:

1. Append `## Review Feedback` to `.ai/context.md` with cited violations and rejection reasons
2. Set `phase` to `"developer"`, append `"reviewer"` to `history`

### Developer → Architect (Re-plan)

**Trigger**: 2 or more plan tasks are unbuildable, scope is fundamentally wrong, or critical assumptions were wrong
**Required**:

1. Append `## Re-plan Request` to `.ai/context.md` explaining exactly what is wrong
2. Set `phase` to `"architect"`, append `"developer"` to `history`

### Emergency Stop (Manual Rescue)

**Trigger**: Any phase exceeds its retry budget (enforced by the workflow runner)
**Required for human**:

1. Inspect `.ai/defects.json` for unresolved defects
2. Inspect `.ai/issues.md` for root-cause blockers
3. Inspect `.ai/learnings.md` for patterns that failed
4. Make a manual decision: edit `.ai/status.json` to re-run or abandon the task

---

## Phase Retry Budgets

These are enforced automatically by the workflow runner:

| Phase     | Max re-entries |
| --------- | -------------- |
| architect | 2              |
| developer | 3              |
| tester    | 3              |
| reviewer  | 2              |
| devops    | 2              |

Exceeding the budget raises an error and stops the workflow. This prevents silent infinite loops.

## Hybrid Session Continuity

The workflow uses a hybrid continuity model:

- Top-level phases remain artifact-driven and should not rely on one shared long-lived primary-agent session.
- `.ai/resume.json` may contain delegated child-session metadata for retrying the exact same subtask.
- A saved child session may only be reused when task scope, delegated agent, and retry target are unchanged.
- If scope changes, blocker class changes, or the prior delegated thread has gone stale, a fresh child session must be started.
- Retry-budget exhaustion may cause the workflow runner to mark a delegated run as `abandoned` in `.ai/resume.json`.

- Only append new phase information
- Only update `status.json` during lifecycle commit

Valid workflow phases are:

- `architect`
- `developer`
- `tester`
- `reviewer`
- `devops`

The value `"completed"` is **NOT a phase**.

## Workflow completion is controlled using the boolean flag:

completed: true

## Tool Discipline

Always prefer built-in tools over shell commands.

Correct tools:

- read
- write
- edit
- glob
- list
- grep

Avoid using bash for tasks already supported by tools.

## Workflow Completion Authority

Only the **Reviewer phase** may mark the workflow as completed.

Rules:

1. `completed: true` may ONLY be written by the Reviewer phase.
2. The `phase` field MUST remain `"reviewer"` when `completed` is set to true.
3. The `"completed"` value is a **boolean flag**, not a phase.

orrect example:

{
"task_id": "TASK-001",
"phase": "reviewer",
"completed": true,
"history": [
"architect",
"developer",
"tester",
"reviewer"
]
}

Incorrect examples:

Tester marking workflow complete:

{
"phase": "completed",
"completed": true
}

Developer marking workflow complete:

{
"phase": "developer",
"completed": true
}

Changing phase to `"completed"` is **not allowed**.

Any attempt to mark completion outside the Reviewer phase is a **workflow violation**.
