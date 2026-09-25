"""Spec compliance smoke tests for vCons built via the python `vcon` library.

These tests are the safety net for adapters built from this template. Keep them
green. If you add a new field to your adapter's vCon construction, add a test
here that proves it conforms to the spec.
"""

from __future__ import annotations

import json
import logging

import pytest

from __ADAPTER_PACKAGE__.vcon_builder import (
    VCON_SYNTAX,
    LawfulBasisConfig,
    add_lawful_basis,
    external_media_url,
    finalize_vcon,
    json_body,
    new_vcon,
    sha512_b64url,
)


def test_syntax_is_0_4_0() -> None:
    v = new_vcon()
    assert v.vcon_dict["vcon"] == "0.4.0"
    assert VCON_SYNTAX == "0.4.0"


def test_build_new_strips_group_and_redacted() -> None:
    v = new_vcon()
    assert "group" not in v.vcon_dict
    assert "redacted" not in v.vcon_dict


def test_subject_is_written_via_vcon_dict() -> None:
    v = new_vcon(subject="Test call")
    assert v.vcon_dict["subject"] == "Test call"


def test_extensions_listed_at_top_level() -> None:
    v = new_vcon(extensions=["sip-signaling", "lawful_basis"])
    assert v.vcon_dict["extensions"] == ["sip-signaling", "lawful_basis"]


def test_lib_add_attachment_uses_purpose_with_party_and_dialog() -> None:
    """vcon-lib >=0.9.2: `add_attachment` is spec-correct out of the box."""
    v = new_vcon()
    v.add_attachment(
        purpose="call_metadata",
        body=json.dumps({"foo": "bar"}),
        encoding="json",
        party=0,
        dialog=0,
    )
    att = v.vcon_dict["attachments"][0]
    assert att["purpose"] == "call_metadata"
    assert "type" not in att  # NEVER use legacy `type` field on attachments
    assert att["party"] == 0
    assert att["dialog"] == 0
    assert att["encoding"] == "json"
    assert json.loads(att["body"]) == {"foo": "bar"}


def test_lib_add_analysis_uses_schema_not_schema_version() -> None:
    v = new_vcon()
    v.add_analysis(
        type="transcript",
        dialog=0,
        vendor="openai-whisper",
        product="whisper-large-v3",
        body=json.dumps({"text": "hello"}),
        encoding="json",
        schema="https://datatracker.ietf.org/doc/draft-howe-vcon-wtf-extension/",
    )
    a = v.vcon_dict["analysis"][0]
    assert a["schema"].startswith("https://")
    assert "schema_version" not in a  # NEVER schema_version
    assert a["vendor"] == "openai-whisper"  # REQUIRED


def test_lib_add_analysis_requires_vendor() -> None:
    """The lib enforces `vendor` as a required kwarg."""
    v = new_vcon()
    with pytest.raises(TypeError):
        v.add_analysis(type="transcript", dialog=0, body="hi")  # type: ignore[call-arg]


def test_lib_add_tag_writes_party_and_dialog() -> None:
    """vcon-lib >=0.9.3 writes `party`/`dialog` on the tags attachment correctly."""
    v = new_vcon()
    v.add_tag("source", "test-platform")
    v.add_tag("session_id", "abc123")
    tags_atts = [a for a in v.vcon_dict["attachments"] if a.get("purpose") == "tags"]
    assert tags_atts, "add_tag should have produced a tags attachment"
    for att in tags_atts:
        assert att["party"] == 0
        assert att["dialog"] == 0


def test_content_hash_format() -> None:
    h = sha512_b64url(b"hello world")
    assert h.startswith("sha512-")
    # base64url has no padding, no `+/` chars
    assert "=" not in h
    assert "+" not in h
    assert "/" not in h


def test_external_media_dialog_has_url_and_content_hash() -> None:
    body = external_media_url(url="https://example.com/r.wav", content=b"x", mediatype="audio/wav")
    assert body["url"] == "https://example.com/r.wav"
    assert body["content_hash"].startswith("sha512-")
    assert body["mediatype"] == "audio/wav"


