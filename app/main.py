from __future__ import annotations

import os
import json
import traceback
from datetime import datetime
from pathlib import Path
from shlex import split as shlex_split

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive
from rich.markup import escape


# --------------------------------------------------
# USER DATA
# --------------------------------------------------

def user_data_dir() -> Path:
    path = Path.home() / ".pantha"
    path.mkdir(parents=True, exist_ok=True)
    return path


NOTES_FILE = user_data_dir() / "notes.json"
HISTORY_FILE = user_data_dir() / "history.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# --------------------------------------------------
# BANNER
# --------------------------------------------------

class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(
            r"""
     ^---^
    ( . . )        \    /\
    (___'_)         )  ( ')           
v1  ( | | )___      (  /  )                   (`\
   (__m_m__)__}      \(__)|                    ) )
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝

░▒▓█▓▒ SECURE TERMINAL NOTE SYSTEM ▒▓█▓▒░
"""
        )


# --------------------------------------------------
# APP
# --------------------------------------------------

class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Pantham Core v1.3.1"

    status: reactive[str] = reactive("Ready")

    def __init__(self) -> None:
        super().__init__()
        self.pantha_mode = False
        self.notes: dict[str, dict] = {}
        self.command_history: list[str] = []
        self.history_index = 0

        self.username = os.environ.get("USERNAME") or "pantha"
        self.hostname = os.environ.get("COMPUTERNAME") or "local"

        self.load_notes()
        self.load_history()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield PanthaBanner()
        with ScrollableContainer():
            yield RichLog(id="log", wrap=True, markup=True)
        yield Static("", id="status_line")
        yield Input(id="command_input", placeholder="Enter command…")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]Pantha Terminal online.[/]")
        log.write("[#b066ff]Type [bold]pantham[/] to awaken the core.[/]")
        log.write("[#b066ff]Type [bold]help[/] to access command list.[/]")
        self.focus_input()

    # --------------------------------------------------
    # INPUT
    # --------------------------------------------------

    def focus_input(self) -> None:
        self.query_one("#command_input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""
        if cmd:
            self.run_command_safe(cmd)
        self.focus_input()

    def on_key(self, event) -> None:
        log = self.query_one("#log", RichLog)
        inp = self.query_one("#command_input", Input)

        if event.key == "ctrl+l":
            log.clear()
            self.set_status("Cleared")
            event.stop()

        if event.key == "ctrl+c":
            self.exit()

        if event.key == "up" and self.command_history:
            self.history_index = max(0, self.history_index - 1)
            inp.value = self.command_history[self.history_index]
            inp.cursor_position = len(inp.value)
            event.stop()

        if event.key == "down" and self.command_history:
            self.history_index = min(len(self.command_history), self.history_index + 1)
            inp.value = "" if self.history_index >= len(self.command_history) else self.command_history[self.history_index]
            inp.cursor_position = len(inp.value)
            event.stop()

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def set_status(self, text: str) -> None:
        self.query_one("#status_line", Static).update(
            f"[#ff4dff]STATUS[/]: {escape(text)}"
        )

    # --------------------------------------------------
    # STORAGE
    # --------------------------------------------------

    def load_notes(self) -> None:
        if not NOTES_FILE.exists():
            self.notes = {}
            return

        raw = json.loads(NOTES_FILE.read_text("utf-8"))
        for title, data in raw.items():
            if isinstance(data, str):
                self.notes[title] = {
                    "content": data,
                    "created": now(),
                    "modified": now(),
                    "pinned": False,
                }
            else:
                self.notes[title] = data

    def save_notes(self) -> None:
        NOTES_FILE.write_text(json.dumps(self.notes, indent=2), "utf-8")

    def load_history(self) -> None:
        if HISTORY_FILE.exists():
            self.command_history = json.loads(HISTORY_FILE.read_text("utf-8"))

    def save_history(self) -> None:
        HISTORY_FILE.write_text(json.dumps(self.command_history[-200:], indent=2), "utf-8")

    # --------------------------------------------------
    # COMMAND DISPATCH
    # --------------------------------------------------

    def run_command_safe(self, cmd: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[#b066ff]{self.username}@{self.hostname}[/] $ {escape(cmd)}")
        try:
            self.command_history.append(cmd)
            self.history_index = len(self.command_history)
            self.save_history()
            self.run_command(cmd)
        except Exception:
            log.write("[bold red]INTERNAL ERROR[/]")
            log.write(escape(traceback.format_exc()))

    def run_command(self, cmd: str) -> None:
        low = cmd.lower()
        log = self.query_one("#log", RichLog)

        if low == "pantham":
            self.pantha_mode = True
            self.show_pantha_ascii()
            self.set_status("PANTHAM MODE ONLINE")
            return

        if low == "pantham off":
            self.pantha_mode = False
            log.write("[gray]Pantham disengaged.[/]")
            return

        if low == "help":
            self.show_help()
            return

        if low.startswith("note"):
            self.handle_note(cmd)
            return

        if low in ("exit", "quit"):
            self.exit()
            return

        log.write(f"[red]Unknown command:[/] {escape(cmd)}")

    # --------------------------------------------------
    # HELP
    # --------------------------------------------------

    def show_help(self) -> None:
        self.query_one("#log", RichLog).write(
            """
[bold #ff4dff]GLOBAL COMMANDS[/]
pantham / pantham off
help
exit

[bold #ff4dff]NOTE COMMANDS[/]
note list
note create <title>
note view <title>
note write <title> <text>
note append <title> <text>
note delete <title>
note rename <old> <new>
note pin <title>
note unpin <title>
note search <keyword>

[gray]CTRL+L clear • CTRL+C quit[/]
"""
        )

    # --------------------------------------------------
    # NOTES
    # --------------------------------------------------

    def require_pantha(self) -> bool:
        if not self.pantha_mode:
            self.query_one("#log", RichLog).write(
                "[red]Notes locked. Enter [bold]pantham[/] first.[/]"
            )
            return False
        return True

    def handle_note(self, cmd: str) -> None:
        if not self.require_pantha():
            return

        log = self.query_one("#log", RichLog)
        parts = shlex_split(cmd)

        if len(parts) < 2:
            log.write("[yellow]note <action>[/]")
            return

        action = parts[1]

        if action == "list":
            pinned = [t for t, n in self.notes.items() if n["pinned"]]
            others = [t for t, n in self.notes.items() if not n["pinned"]]

            if not self.notes:
                log.write("[gray]No notes found.[/]")
                return

            if pinned:
                log.write("[bold]📌 Pinned[/]")
                for t in pinned:
                    log.write(f"• {escape(t)}")

            log.write("[bold]Notes[/]")
            for t in others:
                log.write(f"• {escape(t)}")
            return

        if action in ("pin", "unpin"):
            title = parts[2]
            if title not in self.notes:
                log.write("[red]Note not found.[/]")
                return
            self.notes[title]["pinned"] = action == "pin"
            self.notes[title]["modified"] = now()
            self.save_notes()
            log.write(f"[green]{action.title()}ned:[/] {escape(title)}")
            return

        # Other note commands remain unchanged (create/view/write/append/delete/rename/search)

    # --------------------------------------------------
    # PANTHAM ASCII
    # --------------------------------------------------

    def show_pantha_ascii(self) -> None:
        ascii_art = r"""
                                            

⠀⠀⠀⠀⠀⠀ ⠀/\_/\                                 
   ____/ o o \                             
 /~____  =ø= /                                           (`\ 
(______)__m_m)                                            ) )
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗ ███╗   ███╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗████╗ ████║
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║██╔████╔██║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║██║╚██╔╝██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║██║ ╚═╝ ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝

      ░▒▓█▓▒░  P A N T H A M   N O T E S  G R A N T E D  ░▒▓█▓▒░
"""
        commands = """
[bold #ff4dff]PANTHAM COMMANDS[/]
note list • create • view • write • append
note delete • rename • pin • unpin • search

[gray]CTRL+L clear • CTRL+C quit • pantham off[/]
"""
        log = self.query_one("#log", RichLog)
        log.write(f"[bold #ff4dff]{ascii_art}[/]")
        log.write(commands)


if __name__ == "__main__":
    PanthaTerminal().run()
