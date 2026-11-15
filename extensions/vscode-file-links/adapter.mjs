import { openFileLink, parseFileLink } from "./links.mjs"

const registration = Symbol.for("local.vscode-file-links.adapter")

function descriptorInPrototype(object, key) {
  for (let proto = Object.getPrototypeOf(object); proto; proto = Object.getPrototypeOf(proto)) {
    const descriptor = Object.getOwnPropertyDescriptor(proto, key)
    if (descriptor) return descriptor
  }
}

export function installFileLinks(context, { open = openFileLink } = {}) {
  const renderer = context.renderer
  const toast = (message) => context.ui.toast.show({ title: "VS Code file links", message, variant: "warning" })
  const disabled = (reason) => {
    toast(`Disabled: ${reason}`)
    return () => {}
  }
  const send = renderer && descriptorInPrototype(renderer, "sendMouseEvent")
  const process = renderer && descriptorInPrototype(renderer, "processSingleMouseEvent")
  if (!send || typeof send.value !== "function" || send.value.length !== 2 ||
      !process || typeof process.value !== "function" || process.value.length !== 1 ||
      typeof renderer.getSelection !== "function" || typeof renderer.getLinkAt !== "function" ||
      !Object.isExtensible(renderer)) return disabled("incompatible OpenTUI mouse adapter")

  renderer[registration]?.cleanup()
  const previous = Object.getOwnPropertyDescriptor(renderer, "sendMouseEvent")
  if (previous && (!Object.hasOwn(previous, "value") || previous.configurable !== true))
    return disabled("renderer dispatch is not safely replaceable")
  const original = renderer.sendMouseEvent
  if (typeof original !== "function") return disabled("renderer dispatch is unavailable")
  let active = true
  const state = { cleanup }

  function wrapped(...args) {
    if (!active || this !== renderer) return Reflect.apply(original, this, args)
    const [target, event] = args
    let link
    try {
      if (target && !target.isDestroyed && !renderer.isDestroyed && event?.type === "up" && event.button === 0 &&
          event.isDragging === true && event.modifiers && !event.modifiers.ctrl &&
          !event.modifiers.alt && !event.modifiers.shift && !event.modifiers.meta) {
        const selection = renderer.getSelection()
        if (selection?.isStart === true && selection.behavior === "cell") {
          const href = renderer.getLinkAt(event.x, event.y)
          // Web links take the original path before parsing, session lookup or I/O.
          if (typeof href === "string" && !/^https?:/i.test(href)) link = parseFileLink(href)
        }
      }
    } catch {
      return Reflect.apply(original, this, args)
    }
    if (!link) return Reflect.apply(original, this, args)
    // Swallow only the file-link bubble. processSingleMouseEvent still finishes
    // the selection after this returns; neither event nor selection is mutated.
    Promise.resolve().then(() => active && open(context, link, { isActive: () => active })).catch((error) => {
      if (active) toast(error instanceof Error ? error.message : "Unable to open file link")
    })
    return undefined
  }

  function cleanup() {
    if (!active) return
    active = false
    if (Object.getOwnPropertyDescriptor(renderer, "sendMouseEvent")?.value === wrapped) {
      if (previous) Object.defineProperty(renderer, "sendMouseEvent", previous)
      else delete renderer.sendMouseEvent
    }
    // A later wrapper may retain ours: leave that wrapper untouched and ours inert.
    if (renderer[registration] === state) delete renderer[registration]
  }

  try {
    Object.defineProperty(renderer, "sendMouseEvent", { value: wrapped, writable: true, configurable: true })
    Object.defineProperty(renderer, registration, { value: state, configurable: true })
  } catch {
    cleanup()
    return disabled("renderer dispatch cannot be wrapped")
  }
  return cleanup
}
