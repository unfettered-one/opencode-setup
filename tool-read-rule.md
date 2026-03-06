# Tool Discipline Rules

## File Reading

When reading file contents you MUST use the `read` tool.

Do NOT use bash commands such as:

- cat
- less
- more
- head
- tail

Example:

Correct:
read("file.py")

Incorrect:
bash("cat file.py")

---

## File Discovery

When searching for files or listing directories use:

- `glob`
- `list`

Do NOT use bash commands like:

- ls
- find

---

## Code Search

When searching inside files use:

- `grep`

Do NOT use bash commands like:

- grep via shell
- awk
- sed

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
