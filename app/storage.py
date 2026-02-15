"""
PANTHA STORAGE LAYER
===================

Handles safe disk persistence for encrypted data.
No encryption logic lives here — strictly storage.
"""

from __future__ import annotations

import os
import json
import tempfile
from pathlib import Path
from typing import Dict, Optional


class StorageError(Exception):
    pass


class Storage:
    """
    Secure storage backend for Pantha.
    """

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).expanduser().resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # PATH HELPERS
    # --------------------------------------------------

    def _path(self, name: str) -> Path:
        if not name:
            raise StorageError("Invalid storage key.")
        return self.base_dir / name

    # --------------------------------------------------
    # ATOMIC WRITE
    # --------------------------------------------------

    def write_bytes(self, name: str, data: bytes):
        path = self._path(name)

        try:
            with tempfile.NamedTemporaryFile(
                dir=self.base_dir,
                delete=False
            ) as tmp:
                tmp.write(data)
                tmp.flush()
                os.fsync(tmp.fileno())

            os.replace(tmp.name, path)

        except Exception as e:
            raise StorageError(f"Failed to write file: {e}")

    # --------------------------------------------------
    # READ
    # --------------------------------------------------

    def read_bytes(self, name: str) -> bytes:
        path = self._path(name)

        if not path.exists():
            raise StorageError("File does not exist.")

        try:
            return path.read_bytes()
        except Exception as e:
            raise StorageError(f"Failed to read file: {e}")

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    def delete(self, name: str):
        path = self._path(name)
        try:
            if path.exists():
                path.unlink()
        except Exception as e:
            raise StorageError(f"Failed to delete file: {e}")

    # --------------------------------------------------
    # LIST
    # --------------------------------------------------

    def list(self) -> list[str]:
        try:
            return [p.name for p in self.base_dir.iterdir() if p.is_file()]
        except Exception as e:
            raise StorageError(f"Failed to list files: {e}")

    # --------------------------------------------------
    # METADATA (JSON)
    # --------------------------------------------------

    def write_json(self, name: str, data: Dict):
        self.write_bytes(name, json.dumps(data).encode("utf-8"))

    def read_json(self, name: str) -> Dict:
        raw = self.read_bytes(name)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception as e:
            raise StorageError(f"Invalid JSON data: {e}")

