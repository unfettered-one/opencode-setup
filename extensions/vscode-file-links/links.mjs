import { spawn } from "node:child_process"
import { stat } from "node:fs/promises"
import { hostname } from "node:os"
import path from "node:path"
import { fileURLToPath } from "node:url"

const controls = /[\u0000-\u001f\u007f-\u009f]/u
export const CODE_EXECUTABLE = "/opt/homebrew/bin/code"

function positive(value) {
  const number = Number(value)
  if (!Number.isSafeInteger(number) || number < 1) throw new Error("Invalid file position")
  return number
}

// Split positions before decoding so %23, %3F and %3A remain filename characters.
export function parseFileLink(href) {
  if (typeof href !== "string" || /^https?:/i.test(href)) return
  if (!href || href.trim() !== href || controls.test(href) || href.includes("\\") || href.startsWith("//")) return
  try {
    let destination = href
    let line
    let column
    const fragment = /#L(\d+)(?:C(\d+)|-L(\d+))?$/.exec(destination)
    if (fragment) {
      line = positive(fragment[1])
      column = fragment[2] ? positive(fragment[2]) : undefined
      if (fragment[3] && positive(fragment[3]) < line) return
      destination = destination.slice(0, fragment.index)
    }
    const position = /:(\d+)(?::(\d+))?$/.exec(destination)
    if (position) {
      if (line !== undefined) return
      line = positive(position[1])
      column = position[2] ? positive(position[2]) : undefined
      destination = destination.slice(0, position.index)
    }
    if (!destination || /[?#]/.test(destination)) return
    const scheme = /^([a-z][a-z0-9+.-]*):/i.exec(destination)?.[1]?.toLowerCase()
    let filename
    if (scheme === "file" || scheme === "vscode") {
      const url = new URL(destination)
      if (url.username || url.password || url.port || url.search || url.hash) return
      if (/%2f|%5c/i.test(url.pathname)) return
      if (scheme === "file") {
        if (!/^file:\/\//i.test(destination) || (url.hostname && url.hostname !== "localhost")) return
        filename = fileURLToPath(url)
      } else {
        if (url.hostname !== "file" || !/^vscode:\/\/file\//i.test(destination)) return
        filename = decodeURIComponent(url.pathname)
      }
      if (!path.posix.isAbsolute(filename)) return
    } else {
      if (scheme) return
      filename = decodeURIComponent(destination)
    }
    if (!filename || controls.test(filename) || filename.includes("\\") || filename.startsWith("//")) return
    if (filename === "~" || filename.startsWith("~/")) return
    return { filename, line, column }
  } catch {
    return
  }
}

export function activeLocation(context) {
  const route = context.ui.router.current()
  if (route.type !== "session") throw new Error("Open a local session before following file links")
  const session = context.data.session.get(route.sessionID)
  const location = session?.location
  if (!location || location.workspaceID != null || context.location?.workspaceID != null)
    throw new Error("Remote or unknown session location; file link not opened")
  if (typeof location.directory !== "string" || !path.posix.isAbsolute(location.directory) ||
      location.directory.startsWith("//") || controls.test(location.directory))
    throw new Error("The active session has no safe absolute local directory")
  return location
}

export async function assertLocalServer(context, localHostname = hostname(), isAlive = (pid) => process.kill(pid, 0)) {
  // The client deliberately does not expose its transport URL. A loopback URL alone
  // would also accept SSH forwards, so require a matching host and a live local PID.
  const info = await context.client.server.info()
  if (typeof info.hostname !== "string" || info.hostname !== localHostname ||
      !Number.isSafeInteger(info.pid) || info.pid < 1)
    throw new Error("Server locality cannot be verified; file link not opened")
  try {
    isAlive(info.pid)
  } catch {
    throw new Error("Server process is not local; file link not opened")
  }
}

export function launchCode(args, spawnProcess = spawn) {
  return new Promise((resolve, reject) => {
    const child = spawnProcess(CODE_EXECUTABLE, args, { shell: false, stdio: "ignore" })
    child.once("error", reject)
    child.once("close", (code, signal) => {
      if (code === 0) resolve()
      else reject(new Error(signal ? `VS Code launcher stopped (${signal})` : `VS Code launcher exited (${code})`))
    })
  })
}

export async function openFileLink(context, target, {
  checkLocal = assertLocalServer,
  readStat = stat,
  launch = launchCode,
  isActive = () => true,
} = {}) {
  const location = activeLocation(context)
  const filename = path.posix.resolve(location.directory, target.filename)
  await checkLocal(context)
  if (!isActive()) return
  let info
  try {
    info = await readStat(filename)
  } catch {
    throw new Error("File link target does not exist or cannot be accessed")
  }
  if (!info.isFile()) throw new Error("File link target is not a regular file; directories and special files are not supported")
  if (!isActive()) return
  await launch(["--reuse-window", "--goto", `${filename}:${target.line ?? 1}:${target.column ?? 1}`])
}
