import assert from "node:assert/strict"
import test from "node:test"
import { installFileLinks } from "../adapter.mjs"
import { openFileLink } from "../links.mjs"

const tick = () => new Promise((resolve) => setImmediate(resolve))
const click = (overrides = {}) => ({
  type: "up", button: 0, isDragging: true, x: 4, y: 8,
  modifiers: { ctrl: false, alt: false, shift: false }, ...overrides,
})

class Renderer {
  selection = { isStart: true, behavior: "cell" }
  href = "src/file.ts:25:3"
  calls = []
  getSelection() { return this.selection }
  getLinkAt(x, y) { assert.equal(x, 4); assert.equal(y, 8); return this.href }
  sendMouseEvent(target, event) { this.calls.push({ receiver: this, target, event, args: [...arguments] }); return "original-return" }
  processSingleMouseEvent(raw) {
    this.sendMouseEvent(this.target, { ...raw, isDragging: true })
    this.finishedSelection = true
  }
}

function fixture(app = { version: "2.3.0" }) {
  const renderer = new Renderer()
  const toasts = []
  const opens = []
  const context = {
    app, renderer,
    ui: { toast: { show: (toast) => toasts.push(toast) } },
  }
  const cleanup = installFileLinks(context, { open: async (...args) => opens.push(args) })
  return { renderer, context, toasts, opens, cleanup }
}

test("intercepts file clicks before bubbling, leaves event/selection untouched and allows finishing selection", async () => {
  const f = fixture()
  const event = Object.freeze(click())
  const selection = Object.freeze(f.renderer.selection)
  const target = Object.freeze({})
  assert.equal(f.renderer.sendMouseEvent(target, event), undefined)
  await tick()
  assert.equal(f.opens.length, 1)
  assert.equal(f.opens[0][0], f.context)
  assert.deepEqual(f.opens[0][1], { filename: "src/file.ts", line: 25, column: 3 })
  assert.equal(f.renderer.selection, selection)
  assert.equal(f.renderer.calls.length, 0)
  f.renderer.target = target
  f.renderer.processSingleMouseEvent(event)
  assert.equal(f.renderer.finishedSelection, true)
  f.cleanup()
})

test("HTTP and HTTPS preserve exact receiver, arguments, return and event state with no session or launch work", async () => {
  for (const href of ["http://example.test/a", "https://example.test/b", "HTTPS://example.test/%ZZ", "http:\u0000bad"]) {
    const f = fixture()
    f.renderer.href = href
    Object.defineProperty(f.context, "data", { get() { assert.fail("no session lookup") } })
    Object.defineProperty(f.context, "client", { get() { assert.fail("no server I/O") } })
    const target = Object.freeze({})
    const event = Object.freeze(click())
    const extra = {}
    assert.equal(f.renderer.sendMouseEvent(target, event, extra), "original-return")
    assert.deepEqual(f.renderer.calls, [{ receiver: f.renderer, target, event, args: [target, event, extra] }])
    await tick()
    assert.equal(f.opens.length, 0)
    assert.equal(f.toasts.length, 0)
    f.cleanup()
  }
})

test("drag selections, multiple clicks, modifiers, non-left and unrelated events take original path", async () => {
  const cases = [
    [{ isDragging: false }], [{ type: "down" }], [{ type: "drag" }], [{ type: "drag-end" }],
    [{ button: 1 }], [{ button: 2 }], [{ modifiers: { ctrl: true } }],
    [{ modifiers: { alt: true } }], [{ modifiers: { shift: true } }], [{ modifiers: { meta: true } }],
    [{ modifiers: undefined }], [{}, { isStart: false, behavior: "cell" }],
    [{}, { isStart: true, behavior: "word" }], [{}, undefined],
  ]
  for (const [overrides, ...selection] of cases) {
    const f = fixture()
    if (selection.length) f.renderer.selection = selection[0]
    const event = click(overrides)
    assert.equal(f.renderer.sendMouseEvent({}, event), "original-return")
    assert.equal(f.renderer.calls[0].event, event)
    await tick()
    assert.equal(f.opens.length, 0)
    f.cleanup()
  }
})