@pytest.mark.parametrize("legacy_field", ["appended", "must_support"])
def test_no_legacy_field_names_in_serialized_vcon(legacy_field: str) -> None:
    """`appended` and `must_support` are legacy vcon-mcp column names — never written out."""
    v = new_vcon()
    v.add_analysis(type="t", vendor="v", body="b", dialog=0)
    v.add_attachment(purpose="p", body=json.dumps({}), encoding="json", party=0, dialog=0)
    v.add_tag("x", "y")
    serialized = json.dumps(v.vcon_dict)
    assert legacy_field not in serialized


# --- LawfulBasisConfig -------------------------------------------------


def test_lawful_basis_config_defaults_to_unset() -> None:
    cfg = LawfulBasisConfig(lawful_basis=None)
    assert cfg.lawful_basis is None
    assert cfg.purposes == ("recording",)


def test_lawful_basis_config_rejects_invalid_basis() -> None:
    with pytest.raises(ValueError, match="invalid lawful_basis"):
        LawfulBasisConfig(lawful_basis="because_i_said_so")


def test_lawful_basis_config_from_env_parses_all_fields() -> None:
    env = {
        "LAWFUL_BASIS": "consent",
        "LAWFUL_BASIS_PURPOSE": "recording, transcription,analysis",
        "LAWFUL_BASIS_JURISDICTION": "US-MA",
        "LAWFUL_BASIS_EXPIRATION": "2026-01-02T12:00:00Z",
        "LAWFUL_BASIS_PROOF_MECHANISM": "external_system",
        "LAWFUL_BASIS_PROOF_DESCRIPTION": "consent captured via IVR",
    }
    cfg = LawfulBasisConfig.from_env(env)
    assert cfg.lawful_basis == "consent"
    assert cfg.purposes == ("recording", "transcription", "analysis")
    assert cfg.jurisdiction == "US-MA"
    assert cfg.expiration == "2026-01-02T12:00:00Z"
    assert cfg.proof_mechanism == "external_system"
    assert cfg.proof_description == "consent captured via IVR"


def test_lawful_basis_config_from_env_empty_env_is_unset() -> None:
    cfg = LawfulBasisConfig.from_env({})
    assert cfg.lawful_basis is None
    assert cfg.purposes == ("recording",)


def test_lawful_basis_config_from_env_rejects_invalid_basis() -> None:
    with pytest.raises(ValueError, match="invalid lawful_basis"):
        LawfulBasisConfig.from_env({"LAWFUL_BASIS": "vibes"})


def test_lawful_basis_config_from_yaml_parses_block() -> None:
    block = {
        "lawful_basis": "legitimate_interests",
        "purposes": ["recording", "analysis"],
        "jurisdiction": "EU",
        "expiration": None,
        "proof_mechanism": "external_system",
        "proof_description": "synthetic corpus",
    }
    cfg = LawfulBasisConfig.from_yaml(block)
    assert cfg.lawful_basis == "legitimate_interests"
    assert cfg.purposes == ("recording", "analysis")
    assert cfg.jurisdiction == "EU"
    assert cfg.expiration is None
    assert cfg.proof_mechanism == "external_system"


def test_lawful_basis_config_resolve_env_overrides_yaml_per_field() -> None:
    yaml_block = {
        "lawful_basis": "consent",
        "jurisdiction": "US-MA",
        "proof_mechanism": "external_system",
    }
    env = {"LAWFUL_BASIS_JURISDICTION": "US-CA"}
    cfg = LawfulBasisConfig.resolve(yaml_block=yaml_block, env=env)
    # Overridden by env
    assert cfg.jurisdiction == "US-CA"
    # Falls through from YAML since env didn't set it
    assert cfg.lawful_basis == "consent"
    assert cfg.proof_mechanism == "external_system"


def test_lawful_basis_config_resolve_with_nothing_set_is_unset() -> None:
    cfg = LawfulBasisConfig.resolve(yaml_block=None, env={})
    assert cfg.lawful_basis is None


# --- add_lawful_basis ---------------------------------------------------


