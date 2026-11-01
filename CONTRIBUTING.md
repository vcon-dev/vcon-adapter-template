# Contributing

## Spec Compliance Checklist

**Every PR that touches vCon construction MUST tick these boxes.** Based on [vcon-speckit](https://github.com/vcon-dev/vcon-speckit) non-negotiables.

**Always use the `vcon` library helpers** (`Vcon.add_party`, `add_session`, `add_dialog`, `add_event`, `add_attachment`, `add_analysis`, `add_tag`) rather than writing to `vcon_dict[...]` directly. The lib (`vcon>=1.0.0,<2`) is spec-correct for core-05 out of the box.

### Top-level vCon
- [ ] `vcon` syntax param is exactly `"0.5.0"` (NOT `0.0.1`, NOT `0.0.2`)
- [ ] `uuid` is a v4 UUID string
- [ ] All timestamps are ISO-8601 with timezone (`Z` or explicit offset)
- [ ] No `group: []` or `redacted: {}` left over from `Vcon.build_new()`
- [ ] `subject` written via `v.vcon_dict["subject"]` (no setter exists on the lib)

### Sessions, dialogs and events (core-05)
- [ ] One Session per conversation (`new_vcon()` makes Session 0; `describe_session()` fills it in); at least one Session whenever `dialog` or `events` is non-empty
- [ ] Receivers on the Session (`parties`, first is the implied originator; `originator` only when different); contributors on the Dialog (`parties`)
- [ ] `Vcon.add_dialog(dialog, session=<index>)` so the Session lists its Dialogs
- [ ] No `party_history`, no Dialog `originator`, no transfer Dialogs; joins, leaves and transfers are Events via `Vcon.add_event`
- [ ] Dialog types written: `recording`, `text`, `incomplete` only (not `audio`/`video`)

### Analysis objects
- [ ] Use `Vcon.add_analysis(type, dialog, vendor, body, encoding, schema, product, ...)` — the lib produces spec-correct output and enforces `vendor` as a required kwarg
- [ ] Field name is `schema`, NEVER `schema_version` (the lib's kwarg is already `schema`)
- [ ] `body` is always a string. If JSON, paired with `encoding="json"`
- [ ] WTF transcripts go in `analysis[]` (NOT `attachments[]`)
- [ ] Transcript analysis has `schema=<WTF draft URL>`, `encoding="json"`, `vendor="<provider>"`, `product="<model>"`

### Attachment objects
- [ ] Use `Vcon.add_attachment(purpose, body, encoding, party, dialog=..., session=..., ...)`
- [ ] Field name is `purpose`, NEVER `type` (the lib's keyword arg is already `purpose`, so this happens automatically)
- [ ] Always pass `party` plus `dialog` or `session`. The lib defaults the scope to the only Session when there is exactly one; with several Sessions pass it explicitly. Never widen a dialog index to a Session
- [ ] Lawful basis: `add_lawful_basis()` scopes with `party` plus `session`
- [ ] For JSON-bodied attachments: `encoding="json"` with the raw JSON value as `body` (not a `json.dumps()` string) and `mediatype="application/json"`

### Tags attachment
- [ ] Use `Vcon.add_tag(name, value)` directly. The lib scopes the tags attachment to every Session (adding an empty one if none exists).

### External media
- [ ] `url` AND `content_hash` both present
- [ ] `content_hash` formatted as `sha512-<base64url-of-digest>` (NOT hex)

### Extension naming traps
- [ ] Use `amended` (NOT `appended` — that's a legacy vcon-mcp column name)
- [ ] Use `critical` (NOT `must_support` — also legacy)
- [ ] Any extension used is listed in top-level `extensions[]`

### Lawful basis (if recording consent is tracked)
- [ ] `lawful_basis` attachment uses `type: "lawful_basis"` (extension-defined exception — see speckit)
- [ ] `"lawful_basis"` added to top-level `extensions[]`
- [ ] For synthetic test data: use `lawful_basis: "legitimate_interests"` + `proof_mechanism: external_system`

### Synthetic test data
- [ ] Parties marked with `validation: "synthetic"`
- [ ] `purpose: "synthetic_data_consent"` attachment present

## Dev Workflow

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
ruff check .
mypy src/
```

## Releasing

1. Update `CHANGELOG.md` with a new version section
2. Bump version in `pyproject.toml`
3. Tag: `git tag vX.Y.Z && git push --tags`
4. CI publishes to PyPI on tag push (if configured)
