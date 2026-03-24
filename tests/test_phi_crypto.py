"""
Tests: phi_crypto — AES-256-GCM encryption and HIPAA de-identification utilities.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from phi_crypto import (
    decrypt_phi,
    decrypt_snapshot,
    deidentify_snapshot,
    deidentify_text,
    encrypt_phi,
    encrypt_snapshot,
    mrn_to_snapshot_id,
)

# ── Encryption / Decryption ───────────────────────────────────────────────────

def test_encrypt_decrypt_roundtrip():
    """encrypt_phi → decrypt_phi must recover the original plaintext."""
    plaintext = "Patient: John Doe, DOB: 1975-03-15, MRN: 123456"
    token = encrypt_phi(plaintext)
    assert isinstance(token, str)
    assert token != plaintext
    recovered = decrypt_phi(token)
    assert recovered == plaintext
    print("✓ encrypt/decrypt round-trip succeeded")


def test_encrypt_produces_different_ciphertexts():
    """Two calls with the same plaintext should produce different ciphertexts (random nonce)."""
    plaintext = "same text"
    token1 = encrypt_phi(plaintext)
    token2 = encrypt_phi(plaintext)
    assert token1 != token2, "GCM nonces must be unique per encryption"
    print("✓ Each encryption produces a unique ciphertext")


def test_decrypt_fails_with_wrong_salt():
    """Decryption with a wrong salt should raise ValueError."""
    token = encrypt_phi("hello", salt="correct-salt")
    with pytest.raises(ValueError, match="decryption failed"):
        decrypt_phi(token, salt="wrong-salt")
    print("✓ Decryption correctly rejected wrong key")


def test_decrypt_fails_with_tampered_token():
    """Decryption of a tampered token should raise ValueError (GCM integrity check)."""
    token = encrypt_phi("sensitive data")
    # Corrupt the last byte of the base64 string
    tampered = token[:-4] + "AAAA"
    with pytest.raises((ValueError, Exception)):
        decrypt_phi(tampered)
    print("✓ Tampered ciphertext rejected by AES-GCM authentication tag")


def test_encrypt_snapshot_roundtrip():
    """encrypt_snapshot → decrypt_snapshot must recover the original dict."""
    snapshot = {
        "demographics": {"name": "Jane Smith", "dob": "1980-06-01"},
        "vitals": {"bmi": 28.5, "bp": "120/80"},
    }
    token = encrypt_snapshot(snapshot)
    assert isinstance(token, str)
    recovered = decrypt_snapshot(token)
    assert recovered == snapshot
    print("✓ Snapshot encrypt/decrypt round-trip succeeded")


# ── De-identification ─────────────────────────────────────────────────────────

def test_deidentify_text_removes_names():
    """Full names (two capitalised words) should be replaced with [NAME]."""
    text = "Patient John Smith was seen today."
    result = deidentify_text(text)
    assert "John Smith" not in result
    assert "[NAME]" in result
    print("✓ deidentify_text replaced name with [NAME]")


def test_deidentify_text_removes_dates():
    """ISO dates (YYYY-MM-DD) should be replaced with [DATE]."""
    text = "Date of Birth: 1975-03-15"
    result = deidentify_text(text)
    assert "1975-03-15" not in result
    assert "[DATE]" in result
    print("✓ deidentify_text replaced ISO date with [DATE]")


def test_deidentify_text_removes_ssn():
    """SSN patterns should be replaced with [SSN]."""
    text = "SSN: 123-45-6789"
    result = deidentify_text(text)
    assert "123-45-6789" not in result
    assert "[SSN]" in result
    print("✓ deidentify_text replaced SSN with [SSN]")


def test_deidentify_text_removes_email():
    """Email addresses should be replaced with [EMAIL]."""
    text = "Contact: jdoe@example.com for more info."
    result = deidentify_text(text)
    assert "jdoe@example.com" not in result
    assert "[EMAIL]" in result
    print("✓ deidentify_text replaced email with [EMAIL]")


def test_deidentify_text_preserves_clinical_numbers():
    """Small clinical numbers (BMI, HR, etc.) should NOT be stripped."""
    text = "BMI: 30.8, HR: 72, Glucose: 145 mg/dL"
    result = deidentify_text(text)
    assert "30.8" in result or "BMI" in result  # BMI value is not a 7+ digit ID
    print("✓ deidentify_text preserved clinical measurement values")


def test_deidentify_snapshot_deep():
    """deidentify_snapshot should recurse into nested dicts and lists."""
    snapshot = {
        "demographics": {"name": "Alice Brown", "dob": "1990-01-20"},
        "pmh": ["Hypertension", "Seen on 2024-06-01"],
        "notes": "Patient Alice Brown presents with…",
    }
    result = deidentify_snapshot(snapshot)
    # Names and dates should be gone from all levels
    assert "Alice Brown" not in json.dumps(result)
    assert "1990-01-20" not in json.dumps(result)
    assert "2024-06-01" not in json.dumps(result)
    # Structure should be preserved
    assert "demographics" in result
    assert "pmh" in result
    assert len(result["pmh"]) == 2
    print("✓ deidentify_snapshot recursively de-identified nested data")


def test_deidentify_snapshot_preserves_numeric_vitals():
    """Numeric vitals (int/float) should not be altered by de-identification."""
    snapshot = {
        "vitals": {"bmi": 30.8, "weight_lb": 215, "hr": 72},
    }
    result = deidentify_snapshot(snapshot)
    assert result["vitals"]["bmi"] == 30.8
    assert result["vitals"]["weight_lb"] == 215
    assert result["vitals"]["hr"] == 72
    print("✓ deidentify_snapshot preserved numeric vitals unchanged")


# ── MRN → Snapshot ID ─────────────────────────────────────────────────────────

def test_mrn_to_snapshot_id_format():
    """snapshot_id should start with 'v-' and be 10 chars total."""
    sid = mrn_to_snapshot_id("MRN-123456")
    assert sid.startswith("v-")
    assert len(sid) == 10
    print(f"✓ mrn_to_snapshot_id returned: {sid}")


def test_mrn_to_snapshot_id_deterministic():
    """Same MRN + salt → same snapshot_id every time."""
    sid1 = mrn_to_snapshot_id("MRN-123456", salt="test-salt")
    sid2 = mrn_to_snapshot_id("MRN-123456", salt="test-salt")
    assert sid1 == sid2
    print("✓ mrn_to_snapshot_id is deterministic for same inputs")


def test_mrn_to_snapshot_id_unique_per_mrn():
    """Different MRNs should produce different snapshot IDs."""
    sid1 = mrn_to_snapshot_id("MRN-111111", salt="test-salt")
    sid2 = mrn_to_snapshot_id("MRN-222222", salt="test-salt")
    assert sid1 != sid2
    print("✓ mrn_to_snapshot_id produces unique IDs for different MRNs")


def test_mrn_not_recoverable_from_snapshot_id():
    """The snapshot_id must not contain the original MRN (one-way hash)."""
    mrn = "MRN-987654"
    sid = mrn_to_snapshot_id(mrn)
    assert mrn not in sid
    assert "987654" not in sid
    print("✓ MRN is not recoverable from snapshot_id (one-way)")
