"""
PANTHA VAULT
============

High-level encrypted vault abstraction.
"""

from __future__ import annotations
import time
import uuid
from typing import Dict, Optional
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import json
import base64

class VaultError(Exception):
    pass

class VaultLockedError(VaultError):
    pass

class Vault:
    """
    Encrypted vault for Pantha Notes.
    """

    INDEX_FILE = "vault_index.json"

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._password: Optional[str] = None
        self._index: Dict[str, Dict] = {}  # note_id -> metadata

    # ---------------- VAULT LIFECYCLE ---------------- #

    def unlock(self, password: str):
        self._password = password
        if (self.base_dir / self.INDEX_FILE).exists():
            self._index = self._load_index()
        else:
            self._index = {}
            self._save_index()

    def lock(self):
        self._password = None
        self._index.clear()

    def is_unlocked(self) -> bool:
        return self._password is not None

    def _require_unlocked(self):
        if not self.is_unlocked():
            raise VaultLockedError("Vault is locked.")

    # ---------------- ENCRYPTION HELPERS ---------------- #

    def _derive_key(self, password: str) -> bytes:
        return PBKDF2(password, b"pantha_salt", dkLen=32)

    def _encrypt(self, plaintext: bytes) -> bytes:
        key = self._derive_key(self._password)
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)
        payload = cipher.nonce + tag + ciphertext
        return base64.b64encode(payload)

    def _decrypt(self, data: bytes) -> bytes:
        key = self._derive_key(self._password)
        raw = base64.b64decode(data)
        nonce = raw[:16]
        tag = raw[16:32]
        ciphertext = raw[32:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)

    # ---------------- INDEX MANAGEMENT ---------------- #

    def _save_index(self):
        data = json.dumps(self._index, ensure_ascii=False).encode()
        enc = self._encrypt(data)
        (self.base_dir / self.INDEX_FILE).write_bytes(enc)

    def _load_index(self) -> Dict:
        enc = (self.base_dir / self.INDEX_FILE).read_bytes()
        data = self._decrypt(enc)
        return json.loads(data.decode("utf-8"))

    # ---------------- NOTE OPERATIONS ---------------- #

    def create_note(self, title: str, content: str) -> str:
        self._require_unlocked()
        note_id = str(uuid.uuid4())
        filename = f"{note_id}.note"
        enc = self._encrypt(content.encode())
        (self.base_dir / filename).write_bytes(enc)
        self._index[note_id] = {
            "title": title,
            "file": filename,
            "created": time.time(),
            "updated": time.time(),
        }
        self._save_index()
        return note_id

    def read_note(self, note_id: str) -> str:
        self._require_unlocked()
        meta = self._index.get(note_id)
        if not meta:
            raise VaultError("Note not found.")
        enc = (self.base_dir / meta["file"]).read_bytes()
        return self._decrypt(enc).decode()

    def update_note(self, note_id: str, content: str):
        self._require_unlocked()
        meta = self._index.get(note_id)
        if not meta:
            raise VaultError("Note not found.")
        enc = self._encrypt(content.encode())
        (self.base_dir / meta["file"]).write_bytes(enc)
        meta["updated"] = time.time()
        self._save_index()

    def delete_note(self, note_id: str):
        self._require_unlocked()
        meta = self._index.pop(note_id, None)
        if not meta:
            raise VaultError("Note not found.")
        file_path = self.base_dir / meta["file"]
        if file_path.exists():
            file_path.unlink()
        self._save_index()

    def list_notes(self) -> Dict[str, Dict]:
        self._require_unlocked()
        return dict(self._index)

    # ---------------- TITLE-BASED HELPERS ---------------- #

    def _find_id_by_title(self, title: str) -> str:
        for note_id, meta in self._index.items():
            if meta["title"] == title:
                return note_id
        raise VaultError(f"Note with title '{title}' not found.")

    def read_note_by_title(self, title: str) -> str:
        note_id = self._find_id_by_title(title)
        return self.read_note(note_id)

    def update_note_by_title(self, title: str, content: str):
        note_id = self._find_id_by_title(title)
        self.update_note(note_id, content)

    def delete_note_by_title(self, title: str):
        note_id = self._find_id_by_title(title)
        self.delete_note(note_id)
