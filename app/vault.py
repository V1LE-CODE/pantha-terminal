"""
PANTHA VAULT
============

High-level encrypted vault abstraction.
This is what main.py talks to.
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
    """
    Encrypted vault for Pantha.
    """

    INDEX_FILE = "index.pantha"

    def __init__(self, base_dir: str):
        self.storage = Storage(base_dir)
        self.crypto = PanthaCrypto()
        self._password: Optional[str] = None
        self._index: Dict[str, Dict] = {}

    # --------------------------------------------------
    # VAULT LIFECYCLE
    # --------------------------------------------------

    def unlock(self, password: str):
        """
        Unlock vault with password.
        """
        self._password = password

        if self._index_exists():
            self._index = self._load_index()
        else:
            self._index = {}
            self._save_index()

    def lock(self):
        """
        Lock vault and wipe sensitive memory.
        """
        self._password = None
        self._index.clear()

    def is_unlocked(self) -> bool:
        return self._password is not None

    def _require_unlocked(self):
        if not self.is_unlocked():
            raise VaultLockedError("Vault is locked.")

    # --------------------------------------------------
    # INDEX MANAGEMENT
    # --------------------------------------------------

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

    # --------------------------------------------------
    # NOTE OPERATIONS
    # --------------------------------------------------

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

    def read_note(self, note_id: str) -> str:
        self._require_unlocked()

        meta = self._index.get(note_id)
        if not meta:
            raise VaultError("Note not found.")

        encrypted = self.storage.read_bytes(meta["file"])
        decrypted = self.crypto.decrypt(encrypted, self._password)

        return decrypted.decode()

    def update_note(self, note_id: str, new_content: str):
        self._require_unlocked()

        meta = self._index.get(note_id)
        if not meta:
            raise VaultError("Note not found.")

        encrypted = self.crypto.encrypt(
            new_content.encode(),
            self._password,
            aad=note_id.encode(),
        )

        self.storage.write_bytes(meta["file"], encrypted)
        meta["updated"] = time.time()
        self._save_index()

    def delete_note(self, note_id: str):
        self._require_unlocked()

        meta = self._index.pop(note_id, None)
        if not meta:
            raise VaultError("Note not found.")

        self.storage.delete(meta["file"])
        self._save_index()

    # --------------------------------------------------
    # LISTING
    # --------------------------------------------------

    def list_notes(self) -> Dict[str, Dict]:
        self._require_unlocked()
        return dict(self._index)

    # --------------------------------------------------
    # PASSWORD ROTATION
    # --------------------------------------------------

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

