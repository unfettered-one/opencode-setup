import { Plugin } from "@opencode/plugin/tui"
import { installFileLinks } from "./adapter.mjs"

export default Plugin.define({
  id: "local.vscode-file-links",
  setup: installFileLinks,
})
