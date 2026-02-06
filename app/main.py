from __future__ import annotations

import os
import json
import traceback
from pathlib import Path
from getpass import getpass
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive
from rich.markup import escape

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import secrets

# --------------------------------------------------
# USER DATA DIRECTORY
# --------------------------------------------------

def user_data_dir() -> Path:
    path = Path.home() / ".pantha"
    path.mkdir(parents=True, exist_ok=True)
    return path

NOTES_FILE = user_data_dir() / "notes.enc"
CONFIG_FILE = user_data_dir() / "config.json"

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

░▒▓█▓▒ S E C U R E  N O T E  T E R M I N A L ▒▓█▓▒░
"""
        )

# --------------------------------------------------
# ENCRYPTION HELPERS
# --------------------------------------------------

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def encrypt_notes(notes: dict[str, str], password: str) -> bytes:
    salt = secrets.token_bytes(16)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    data = json.dumps(notes, ensure_ascii=False).encode("utf-8")
    nonce = secrets.token_bytes(12)
    encrypted = aesgcm.encrypt(nonce, data, None)
    return salt + nonce + encrypted

def decrypt_notes(blob: bytes, password: str) -> dict[str, str]:
    salt = blob[:16]
    nonce = blob[16:28]
    ciphertext = blob[28:]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(decrypted.decode("utf-8"))

# --------------------------------------------------
# APP
# --------------------------------------------------

class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Pantha Terminal v1.2.0"

    status_text: reactive[str] = reactive("Ready")
    pantha_mode: bool = False
    master_password: Optional[str] = None
    notes: dict[str, str] = {}

    def __init__(self) -> None:
        super().__init__()
        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = os.environ.get("COMPUTERNAME") or "local"
        self.command_history: list[str] = []
        self.history_index = -1
        self.load_or_create_master_password()
        self.load_notes()

    # --------------------------------------------------
    # MASTER PASSWORD
    # --------------------------------------------------

    def load_or_create_master_password(self) -> None:
        if CONFIG_FILE.exists():
            config = json.loads(CONFIG_FILE.read_text("utf-8"))
            self.master_password = config.get("master_password")
        else:
            print("First time setup: create a master password for Pantham mode")
            while True:
                pw = getpass("Enter master password: ")
                pw2 = getpass("Confirm password: ")
                if pw == pw2 and pw.strip():
                    self.master_password = pw
                    CONFIG_FILE.write_text(json.dumps({"master_password": self.master_password}))
                    print("Master password saved securely.")
                    break
                print("Passwords do not match or are empty. Try again.")

    def require_pantha(self) -> bool:
        if not self.pantha_mode:
            log = self.query_one("#log", RichLog)
            log.write("[red]Notes locked. Enter [bold]pantham[/] first.[/]")
            return False
        return True

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
        log.write("[bold #ff4dff]Pantha Terminal Online.[/]")
        log.write("[#b066ff]Type [bold]pantham[/] to awaken the core.[/]")
        self.focus_input()

    def focus_input(self) -> None:
        self.query_one("#command_input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""
        self.run_command_safe(cmd)
        self.focus_input()

    def on_key(self, event) -> None:
        log = self.query_one("#log", RichLog)
        if event.key == "ctrl+l":
            log.clear()
            self.update_status("Cleared")
            event.stop()
        if event.key == "ctrl+c":
            self.exit()
    
    # --------------------------------------------------
    # NOTES STORAGE
    # --------------------------------------------------

    def load_notes(self) -> None:
        try:
            if NOTES_FILE.exists() and self.master_password:
                blob = NOTES_FILE.read_bytes()
                self.notes = decrypt_notes(blob, self.master_password)
            else:
                self.notes = {}
        except Exception:
            self.notes = {}

    def save_notes(self) -> None:
        if self.master_password:
            blob = encrypt_notes(self.notes, self.master_password)
            NOTES_FILE.write_bytes(blob)

    # --------------------------------------------------
    # COMMAND EXECUTION
    # --------------------------------------------------

    def run_command_safe(self, cmd: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[#b066ff]{self.username}@{self.hostname}[/] $ {escape(cmd)}")
        try:
            self.run_command(cmd)
        except Exception:
            log.write("[bold red]INTERNAL ERROR[/]")
            log.write(escape(traceback.format_exc()))

    def run_command(self, cmd: str) -> None:
        low = cmd.lower()
        log = self.query_one("#log", RichLog)

        if low == "pantham":
            # ask for password
            pw = getpass("Enter master password: ")
            if pw != self.master_password:
                log.write("[red]Incorrect password![/]")
                return
            self.pantha_mode = True
            self.show_pantha_ascii()
            self.update_status("PANTHAM MODE ONLINE")
            return

        if low == "pantham off":
            self.pantha_mode = False
            log.write("[gray]Pantham disengaged.[/]")
            self.update_status("PANTHAM MODE OFF")
            return

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

        if low == "help":
            self.show_help()
            return

        log.write(f"[red]Unknown command:[/] {escape(cmd)}")

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def update_status(self, text: str) -> None:
        self.query_one("#status_line", Static).update(f"[#ff4dff]STATUS:[/] {escape(text)}")

    # --------------------------------------------------
    # NOTE COMMANDS
    # --------------------------------------------------

    def handle_note_command(self, cmd: str) -> None:
        if not self.require_pantha():
            return
        log = self.query_one("#log", RichLog)
        parts = cmd.split(maxsplit=2)
        if len(parts) < 2:
            log.write("[yellow]Usage: note list|create|view|write|delete|export|import[/]")
            return
        action = parts[1].lower()

        if action == "list":
            if not self.notes:
                log.write("[gray]No notes found.[/]")
                return
            log.write("[bold]Notes:[/]")
            for t in self.notes:
                log.write(f"• {escape(t)}")
            return

        if action == "create":
            if len(parts) < 3:
                log.write("[yellow]note create <title>[/]")
                return
            title = parts[2]
            if title in self.notes:
                log.write("[red]Note already exists.[/]")
                return
            self.notes[title] = ""
            self.save_notes()
            log.write(f"[green]Created note:[/] {escape(title)}")
            return

        if action == "view":
            if len(parts) < 3:
                log.write("[yellow]note view <title>[/]")
                return
            title = parts[2]
            if title not in self.notes:
                log.write("[red]Note not found.[/]")
                return
            content = escape(self.notes[title]) or "[gray]<empty>[/]"
            log.write(f"[bold]{escape(title)}[/]\n{content}")
            return

        if action == "write":
            if len(parts) < 3 or " " not in parts[2]:
                log.write("[yellow]note write <title> <text>[/]")
                return
            title, text = parts[2].split(" ", 1)
            if title not in self.notes:
                log.write("[red]Note not found.[/]")
                return
            self.notes[title] = text
            self.save_notes()
            log.write(f"[green]Updated note:[/] {escape(title)}")
            return

        if action == "delete":
            if len(parts) < 3:
                log.write("[yellow]note delete <title>[/]")
                return
            title = parts[2]
            if title not in self.notes:
                log.write("[red]Note not found.[/]")
                return
            del self.notes[title]
            self.save_notes()
            log.write(f"[green]Deleted note:[/] {escape(title)}")
            return

        if action == "export":
            if len(parts) < 3:
                log.write("[yellow]note export <title>[/]")
                return
            title = parts[2]
            if title not in self.notes:
                log.write("[red]Note not found.[/]")
                return
            with open(Path.cwd() / f"{title}.txt", "w", encoding="utf-8") as f:
                f.write(self.notes[title])
            log.write(f"[green]Exported note:[/] {escape(title)}.txt")
            return

        if action == "import":
            if len(parts) < 3:
                log.write("[yellow]note import <filename>[/]")
                return
            file = Path(parts[2])
            if not file.exists() or not file.is_file():
                log.write("[red]File not found.[/]")
                return
            title = file.stem
            text = file.read_text("utf-8")
            self.notes[title] = text
            self.save_notes()
            log.write(f"[green]Imported note:[/] {escape(title)}")
            return

        log.write("[yellow]Unknown note command.[/]")

    # --------------------------------------------------
    # PANtham ASCII + COMMANDS
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
"""
        commands = """
[bold #ff4dff]PANTHAM COMMANDS[/]
[#b066ff]────────────────[/]

[#ffffff]note list[/]
[#ffffff]note create <title>[/]
[#ffffff]note view <title>[/]
[#ffffff]note write <title> <text>[/]
[#ffffff]note delete <title>[/]
[#ffffff]note export <title>[/]
[#ffffff]note import <file>[/]

[#888888]CTRL+L → clear[/]
[#888888]CTRL+C → quit[/]
[#888888]pantham off[/]
[#888888]help → show this menu[/]
"""
        log = self.query_one("#log", RichLog)
        log.write(f"[bold #ff4dff]{ascii_art}[/]")
        log.write(commands)

    def show_help(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]Available Commands[/]")
        log.write("""
pantham            → enter Pantham mode
pantham off        → exit Pantham mode
clear              → clear terminal
exit / quit        → quit terminal
help               → show this help menu
note list          → list all notes
note create <title>→ create new note
note view <title>  → view note
note write <title> <text> → write or overwrite note
note delete <title>→ delete note
note export <title>→ export note to txt
note import <file> → import note from txt
""")

# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    PanthaTerminal().run()
