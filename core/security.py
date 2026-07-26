"""
security.py — encryption-at-rest for everything Alfred remembers.

Design goals:
- The encryption key is generated once, locally, and never transmitted anywhere.
- Key file permissions are locked down (owner read/write only) on POSIX systems.
- If encryption is disabled in config, this becomes a harmless pass-through,
  so the rest of the codebase never needs to branch on ENCRYPT_AT_REST.
"""

import os
import stat
from cryptography.fernet import Fernet

from config import KEY_FILE_PATH, ENCRYPT_AT_REST


def _load_or_create_key() -> bytes:
    if KEY_FILE_PATH.exists():
        return KEY_FILE_PATH.read_bytes()

    key = Fernet.generate_key()
    KEY_FILE_PATH.write_bytes(key)
    try:
        # Owner read/write only. Best-effort; ignored on platforms without chmod semantics.
        os.chmod(KEY_FILE_PATH, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return key


class Vault:
    """Encrypts/decrypts strings using a locally-stored symmetric key."""

    def __init__(self):
        self.enabled = ENCRYPT_AT_REST
        self._fernet = Fernet(_load_or_create_key()) if self.enabled else None

    def encrypt(self, plaintext: str) -> bytes:
        if not self.enabled:
            return plaintext.encode("utf-8")
        return self._fernet.encrypt(plaintext.encode("utf-8"))

    def decrypt(self, ciphertext: bytes) -> str:
        if not self.enabled:
            return ciphertext.decode("utf-8")
        return self._fernet.decrypt(ciphertext).decode("utf-8")


vault = Vault()
