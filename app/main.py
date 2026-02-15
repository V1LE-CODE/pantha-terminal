from __future__ import annotations

import os
import json
import traceback
from pathlib import Path
from shlex import split as shlex_split
from typing import List

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive
from rich.markup import escape

from vault import Vault


# ============================================================
# PATHS
# ============================================================

def user_data_dir() -> Path:
    path = Path.home() / ".pantha"
    path.mkdir(parents=True, exist_ok=True)
    return path


HISTORY_FILE = user_data_dir() / "history.json"


# ============================================================
# BANNER
# ============================================================

class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(
r"""
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝

        S E C U R E   E N C R Y P T E D   T E R M I N A L
"""
        )


# ============================================================
# MAIN APP
# ============================================================

class PanthaTerminal(App):

    TITLE = "Pantha Terminal"
    SUB_TITLE = "Vault Encryption Edition"

    status_text: reactive[str] = reactive("LOCKED")

    CSS = """
    Screen { background: #020005; color: #eadcff; }
    #log { background: #1a001f; color: #ffffff; }
    Input { background: #120017; color: #ffffff; border: round #ffffff; }
    #status_line { background: #120017; color: #00ff3c; }
    Header, Footer { background: #1a001f; color: #ffffff; }
    """

    # --------------------------------------------------------

    def __init__(self):
        super().__init__()

        self.vault: Vault | None = None
        self.pantha_mode = False

        self.command_history: List[str] = []
        self.history_index = -1

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = os.environ.get("COMPUTERNAME") or "local"

        self.load_history()

    # ============================================================
    # UI
    # ============================================================

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield PanthaBanner()

        with ScrollableContainer():
            yield RichLog(id="log", markup=True, wrap=True)

        yield Static("", id="status_line")
        yield Input(id="command_input", placeholder="Type a command...")
        yield Footer()

    def on_mount(self):
        log = self.query_one("#log", RichLog)
        log.write("[bold #a366ff]Pantha Secure Terminal Online.[/]")
        log.write("[#7c33ff]Type [bold]unlock <password>[/] to access vault.[/]")
        self.update_status("LOCKED")
        self.focus_input()

    # ============================================================
    # INPUT HANDLING
    # ============================================================

    def focus_input(self):
        self.query_one("#command_input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted):
        cmd = event.value.strip()
        event.input.value = ""
        self.run_command_safe(cmd)
        self.focus_input()

    def on_key(self, event):
        log = self.query_one("#log", RichLog)

        if event.key == "ctrl+l":
            log.clear()
            self.update_status("CLEARED")
            event.stop()
            return

        if event.key == "ctrl+c":
            self.exit()

        inp = self.query_one("#command_input", Input)

        if event.key == "up" and self.command_history:
            self.history_index = max(0, self.history_index - 1)
            inp.value = self.command_history[self.history_index]
            inp.cursor_position = len(inp.value)
            event.stop()

        if event.key == "down" and self.command_history:
            self.history_index = min(len(self.command_history), self.history_index + 1)
            if self.history_index >= len(self.command_history):
                inp.value = ""
            else:
                inp.value = self.command_history[self.history_index]
            inp.cursor_position = len(inp.value)
            event.stop()

    # ============================================================
    # HISTORY
    # ============================================================

    def load_history(self):
        try:
            if HISTORY_FILE.exists():
                self.command_history = json.loads(HISTORY_FILE.read_text())
        except Exception:
            self.command_history = []

    def save_history(self):
        try:
            HISTORY_FILE.write_text(json.dumps(self.command_history, indent=2))
        except Exception:
            pass

    # ============================================================
    # SAFE EXECUTION
    # ============================================================

    def run_command_safe(self, cmd: str):
        log = self.query_one("#log", RichLog)
        log.write(f"[#7c33ff]{self.username}@{self.hostname}[/] $ {escape(cmd)}")

        if not cmd:
            return

        try:
            self.command_history.append(cmd)
            self.history_index = len(self.command_history)
            self.save_history()
            self.run_command(cmd)
        except Exception:
            log.write("[bold red]INTERNAL ERROR[/]")
            log.write(escape(traceback.format_exc()))

    # ============================================================
    # COMMAND ROUTER
    # ============================================================

    def run_command(self, cmd: str):
        parts = shlex_split(cmd)
        base = parts[0].lower()

        if base == "unlock":
            self.command_unlock(parts)
            return

        if base == "lock":
            self.command_lock()
            return

        if base == "note":
            self.command_note(parts)
            return

        if base == "help":
            self.command_help()
            return

        if base in ("exit", "quit"):
            self.exit()
            return

        if base == "clear":
            self.query_one("#log", RichLog).clear()
            return

        self.query_one("#log", RichLog).write(f"[red]Unknown command:[/] {escape(cmd)}")

    # ============================================================
    # CORE COMMANDS
    # ============================================================

    def command_unlock(self, parts):
        log = self.query_one("#log", RichLog)

        if len(parts) < 2:
            log.write("[yellow]Usage: unlock <password>[/]")
            return

        password = parts[1]

        self.vault = Vault()
        self.vault.unlock(password)

        self.pantha_mode = True
        self.update_status("UNLOCKED")
        log.write("[green]Vault unlocked.[/]")

    def command_lock(self):
        if self.vault:
            self.vault.lock()
        self.vault = None
        self.pantha_mode = False
        self.update_status("LOCKED")
        self.query_one("#log", RichLog).write("[gray]Vault locked.[/]")

    def command_help(self):
        log = self.query_one("#log", RichLog)
        log.write("""
[bold]CORE COMMANDS[/]
unlock <password>
lock
note list
note create <title>
note view <title>
note append <title> <text>
note delete <title>
note rename <old> <new>
note search <keyword>
note export <title>
note import <path>
clear
exit
""")

    # ============================================================
    # NOTE SYSTEM
    # ============================================================

    def require_vault(self) -> bool:
        if not self.vault:
            self.query_one("#log", RichLog).write(
                "[red]Vault locked. Use unlock first.[/]"
            )
            return False
        return True

    def command_note(self, parts):
        log = self.query_one("#log", RichLog)

        if not self.require_vault():
            return

        if len(parts) < 2:
            log.write("[yellow]Usage: note <action>[/]")
            return

        action = parts[1].lower()

        try:

            if action == "list":
                notes = self.vault.list_notes()
                if not notes:
                    log.write("[gray]No notes.[/]")
                    return
                for n in notes:
                    log.write(f"• {escape(n)}")
                return

            if action == "create":
                title = parts[2]
                self.vault.create_note(title)
                log.write(f"[green]Created:[/] {escape(title)}")
                return

            if action == "view":
                title = parts[2]
                content = self.vault.get_note(title)
                log.write(f"[bold]{escape(title)}[/]\n{escape(content)}")
                return

            if action == "append":
                title = parts[2]
                text = " ".join(parts[3:])
                current = self.vault.get_note(title)
                self.vault.update_note(title, current + "\n" + text)
                log.write(f"[green]Updated:[/] {escape(title)}")
                return

            if action == "delete":
                title = parts[2]
                self.vault.delete_note(title)
                log.write(f"[green]Deleted:[/] {escape(title)}")
                return

            if action == "rename":
                old, new = parts[2], parts[3]
                self.vault.rename_note(old, new)
                log.write("[green]Renamed.[/]")
                return

            if action == "search":
                keyword = " ".join(parts[2:])
                results = self.vault.search(keyword)
                if not results:
                    log.write("[gray]No matches.[/]")
                    return
                for r in results:
                    log.write(f"• {escape(r)}")
                return

            if action == "export":
                title = parts[2]
                path = user_data_dir() / f"{title}.txt"
                self.vault.export_note(title, path)
                log.write(f"[green]Exported:[/] {path}")
                return

            if action == "import":
                path = Path(parts[2])
                self.vault.import_note(path)
                log.write(f"[green]Imported:[/] {path}")
                return

            log.write("[yellow]Unknown note command.[/]")

        except Exception:
            log.write("[red]Note operation failed.[/]")
            log.write(escape(traceback.format_exc()))

    # ============================================================

    def update_status(self, text: str):
        self.query_one("#status_line", Static).update(
            f"[#a366ff]STATUS:[/] {escape(text)}"
        )


# ============================================================

if __name__ == "__main__":
    PanthaTerminal().run()
