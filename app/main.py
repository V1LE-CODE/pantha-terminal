from __future__ import annotations

import os
import traceback
from pathlib import Path
from shlex import split as shlex_split

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive
from rich.markup import escape

from vault import Vault, VaultError


# --------------------------------------------------
# USER DATA
# --------------------------------------------------

def user_data_dir() -> Path:
    path = Path.home() / ".pantha"
    path.mkdir(parents=True, exist_ok=True)
    return path


# --------------------------------------------------
# BANNER
# --------------------------------------------------

class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(
            r"""
██████   █████  ███    ██ ████████ ██   ██  █████
██   ██ ██   ██ ████   ██    ██    ██   ██ ██   ██
██████  ███████ ██ ██  ██    ██    ███████ ███████
██      ██   ██ ██  ██ ██    ██    ██   ██ ██   ██
██      ██   ██ ██   ████    ██    ██   ██ ██   ██
"""
        )


# --------------------------------------------------
# APP
# --------------------------------------------------

class PanthaTerminal(App):

    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Encrypted Pantha Terminal"

    CSS = """
    Screen { background: #020005; color: #eadcff; }
    #log { background: #1a001f; }
    Input { background: #120017; border: round #ffffff; }
    #status_line { background: #120017; color: #00ff3c; }
    """

    status_text: reactive[str] = reactive("Ready")

    def __init__(self) -> None:
        super().__init__()

        self.username = os.environ.get("USERNAME") or "pantha"
        self.hostname = os.environ.get("COMPUTERNAME") or "local"

        self.vault = Vault(str(user_data_dir()))
        self.awaiting_password = False

        self.command_history: list[str] = []
        self.history_index = -1

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield PanthaBanner()

        with ScrollableContainer():
            yield RichLog(id="log", markup=True, wrap=True)

        yield Static("", id="status_line")
        yield Input(id="command_input", placeholder="Type a command...")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold #a366ff]Pantha Terminal Online.[/]")
        log.write("[#7c33ff]Type [bold]pantham[/] to awaken encrypted vault.[/]")
        self.focus_input()

    # --------------------------------------------------
    # INPUT
    # --------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""

        if self.awaiting_password:
            self.handle_password(cmd)
            self.focus_input()
            return

        self.run_command_safe(cmd)
        self.focus_input()

    def focus_input(self) -> None:
        self.query_one("#command_input", Input).focus()

    # --------------------------------------------------
    # PASSWORD FLOW
    # --------------------------------------------------

    def handle_password(self, password: str) -> None:
        log = self.query_one("#log", RichLog)
        try:
            self.vault.unlock(password)
            log.write("[green]Vault unlocked.[/]")
            self.update_status("VAULT UNLOCKED")
        except Exception:
            log.write("[red]Incorrect password.[/]")
        finally:
            self.awaiting_password = False

    # --------------------------------------------------
    # COMMAND EXECUTION
    # --------------------------------------------------

    def run_command_safe(self, cmd: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[#7c33ff]{self.username}@{self.hostname}[/] $ {escape(cmd)}")

        try:
            self.run_command(cmd)
        except Exception:
            log.write("[bold red]INTERNAL ERROR[/]")
            log.write(escape(traceback.format_exc()))

    def run_command(self, cmd: str) -> None:
        low = cmd.lower()
        log = self.query_one("#log", RichLog)

        # ---------------- PANTHAM ----------------
        if low == "pantham":
            if not self.vault.is_unlocked():
                log.write("[yellow]Enter master password:[/]")
                self.awaiting_password = True
            else:
                self.show_pantha_ascii()
            return

        if low == "pantham off":
            self.vault.lock()
            log.write("[gray]Vault locked.[/]")
            self.update_status("LOCKED")
            return

        # ---------------- NOTES ----------------
        if low.startswith("note"):
            self.handle_note_command(cmd)
            return

        if low in ("exit", "quit"):
            self.exit()
            return

        if low == "clear":
            log.clear()
            self.update_status("Cleared")
            return

        log.write(f"[red]Unknown command:[/] {escape(cmd)}")

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def update_status(self, text: str) -> None:
        self.query_one("#status_line", Static).update(
            f"[#a366ff]STATUS:[/] {escape(text)}"
        )

    # --------------------------------------------------
    # NOTE COMMANDS (ENCRYPTED BACKEND)
    # --------------------------------------------------

    def handle_note_command(self, cmd: str) -> None:

        log = self.query_one("#log", RichLog)

        if not self.vault.is_unlocked():
            log.write("[red]Vault locked. Use pantham first.[/]")
            return

        try:
            parts = shlex_split(cmd)
        except Exception:
            log.write("[red]Invalid command format.[/]")
            return

        if len(parts) < 2:
            log.write("[yellow]note list|create|view|append|delete|rename|search|export|import[/]")
            return

        action = parts[1].lower()
        notes = self.vault.list_notes()

        # LIST
        if action == "list":
            if not notes:
                log.write("[gray]No notes found.[/]")
                return
            log.write("[bold]Encrypted Notes:[/]")
            for meta in notes.values():
                log.write(f"• {escape(meta['title'])}")
            return

        # CREATE
        if action == "create":
            title = parts[2]
            self.vault.create_note(title, "")
            log.write(f"[green]Created encrypted note:[/] {escape(title)}")
            return

        # VIEW
        if action == "view":
            title = parts[2]
            for nid, meta in notes.items():
                if meta["title"] == title:
                    content = self.vault.read_note(nid)
                    log.write(f"[bold]{escape(title)}[/]\n{escape(content)}")
                    return
            log.write("[red]Note not found.[/]")
            return

        # APPEND
        if action == "append":
            title = parts[2]
            text = " ".join(parts[3:])
            for nid, meta in notes.items():
                if meta["title"] == title:
                    old = self.vault.read_note(nid)
                    self.vault.update_note(nid, old + "\n" + text)
                    log.write(f"[green]Updated encrypted note:[/] {escape(title)}")
                    return
            log.write("[red]Note not found.[/]")
            return

        # DELETE
        if action == "delete":
            title = parts[2]
            for nid, meta in notes.items():
                if meta["title"] == title:
                    self.vault.delete_note(nid)
                    log.write(f"[green]Deleted encrypted note:[/] {escape(title)}")
                    return
            log.write("[red]Note not found.[/]")
            return

        # RENAME
        if action == "rename":
            old, new = parts[2], parts[3]
            for nid, meta in notes.items():
                if meta["title"] == old:
                    content = self.vault.read_note(nid)
                    self.vault.delete_note(nid)
                    self.vault.create_note(new, content)
                    log.write(f"[green]Renamed:[/] {escape(old)} → {escape(new)}")
                    return
            log.write("[red]Note not found.[/]")
            return

        # SEARCH
        if action == "search":
            keyword = " ".join(parts[2:])
            found = []
            for nid, meta in notes.items():
                content = self.vault.read_note(nid)
                if keyword.lower() in content.lower():
                    found.append(meta["title"])
            if not found:
                log.write("[gray]No matches found.[/]")
                return
            log.write(f"[bold]Matches for '{escape(keyword)}':[/]")
            for t in found:
                log.write(f"• {escape(t)}")
            return

        # EXPORT
        if action == "export":
            title = parts[2]
            for nid, meta in notes.items():
                if meta["title"] == title:
                    content = self.vault.read_note(nid)
                    export_file = user_data_dir() / f"{title}.txt"
                    export_file.write_text(content, encoding="utf-8")
                    log.write(f"[green]Exported:[/] {export_file}")
                    return
            log.write("[red]Note not found.[/]")
            return

        # IMPORT
        if action == "import":
            path = Path(parts[2])
            if not path.exists():
                log.write("[red]File not found.[/]")
                return
            content = path.read_text(encoding="utf-8")
            self.vault.create_note(path.stem, content)
            log.write(f"[green]Imported encrypted note:[/] {escape(path.stem)}")
            return

        log.write("[yellow]Unknown note command.[/]")

    # --------------------------------------------------
    # PANTHAM ASCII
    # --------------------------------------------------

    def show_pantha_ascii(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold #a366ff]PANTHAM MODE GRANTED — ENCRYPTED ACCESS[/]")
        log.write("[#7c33ff]All notes are encrypted at rest using AES-256-GCM + Argon2.[/]")


# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    PanthaTerminal().run()
