from __future__ import annotations

import os
import subprocess
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive


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
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║
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
    awaiting_note_name: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self.command_history: list[str] = []
        self.history_index = -1
        self.pantha_mode = False
        self.pending_note_action: str | None = None  # "add" or "open/delete"

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = (
            os.environ.get("COMPUTERNAME")
            or (os.uname().nodename if hasattr(os, "uname") else "local")
        )

        # Notes system
        self.notes_dir = Path("notes")
        self.notes_dir.mkdir(exist_ok=True)

    # --------------------------------------------------
    # STYLES
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
                            "ENTER     → run command\n"
                            "UP/DOWN   → history\n"
                            "CTRL+C    → quit\n"
                            "CTRL+L    → clear log\n"
                            "pantham   → toggle mode",
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
    # LIFECYCLE
    # --------------------------------------------------

    def on_mount(self) -> None:
        self.load_tcss()
        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]Pantha Terminal Online.[/]")
        log.write("[#b066ff]Type [bold]pantham[/] to awaken the core.[/]")
        self.update_status("Ready")
        self.query_one("#command_input", Input).focus()

    # --------------------------------------------------
    # INPUT HANDLING
    # --------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""

        # Handle awaiting note name
        if self.awaiting_note_name:
            self.awaiting_note_name = False
            self.add_note_editor(cmd)
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

    # --------------------------------------------------
    # COMMANDS
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

        self.command_history.append(cmd)
        self.history_index = len(self.command_history)
        log = self.query_one("#log", RichLog)
        log.write(f"{self.prompt()} [#ffffff]{cmd}[/]")

        low = cmd.lower()

        # -------------------------
        # General Commands
        # -------------------------
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
        if not self.pantha_mode:
            if low in ("exit", "quit"):
                self.exit()
                return
            self.run_shell(cmd)
            return

        # -------------------------
        # Pantham Mode Commands
        # -------------------------
        if low.startswith("add note"):
            log.write("[#ff4dff]Enter note name:[/]")
            self.awaiting_note_name = True
            return

        if low.startswith("open note"):
            self.open_note_autocomplete(cmd, action="open")
            return
        if low.startswith("delete note"):
            self.open_note_autocomplete(cmd, action="delete")
            return

        if low in ("exit", "quit"):
            self.exit()
            return

        log.write(f"[red]Unknown Pantham command:[/] {cmd}")

    # --------------------------------------------------
    # PANTHAM ASCII
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

    # --------------------------------------------------
    # NOTE SYSTEM
    # --------------------------------------------------

    def add_note_editor(self, note_name: str) -> None:
        log = self.query_one("#log", RichLog)
        note_name = note_name.strip()
        if not note_name:
            log.write("[red]Cancelled: no name provided[/]")
            return
        final_path = self.notes_dir / f"{note_name}.txt"
        if final_path.exists():
            log.write(f"[red]Note already exists:[/] {note_name}")
            return
        editor = os.environ.get("EDITOR", "nano" if os.name != "nt" else "notepad")
        subprocess.call([editor, str(final_path)])
        if final_path.exists() and final_path.stat().st_size > 0:
            log.write(f"[green]Note saved:[/] {final_path.name}")
        else:
            if final_path.exists():
                final_path.unlink()
            log.write("[yellow]Empty note discarded[/]")

    def open_note_autocomplete(self, cmd: str, action: str) -> None:
        log = self.query_one("#log", RichLog)
        parts = cmd.split(maxsplit=2)
        if len(parts) < 3:
            log.write(f"[#ff4dff]Usage: {action} note <name>[/]")
            return
        name = parts[2]
        matches = [n.stem for n in self.notes_dir.glob("*.txt") if n.stem.startswith(name)]
        if not matches:
            log.write(f"[red]No matching note found:[/] {name}")
            return
        final_name = matches[0]
        final_path = self.notes_dir / f"{final_name}.txt"
        if action == "open":
            editor = os.environ.get("EDITOR", "nano" if os.name != "nt" else "notepad")
            subprocess.call([editor, str(final_path)])
            log.write(f"[green]Opened note:[/] {final_path.name}")
        elif action == "delete":
            final_path.unlink()
            log.write(f"[green]Deleted note:[/] {final_path.name}")


if __name__ == "__main__":
    PanthaTerminal().run()
