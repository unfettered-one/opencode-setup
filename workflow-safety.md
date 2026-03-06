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

Rules:

- Never delete these files
- Never overwrite previous sections
- Only append new phase information
- Only update `status.json` during lifecycle commit

---

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