def test_add_lawful_basis_unset_logs_warning_and_adds_nothing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    import __ADAPTER_PACKAGE__.vcon_builder as vb

    vb._warned_no_lawful_basis = False  # isolate from other tests / warn-once state
    v = new_vcon()
    cfg = LawfulBasisConfig(lawful_basis=None)

    with caplog.at_level(logging.WARNING):
        added = add_lawful_basis(v, cfg, granted_at="2026-01-02T12:00:00Z")

    assert added is False
    assert v.vcon_dict["attachments"] == []
    assert "extensions" not in v.vcon_dict or "lawful_basis" not in v.vcon_dict.get(
        "extensions", []
    )
    assert any("lawful_basis" in rec.message.lower() for rec in caplog.records)


def test_add_lawful_basis_unset_warns_once_per_process(caplog: pytest.LogCaptureFixture) -> None:
    import __ADAPTER_PACKAGE__.vcon_builder as vb

    vb._warned_no_lawful_basis = False
    cfg = LawfulBasisConfig(lawful_basis=None)

    with caplog.at_level(logging.WARNING):
        add_lawful_basis(new_vcon(), cfg, granted_at="2026-01-02T12:00:00Z")
        add_lawful_basis(new_vcon(), cfg, granted_at="2026-01-02T12:00:00Z")

    warnings = [r for r in caplog.records if "lawful_basis" in r.message.lower()]
    assert len(warnings) == 1


def test_add_lawful_basis_set_produces_exact_attachment_shape() -> None:
    import __ADAPTER_PACKAGE__.vcon_builder as vb

    vb._warned_no_lawful_basis = False
    v = new_vcon()
    cfg = LawfulBasisConfig(
        lawful_basis="consent",
        purposes=("recording", "transcription"),
        jurisdiction="US-MA",
        expiration="2026-01-02T12:00:00Z",
        proof_mechanism="audio_recording",
        proof_description="Verbal consent captured at start of recording",
    )

    added = add_lawful_basis(v, cfg, granted_at="2025-01-02T12:15:30Z", party=0, dialog=0)

    assert added is True
    atts = [a for a in v.vcon_dict["attachments"] if a["purpose"] == "lawful_basis"]
    assert len(atts) == 1
    att = atts[0]

    assert att["purpose"] == "lawful_basis"
    assert "type" not in att  # never the legacy `type` field
    assert att["start"] == "2025-01-02T12:15:30Z"
    assert att["party"] == 0
    assert att["dialog"] == 0
    assert att["encoding"] == "json"
    assert att["mediatype"] == "application/json"
    # -04 §2.3.2: encoding: "json" -> body is the raw JSON value, not a
    # json.dumps() string.
    assert not isinstance(att["body"], str)
    assert isinstance(att["body"], dict)

    body = att["body"]
    assert body["lawful_basis"] == "consent"
    assert body["expiration"] == "2026-01-02T12:00:00Z"
    assert body["jurisdiction"] == "US-MA"
    assert body["purpose_grants"] == [
        {"purpose": "recording", "granted": True, "granted_at": "2025-01-02T12:15:30Z"},
        {"purpose": "transcription", "granted": True, "granted_at": "2025-01-02T12:15:30Z"},
    ]
    assert body["proof_mechanisms"] == [
        {
            "mechanism_type": "audio_recording",
            "description": "Verbal consent captured at start of recording",
        }
    ]

    assert v.vcon_dict["extensions"] == ["lawful_basis"]


def test_add_lawful_basis_omits_optional_keys_when_not_configured() -> None:
    v = new_vcon()
    cfg = LawfulBasisConfig(lawful_basis="legitimate_interests", expiration=None)

    add_lawful_basis(v, cfg, granted_at="2026-01-02T12:00:00Z")

    att = next(a for a in v.vcon_dict["attachments"] if a["purpose"] == "lawful_basis")
    body = att["body"]
    assert "expiration" not in body
    assert "jurisdiction" not in body
    assert "proof_mechanisms" not in body


def test_add_lawful_basis_does_not_duplicate_extension() -> None:
    v = new_vcon(extensions=["lawful_basis", "sip-signaling"])
    cfg = LawfulBasisConfig(lawful_basis="consent", expiration="2026-01-02T12:00:00Z")

    add_lawful_basis(v, cfg, granted_at="2025-01-02T12:15:30Z")

    assert v.vcon_dict["extensions"].count("lawful_basis") == 1
    assert "sip-signaling" in v.vcon_dict["extensions"]


