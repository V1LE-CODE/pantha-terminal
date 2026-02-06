from __future__ import annotations

import os
import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive

from commands import run_command as external_command  # your commands.py


def resource_path(relative: str) -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative)


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
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╚══██║██╔══██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝

        ░▒▓█▓▒░  P A N T H A   T E R M I N A L  ░▒▓█▓▒░
"""
        )


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

        # ---------------- Note system ----------------
        self.notes_dir = Path("notes")
        try:
            self.notes_dir.mkdir(exist_ok=True)
        except Exception:
            pass
        self.adding_note: bool = False
        self.current_note_name: str = ""
        self.note_buffer: list[str] = []

        # ---------------- User/host ----------------
        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = (
            os.environ.get("COMPUTERNAME")
            or (os.uname().nodename if hasattr(os, "uname") else "local")
        )

    # ---------------- Styles ----------------
    def load_tcss(self) -> None:
        try:
            dev = Path(__file__).parent / "styles.tcss"
            if dev.exists() and hasattr(self, "stylesheet") and self.stylesheet:
                self.stylesheet.read(dev)
                return

            packed = Path(resource_path("app/styles.tcss"))
            if packed.exists() and hasattr(self, "stylesheet") and self.stylesheet:
                self.stylesheet.read(packed)
        except Exception:
            # fail silently so app doesn't crash
            pass

    # ---------------- UI ----------------
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
                            "ENTER     → run command\n"
                            "UP/DOWN   → history\n"
                            "CTRL+C    → quit\n"
                            "CTRL+L    → clear log\n"
                            "pantham   → toggle mode\n"
                            "add note <name>\n"
                            "open note <name>\n"
                            "delete note <name>\n"
                            "help / about / ls / pwd / echo / time / system / exit",
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

    # ---------------- Lifecycle ----------------
    def on_mount(self) -> None:
        self.load_tcss()

        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]Pantha Terminal Online.[/]")
        log.write("[#b066ff]Type [bold]pantham[/] to awaken the core.[/]")
        self.update_status("Ready")

        self.query_one("#command_input", Input).focus()

    # ---------------- Input handling ----------------
    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""

        log = self.query_one("#log", RichLog)

        # If currently adding a note
        if self.adding_note:
            if cmd.lower() == "end":
                note_path = self.notes_dir / f"{self.current_note_name}.txt"
                note_path.write_text("\n".join(self.note_buffer))
                log.write(f"[green]Saved note:[/] {self.current_note_name}")
                self.adding_note = False
                self.current_note_name = ""
                self.note_buffer = []
            else:
                self.note_buffer.append(cmd)
            return

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

    # ---------------- Commands ----------------
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

        self.command_history.append(cmd)
        self.history_index = len(self.command_history)

        log = self.query_one("#log", RichLog)
        log.write(f"{self.prompt()} [#ffffff]{cmd}[/]")

        low = cmd.lower()

        # Built-in commands
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

        # Pantham note commands
        if self.pantha_mode:
            if low.startswith("add note"):
                parts = cmd.split(maxsplit=2)
                if len(parts) < 3:
                    log.write("[#ff4dff]Usage: add note <name>[/]")
                else:
                    self.adding_note = True
                    self.current_note_name = parts[2]
                    self.note_buffer = []
                    log.write(f"[#ff4dff]Adding note '{self.current_note_name}' (type lines, 'end' to save)[/]")
                return

            if low.startswith("open note"):
                parts = cmd.split(maxsplit=2)
                if len(parts) < 3:
                    log.write("[#ff4dff]Usage: open note <name>[/]")
                else:
                    path = self.notes_dir / f"{parts[2]}.txt"
                    if path.exists():
                        log.write(f"[green]Contents of {parts[2]}:[/]\n{path.read_text()}")
                    else:
                        log.write(f"[red]Note not found:[/] {parts[2]}")
                return

            if low.startswith("delete note"):
                parts = cmd.split(maxsplit=2)
                if len(parts) < 3:
                    log.write("[#ff4dff]Usage: delete note <name>[/]")
                else:
                    path = self.notes_dir / f"{parts[2]}.txt"
                    if path.exists():
                        path.unlink()
                        log.write(f"[green]Deleted note:[/] {parts[2]}")
                    else:
                        log.write(f"[red]Note not found:[/] {parts[2]}")
                return

            # Unknown Pantham command
            log.write(f"[red]Unknown Pantham command:[/] {cmd}")
            return

        # External commands from commands.py
        output, action = external_command(cmd)
        if action == "clear":
            log.clear()
            self.update_status("Cleared")
        elif action == "exit":
            self.exit()
        else:
            log.write(output)

    # ---------------- Pantham ASCII ----------------
    def show_pantha_ascii(self) -> None:
        ascii_art = r"""
⠀⠀⠀⠀⠀⠀⠀/\_/\ 
   ____/ o o \
 /~____  =ø= /
(______)__m_m)
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗ ███╗   ███╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗████╗ ████║
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║██╔████╔██║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╚══██║██╔══██║██║╚██╔╝██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║██║ ╚═╝ ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝

      ░▒▓█▓▒░  P A N T H A M   A W A K E N E D  ░▒▓█▓▒░
      ░▒▓█▓▒░  SYSTEM • TERMINAL • CONTROL      ░▒▓█▓▒░
"""
        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]" + ascii_art + "[/]")

if __name__ == "__main__":
    PanthaTerminal().run()