test("unsupported, missing and malformed hrefs retain original behavior", async () => {
  for (const href of [undefined, "", "command:danger", "javascript:x", "data:x", "vscode://extension/run", "//host/file", "/a%ZZ", "/a#unknown"]) {
    const f = fixture()
    f.renderer.href = href
    assert.equal(f.renderer.sendMouseEvent({}, click()), "original-return")
    await tick()
    assert.equal(f.opens.length, 0)
    f.cleanup()
  }
})

test("inspection errors do not change original exception or return behavior", () => {
  const f = fixture()
  f.renderer.getLinkAt = () => { throw Error("renderer read failure") }
  assert.equal(f.renderer.sendMouseEvent({}, click()), "original-return")
  f.cleanup()
  const renderer = new Renderer()
  const expected = Error("original exception")
  renderer.sendMouseEvent = () => { throw expected }
  installFileLinks({ ...f.context, renderer })
  renderer.href = "https://example.test"
  assert.throws(() => renderer.sendMouseEvent({}, click()), (error) => error === expected)
})

test("destroyed targets/renderers and foreign receivers take original path", async () => {
  for (const kind of ["target", "renderer", "receiver"]) {
    const f = fixture()
    const target = { isDestroyed: kind === "target" }
    f.renderer.isDestroyed = kind === "renderer"
    const receiver = kind === "receiver" ? { calls: [] } : f.renderer
    assert.equal(f.renderer.sendMouseEvent.call(receiver, target, click()), "original-return")
    await tick()
    assert.equal(f.opens.length, 0)
    f.cleanup()
  }
})

test("dispatch without a target retains the original path", async () => {
  const f = fixture()
  assert.equal(f.renderer.sendMouseEvent(null, click()), "original-return")
  await tick()
  assert.equal(f.opens.length, 0)
  f.cleanup()
})

test("launch and filesystem failures become toasts without falling through to host URL opener", async () => {
  for (const error of [Error("File link target does not exist"), Error("VS Code launcher exited (1)"), "failure"]) {
    const f = fixture()
    f.cleanup()
    const stop = installFileLinks(f.context, { open: () => { throw error } })
    f.renderer.sendMouseEvent({}, click())
    await tick()
    assert.equal(f.renderer.calls.length, 0)
    assert.equal(f.toasts.length, 1)
    assert.match(f.toasts[0].message, /does not exist|exited|Unable to open/)
    stop()
  }
})

test("directory clicks show a clear toast and never launch or reach the host URL opener", async () => {
  const f = fixture()
  f.cleanup()
  f.renderer.href = "directory/"
  f.context.ui.router = { current: () => ({ type: "session", sessionID: "active" }) }
  f.context.data = { session: { get: () => ({ location: { directory: "/active/session" } }) } }
  const stop = installFileLinks(f.context, {
    open: (context, target, options) => openFileLink(context, target, {
      ...options,
      checkLocal: async () => {},
      readStat: async () => ({ isFile: () => false, isDirectory: () => true }),
      launch: () => assert.fail("directory must never launch"),
    }),
  })
  try {
    f.renderer.sendMouseEvent({}, click())
    await tick()
    assert.equal(f.renderer.calls.length, 0)
    assert.equal(f.toasts.length, 1)
    assert.equal(f.toasts[0].variant, "warning")
    assert.match(f.toasts[0].message, /not a regular file; directories/)
  } finally {
    stop()
  }
})

