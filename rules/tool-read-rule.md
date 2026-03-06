# Tool Discipline Rules

This document defines strict rules for how agents must interact with the
codebase and external systems using available tools.

Agents MUST follow these rules to ensure safe, deterministic, and
efficient operation.

---

## Tool Selection Priority

When performing operations, use the following priority order:

1. Srclight MCP → Code structure, symbol discovery, dependency analysis
2. Filesystem tools → Reading specific files
3. Postman MCP → API requests
4. Playwright MCP → Browser automation / UI validation
5. Memory MCP → Persisting structured knowledge
6. Sequential Thinking MCP → Complex reasoning
7. Time MCP → Timestamp or time-related queries

Agents must always prefer specialized MCP tools over generic filesystem scanning.

---

## Codebase Exploration (Critical Rule)

When analyzing a repository structure you MUST use Srclight MCP tools first.

Examples of correct usage:

- Search for symbols
- Find references to functions
- Locate authentication logic
- Identify module relationships
- Discover where a feature is implemented

Do NOT scan the entire repository manually using glob unless Srclight cannot provide the information.

Incorrect example:

glob("**/*.ts")
read many unrelated files

Correct example:

srclight search auth
srclight search token
srclight symbols AuthContext

Then read only the relevant files.

---

## File Reading

When reading file contents you MUST use the `read` tool.

Do NOT use bash commands such as:

- cat
- less
- more
- head
- tail

Correct:

read("file.py")

Incorrect:

bash("cat file.py")

---

## File Discovery

When searching for files or listing directories use:

- glob
- list

Do NOT use bash commands like:

- ls
- find

Correct:

glob("src/**/*.ts")

Incorrect:

bash("ls src")

---

## Code Search

When searching inside files use:

- grep

Do NOT use shell commands such as:

- grep via bash
- awk
- sed

Correct:

grep("access_token", "src/")

Incorrect:

bash("grep access_token -r src")

---

## Prefer Built-in Tools

Always prefer dedicated tools over bash commands.

Use:

- read
- edit
- write
- glob
- list
- grep

Avoid using bash for operations already supported by tools.

---

## Repository Analysis Guidelines

When investigating a feature or bug:

1. Start with Srclight to locate relevant symbols or modules.
2. Identify the files that implement the functionality.
3. Use read to inspect only those files.
4. Avoid scanning large parts of the repository unnecessarily.

Example workflow:

1. srclight search auth
2. srclight search refresh_token
3. identify relevant files
4. read those files

Do NOT perform full-repository scans unless absolutely necessary.

---

## API Testing

When interacting with backend APIs use Postman MCP.

Do NOT manually construct HTTP requests via bash or other tools.

Correct example:

postman request GET /api/auth/me

---

## UI Testing

When browser automation is required use Playwright MCP.

Example use cases:

- validating login flows
- checking UI rendering
- verifying user interactions

---

## Memory Usage

Use Memory MCP to store reusable knowledge such as:

- architectural decisions
- discovered design patterns
- important system behavior

Avoid storing trivial or temporary information.

---

## Deterministic Behavior Requirement

Agents must behave deterministically and avoid unnecessary exploration.

Guidelines:

- Use Srclight before filesystem scanning
- Read only files required for the task
- Avoid redundant tool calls
- Avoid repeated full-directory scans

---

## Summary

Correct workflow for code analysis:

Srclight → discover structure  
read → inspect specific files  
edit/write → implement changes  
Postman → test APIs  
Playwright → test UI

Never use bash when an appropriate tool already exists.
