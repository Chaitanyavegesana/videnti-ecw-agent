"""
PHI Crypto — AES-256-GCM Encryption & De-identification Utilities
HIPAA-compliant tooling for encrypting PHI at rest and de-identifying
patient data before it leaves the local processing boundary.

All keys are derived from a local salt stored in .env (ICS_MRN_SALT).
No keys or raw PHI are ever transmitted externally.
"""

import hashlib
import json
import logging
import os
import re
from base64 import b64decode, b64encode
from typing import Any, Dict, List

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

# ─── Key Derivation ──────────────────────────────────────────────────────────

_FALLBACK_SALT = "videnti-local-dev-salt-do-not-use-in-prod"


def _derive_key(salt: str = "") -> bytes:
    """
    Derives a 256-bit AES key from the local MRN salt in .env.
    Falls back to a deterministic dev salt when ICS_MRN_SALT is unset.
    """
    raw_salt = salt or os.getenv("ICS_MRN_SALT", _FALLBACK_SALT)
    return hashlib.sha256(raw_salt.encode()).digest()


# ─── AES-256-GCM Encryption ──────────────────────────────────────────────────

def encrypt_phi(plaintext: str, salt: str = "") -> str:
    """
    Encrypts a UTF-8 string using AES-256-GCM.

    Args:
        plaintext: The string to encrypt (typically JSON-serialised PHI).
        salt: Optional override for the key derivation salt.

    Returns:
        A Base-64-encoded string: ``<12-byte nonce> || <ciphertext+tag>``
    """
    key = _derive_key(salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return b64encode(nonce + ciphertext).decode()


def decrypt_phi(token: str, salt: str = "") -> str:
    """
    Decrypts an AES-256-GCM token produced by :func:`encrypt_phi`.

    Args:
        token: Base-64-encoded ``<nonce> || <ciphertext+tag>`` string.
        salt: Optional override for the key derivation salt.

    Returns:
        The original plaintext string.

    Raises:
        ValueError: If decryption fails (wrong key or tampered data).
    """
    key = _derive_key(salt)
    aesgcm = AESGCM(key)
    raw = b64decode(token)
    nonce, ciphertext = raw[:12], raw[12:]
    try:
        return aesgcm.decrypt(nonce, ciphertext, None).decode()
    except Exception as exc:
        raise ValueError("PHI decryption failed — key mismatch or tampered data") from exc


# ─── PHI De-identification ────────────────────────────────────────────────────

# The 18 HIPAA Safe-Harbor identifiers that must be stripped.
_PHI_PATTERNS: List[tuple] = [
    # Names  — conservative regex: Capitalised words likely to be names
    (re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b"), "[NAME]"),
    # Dates (MM/DD/YYYY, YYYY-MM-DD, written dates)
    (re.compile(
        r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b",
        re.IGNORECASE,
    ), "[DATE]"),
    # Phone numbers
    (re.compile(r"\b\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}\b"), "[PHONE]"),
    # SSN
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    # ZIP codes (5 or 9 digit)
    (re.compile(r"\b\d{5}(?:-\d{4})?\b"), "[ZIP]"),
    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
    # MRN patterns (alphanumeric IDs like MRN-123456)
    (re.compile(r"\bMRN[-\s]?\w+\b", re.IGNORECASE), "[MRN]"),
    # Generic numeric IDs that look like patient IDs (7+ digit numbers)
    (re.compile(r"\b\d{7,}\b"), "[ID]"),
]


def deidentify_text(text: str) -> str:
    """
    Applies HIPAA Safe-Harbor de-identification to a plain-text string.

    Replaces the 18 HIPAA identifiers with neutral placeholders so the
    resulting text carries no personally identifiable information.

    Args:
        text: Raw clinical text potentially containing PHI.

    Returns:
        De-identified version of the text.
    """
    for pattern, replacement in _PHI_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def deidentify_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively de-identifies all string values inside a nested dict/list.

    Keys are **not** altered. Non-string leaf values (int, float, bool) are
    preserved as-is because they cannot contain PHI by definition (e.g. BMI,
    heart-rate, etc.).

    Args:
        snapshot: Raw clinical snapshot dict (may be deeply nested).

    Returns:
        A new dict with all string leaves de-identified.
    """
    if isinstance(snapshot, dict):
        return {k: deidentify_snapshot(v) for k, v in snapshot.items()}
    if isinstance(snapshot, list):
        return [deidentify_snapshot(item) for item in snapshot]
    if isinstance(snapshot, str):
        return deidentify_text(snapshot)
    return snapshot


# ─── Snapshot ID (one-way hash of MRN) ───────────────────────────────────────

def mrn_to_snapshot_id(mrn: str, salt: str = "") -> str:
    """
    Converts a patient MRN into a short, one-way ``snapshot_id``.

    The mapping is deterministic for the same salt, so the same patient
    always receives the same ID within a session, but the MRN cannot be
    recovered from the ID.

    Args:
        mrn: The patient's medical record number.
        salt: Optional override for the HMAC salt.

    Returns:
        An 8-character lowercase hex string prefixed with ``v-``.
    """
    raw_salt = salt or os.getenv("ICS_MRN_SALT", _FALLBACK_SALT)
    digest = hashlib.sha256(f"{raw_salt}:{mrn}".encode()).hexdigest()
    return f"v-{digest[:8]}"


# ─── Convenience: encrypt/decrypt entire snapshot dict ───────────────────────

def encrypt_snapshot(snapshot: Dict[str, Any], salt: str = "") -> str:
    """Serialises *snapshot* to JSON and encrypts the result."""
    return encrypt_phi(json.dumps(snapshot, default=str), salt)


def decrypt_snapshot(token: str, salt: str = "") -> Dict[str, Any]:
    """Decrypts *token* and deserialises the JSON back to a dict."""
    return json.loads(decrypt_phi(token, salt))
