from __future__ import annotations

import os
import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive

# --------------------------------------------------
# Paths
# --------------------------------------------------
NOTES_DIR = Path(__file__).parent / "notes"
NOTES_DIR.mkdir(exist_ok=True)

def resource_path(relative: str) -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative)


# --------------------------------------------------
# Banner
# --------------------------------------------------
class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(
            r"""

     ^---^
    ( . . )
    (___'_)
v1  ( | | )___
   (__m_m__)__}
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝

        ░▒▓█▓▒░  P A N T H A   T E R M I N A L  ░▒▓█▓▒░
"""
        )


# --------------------------------------------------
# Terminal
# --------------------------------------------------
class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Pantha Terminal V1.0.0"

    CSS_PATH = None
    status_text: reactive[str] = reactive("Ready")

    def __init__(self) -> None:
        super().__init__()
        self.command_history: list[str] = []
        self.history_index = -1
        self.pantha_mode = False

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = (
            os.environ.get("COMPUTERNAME")
            or (os.uname().nodename if hasattr(os, "uname") else "local")
        )

        # For note creation mode
        self.current_note_name: str | None = None
        self.current_note_lines: list[str] = []

    # --------------------------------------------------
    # Styles
    # --------------------------------------------------
    def load_tcss(self) -> None:
        dev = Path(__file__).parent / "styles.tcss"
        if dev.exists():
            self.stylesheet.read(dev)
            return

        packed = Path(resource_path("app/styles.tcss"))
        if packed.exists():
            self.stylesheet.read(packed)

    # --------------------------------------------------
    # UI
    # --------------------------------------------------
    def compose(self) -> ComposeResult:
        with Vertical(id="frame"):
            yield Header(show_clock=True)

            with Vertical(id="root"):
                yield PanthaBanner(id="banner")

                with Horizontal(id="main_row"):
                    with Vertical(id="left_panel"):
                        yield Static("SYSTEM", id="panel_title")
                        yield Static(
                            f"• User: {self.username}\n"
                            f"• Host: {self.hostname}\n"
                            "• Pantha Terminal\n"
                            "• Purple Aesthetic\n"
                            "• Pantham Mode",
                            id="system_info",
                        )

                        yield Static("HOTKEYS", id="panel_title2")
                        yield Static(
                            "ENTER       → run command\n"
                            "UP/DOWN     → history\n"
                            "CTRL+C      → quit\n"
                            "CTRL+L      → clear log\n"
                            "pantham     → toggle mode\n"
                            "add note    → create a note\n"
                            "open note   → view a note\n"
                            "delete note → remove a note",
                            id="hotkeys",
                        )

                    with Vertical(id="right_panel"):
                        yield Static("OUTPUT", id="output_title")

                        with ScrollableContainer(id="log_wrap"):
                            yield RichLog(id="log", highlight=True, markup=True, wrap=True)

                        yield Static("", id="status_line")
                        yield Input(
                            placeholder="Type a command...",
                            id="command_input",
                        )

            yield Footer()

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------
    def on_mount(self) -> None:
        self.load_tcss()

        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]Pantha Terminal Online.[/]")
        log.write("[#b066ff]Type [bold]pantham[/] to awaken the core.[/]")
        self.update_status("Ready")

        self.query_one("#command_input", Input).focus()

    # --------------------------------------------------
    # Input Handling
    # --------------------------------------------------
    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""
        self.run_command(cmd)

    def on_key(self, event) -> None:
        inp = self.query_one("#command_input", Input)

        if event.key == "ctrl+l":
            self.query_one("#log", RichLog).clear()
            self.update_status("Cleared")
            event.stop()
            return

        if event.key == "up" and self.command_history:
            self.history_index = max(0, self.history_index - 1)
            inp.value = self.command_history[self.history_index]
            inp.cursor_position = len(inp.value)
            event.stop()
            return

        if event.key == "down" and self.command_history:
            self.history_index = min(len(self.command_history), self.history_index + 1)
            inp.value = "" if self.history_index >= len(self.command_history) else self.command_history[self.history_index]
            inp.cursor_position = len(inp.value)
            event.stop()
            return

    # --------------------------------------------------
    # Commands
    # --------------------------------------------------
    def update_status(self, text: str) -> None:
        self.status_text = text
        self.query_one("#status_line", Static).update(
            f"[#ff4dff]STATUS:[/] [#ffffff]{text}[/]"
        )

    def prompt(self) -> str:
        return f"[#b066ff]{self.username}[/]@[#ff4dff]{self.hostname}[/]:[#ffffff]~$[/]"

    def run_command(self, cmd: str) -> None:
        if not cmd:
            return

        log = self.query_one("#log", RichLog)
        # If in note writing mode
        if self.current_note_name:
            if cmd == ".":
                note_path = NOTES_DIR / f"{self.current_note_name}.txt"
                note_path.write_text("\n".join(self.current_note_lines))
                log.write(f"[green]Note '{self.current_note_name}' saved.[/]")
                self.update_status(f"Note '{self.current_note_name}' saved")
                self.current_note_name = None
                self.current_note_lines = []
            else:
                self.current_note_lines.append(cmd)
            return

        self.command_history.append(cmd)
        self.history_index = len(self.command_history)
        log.write(f"{self.prompt()} [#ffffff]{cmd}[/]")

        low = cmd.lower()
        if low == "clear":
            log.clear()
            self.update_status("Cleared")
            return
        if low == "pantham":
            self.pantha_mode = True
            self.show_pantha_ascii()
            self.update_status("PANTHAM MODE ONLINE")
            return
        if low == "pantham off":
            self.pantha_mode = False
            log.write("[#888888]Pantham Mode disengaged.[/]")
            self.update_status("PANTHAM MODE OFF")
            return
        if low in ("exit", "quit"):
            self.exit()
            return

        # ---------------------- Notes system ----------------------
        if low.startswith("add note "):
            note_name = cmd[9:].strip()
            if not note_name:
                log.write("[red]Please provide a note name.[/]")
                return
            self.current_note_name = note_name
            self.current_note_lines = []
            log.write(f"[cyan]Adding note '{note_name}'. Type lines and enter '.' to finish.[/]")
            return

        if low.startswith("open note "):
            note_name = cmd[10:].strip()
            note_path = NOTES_DIR / f"{note_name}.txt"
            if note_path.exists():
                content = note_path.read_text()
                log.write(f"[yellow]--- {note_name} ---[/]")
                log.write(content)
            else:
                log.write(f"[red]Note '{note_name}' does not exist.[/]")
            return

        if low.startswith("delete note "):
            note_name = cmd[12:].strip()
            note_path = NOTES_DIR / f"{note_name}.txt"
            if note_path.exists():
                note_path.unlink()
                log.write(f"[green]Note '{note_name}' deleted.[/]")
            else:
                log.write(f"[red]Note '{note_name}' does not exist.[/]")
            return

        # ---------------------- Run as shell fallback ----------------------
        self.run_shell(cmd)

    # --------------------------------------------------
    # Pantham Mode ASCII
    # --------------------------------------------------
    def show_pantha_ascii(self) -> None:
        ascii_art = r"""
⠀⠀⠀⠀⠀⠀⠀/\_/\ 
   ____/ o o \
 /~____  =ø= /
(______)__m_m)
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗ ███╗   ███╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗████╗ ████║
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║██╔████╔██║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║██║╚██╔╝██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║██║ ╚═╝ ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝

      ░▒▓█▓▒░  P A N T H A M   A W A K E N E D  ░▒▓█▓▒░
      ░▒▓█▓▒░  SYSTEM • TERMINAL • CONTROL      ░▒▓█▓▒░
"""
        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]" + ascii_art + "[/]")

if __name__ == "__main__":
    PanthaTerminal().run()
