import assert from "node:assert/strict"
import { EventEmitter } from "node:events"
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import test from "node:test"
import { activeLocation, assertLocalServer, CODE_EXECUTABLE, launchCode, openFileLink, parseFileLink } from "../links.mjs"

const context = (directory = "/active/session") => ({
  location: { directory: "/startup/not-active" },
  ui: { router: { current: () => ({ type: "session", sessionID: "active" }) } },
  data: { session: { get: (id) => { assert.equal(id, "active"); return { location: { directory } } } } },
})

test("supported file targets and positions", () => {
  for (const [href, filename, line, column] of [
    ["src/main.ts", "src/main.ts"],
    ["./src/main.ts:25:3", "./src/main.ts", 25, 3],
    ["main.ts:25", "main.ts", 25],
    ["../main.ts#L25C3", "../main.ts", 25, 3],
    ["src/main.ts#L25-L30", "src/main.ts", 25],
    ["/absolute/main.ts#L25", "/absolute/main.ts", 25],
    ["file:///absolute/main.ts:25:3", "/absolute/main.ts", 25, 3],
    ["file://localhost/absolute/main.ts", "/absolute/main.ts"],
    ["vscode://file/absolute/main.ts:25:3", "/absolute/main.ts", 25, 3],
    ["vscode://file/absolute/main.ts#L25C3", "/absolute/main.ts", 25, 3],
    ["/a%20b/file%23name%3F.ts#L2", "/a b/file#name?.ts", 2],
    ["file:///a%23b%3Fc%2520.ts", "/a#b?c%20.ts"],
    ["vscode://file/a%23b%3Fc.ts", "/a#b?c.ts"],
    ["/folder/", "/folder/"],
  ]) assert.deepEqual(parseFileLink(href), { filename, line, column }, href)
})

test("web, unsupported, nonlocal and malformed targets are not file links", () => {
  for (const href of [
    "http://example.test/a.ts:25", "HTTPS://example.test/a#L25", "http:\u0000bad",
    "command:workbench.action.files.openFile", "javascript:alert(1)", "data:text/plain,x",
    "vscode://extension/launch", "vscode-insiders://file/a", "vscode://file@evil/a",
    "vscode://file:10/a", "file://remote/a", "file:relative", "file:/absolute",
    "//example.test/a", "\\\\server\\file", "/a\\b", " /a", "/a ", "", null,
    "/a\u0000b", "/a\nb", "/a%00b", "/a%C2%85b", "/a%ZZ", "/a%E0%A4", "/a%",
    "/a#section", "/a?query", "/a:0", "/a:1:0", "/a#L0", "/a#L5-L2",
    "/a#L9007199254740992", "/a:2#L3", "file:///a%2fb", "vscode://file/a%5cb",
    "%2F%2Fhost/a", "~/a", "~", "#L25", "/a#L2#L3",
  ]) assert.equal(parseFileLink(href), undefined, String(href))
})

test("relative paths resolve against the active session, not startup or cwd", async () => {
  const calls = []
  await openFileLink(context(), parseFileLink("../file.ts:25:3"), {
    checkLocal: async () => calls.push("local"),
    readStat: async (filename) => { calls.push(filename); return { isFile: () => true, isDirectory: () => false } },
    launch: async (args) => calls.push(args),
  })
  assert.deepEqual(calls, ["local", "/active/file.ts", ["--reuse-window", "--goto", "/active/file.ts:25:3"]])
})

test("existing real files use goto; directories and missing targets never launch", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "vscode-file-links-"))
  try {
    await writeFile(path.join(root, "file#?.ts"), "test")
    await mkdir(path.join(root, "directory"))
    const launches = []
    const options = { checkLocal: async () => {}, launch: async (args) => launches.push(args) }
    await openFileLink(context(root), parseFileLink("file%23%3F.ts"), options)
    for (const href of ["directory", "directory/", "directory#L10"])
      await assert.rejects(openFileLink(context(root), parseFileLink(href), options), /not a regular file; directories/)
    await assert.rejects(openFileLink(context(root), parseFileLink("missing.ts"), options), /does not exist/)
    assert.deepEqual(launches, [
      ["--reuse-window", "--goto", `${root}/file#?.ts:1:1`],
    ])
  } finally {
    await rm(root, { recursive: true, force: true })
  }
})