test("version metadata does not gate installation, file interception or cleanup with a compatible renderer fixture", async () => {
  const apps = ["2.3.1", "2.4.0", "2.99.0"].map((version) => ({ version }))
  apps.push({ get version() { assert.fail("version metadata must not be read") } })
  for (const app of apps) {
    const f = fixture(app)
    try {
      assert.equal(Object.hasOwn(f.renderer, "sendMouseEvent"), true)
      assert.equal(f.renderer.sendMouseEvent({}, click()), undefined)
      await tick()
      assert.equal(f.opens.length, 1)
      assert.equal(f.opens[0][0], f.context)
      assert.deepEqual(f.opens[0][1], { filename: "src/file.ts", line: 25, column: 3 })
      assert.equal(f.renderer.calls.length, 0)
      assert.equal(f.toasts.length, 0)
    } finally {
      f.cleanup()
    }
    assert.equal(Object.hasOwn(f.renderer, "sendMouseEvent"), false)
    assert.equal(f.renderer.sendMouseEvent, Renderer.prototype.sendMouseEvent)
    assert.equal(f.renderer.sendMouseEvent({}, click()), "original-return")
    await tick()
    assert.equal(f.opens.length, 1)
  }
})

test("incompatible renderers fail closed with toast and no wrapping", () => {
  for (const kind of ["prototype", "selection", "readonly", "sealed"]) {
    const f = fixture()
    f.cleanup()
    if (kind === "prototype") f.context.renderer = { sendMouseEvent() {}, getSelection() {}, getLinkAt() {} }
    if (kind === "selection") f.renderer.getSelection = undefined
    if (kind === "readonly") Object.defineProperty(f.renderer, "sendMouseEvent", { value() {}, configurable: false })
    if (kind === "sealed") Object.preventExtensions(f.renderer)
    const original = f.context.renderer.sendMouseEvent
    const stop = installFileLinks(f.context)
    assert.equal(f.context.renderer.sendMouseEvent, original)
    assert.equal(f.toasts.length, 1)
    assert.match(f.toasts[0].message, /^Disabled:/)
    stop()
  }
})

test("cleanup restores inherited method, is idempotent and cancels queued opens", async () => {
  const f = fixture()
  f.renderer.sendMouseEvent({}, click())
  f.cleanup()
  f.cleanup()
  assert.equal(Object.hasOwn(f.renderer, "sendMouseEvent"), false)
  assert.equal(f.renderer.sendMouseEvent, Renderer.prototype.sendMouseEvent)
  await tick()
  assert.equal(f.opens.length, 0)
})

test("existing own wrapper descriptor is restored exactly", () => {
  const f = fixture()
  f.cleanup()
  const wrapper = function (...args) { return Renderer.prototype.sendMouseEvent.apply(this, args) }
  Object.defineProperty(f.renderer, "sendMouseEvent", { value: wrapper, enumerable: true, writable: false, configurable: true })
  const before = Object.getOwnPropertyDescriptor(f.renderer, "sendMouseEvent")
  const stop = installFileLinks(f.context)
  stop()
  assert.deepEqual(Object.getOwnPropertyDescriptor(f.renderer, "sendMouseEvent"), before)
})

test("later wrappers are not overwritten and retained adapter becomes inert", async () => {
  const f = fixture()
  const retained = f.renderer.sendMouseEvent
  let laterCalls = 0
  const later = function (...args) { laterCalls++; return retained.apply(this, args) }
  f.renderer.sendMouseEvent = later
  f.cleanup()
  assert.equal(f.renderer.sendMouseEvent, later)
  assert.equal(f.renderer.sendMouseEvent({}, click()), "original-return")
  await tick()
  assert.equal(laterCalls, 1)
  assert.equal(f.opens.length, 0)
})

test("reload has one active adapter, including when a later wrapper retains an old generation", async () => {
  for (const retain of [false, true]) {
    const f = fixture()
    if (retain) {
      const old = f.renderer.sendMouseEvent
      f.renderer.sendMouseEvent = function (...args) { return old.apply(this, args) }
    }
    const newOpens = []
    const stop = installFileLinks(f.context, { open: async (...args) => newOpens.push(args) })
    f.cleanup()
    f.renderer.sendMouseEvent({}, click())
    await tick()
    assert.equal(f.opens.length, 0)
    assert.equal(newOpens.length, 1)
    stop()
    assert.equal(f.renderer.sendMouseEvent({}, click()), "original-return")
  }
})
