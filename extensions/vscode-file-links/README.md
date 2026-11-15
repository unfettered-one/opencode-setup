# Local VS Code file links

TUI-only OpenCode V2 plugin. Clicking an existing rendered file hyperlink in
normal conversation opens the local VS Code last active window, or launches
VS Code if it is closed. Only existing regular files are supported, using
`code --reuse-window --goto`. Directories never launch VS Code. The executable is fixed to
`/opt/homebrew/bin/code`. No shell command is constructed from a link.

## Installation

Copy this repository's configuration files and folders into `~/.config/opencode/`,
including `extensions/` alongside `cli.json` (or use `$XDG_CONFIG_HOME/opencode/`
when set). The repository's `cli.json` registers the plugin with:

```json
{
  "plugins": ["./extensions/vscode-file-links"]
}
```

Merge that entry into an existing global `cli.json` without replacing unrelated
settings. The relative plugin path resolves from the directory containing
`cli.json`, not the current session directory. There is no project-local CLI
configuration; keeping these files in a checkout alone does not enable the plugin.
Valid CLI config edits hot-reload; no restart is needed. The host resolves
`@opencode/plugin/tui`; there are no runtime dependencies to install. No OpenCode
executable/source changes are needed.

## Supported links

- Local absolute POSIX paths, such as `/path/to/app/src/main.ts`.
- Relative Markdown destinations, such as `[main](src/main.ts)` or
  `[main](../app/src/main.ts:25:3)`, resolved against the **active session's**
  cached `location.directory`, never the TUI startup directory or `process.cwd()`.
- `file:///path/to/app/src/main.ts` (`localhost` authority also accepted).
- `vscode://file/path/to/app/src/main.ts:25:3`.
- File positions `:25`, `:25:3`, `#L25`, `#L25C3`, and `#L25-L30` (range opens
  its first line). Without a position, files open at line 1, column 1.
- Percent-encoded spaces, `#` and `?` in names. Encode filename delimiters as
  `%23`, `%3F`, or `%3A`; positions are split before decoding. A literal `%`
  must be encoded as `%25`.

The target must already exist and be a regular file. Directories, special files,
inaccessible and missing targets show a toast without launching the editor or
deliberately creating a file. Symlinks follow normal local filesystem resolution;
their resolved target must be a regular file. There is still an ordinary
stat/launch race if a target is removed immediately after validation.

Plain text paths and inline code without a hyperlink are **not** auto-detected.
The renderer must already expose an actual link at the clicked cell. Unsupported
schemes, malformed links, protocol-relative URLs, control characters, backslashes,
tilde expansion, arbitrary fragments and query strings are not handled by this
plugin. They retain the original host behavior (which may reject them).

HTTP and HTTPS always retain OpenCode's original browser-opening path, including
its validation. They do not trigger parsing, session lookup, server requests,
filesystem access or editor launch by this plugin. Modified clicks, right clicks,
double-click word selection and actual selection drags also retain host behavior.
Terminal-managed modifier-click hyperlinks remain the terminal's responsibility.

## Locality boundary

Before local filesystem access, each file click checks the current session and
calls `context.client.server.info()`. A missing or mismatched server hostname, a
non-live local server PID, an unavailable session, or a workspace ID on either
available location prevents opening. Unknown locality fails closed with a toast.
The API's public session location omits workspace IDs, so checking that field
alone is deliberately insufficient. A same-host server hostname and live local
PID are conservative locality signals, not cryptographic host attestation; do
not use this plugin with untrusted servers or environments that spoof host/PID
identity. Remote sessions/remote workspace mapping are unsupported.

## Compatibility and adapter

This is **not a dedicated supported file-click hook**; OpenCode exposes none.
Targets OpenCode 2.x. Tested on 2.3.0 with OpenTUI 0.8.4. Other 2.x versions are not yet verified.
The exact version gate has been removed. This small low-level renderer adapter
still disables itself with a toast for incompatible renderer shapes. Behavioral
changes may require adapter updates; it is not update-proof.

