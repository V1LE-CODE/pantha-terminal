# app/vault.py
from __future__ import annotations
import os
import uuid
import time
from typing import Dict, Optional
from pathlib import Path
import json

from encryption import PanthaCrypto, PanthaCryptoError
from storage import Storage, StorageError


class VaultError(Exception):
    pass


class VaultLockedError(VaultError):
    pass


class Vault:
    """
    Encrypted vault for Pantha using title-based note management.
    """
    INDEX_FILE = "index.pantha"

    def __init__(self, base_dir: str):
        self.storage = Storage(base_dir)
        self.crypto = PanthaCrypto()
        self._password: Optional[str] = None
        self._index: Dict[str, Dict] = {}

    # ----------------- VAULT -----------------
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

    # ----------------- INDEX -----------------
    def _index_exists(self) -> bool:
        try:
            self.storage.read_bytes(self.INDEX_FILE)
            return True
        except StorageError:
            return False

    def _save_index(self):
        encrypted = self.crypto.encrypt(
            plaintext=json.dumps(self._index).encode(),
            password=self._password,
            aad=b"vault-index",
        )
        self.storage.write_bytes(self.INDEX_FILE, encrypted)

    def _load_index(self) -> Dict:
        encrypted = self.storage.read_bytes(self.INDEX_FILE)
        decrypted = self.crypto.decrypt(encrypted, self._password)
        return json.loads(decrypted.decode())

    # ----------------- NOTE METHODS -----------------
    def create_note(self, title: str, content: str) -> str:
        self._require_unlocked()
        if title in self._index:
            raise VaultError("Note already exists.")

        note_id = str(uuid.uuid4())
        filename = f"{note_id}.note"
        encrypted = self.crypto.encrypt(content.encode(), self._password, aad=note_id.encode())
        self.storage.write_bytes(filename, encrypted)

        self._index[title] = {"id": note_id, "file": filename, "created": time.time(), "updated": time.time()}
        self._save_index()
        return title

    def read_note_by_title(self, title: str) -> str:
        self._require_unlocked()
        meta = self._index.get(title)
        if not meta:
            raise VaultError("Note not found.")
        encrypted = self.storage.read_bytes(meta["file"])
        return self.crypto.decrypt(encrypted, self._password).decode()

    def update_note_by_title(self, title: str, new_content: str):
        self._require_unlocked()
        meta = self._index.get(title)
        if not meta:
            raise VaultError("Note not found.")
        encrypted = self.crypto.encrypt(new_content.encode(), self._password, aad=meta["id"].encode())
        self.storage.write_bytes(meta["file"], encrypted)
        meta["updated"] = time.time()
        self._save_index()

    def delete_note_by_title(self, title: str):
        self._require_unlocked()
        meta = self._index.pop(title, None)
        if not meta:
            raise VaultError("Note not found.")
        self.storage.delete(meta["file"])
        self._save_index()

    def list_notes(self) -> Dict[str, Dict]:
        self._require_unlocked()
        return dict(self._index)
