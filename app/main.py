from __future__ import annotations

import os
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog, TextArea
from textual.reactive import reactive
from textual import events


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


class NoteEditor(Vertical):
    """Internal note editor"""

    def __init__(self, path: Path, callback, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.callback = callback
        self.text_area = TextArea()
        self.load_note()

    def load_note(self):
        if self.path.exists():
            self.text_area.value = self.path.read_text()
        else:
            self.text_area.value = ""

    def compose(self) -> ComposeResult:
        yield Static(f"Editing Note: {self.path.name} — [Ctrl+S] save, [Ctrl+Q] cancel", id="note_title")
        yield self.text_area

    async def on_key(self, event: events.Key) -> None:
        if event.key == "ctrl+s":
            self.path.write_text(self.text_area.value)
            self.callback(f"Saved note: {self.path.name}")
            self.remove()
            event.stop()
        elif event.key == "ctrl+q":
            self.callback(f"Cancelled note: {self.path.name}")
            self.remove()
            event.stop()


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
        self.query_one("#status_line", Static).update(f"[#ff4dff]STATUS:[/] [#ffffff]{text}[/]")

    def prompt(self) -> str:
        return f"[#b066ff]{self.username}[/]@[#ff4dff]{self.hostname}[/]:[#ffffff]~$[/]"

    # ---------------- Input Handling ----------------

    def on_input_submitted(self, event):
        cmd = event.value.strip()
        event.input.value = ""

        if self.awaiting_note_name:
            self.awaiting_note_name = False
            note_path = self.notes_dir / f"{cmd}.txt"
            self.mount(NoteEditor(note_path, callback=self.note_done), before="#frame")
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

    # ---------------- Command Execution ----------------

    def run_command(self, cmd: str) -> None:
        if not cmd:
            return

        self.command_history.append(cmd)
        self.history_index = len(self.command_history)
        log = self.query_one(RichLog)
        log.write(f"{self.prompt()} [#ffffff]{cmd}[/]")

        low = cmd.lower()

        # Clear screen
        if low == "clear":
            log.clear()
            self.update_status("Cleared")
            return

        # Pantham mode toggle
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
                log.write("[#ff4dff]Enter note name:[/]")
                self.awaiting_note_name = True
                return

            if low.startswith("open note"):
                parts = cmd.split(maxsplit=2)
                if len(parts) < 3:
                    log.write("[#ff4dff]Usage: open note <name>[/]")
                    return
                self.open_note(parts[2])
                return

            if low.startswith("delete note"):
                parts = cmd.split(maxsplit=2)
                if len(parts) < 3:
                    log.write("[#ff4dff]Usage: delete note <name>[/]")
                    return
                self.delete_note(parts[2])
                return

        # Unknown command
        log.write(f"[red]Unknown command:[/] {cmd}")

    # ---------------- Note System ----------------

    def note_done(self, message: str):
        self.query_one(RichLog).write(f"[green]{message}[/]")

    def open_note(self, name: str):
        path = self.notes_dir / f"{name}.txt"
        if not path.exists():
            self.query_one(RichLog).write(f"[red]Note not found:[/] {name}")
            return
        self.mount(NoteEditor(path, callback=self.note_done), before="#frame")

    def delete_note(self, name: str):
        path = self.notes_dir / f"{name}.txt"
        if not path.exists():
            self.query_one(RichLog).write(f"[red]Note not found:[/] {name}")
            return
        path.unlink()
        self.query_one(RichLog).write(f"[green]Deleted note:[/] {name}")

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
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║██║╚██╔╝██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║██║ ╚═╝ ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝

      ░▒▓█▓▒░  P A N T H A M   A W A K E N E D  ░▒▓█▓▒░
      ░▒▓█▓▒░  SYSTEM • TERMINAL • CONTROL      ░▒▓█▓▒░
"""
        self.query_one(RichLog).write("[bold #ff4dff]" + ascii_art + "[/]")


if __name__ == "__main__":
    PanthaTerminal().run()