The adapter wraps only the renderer instance's `sendMouseEvent`. It intercepts a
plain left `up` marked `isDragging` only when `getSelection()` reports a fresh
`cell` selection and `getLinkAt()` returns a supported file href. Skipping that
one bubble prevents OpenCode's HTTP-only URL handler from receiving the file
href. OpenTUI's original `processSingleMouseEvent` continues and finishes the
selection. Other dispatches call the prior function with the same receiver,
arguments and return value; no event or selection is changed. No read method,
terminal input parser, root tree or OpenCode URL opener is replaced.

Cleanup restores the exact former own property descriptor (or inherited method)
when this plugin still owns the dispatch property. A later wrapper is not
overwritten: retained old adapters become inert. A renderer-local registration
prevents more than one active generation across reloads. Pending asynchronous
opens are cancelled on cleanup before launch; an already spawned editor cannot
be recalled.

Reviewed upstream contracts:

- [OpenCode 2.3.0 clickedLink/plainClick](https://github.com/anomalyco/opencode/blob/v2.3.0/packages/tui/src/ui/link.tsx)
- [OpenCode 2.3.0 plugin context](https://github.com/anomalyco/opencode/blob/v2.3.0/packages/plugin/src/tui/context.ts)
- [OpenCode 2.3.0 client types](https://github.com/anomalyco/opencode/blob/v2.3.0/packages/client/src/promise/generated/types.ts)
- [OpenCode 2.3.0 dependency catalog](https://github.com/anomalyco/opencode/blob/v2.3.0/package.json)

## Verification

From the repository root:

```sh
cd extensions/vscode-file-links
node --test test/*.test.mjs
node --check links.mjs
node --check adapter.mjs
node --check tui.ts
```

Historical validation of the original local extension on 2026-11-15 with Node 26.13.1:

- Local unit suite: **24 passed**, plus syntax checks for `links.mjs`,
  `adapter.mjs` and `tui.ts`. It uses fake renderer dispatch and fake editor
  launch, with temporary real files/directories for existence checks. Directory
  clicks are covered for both rejection without launch and a clear warning toast.
- Native renderer harness: **20 passed** against exact `@opentui/core` **0.8.4**,
  importing the production adapter with real native Markdown/Text renderables.
  It covers file interception, HTTP/HTTPS dispatch, wrapped links, selections,
  modifiers, reload and cleanup. The file-open callback is fake: it does not
  launch an editor or browser or exercise filesystem/locality checks. This
  temporary harness is not included in the repository; these were 24 unit tests
  and 20 separate native tests, not 44 included unit tests.
- Authorized launcher smoke: `openFileLink` opened the original installed
  extension's existing `README.md` through the default `activeLocation`, locality
  check, filesystem stat and `launchCode` chain; `code --reuse-window --goto`
  exited successfully. Session routing/cache were fixtures pointing at that
  installation; server info was live JSON obtained through
  `opencode api get /api/info` using CLI discovery/authentication.

Validation after removing the exact version gate on 2026-11-15: **25 unit tests
passed** in each plugin copy, plus syntax checks. The existing native harness
was rerun against the installed adapter: **20 passed** on OpenTUI **0.8.4** only.
The added regression uses a compatible fake renderer with version metadata
`2.3.1`, `2.4.0`, `2.99.0` and a throwing version getter to check installation,
file interception and cleanup without reading that metadata. This does not
verify actual host compatibility on those versions.

The tests and launcher smoke above do **not** verify an actual installed-TUI click
end to end; that final manual integration check remains unverified. No browser
was launched. Adding the extension to this repository does not change live global
configuration.

## Rollback

To disable after deployment, remove only `./extensions/vscode-file-links` from
the `plugins` array in the global `cli.json` (or disable
`local.vscode-file-links` in the host plugin controls). OpenCode watches its CLI
configuration; `/reload` can force reload. Cleanup removes this plugin's active
interception without replacing wrappers installed by other plugins. No server
restart, executable restoration, dependency uninstall or project change is
needed. Keep or remove this inactive directory as desired.