test("unknown, remote workspace and invalid session directories never reach filesystem or launcher", async () => {
  const contexts = [context("relative"), context("//remote/a"), context("/a\u0000b")]
  const remote = context()
  remote.location.workspaceID = "wrk_remote"
  contexts.push(remote)
  const remoteSession = context()
  remoteSession.data.session.get = () => ({ location: { directory: "/a", workspaceID: "wrk_remote" } })
  contexts.push(remoteSession)
  const home = context()
  home.ui.router.current = () => ({ type: "home" })
  contexts.push(home)
  const missing = context()
  missing.data.session.get = () => undefined
  contexts.push(missing)
  for (const value of contexts) {
    await assert.rejects(openFileLink(value, parseFileLink("/file.ts"), {
      checkLocal: () => assert.fail("locality check must follow location check"),
      readStat: () => assert.fail("no stat"), launch: () => assert.fail("no launch"),
    }))
  }
})

test("server locality requires exact hostname and live local PID", async () => {
  const make = (info) => ({ client: { server: { info: async () => info } } })
  let checked
  await assertLocalServer(make({ hostname: "local", pid: 123 }), "local", (pid) => { checked = pid })
  assert.equal(checked, 123)
  for (const info of [{}, { hostname: "remote", pid: 123 }, { hostname: "local", pid: 0 }, { hostname: "local", pid: 1.5 }])
    await assert.rejects(assertLocalServer(make(info), "local", () => assert.fail("no PID probe")), /cannot be verified/)
  await assert.rejects(assertLocalServer(make({ hostname: "local", pid: 123 }), "local", () => { throw Error("ESRCH") }), /not local/)
})

test("nonlocal server and special targets never launch", async () => {
  await assert.rejects(openFileLink(context(), parseFileLink("file.ts"), {
    checkLocal: async () => { throw Error("nonlocal") },
    readStat: () => assert.fail("no stat on remote"), launch: () => assert.fail("no launch"),
  }), /nonlocal/)
  await assert.rejects(openFileLink(context(), parseFileLink("pipe"), {
    checkLocal: async () => {},
    readStat: async () => ({ isFile: () => false, isDirectory: () => false }),
    launch: () => assert.fail("no launch"),
  }), /not a regular/)
})

test("deactivation during locality or stat cancels pending launches", async () => {
  for (const boundary of ["local", "stat"]) {
    let active = true
    await openFileLink(context(), parseFileLink("file.ts"), {
      checkLocal: async () => { if (boundary === "local") active = false },
      readStat: async () => { active = false; return { isFile: () => true, isDirectory: () => false } },
      isActive: () => active,
      launch: () => assert.fail("no launch after cleanup"),
    })
  }
})

test("safe launcher uses fixed executable, argument array, no shell and reports failures", async () => {
  const args = ["--reuse-window", "--goto", "/a/$(touch nope);.ts:1:1"]
  for (const outcome of [0, 7, "error", "signal", "throw"]) {
    const result = launchCode(args, (executable, actualArgs, options) => {
      assert.equal(executable, CODE_EXECUTABLE)
      assert.equal(actualArgs, args)
      assert.deepEqual(options, { shell: false, stdio: "ignore" })
      if (outcome === "throw") throw Error("spawn failed")
      const child = new EventEmitter()
      queueMicrotask(() => {
        if (outcome === "error") child.emit("error", Error("ENOENT"))
        else child.emit("close", outcome === "signal" ? null : outcome, outcome === "signal" ? "SIGTERM" : null)
      })
      return child
    })
    if (outcome === 0) await result
    else await assert.rejects(result)
  }
})

test("active location does not fall back when session cache is unavailable", () => {
  const value = context()
  value.data.session.get = () => undefined
  assert.throws(() => activeLocation(value), /unknown session/)
})