# --- finalize_vcon --------------------------------------------------------


def test_finalize_vcon_strips_empty_meta_from_real_dialog() -> None:
    """Reproduces vcon-lib 0.9.6's actual bug: `Dialog.__init__` defaults
    both `meta` and `metadata` to `{}`, and `Dialog.to_dict()` includes any
    attribute that isn't `None` — so `add_dialog()` always emits both keys
    as empty objects unless something strips them.
    """
    from vcon.dialog import Dialog

    v = new_vcon()
    v.add_dialog(
        Dialog(
            type="recording",
            start="2026-01-02T12:00:00Z",
            parties=[0],
            mediatype="audio/wav",
            url="https://example.com/r.wav",
            content_hash="sha512-abc",
        )
    )
    # Confirm the bug is actually present before asserting the fix removes it.
    assert v.vcon_dict["dialog"][0].get("meta") == {}
    assert v.vcon_dict["dialog"][0].get("metadata") == {}

    result = finalize_vcon(v.vcon_dict)

    assert "meta" not in result["dialog"][0]
    assert "metadata" not in result["dialog"][0]
    # Real fields survive untouched.
    assert result["dialog"][0]["mediatype"] == "audio/wav"


def test_finalize_vcon_returns_the_same_dict_it_was_given() -> None:
    v = new_vcon()
    result = finalize_vcon(v.vcon_dict)
    assert result is v.vcon_dict


def test_finalize_vcon_strips_empty_meta_metadata_anywhere_nested() -> None:
    vcon_dict = {
        "vcon": "0.4.0",
        "parties": [{"name": "a", "meta": {}}],
        "attachments": [{"purpose": "tags", "metadata": {}, "body": "{}"}],
        "dialog": [{"type": "text", "meta": {}, "metadata": {"has": "content"}}],
    }

    result = finalize_vcon(vcon_dict)

    assert "meta" not in result["parties"][0]
    assert "metadata" not in result["attachments"][0]
    assert "meta" not in result["dialog"][0]
    # Non-empty metadata is left alone.
    assert result["dialog"][0]["metadata"] == {"has": "content"}


def test_finalize_vcon_leaves_vcon_without_empty_placeholders_unchanged() -> None:
    v = new_vcon(subject="no placeholders here")
    before = json.dumps(v.vcon_dict, sort_keys=True)
    finalize_vcon(v.vcon_dict)
    after = json.dumps(v.vcon_dict, sort_keys=True)
    assert before == after


# --- json_body -------------------------------------------------------------


def test_json_body_returns_raw_value_body_unchanged() -> None:
    """-04-shaped attachment: body is already the JSON value."""
    att = {"purpose": "tags", "encoding": "json", "body": {"department": "sales"}}
    assert json_body(att) == {"department": "sales"}


def test_json_body_parses_legacy_string_body() -> None:
    """-02-shaped (or pre-fix) attachment: body was json.dumps()'d."""
    att = {"purpose": "tags", "encoding": "json", "body": json.dumps({"department": "sales"})}
    assert json_body(att) == {"department": "sales"}


def test_json_body_handles_list_and_scalar_json_values() -> None:
    assert json_body({"encoding": "json", "body": [1, 2, 3]}) == [1, 2, 3]
    assert json_body({"encoding": "json", "body": 42}) == 42
    assert json_body({"encoding": "json", "body": True}) is True
    assert json_body({"encoding": "json", "body": None}) is None


def test_json_body_rejects_non_json_encoding() -> None:
    att = {"purpose": "tags", "encoding": "none", "body": "plain text"}
    with pytest.raises(ValueError, match="encoding"):
        json_body(att)


def test_json_body_on_real_add_lawful_basis_attachment_round_trips() -> None:
    v = new_vcon()
    cfg = LawfulBasisConfig(lawful_basis="consent", expiration="2026-01-02T12:00:00Z")
    add_lawful_basis(v, cfg, granted_at="2025-01-02T12:15:30Z")
    att = next(a for a in v.vcon_dict["attachments"] if a["purpose"] == "lawful_basis")

    assert json_body(att) == att["body"]
    assert json_body(att)["lawful_basis"] == "consent"
