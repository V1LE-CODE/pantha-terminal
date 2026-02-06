from __future__ import annotations
import os
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive

class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(r"""
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
""")

class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Pantha Terminal V1.0.0"

    status_text: reactive[str] = reactive("Ready")
    pantha_mode: reactive[bool] = reactive(False)
    adding_note: reactive[bool] = reactive(False)
    current_note_name: str = ""

    def __init__(self):
        super().__init__()
        self.command_history = []
        self.history_index = -1
        self.notes_dir = Path("notes")
        self.notes_dir.mkdir(exist_ok=True)
        self.note_buffer = []

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = os.environ.get("COMPUTERNAME") or "local"

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

    def on_mount(self):
        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]Pantha Terminal Online.[/]")
        log.write("[#b066ff]Type [bold]pantham[/] to awaken the core.[/]")
        self.query_one("#command_input", Input).focus()
        self.update_status("Ready")

    def update_status(self, text: str):
        self.status_text = text
        self.query_one("#status_line", Static).update(f"[#ff4dff]STATUS:[/] [#ffffff]{text}[/]")

    def prompt(self):
        return f"[#b066ff]{self.username}[/]@[#ff4dff]{self.hostname}[/]:[#ffffff]~$[/]"

    def on_input_submitted(self, event):
        cmd = event.value.strip()
        event.input.value = ""

        log = self.query_one("#log", RichLog)

        # Handle adding note line by line
        if self.adding_note:
            if cmd.lower() == "end":
                note_path = self.notes_dir / f"{self.current_note_name}.txt"
                note_path.write_text("\n".join(self.note_buffer))
                log.write(f"[green]Saved note:[/] {self.current_note_name}")
                self.adding_note = False
                self.note_buffer = []
                self.current_note_name = ""
            else:
                self.note_buffer.append(cmd)
            return

        self.command_history.append(cmd)
        self.history_index = len(self.command_history)
        log.write(f"{self.prompt()} [#ffffff]{cmd}[/]")

        low = cmd.lower()

        # Core commands
        if low == "clear":
            log.clear()
            self.update_status("Cleared")
        elif low == "pantham":
            self.pantha_mode = True
            self.show_pantha_ascii()
            self.update_status("PANTHAM MODE ONLINE")
        elif low == "pantham off":
            self.pantha_mode = False
            log.write("[#888888]Pantham Mode disengaged.[/]")
            self.update_status("PANTHAM MODE OFF")
        elif low in ("exit", "quit"):
            self.exit()
        elif self.pantha_mode:
            # Pantham commands
            if low.startswith("add note"):
                parts = cmd.split(maxsplit=2)
                if len(parts) < 3:
                    log.write("[#ff4dff]Usage: add note <name>[/]")
                else:
                    self.adding_note = True
                    self.current_note_name = parts[2]
                    self.note_buffer = []
                    log.write(f"[#ff4dff]Adding note '{self.current_note_name}' (type lines, 'end' to save)[/]")
            elif low.startswith("open note"):
                parts = cmd.split(maxsplit=2)
                if len(parts) < 3:
                    log.write("[#ff4dff]Usage: open note <name>[/]")
                else:
                    note_path = self.notes_dir / f"{parts[2]}.txt"
                    if note_path.exists():
                        contents = note_path.read_text()
                        log.write(f"[green]Contents of {parts[2]}:[/]\n{contents}")
                    else:
                        log.write(f"[red]Note not found:[/] {parts[2]}")
            elif low.startswith("delete note"):
                parts = cmd.split(maxsplit=2)
                if len(parts) < 3:
                    log.write("[#ff4dff]Usage: delete note <name>[/]")
                else:
                    note_path = self.notes_dir / f"{parts[2]}.txt"
                    if note_path.exists():
                        note_path.unlink()
                        log.write(f"[green]Deleted note:[/] {parts[2]}")
                    else:
                        log.write(f"[red]Note not found:[/] {parts[2]}")
            else:
                log.write(f"[red]Unknown Pantham command:[/] {cmd}")
        else:
            log.write(f"[red]Unknown command:[/] {cmd}")

    def on_key(self, event):
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
        self.query_one("#log", RichLog).write("[bold #ff4dff]" + ascii_art + "[/]")

if __name__ == "__main__":
    PanthaTerminal().run()
