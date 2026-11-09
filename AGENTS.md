# CLI Commands Instructions

## Command Execution Rules

- **Non-Interactive Only:** Only execute non-interactive, automated commands.
- **Prohibited Tools:** Never use interactive text user interfaces (TUIs) like `lazygit`, `nano`, `vim`, or `htop`, as they will freeze your execution environment.
- **Available Tools:** You have `jq` (for JSON) and `rg` (`ripgrep` for searching) fully installed and available via Homebrew paths. Use them for fast processing.
- **Paths:** Use macOS style paths (e.g., `/Users/username/...`).

## Package Management & Dependencies

- **Primary Package Manager:** If a required CLI tool or dependency is missing, use Homebrew (`brew install <package>`) to install it.

## Environment Constraints

- **Operating System:** You are running in a WSL (Windows Subsystem for Linux) Ubuntu environment.
- **Shell:** Always use standard `bash` commands. Do NOT use Windows PowerShell or CMD commands.

## Time mcp usage

- use `time` mcp to get teh correct date and time.
- alaways try to retrieve ist time.


## Implementation

- Alaways use `Rivet` as subagent for implementation of suff , no matter how small
- Alaways use `Caliper` as subagent for review of code chanmge(this is not for any review but for code change, MR, PR or commit), no matter how small
- Provide Rivet and Caliper all context that can materially affect architecture, contracts, integration boundaries, compatibility decisions, and acceptance criteria. Include relevant existing extension points and upstream/downstream contracts. Exclude unrelated detail.
- dont tell `Caliper` how to review, just tell iut teh cnages made, and let it do its job , dont steer it to expected verdict.
- Alawasy use `Browser` for any broswer-automation or browser-validation or any task related to running browser. You can deploy them parallely if they are independent tasks and don't interfere with each other. (making sure you provide clear context to browser agnent)

## Behaviour

- You answer precisely and consisely. Always tell your Intent and Evidence beside every descison.
- Don't greet, say happy things just to be polite, save your words for technical/useful conversations.
- Never hide your intention masked with politeness, be on point, hasrh and decisive.
- For UI/frontend browser validation, use the browse MCP through the Browser subagent.

