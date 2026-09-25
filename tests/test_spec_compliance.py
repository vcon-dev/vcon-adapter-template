"""Validate a sample vCon (built via this template's own builder, with a
lawful-basis attachment) against the vendored official JSON schema, plus the
non-negotiables the schema alone doesn't fully enforce.

`assert_spec_compliant()` is written to be copied verbatim into other
vCon-writing repos' test suites — it only depends on `jsonschema` (stdlib
`json`/`pathlib` aside) and a vendored schema file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from vcon.dialog import Dialog
from vcon.party import Party

from __ADAPTER_PACKAGE__.vcon_builder import LawfulBasisConfig, add_lawful_basis, new_vcon

SCHEMA_PATH = Path(__file__).parent / "schema" / "vcon_json_schema.json"


def _walk(node: Any) -> Any:
    """Yield every dict found anywhere in a nested JSON-like structure."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def assert_spec_compliant(vcon_dict: dict[str, Any], schema_path: Path | str) -> None:
    """Assert `vcon_dict` conforms to the vendored vCon core JSON schema and
    to the project's non-negotiable field-naming rules.

    Raises `AssertionError` with the collected schema errors (if any), or on
    the first non-negotiable violation.
    """
    schema = json.loads(Path(schema_path).read_text())
    validator = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(vcon_dict), key=lambda e: list(e.path))
    assert not errors, "schema violations:\n" + "\n".join(
        f"  {list(e.path)}: {e.message}" for e in errors
    )

    # `mediatype`, never `mimetype`, anywhere in the document.
    for node in _walk(vcon_dict):
        assert "mimetype" not in node, f"found legacy `mimetype` key in: {node}"

    # Every attachment carries purpose/start/party/dialog, and a string body.
    for att in vcon_dict.get("attachments", []):
        assert "purpose" in att, f"attachment missing `purpose`: {att}"
        assert "type" not in att, f"attachment uses legacy `type` instead of `purpose`: {att}"
        assert "start" in att, f"attachment missing `start`: {att}"
        assert "party" in att, f"attachment missing `party`: {att}"
        assert "dialog" in att, f"attachment missing `dialog`: {att}"
        if "body" in att:
            assert isinstance(att["body"], str), f"attachment `body` is not a string: {att}"

    # Every analysis body is a string too.
    for analysis in vcon_dict.get("analysis", []):
        if "body" in analysis:
            assert isinstance(analysis["body"], str), f"analysis `body` is not a string: {analysis}"
        assert "schema_version" not in analysis, f"legacy `schema_version` in: {analysis}"
        assert "vendor" in analysis, f"analysis missing required `vendor`: {analysis}"

    # No empty `meta`/`metadata`/`group`/`redacted` anywhere in the document.
    for node in _walk(vcon_dict):
        for key in ("meta", "metadata", "group", "redacted"):
            if key in node:
                assert node[key] not in ({}, [], None), f"empty `{key}` present in: {node}"


@pytest.fixture
def sample_vcon_dict() -> dict[str, Any]:
    """A representative vCon built through this template's own helpers,
    including a lawful-basis attachment, for the compliance check below.
    """
    v = new_vcon(subject="Spec compliance sample", extensions=["sip-signaling"])
    v.add_party(Party(name="Caller", tel="+15555550100"))
    v.add_party(Party(name="Agent", tel="+15555550101"))
    v.add_dialog(
        Dialog(
            type="recording",
            start="2026-01-02T12:00:00Z",
            parties=[0, 1],
            mediatype="audio/wav",
            url="https://example.com/recordings/sample.wav",
            content_hash="sha512-4kqcuBz1QLDYS93t2Bq6oGmVQI8-Fmcv5Ldg3f97vw",
        )
    )
    # vcon-lib 0.9.6's Dialog.to_dict() always emits empty `meta: {}` and
    # `metadata: {}`, which violates the "no empty meta/metadata" rule.
    # This is a vcon-lib bug (out of scope for this adapter template's
    # new_vcon() wrapper, which only touches build_new()'s output) — strip
    # them here so the sample is compliant, and see the CON-1081 report for
    # the flag.
    for dlg in v.vcon_dict["dialog"]:
        for key in ("meta", "metadata"):
            if dlg.get(key) == {}:
                del dlg[key]

    cfg = LawfulBasisConfig(
        lawful_basis="consent",
        purposes=("recording", "transcription"),
        jurisdiction="US-MA",
        expiration="2027-01-02T12:00:00Z",
        proof_mechanism="audio_recording",
        proof_description="Verbal consent captured at start of recording",
    )
    added = add_lawful_basis(v, cfg, granted_at="2026-01-02T12:00:00Z", party=0, dialog=0)
    assert added is True

    v.add_analysis(
        type="transcript",
        dialog=0,
        vendor="openai-whisper",
        product="whisper-large-v3",
        body=json.dumps({"text": "hello there"}),
        encoding="json",
        schema="https://datatracker.ietf.org/doc/draft-howe-vcon-wtf-extension/",
    )

    return v.vcon_dict  # type: ignore[no-any-return]


def test_schema_file_present_and_parses() -> None:
    schema = json.loads(SCHEMA_PATH.read_text())
    assert schema.get("title") or schema.get("$id"), "schema file looks empty/malformed"


def test_sample_vcon_with_lawful_basis_is_spec_compliant(
    sample_vcon_dict: dict[str, Any],
) -> None:
    assert_spec_compliant(sample_vcon_dict, SCHEMA_PATH)


def test_bare_new_vcon_is_spec_compliant() -> None:
    """`build_new()`'s own output, unmodified beyond `new_vcon()`'s cleanup,
    must also validate — this is the check called for by the card: if
    vcon-lib's `build_new()` output fails the schema, fix it in `new_vcon()`.
    """
    v = new_vcon()
    assert_spec_compliant(v.vcon_dict, SCHEMA_PATH)


def test_mimetype_key_fails_the_check() -> None:
    bad = new_vcon().vcon_dict
    bad["dialog"] = [{"type": "recording", "mimetype": "audio/wav"}]
    with pytest.raises(AssertionError, match="mimetype"):
        assert_spec_compliant(bad, SCHEMA_PATH)


def test_attachment_missing_dialog_index_fails_the_check() -> None:
    bad = new_vcon().vcon_dict
    bad["attachments"] = [
        {"purpose": "tags", "start": "2026-01-02T12:00:00Z", "party": 0, "body": "{}"}
    ]
    with pytest.raises((AssertionError, jsonschema.ValidationError)):
        assert_spec_compliant(bad, SCHEMA_PATH)


def test_non_string_analysis_body_fails_the_check() -> None:
    bad = new_vcon().vcon_dict
    bad["analysis"] = [
        {
            "type": "summary",
            "dialog": 0,
            "vendor": "v",
            "encoding": "none",
            "body": {"not": "a string"},
        }
    ]
    with pytest.raises(AssertionError, match="not a string"):
        assert_spec_compliant(bad, SCHEMA_PATH)
