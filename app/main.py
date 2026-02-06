import os
import subprocess
from pathlib import Path
import asyncio

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive


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

    status_text: reactive[str] = reactive("Ready")
    awaiting_note_name: reactive[bool] = reactive(False)

    def __init__(self):
        super().__init__()
        self.command_history = []
        self.history_index = -1
        self.pantha_mode = False
        self.pending_note_action = None

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = os.environ.get("COMPUTERNAME") or "local"

        self.notes_dir = Path("notes")
        self.notes_dir.mkdir(exist_ok=True)

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
                        yield Input(placeholder="Type a command...", id="command_input")
            yield Footer()

    def on_mount(self) -> None:
        log = self.query_one(RichLog)
        log.write("[bold #ff4dff]Pantha Terminal Online.[/]")
        log.write("[#b066ff]Type [bold]pantham[/] to awaken the core.[/]")
        self.query_one("#command_input", Input).focus()
        self.update_status("Ready")

    def update_status(self, text: str) -> None:
        self.status_text = text
        self.query_one("#status_line", Static).update(
            f"[#ff4dff]STATUS:[/] [#ffffff]{text}[/]"
        )

    def prompt(self) -> str:
        return f"[#b066ff]{self.username}[/]@[#ff4dff]{self.hostname}[/]:[#ffffff]~$[/]"

    async def run_editor(self, path: Path):
        editor = os.environ.get("EDITOR", "nano" if os.name != "nt" else "notepad")
        await asyncio.to_thread(subprocess.call, [editor, str(path)])

    def run_command(self, cmd: str):
        if not cmd:
            return

        self.command_history.append(cmd)
        self.history_index = len(self.command_history)
        log = self.query_one(RichLog)
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

        if not self.pantha_mode:
            if low in ("exit", "quit"):
                self.exit()
                return
            subprocess.call(cmd, shell=True)
            return

        # Pantham commands
        if low.startswith("add note"):
            log.write("[#ff4dff]Enter note name:[/]")
            self.awaiting_note_name = True
            self.pending_note_action = "add"
            return
        if low.startswith("open note"):
            self.open_note_autocomplete(cmd, action="open")
            return
        if low.startswith("delete note"):
            self.open_note_autocomplete(cmd, action="delete")
            return
        log.write(f"[red]Unknown Pantham command:[/] {cmd}")

    def on_input_submitted(self, event):
        cmd = event.value.strip()
        event.input.value = ""

        if self.awaiting_note_name:
            self.awaiting_note_name = False
            asyncio.create_task(self.add_note_editor(cmd))
            return

        self.run_command(cmd)

    async def add_note_editor(self, note_name: str):
        log = self.query_one(RichLog)
        note_name = note_name.strip()
        if not note_name:
            log.write("[red]Cancelled: no name provided[/]")
            return
        path = self.notes_dir / f"{note_name}.txt"
        if path.exists():
            log.write(f"[red]Note already exists:[/] {note_name}")
            return
        await self.run_editor(path)
        if path.exists() and path.stat().st_size > 0:
            log.write(f"[green]Note saved:[/] {path.name}")
        else:
            if path.exists():
                path.unlink()
            log.write("[yellow]Empty note discarded[/]")

    def open_note_autocomplete(self, cmd: str, action: str):
        log = self.query_one(RichLog)
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
        path = self.notes_dir / f"{final_name}.txt"
        if action == "open":
            asyncio.create_task(self.run_editor(path))
            log.write(f"[green]Opened note:[/] {path.name}")
        elif action == "delete":
            path.unlink()
            log.write(f"[green]Deleted note:[/] {path.name}")

    def show_pantha_ascii(self):
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
        log = self.query_one(RichLog)
        log.write("[bold #ff4dff]" + ascii_art + "[/]")

if __name__ == "__main__":
    PanthaTerminal().run()
