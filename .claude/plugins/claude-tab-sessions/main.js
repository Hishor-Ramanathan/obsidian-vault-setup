const { Plugin, WorkspaceLeaf } = require("obsidian");

const KEY = "OBSIDIAN_TAB_ID";
const MARK = "claude-tab.cmd";

function tabIdOf(st) {
  const env = st && st.profile && Array.isArray(st.profile.environment) ? st.profile.environment : [];
  const e = env.find((e) => Array.isArray(e) && e[0] === KEY);
  return e ? e[1] : null;
}

// Gives each Terminal tab running claude-tab.cmd a stable id, saved with the tab, so
// claude-tab.cmd can find the Claude session that tab had running and resume it.
module.exports = class ClaudeTabSessions extends Plugin {
  onload() {
    const app = this.app;
    const orig = WorkspaceLeaf.prototype.setViewState;
    this.orig = orig;

    // Report a stable state for Claude tabs. The Terminal plugin's state carries the
    // terminal size and scrollback (serial) and focus, which change on every resize or
    // Tab Groups move. Pinned Tabs identifies a pinned tab by its whole state, so each
    // change looked like "pinned tab missing": it unpinned the live tab (a note then
    // opened over it) and opened a restore copy (closed again below = cmd churn).
    // Dropping serial also skips the scrollback replay; claude --resume redraws anyway.
    const origGet = WorkspaceLeaf.prototype.getViewState;
    this.origGet = origGet;
    WorkspaceLeaf.prototype.getViewState = function (...a) {
      const vs = origGet.apply(this, a);
      try {
        const st = vs && vs.type === "terminal:terminal" && vs.state && vs.state["terminal:terminal"];
        const args = st && st.profile && st.profile.args;
        if (Array.isArray(args) && args.some((x) => String(x).includes(MARK))) {
          return { ...vs, state: { ...vs.state, "terminal:terminal": { ...st, focus: false, serial: null } } };
        }
      } catch (e) {
        console.error("claude-tab-sessions", e);
      }
      return vs;
    };
    WorkspaceLeaf.prototype.setViewState = function (vs, ...rest) {
      try {
        if (vs && vs.type === "terminal:terminal") {
          const st = vs.state && vs.state["terminal:terminal"];
          const p = st && st.profile;
          if (p && Array.isArray(p.args) && p.args.some((a) => String(a).includes(MARK))) {
            const id = tabIdOf(st);
            // Same id in another tab = the same tab restored twice (workspace + Compact
            // Pinned Tabs). Close the copy: a fresh id would be saved as yet another
            // pinned tab, and the set grows on every start.
            const taken = id && app.workspace.getLeavesOfType("terminal:terminal").some(
              (l) => l !== this && tabIdOf(l.getViewState().state?.["terminal:terminal"]) === id
            );
            if (taken) {
              setTimeout(() => this.detach(), 0);
              return Promise.resolve();
            }
            if (!id) {
              const env = Array.isArray(p.environment) ? p.environment : [];
              // state objects may be frozen: rebuild instead of mutating
              const profile = { ...p, environment: [...env, [KEY, crypto.randomUUID()]] };
              vs = { ...vs, state: { ...vs.state, "terminal:terminal": { ...st, profile } } };
            }
          }
        }
      } catch (e) {
        console.error("claude-tab-sessions", e);
      }
      return orig.call(this, vs, ...rest);
    };

    // Ctrl+C copies when terminal text is selected, else it goes to the shell as usual
    // (like Windows Terminal). The Terminal plugin's keymaps have no copy action.
    this.registerDomEvent(window, "keydown", (ev) => {
      if (!ev.ctrlKey || ev.shiftKey || ev.altKey || ev.metaKey || ev.key.toLowerCase() !== "c") return;
      if (!(ev.target instanceof Element) || !ev.target.closest(".xterm")) return;
      // xterm's own copy handler fills the clipboard (and cancels the event) only
      // when it has a selection; fire a copy and see whether it did
      let copied = false;
      const onCopy = (c) => { copied = c.defaultPrevented; };
      window.addEventListener("copy", onCopy);
      try {
        document.execCommand("copy");
      } finally {
        window.removeEventListener("copy", onCopy);
      }
      if (!copied) return;
      ev.preventDefault();
      ev.stopImmediatePropagation();
    }, true);
  }
  onunload() {
    if (this.orig) WorkspaceLeaf.prototype.setViewState = this.orig;
    if (this.origGet) WorkspaceLeaf.prototype.getViewState = this.origGet;
  }
};
