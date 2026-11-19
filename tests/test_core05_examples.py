"""Validate the draft-ietf-vcon-vcon-core-05 Appendix B examples against the
vendored Appendix C JSON schema (tests/schema/vcon_json_schema.json).

The schema covers the unsigned form only. B6 (JWS) is validated through its
decoded payload; B7 (JWE) is ciphertext and cannot be checked without the
key, so it is asserted to be rejected as an unsigned vCon.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

HERE = Path(__file__).parent
SCHEMA = json.loads((HERE / "schema" / "vcon_json_schema.json").read_text())
EXAMPLES = HERE / "schema" / "examples"

UNSIGNED = [
    "B1-two-party-call-inline-recording.json",
    "B2-email-thread-multipart.json",
    "B3-email-thread-text.json",
    "B4-two-party-call-external-recording.json",
    "B5-two-party-call-with-analysis.json",
    "B8-redacted.json",
    "B9-amended-signed.json",
]


def _validator() -> jsonschema.Draft7Validator:
    return jsonschema.Draft7Validator(SCHEMA, format_checker=jsonschema.FormatChecker())


def _load(name: str) -> Any:
    return json.loads((EXAMPLES / name).read_text())


@pytest.mark.parametrize("name", UNSIGNED)
def test_unsigned_example_validates(name: str) -> None:
    errors = list(_validator().iter_errors(_load(name)))
    assert not errors, [f"{list(e.path)}: {e.message}" for e in errors]


def test_signed_example_payload_validates() -> None:
    jws = _load("B6-signed.json")
    payload = jws["payload"]
    raw = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
    errors = list(_validator().iter_errors(json.loads(raw)))
    assert not errors, [f"{list(e.path)}: {e.message}" for e in errors]


def test_encrypted_example_is_not_an_unsigned_vcon() -> None:
    assert list(_validator().iter_errors(_load("B7-encrypted.json")))
