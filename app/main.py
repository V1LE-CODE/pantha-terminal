from __future__ import annotations

import os
import json
import base64
import traceback
from pathlib import Path
from shlex import split as shlex_split
from typing import Dict

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive
from rich.markup import escape

# ---------------- CRYPTO ----------------
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken

# --------------------------------------------------
# USER DATA
# --------------------------------------------------

def user_data_dir() -> Path:
    path = Path.home() / ".pantha"
    path.mkdir(parents=True, exist_ok=True)
    return path

NOTES_FILE = user_data_dir() / "notes.json"
HISTORY_FILE = user_data_dir() / "history.json"

# --------------------------------------------------
# BANNER
# --------------------------------------------------

class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(
            r"""
                   \    /\
                    )  ( ')
                    (  /  )                   (`
                     \(__)|                    ) )
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝

░▒▓█▓▒ S E C U R E  N O T E  T E R M I N A L ▒▓█▓▒░
"""
        )

# --------------------------------------------------
# APP
# --------------------------------------------------

class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Pantha Secure Notes v2.0"

    status_text = reactive("LOCKED")

    def __init__(self) -> None:
        super().__init__()
        self.pantha_mode = False
        self.notes: Dict[str, dict] = {}
        self.command_history = []
        self.history_index = -1

        self.master_key: bytes | None = None
        self.crypto: Fernet | None = None

        self.username = os.getenv("USER", "pantha")
        self.hostname = os.getenv("COMPUTERNAME", "local")

        self.load_notes()
        self.load_history()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield PanthaBanner()
        with ScrollableContainer():
            yield RichLog(id="log", markup=True, wrap=True)
        yield Static("", id="status_line")
        yield Input(id="command_input", placeholder="Type a command…")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]Pantha Terminal Online[/]")
        log.write("[#b066ff]Type [bold]pantham[/] to unlock notes[/]")
        self.focus_input()

    def focus_input(self) -> None:
        self.query_one("#command_input", Input).focus()

    # --------------------------------------------------
    # INPUT
    # --------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""
        self.run_command_safe(cmd)

    # --------------------------------------------------
    # STORAGE
    # --------------------------------------------------

    def load_notes(self) -> None:
        if NOTES_FILE.exists():
            self.notes = json.loads(NOTES_FILE.read_text("utf-8"))
        else:
            self.notes = {}
            self.save_notes()

    def save_notes(self) -> None:
        NOTES_FILE.write_text(json.dumps(self.notes, indent=2), "utf-8")

    def load_history(self) -> None:
        if HISTORY_FILE.exists():
            self.command_history = json.loads(HISTORY_FILE.read_text("utf-8"))

    def save_history(self) -> None:
        HISTORY_FILE.write_text(json.dumps(self.command_history), "utf-8")

    # --------------------------------------------------
    # CRYPTO
    # --------------------------------------------------

    def derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=390_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    # --------------------------------------------------
    # COMMANDS
    # --------------------------------------------------

    def run_command_safe(self, cmd: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[#b066ff]{self.username}@{self.hostname}[/] $ {escape(cmd)}")
        try:
            self.command_history.append(cmd)
            self.save_history()
            self.run_command(cmd)
        except Exception:
            log.write("[red]CRITICAL ERROR[/]")
            log.write(escape(traceback.format_exc()))

    def run_command(self, cmd: str) -> None:
        low = cmd.lower()
        log = self.query_one("#log", RichLog)

        # -------- PANTHAM --------
        if low == "pantham":
            self.show_pantha_ascii()
            self.pantha_mode = True
            self.update_status("PANTHAM MODE")
            return

        if low.startswith("unlock "):
            password = cmd.split(" ", 1)[1]
            salt = b"pantha-master-salt"
            self.master_key = self.derive_key(password, salt)
            self.crypto = Fernet(self.master_key)
            self.update_status("UNLOCKED")
            log.write("[green]Master key accepted[/]")
            return

        if low.startswith("note"):
            self.handle_note_command(cmd)
            return

        log.write("[red]Unknown command[/]")

    # --------------------------------------------------
    # NOTES
    # --------------------------------------------------

    def handle_note_command(self, cmd: str) -> None:
        log = self.query_one("#log", RichLog)
        parts = shlex_split(cmd)
        if len(parts) < 2:
            return

        action = parts[1]

        if action == "create":
            title = parts[2]
            key = Fernet.generate_key().decode()
            self.notes[title] = {
                "pinned": False,
                "key": key,
                "data": ""
            }
            self.save_notes()
            log.write(f"[green]Note created[/]: {escape(title)}")
            log.write(f"[yellow]NOTE KEY:[/] {key}")
            return

        if action == "view":
            title = parts[2]
            note = self.notes.get(title)
            if not note:
                log.write("[red]Not found[/]")
                return
            if note["data"]:
                try:
                    decrypted = Fernet(note["key"].encode()).decrypt(note["data"].encode()).decode()
                except InvalidToken:
                    decrypted = "[red]<INVALID KEY>[/]"
            else:
                decrypted = "<empty>"
            log.write(f"[bold]{escape(title)}[/]\n{escape(decrypted)}")
            return

        if action == "append":
            title, text = parts[2], " ".join(parts[3:])
            note = self.notes[title]
            f = Fernet(note["key"].encode())
            current = ""
            if note["data"]:
                current = f.decrypt(note["data"].encode()).decode()
            note["data"] = f.encrypt((current + "\n" + text).encode()).decode()
            self.save_notes()
            log.write("[green]Updated[/]")
            return

        if action == "pin":
            self.notes[parts[2]]["pinned"] = True
            self.save_notes()
            log.write("[yellow]Pinned[/]")
            return

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def update_status(self, text: str) -> None:
        self.query_one("#status_line", Static).update(f"[#ff4dff]STATUS[/]: {text}")

    # --------------------------------------------------
    # ASCII
    # --------------------------------------------------

    def show_pantha_ascii(self) -> None:
    log = self.query_one("#log", RichLog)

    ascii_art = r"""
(\ 
\'\ 
 \'\     __________  
 / '|   ()_________)
 \ '/    \ ~~~~~~~~ \
   \       \ ~~~~~~   \
   ==).      \__________\
  (__)       ()__________)
"""

    commands = """
[#ff4dff]██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗[/]
[#ff4dff]██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗[/]
[#ff4dff]██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║[/]
[#ff4dff]██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║[/]
[#ff4dff]██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║[/]
[#ff4dff]╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝[/]

[#ff4dff]░▒▓█▓▒░[/] [bold #b066ff]PANTHAM MODE ENABLED[/] [#ff4dff]░▒▓█▓▒░[/]

[bold #ff4dff]UNLOCK[/]
[#b066ff]unlock <master_password>[/]

[bold #ff4dff]NOTES[/]
[#b066ff]note list[/]
[#b066ff]note create <title>[/]
[#b066ff]note view <title>[/]
[#b066ff]note append <title> <text>[/]
[#b066ff]note pin <title>[/]

[bold #ff4dff]SECURITY[/]
[#888888]• Notes are encrypted at rest[/]
[#888888]• Each note has its own key[/]
[#888888]• Note keys are shown once on creation[/]

[bold #ff4dff]SYSTEM[/]
[#888888]CTRL+L → clear[/]
[#888888]CTRL+C → quit[/]
[#888888]pantham off[/]
"""

    log.write(f"[bold #ff4dff]{ascii_art}[/]")
    log.write(commands)

# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    PanthaTerminal().run()
