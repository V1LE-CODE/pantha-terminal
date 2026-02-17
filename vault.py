from __future__ import annotations
import os
import time
import uuid
import json
import base64
import hashlib
from typing import Dict, Optional
from pathlib import Path

# ---------------------------------------------------------
# OPTIONAL CRYPTO IMPORT
# ---------------------------------------------------------
CRYPTO_AVAILABLE = True
try:
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Random import get_random_bytes
except Exception:
    CRYPTO_AVAILABLE = False

# ---------------------------------------------------------
# ERRORS
# ---------------------------------------------------------
class VaultError(Exception): pass
class VaultLockedError(VaultError): pass
class VaultIntegrityError(VaultError): pass

# ---------------------------------------------------------
# VAULT
# ---------------------------------------------------------
class Vault:
    INDEX_FILE = "vault_index.bin"
    SALT_FILE = "vault.salt"

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self._password: Optional[str] = None
        self._index: Dict[str, Dict] = {}
        self._key: Optional[bytes] = None
        self._salt_path = self.base_dir / self.SALT_FILE

    # ------------------------------
    # PASSWORD CHECK / SET
    # ------------------------------
    def has_password(self) -> bool:
        return self._salt_path.exists()

    def set_password(self, password: str):
        if self.has_password():
            raise VaultError("Vault already has a password.")
        self._salt_path.write_bytes(os.urandom(32))
        self._key = self._derive_key(password, self._salt_path.read_bytes())
        self._password = password
        self._index = {}
        self._save_index()

    # ------------------------------
    # UNLOCK / LOCK
    # ------------------------------
    def unlock(self, password: str):
        if not self.has_password():
            raise VaultError("No password set. Use set_password first.")
        salt = self._salt_path.read_bytes()
        self._key = self._derive_key(password, salt)
        self._password = password

        index_path = self.base_dir / self.INDEX_FILE
        if index_path.exists():
            self._index = self._load_index()
        else:
            self._index = {}
            self._save_index()

    def lock(self):
        self._password = None
        self._key = None
        self._index.clear()

    def is_unlocked(self) -> bool:
        return self._key is not None

    def _require_unlocked(self):
        if not self.is_unlocked():
            raise VaultLockedError("Vault is locked.")

    # ------------------------------
    # KEY DERIVATION
    # ------------------------------
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        if CRYPTO_AVAILABLE:
            return PBKDF2(password, salt, dkLen=32, count=200000)
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200000, dklen=32)

    # ------------------------------
    # ENCRYPT / DECRYPT
    # ------------------------------
    def _encrypt(self, plaintext: bytes) -> bytes:
        self._require_unlocked()
        if CRYPTO_AVAILABLE:
            cipher = AES.new(self._key, AES.MODE_GCM)
            ciphertext, tag = cipher.encrypt_and_digest(plaintext)
            return base64.b64encode(cipher.nonce + tag + ciphertext)

        nonce = os.urandom(16)
        stream = hashlib.sha256(self._key + nonce).digest()
        encrypted = bytes(b ^ stream[i % len(stream)] for i, b in enumerate(plaintext))
        mac = hashlib.sha256(self._key + encrypted).digest()
        return base64.b64encode(nonce + mac + encrypted)

    def _decrypt(self, data: bytes) -> bytes:
        self._require_unlocked()
        raw = base64.b64decode(data)
        if CRYPTO_AVAILABLE:
            nonce, tag, ciphertext = raw[:16], raw[16:32], raw[32:]
            cipher = AES.new(self._key, AES.MODE_GCM, nonce=nonce)
            return cipher.decrypt_and_verify(ciphertext, tag)

        nonce, mac, ciphertext = raw[:16], raw[16:48], raw[48:]
        expected = hashlib.sha256(self._key + ciphertext).digest()
        if mac != expected:
            raise VaultIntegrityError("Invalid password or corrupted vault.")
        stream = hashlib.sha256(self._key + nonce).digest()
        return bytes(b ^ stream[i % len(stream)] for i, b in enumerate(ciphertext))

    # ------------------------------
    # INDEX
    # ------------------------------
    def _save_index(self):
        data = json.dumps(self._index, ensure_ascii=False).encode()
        enc = self._encrypt(data)
        (self.base_dir / self.INDEX_FILE).write_bytes(enc)

    def _load_index(self) -> Dict:
        enc = (self.base_dir / self.INDEX_FILE).read_bytes()
        data = self._decrypt(enc)
        return json.loads(data.decode("utf-8"))

    # ------------------------------
    # NOTE OPERATIONS
    # ------------------------------
    def create_note(self, title: str, content: str) -> str:
        self._require_unlocked()
        note_id = str(uuid.uuid4())
        filename = f"{note_id}.note"
        (self.base_dir / filename).write_bytes(self._encrypt(content.encode()))
        self._index[note_id] = {"title": title, "file": filename, "created": time.time(), "updated": time.time()}
        self._save_index()
        return note_id

    def read_note_by_title(self, title: str) -> str:
        return self.read_note(self._find_id_by_title(title))

    def read_note(self, note_id: str) -> str:
        self._require_unlocked()
        meta = self._index.get(note_id)
        if not meta:
            raise VaultError("Note not found.")
        enc = (self.base_dir / meta["file"]).read_bytes()
        return self._decrypt(enc).decode()

    def update_note_by_title(self, title: str, content: str):
        self.update_note(self._find_id_by_title(title), content)

    def update_note(self, note_id: str, content: str):
        self._require_unlocked()
        meta = self._index.get(note_id)
        if not meta:
            raise VaultError("Note not found.")
        (self.base_dir / meta["file"]).write_bytes(self._encrypt(content.encode()))
        meta["updated"] = time.time()
        self._save_index()

    def delete_note_by_title(self, title: str):
        self.delete_note(self._find_id_by_title(title))

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

    def _find_id_by_title(self, title: str) -> str:
        for note_id, meta in self._index.items():
            if meta["title"] == title:
                return note_id
        raise VaultError(f"Note '{title}' not found.")
