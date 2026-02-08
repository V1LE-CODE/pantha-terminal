from __future__ import annotations

import os
import json
import base64
import secrets
from pathlib import Path
from shlex import split as shlex_split
from getpass import getpass

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.screen import ModalScreen

# --------------------------------------------------
# PATHS
# --------------------------------------------------

APP_DIR = Path.home() / ".pantha"
APP_DIR.mkdir(exist_ok=True)
NOTES_FILE = APP_DIR / "notes.json"
META_FILE = APP_DIR / "meta.json"

# --------------------------------------------------
# CRYPTO
# --------------------------------------------------

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt(data: str, key: bytes) -> str:
    return Fernet(key).encrypt(data.encode()).decode()

def decrypt(token: str, key: bytes) -> str:
    return Fernet(key).decrypt(token.encode()).decode()

# --------------------------------------------------
# ASCII BANNER
# --------------------------------------------------

class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(
            r"""
                   \    /\
                    )  ( ')
                    (  /  )                   (`\
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
# MASTER PASSWORD PROMPT
# --------------------------------------------------

class MasterUnlock(ModalScreen[str]):
    def compose(self) -> ComposeResult:
        yield Static("Enter master password:", classes="title")
        self.input = Input(password=True)
        yield self.input

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

# --------------------------------------------------
# APP
# --------------------------------------------------

class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Pantham v2.0"

    BINDINGS = [
        ("ctrl+l", "clear", "Clear"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.pantha_mode = False
        self.master_key: bytes | None = None
        self.notes = self.load_notes()
        self.meta = self.load_meta()

    # --------------------------------------------------
    # STORAGE
    # --------------------------------------------------

    def load_meta(self) -> dict:
        if META_FILE.exists():
            return json.loads(META_FILE.read_text())
        salt = base64.b64encode(secrets.token_bytes(16)).decode()
        meta = {"salt": salt}
        META_FILE.write_text(json.dumps(meta))
        return meta

    def load_notes(self) -> dict:
        if NOTES_FILE.exists():
            return json.loads(NOTES_FILE.read_text())
        return {}

    def save_notes(self) -> None:
        NOTES_FILE.write_text(json.dumps(self.notes, indent=2))

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield PanthaBanner()
            yield RichLog(id="log", wrap=True)
            yield Input(id="input", placeholder="pantha >")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold magenta]Pantha online.[/]")
        log.write("Type [bold]pantham[/] to authenticate.")

    def action_clear(self) -> None:
        self.query_one("#log", RichLog).clear()

    # --------------------------------------------------
    # INPUT
    # --------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.clear()
        self.run_command(cmd)

    # --------------------------------------------------
    # COMMAND ROUTER
    # --------------------------------------------------

    def run_command(self, cmd: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[cyan]› {cmd}[/]")

        if cmd == "pantham":
            self.authenticate()
            return

        if cmd == "pantham off":
            self.master_key = None
            self.pantha_mode = False
            log.write("[yellow]Pantham locked.[/]")
            return

        if cmd.startswith("note"):
            self.handle_note(cmd)
            return

        log.write("[red]Unknown command[/]")

    # --------------------------------------------------
    # AUTH
    # --------------------------------------------------

    def authenticate(self) -> None:
        def done(password: str) -> None:
            salt = base64.b64decode(self.meta["salt"])
            self.master_key = derive_key(password, salt)
            self.pantha_mode = True
            self.show_pantha_ascii()

        self.push_screen(MasterUnlock(), done)

    # --------------------------------------------------
    # NOTES
    # --------------------------------------------------

    def require_pantha(self) -> bool:
        if not self.pantha_mode or not self.master_key:
            self.query_one("#log", RichLog).write("[red]Locked.[/]")
            return False
        return True

    def handle_note(self, cmd: str) -> None:
        if not self.require_pantha():
            return

        log = self.query_one("#log", RichLog)
        parts = shlex_split(cmd)
        action = parts[1]

        # CREATE
        if action == "create":
            title = parts[2]
            note_key = secrets.token_urlsafe(12)
            salt = secrets.token_bytes(16)

            inner_key = derive_key(note_key, salt)
            encrypted_inner = encrypt("", inner_key)
            outer = encrypt(encrypted_inner, self.master_key)

            self.notes[title] = {
                "data": outer,
                "salt": base64.b64encode(salt).decode(),
                "pinned": False,
            }
            self.save_notes()

            log.write(f"[green]Created note: {title}[/]")
            log.write(f"[bold red]NOTE KEY (SAVE THIS): {note_key}[/]")
            return

        # LIST
        if action == "list":
            for t, n in self.notes.items():
                icon = "📌" if n["pinned"] else "•"
                log.write(f"{icon} {t}")
            return

        # VIEW
        if action == "view":
            title, note_key = parts[2], parts[3]
            note = self.notes[title]

            try:
                salt = base64.b64decode(note["salt"])
                inner = decrypt(note["data"], self.master_key)
                inner_key = derive_key(note_key, salt)
                text = decrypt(inner, inner_key)
                log.write(text or "[dim]<empty>[/]")
            except InvalidToken:
                log.write("[red]Invalid key[/]")
            return

        # APPEND
        if action == "append":
            title, note_key = parts[2], parts[3]
            text = " ".join(parts[4:])
            note = self.notes[title]

            try:
                salt = base64.b64decode(note["salt"])
                inner = decrypt(note["data"], self.master_key)
                inner_key = derive_key(note_key, salt)
                current = decrypt(inner, inner_key)
                new_inner = encrypt(current + "\n" + text, inner_key)
                note["data"] = encrypt(new_inner, self.master_key)
                self.save_notes()
                log.write("[green]Updated.[/]")
            except InvalidToken:
                log.write("[red]Invalid key[/]")
            return

        # PIN / UNPIN
        if action in ("pin", "unpin"):
            title, note_key = parts[2], parts[3]
            note = self.notes[title]

            try:
                salt = base64.b64decode(note["salt"])
                inner = decrypt(note["data"], self.master_key)
                decrypt(inner, derive_key(note_key, salt))
                note["pinned"] = action == "pin"
                self.save_notes()
                log.write("[green]Pin updated.[/]")
            except InvalidToken:
                log.write("[red]Invalid key[/]")
            return

        # DELETE
        if action == "delete":
            title, note_key = parts[2], parts[3]
            note = self.notes[title]

            try:
                salt = base64.b64decode(note["salt"])
                inner = decrypt(note["data"], self.master_key)
                decrypt(inner, derive_key(note_key, salt))
                del self.notes[title]
                self.save_notes()
                log.write("[red]Deleted.[/]")
            except InvalidToken:
                log.write("[red]Invalid key[/]")

    # --------------------------------------------------
    # ASCII PANTHAM
    # --------------------------------------------------

    def show_pantha_ascii(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write(
            r"""
(\ 
\'\ 
 \'\     __________  
 / '|   ()_________)
 \ '/    \ ~~~~~~~~ \
   \       \ ~~~~~~   \
   ==).      \__________\
  (__)       ()__________)

░▒▓█▓▒░  P A N T H A M   N O T E S   G R A N T E D  ░▒▓█▓▒░

Commands:
 note list
 note create <title>
 note view <title> <key>
 note append <title> <key> <text>
 note pin <title> <key>
 note unpin <title> <key>
 note delete <title> <key>

 CTRL+L clear | CTRL+C quit | pantham off
"""
        )

# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":
    PanthaTerminal().run()
