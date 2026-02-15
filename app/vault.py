"""
PANTHA VAULT
============

Encrypted vault for Pantha Terminal notes.
"""

from __future__ import annotations

import time
import uuid
from typing import Dict, Optional

from encryption import PanthaCrypto, PanthaCryptoError
from storage import Storage, StorageError


class VaultError(Exception):
    pass


class VaultLockedError(VaultError):
    pass


class Vault:
    INDEX_FILE = "index.pantha"

    def __init__(self, base_dir: str):
        self.storage = Storage(base_dir)
        self.crypto = PanthaCrypto()
        self._password: Optional[str] = None
        self._index: Dict[str, Dict] = {}

    # -------------------------
    # VAULT LIFECYCLE
    # -------------------------

    def unlock(self, password: str):
        self._password = password
        if self._index_exists():
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

    # -------------------------
    # INDEX MANAGEMENT
    # -------------------------

    def _index_exists(self) -> bool:
        try:
            self.storage.read_bytes(self.INDEX_FILE)
            return True
        except StorageError:
            return False

    def _save_index(self):
        encrypted = self.crypto.encrypt(
            plaintext=str(self._index).encode(),
            password=self._password,
            aad=b"vault-index",
        )
        self.storage.write_bytes(self.INDEX_FILE, encrypted)

    def _load_index(self) -> Dict:
        encrypted = self.storage.read_bytes(self.INDEX_FILE)
        decrypted = self.crypto.decrypt(encrypted, self._password)
        return eval(decrypted.decode())  # controlled internal data

    # -------------------------
    # NOTE OPERATIONS
    # -------------------------

    def create_note(self, title: str, content: str) -> str:
        self._require_unlocked()
        note_id = str(uuid.uuid4())
        filename = f"{note_id}.note"
        encrypted = self.crypto.encrypt(
            content.encode(),
            self._password,
            aad=note_id.encode(),
        )
        self.storage.write_bytes(filename, encrypted)
        self._index[note_id] = {
            "title": title,
            "file": filename,
            "created": time.time(),
            "updated": time.time(),
        }
        self._save_index()
        return note_id

    def read_note_by_title(self, title: str) -> str:
        self._require_unlocked()
        note_id = self._get_id_by_title(title)
        if not note_id:
            raise VaultError("Note not found.")
        encrypted = self.storage.read_bytes(self._index[note_id]["file"])
        return self.crypto.decrypt(encrypted, self._password).decode()

    def update_note_by_title(self, title: str, new_content: str):
        self._require_unlocked()
        note_id = self._get_id_by_title(title)
        if not note_id:
            raise VaultError("Note not found.")
        encrypted = self.crypto.encrypt(
            new_content.encode(),
            self._password,
            aad=note_id.encode(),
        )
        self.storage.write_bytes(self._index[note_id]["file"], encrypted)
        self._index[note_id]["updated"] = time.time()
        self._save_index()

    def delete_note_by_title(self, title: str):
        self._require_unlocked()
        note_id = self._get_id_by_title(title)
        if not note_id:
            raise VaultError("Note not found.")
        self.storage.delete(self._index[note_id]["file"])
        del self._index[note_id]
        self._save_index()

    def list_notes(self) -> Dict[str, Dict]:
        self._require_unlocked()
        return dict(self._index)

    def _get_id_by_title(self, title: str) -> Optional[str]:
        for note_id, meta in self._index.items():
            if meta["title"] == title:
                return note_id
        return None

    # -------------------------
    # PASSWORD ROTATION
    # -------------------------

    def rotate_password(self, new_password: str):
        self._require_unlocked()
        for note_id, meta in self._index.items():
            encrypted = self.storage.read_bytes(meta["file"])
            rotated = self.crypto.rotate_password(
                encrypted,
                self._password,
                new_password,
            )
            self.storage.write_bytes(meta["file"], rotated)
        self._password = new_password
        self._save_index()
