from __future__ import annotations

import json
import traceback
from pathlib import Path
from shlex import split as shlex_split
from typing import List, Dict

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static, RichLog, TextArea
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.timer import Timer

from rich.markup import escape
from rich.syntax import Syntax
from rich.panel import Panel
from rich.markdown import Markdown

from vault import Vault, VaultError, VaultLockedError


# =========================================================
# PATHS
# =========================================================

DATA_DIR = Path.home() / ".pantha"
DATA_DIR.mkdir(exist_ok=True)

HISTORY_FILE = DATA_DIR / "history.json"
PIN_FILE = DATA_DIR / "pins.json"
CURSOR_FILE = DATA_DIR / "cursor.json"


# =========================================================
# TAB MODEL
# =========================================================

class EditorTab:
    def __init__(self, title: str, content: str = ""):
        self.title = title
        self.content = content
        self.undo: List[str] = []
        self.redo: List[str] = []
        self.cursor = 0
        self.readonly = False
        self.preview = False
        self.syntax = False


# =========================================================
# MAIN APP
# =========================================================

class PanthaTerminal(App):

    TITLE = "Pantha Terminal"
    SUB_TITLE = "Encrypted Notes"

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+l", "clear_log", "Clear"),
        ("ctrl+s", "save", "Save"),
        ("ctrl+z", "undo", "Undo"),
        ("ctrl+y", "redo", "Redo"),
        ("ctrl+t", "new_tab", "New Tab"),
        ("ctrl+w", "close_tab", "Close Tab"),
        ("ctrl+tab", "next_tab", "Next Tab"),
        ("ctrl+shift+tab", "prev_tab", "Prev Tab"),
        ("ctrl+p", "preview", "Preview"),
        ("ctrl+e", "syntax", "Syntax"),
        ("ctrl+r", "readonly", "Readonly"),
        ("ctrl+h", "help", "Help"),
    ]

    CSS = """
    Screen { background:#020005; color:#eadcff; }
    #log { background:#14001a; height:1fr; }
    Input { border:round #aa00ff; background:#120017; }
    #status { height:1; background:#120017; color:#00ffd0; }
    TextArea { background:#0a0010; }
    """

    status_text: reactive[str] = reactive("Ready")

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self):
        super().__init__()

        self.vault: Vault | None = None
        self.unlocked = False

        self.history: List[str] = []
        self.history_index = -1

        self.tabs: List[EditorTab] = []
        self.current_tab = -1

        self.pins: set[str] = set()
        self.cursor_memory: Dict[str, int] = {}

        self.autosave_timer: Timer | None = None

        self.load_state()

    # =====================================================
    # UI
    # =====================================================

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal():

            with Vertical():
                yield RichLog(id="log", wrap=True, markup=True)
                yield Input(placeholder="command...", id="cmd")

            yield TextArea(id="editor")

        yield Static("STATUS: Ready", id="status")
        yield Footer()

    def on_mount(self):
        self.log("Pantha ready. Type help")
        self.focus_cmd()
        self.autosave_timer = self.set_interval(5, self.autosave)

    # =====================================================
    # STATE
    # =====================================================

    def load_state(self):

        if HISTORY_FILE.exists():
            self.history = json.loads(HISTORY_FILE.read_text())

        if PIN_FILE.exists():
            self.pins = set(json.loads(PIN_FILE.read_text()))

        if CURSOR_FILE.exists():
            self.cursor_memory = json.loads(CURSOR_FILE.read_text())

    def save_state(self):

        HISTORY_FILE.write_text(json.dumps(self.history))
        PIN_FILE.write_text(json.dumps(list(self.pins)))
        CURSOR_FILE.write_text(json.dumps(self.cursor_memory))

    # =====================================================
    # HELPERS
    # =====================================================

    def log(self, text: str):
        self.query_one("#log", RichLog).write(text)

    def status(self, text: str):
        self.query_one("#status", Static).update("STATUS: " + text)

    def editor(self) -> TextArea:
        return self.query_one("#editor", TextArea)

    def current(self) -> EditorTab | None:
        if 0 <= self.current_tab < len(self.tabs):
            return self.tabs[self.current_tab]
        return None

    def focus_cmd(self):
        self.query_one("#cmd", Input).focus()

    # =====================================================
    # INPUT
    # =====================================================

    def on_input_submitted(self, e: Input.Submitted):
        cmd = e.value.strip()
        e.input.value = ""

        self.history.append(cmd)
        self.save_state()

        self.run_command_safe(cmd)

    # =====================================================
    # COMMAND SAFE
    # =====================================================

    def run_command_safe(self, cmd: str):
        self.log("> " + escape(cmd))

        try:
            self.run_command(cmd)
        except Exception:
            self.log("[red]ERROR[/]")
            self.log(escape(traceback.format_exc()))

    # =====================================================
    # COMMAND ROUTER
    # =====================================================

    def run_command(self, cmd: str):

        parts = shlex_split(cmd)
        if not parts:
            return

        c = parts[0].lower()

        # -------- HELP --------
        if c == "help":
            self.log(
                "Commands:\n"
                "unlock <pass>\n"
                "lock\n"
                "note list\n"
                "note create <title>\n"
                "note open <title>\n"
                "note delete <title>\n"
                "pin <title>\n"
                "unpin <title>\n"
            )
            return

        # -------- UNLOCK --------
        if c == "unlock":
            self.vault = Vault(str(DATA_DIR))
            self.vault.unlock(parts[1])
            self.unlocked = True
            self.status("Unlocked")
            return

        # -------- LOCK --------
        if c == "lock":
            if self.vault:
                self.vault.lock()
            self.unlocked = False
            self.status("Locked")
            return

        # -------- NOTES --------
        if c == "note":
            self.handle_note(parts)
            return

        # -------- PIN --------
        if c == "pin":
            self.pins.add(parts[1])
            self.save_state()
            self.status("Pinned")

        if c == "unpin":
            self.pins.discard(parts[1])
            self.save_state()
            self.status("Unpinned")

        else:
            self.log("Unknown command")

    # =====================================================
    # NOTE COMMANDS
    # =====================================================

    def handle_note(self, parts):

        if not self.unlocked or not self.vault:
            self.log("Unlock vault first")
            return

        cmd = parts[1]

        if cmd == "list":

            notes = self.vault.list_notes().values()

            for n in sorted(notes, key=lambda x: x["title"]):
                t = n["title"]
                prefix = "[PIN] " if t in self.pins else ""
                self.log(prefix + t)

        elif cmd == "create":

            title = parts[2]
            self.vault.create_note(title, "")

            self.tabs.append(EditorTab(title))
            self.current_tab = len(self.tabs) - 1
            self.refresh_editor()

        elif cmd == "open":

            title = parts[2]
            text = self.vault.read_note_by_title(title)

            tab = EditorTab(title, text)
            tab.cursor = self.cursor_memory.get(title, 0)

            self.tabs.append(tab)
            self.current_tab = len(self.tabs) - 1
            self.refresh_editor()

        elif cmd == "delete":

            self.vault.delete_note_by_title(parts[2])
            self.log("Deleted")

    # =====================================================
    # TABS
    # =====================================================

    def refresh_editor(self):

        tab = self.current()
        ed = self.editor()

        if not tab:
            ed.value = ""
            return

        ed.value = tab.content
        ed.cursor_position = tab.cursor

        self.status(f"Tab: {tab.title}")

    def action_new_tab(self):
        self.tabs.append(EditorTab("untitled"))
        self.current_tab = len(self.tabs) - 1
        self.refresh_editor()

    def action_close_tab(self):
        if self.current_tab >= 0:
            self.tabs.pop(self.current_tab)
            self.current_tab -= 1
            self.refresh_editor()

    def action_next_tab(self):
        if self.tabs:
            self.current_tab = (self.current_tab + 1) % len(self.tabs)
            self.refresh_editor()

    def action_prev_tab(self):
        if self.tabs:
            self.current_tab = (self.current_tab - 1) % len(self.tabs)
            self.refresh_editor()

    # =====================================================
    # EDITOR CHANGE
    # =====================================================

    def on_text_area_changed(self, e: TextArea.Changed):

        tab = self.current()
        if not tab or tab.readonly:
            return

        tab.undo.append(tab.content)
        tab.content = e.text
        tab.cursor = e.cursor_position

        self.cursor_memory[tab.title] = tab.cursor

    # =====================================================
    # AUTOSAVE
    # =====================================================

    def autosave(self):

        tab = self.current()

        if not tab or not self.unlocked or not self.vault:
            return

        self.vault.update_note_by_title(tab.title, tab.content)
        self.status("Autosaved")

    # =====================================================
    # ACTIONS
    # =====================================================

    def action_save(self):
        tab = self.current()
        if tab and self.vault:
            self.vault.update_note_by_title(tab.title, tab.content)
            self.status("Saved")

    def action_clear_log(self):
        self.query_one("#log", RichLog).clear()

    def action_quit(self):
        self.save_state()
        self.exit()

    def action_help(self):
        self.run_command("help")

    # -------- UNDO REDO --------

    def action_undo(self):
        tab = self.current()
        if tab and tab.undo:
            tab.redo.append(tab.content)
            tab.content = tab.undo.pop()
            self.refresh_editor()

    def action_redo(self):
        tab = self.current()
        if tab and tab.redo:
            tab.undo.append(tab.content)
            tab.content = tab.redo.pop()
            self.refresh_editor()

    # -------- TOGGLES --------

    def action_readonly(self):
        tab = self.current()
        if tab:
            tab.readonly = not tab.readonly
            self.status("Readonly ON" if tab.readonly else "Readonly OFF")

    def action_preview(self):

        tab = self.current()
        if not tab:
            return

        for w in self.query("#preview"):
            w.remove()

        tab.preview = not tab.preview

        if tab.preview:
            self.editor().visible = False
            self.mount(Static(Markdown(tab.content), id="preview"))
        else:
            self.editor().visible = True

    def action_syntax(self):

        tab = self.current()
        if not tab:
            return

        for w in self.query("#syntax"):
            w.remove()

        tab.syntax = not tab.syntax

        if tab.syntax:
            code = Syntax(tab.content, "python", line_numbers=True)
            self.mount(Static(Panel(code), id="syntax"))

    # =====================================================
    # EXIT SAVE
    # =====================================================

    def on_shutdown(self):
        self.save_state()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    PanthaTerminal().run()
