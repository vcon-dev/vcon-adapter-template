# Using This Template

This repo is a scaffold. Don't fork it — **clone it as a new repo**, replace placeholders, and customize.

## Step 1 — Create your repo

```bash
# Replace foo with your adapter name (kebab-case)
git clone https://github.com/vcon-dev/vcon-adapter-template.git vcon-foo-adapter
cd vcon-foo-adapter
rm -rf .git
git init
```

## Step 2 — Run find-and-replace

The template uses three placeholders. Replace them all in one pass:

```bash
# Adapter name (kebab-case) — e.g. signalwire
ADAPTER_NAME=foo
# Python package (snake_case) — e.g. signalwire_adapter
ADAPTER_PACKAGE=foo_adapter
# Human-readable platform name — e.g. SignalWire
SOURCE_PLATFORM=Foo

# Rename the package directory
mv "src/__ADAPTER_PACKAGE__" "src/${ADAPTER_PACKAGE}"

# Substitute placeholders in all files
find . -type f \( -name "*.py" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.md" -o -name "Dockerfile" \) \
  -not -path "./.git/*" \
  -exec sed -i.bak \
    -e "s/__ADAPTER_PACKAGE__/${ADAPTER_PACKAGE}/g" \
    -e "s/__ADAPTER_NAME__/${ADAPTER_NAME}/g" \
    -e "s/__SOURCE_PLATFORM__/${SOURCE_PLATFORM}/g" \
    {} \;
find . -name "*.bak" -delete
```

## Step 3 — Customize

1. Delete this `USAGE.md` file
2. Delete the "What this is" section at the top of `README.md`
3. Edit `config.example.yaml` — add your platform-specific options under `source:`
4. Implement your platform listener in `src/<package>/cli.py` (search for the `TODO: wire your source-platform listener` comment)
5. Call `add_lawful_basis()` for every vCon you build. Load its config once at
   startup with `LawfulBasisConfig.from_env()` (env vars only) or
   `LawfulBasisConfig.resolve(yaml_block=config.vcon.get("lawful_basis"), env=...)`
   (YAML + env, env wins per-field — this is what `config.load_config()`
   already wires into `Config.lawful_basis`). Then, for each vCon:

   ```python
   from datetime import datetime, timezone
   from .vcon_builder import add_lawful_basis

   granted_at = datetime.now(timezone.utc).isoformat()
   add_lawful_basis(v, config.lawful_basis, granted_at=granted_at, party=0, session=0)
   ```

   The attachment is scoped with `party` plus `session` (core-05). With one
   Session `session` may be omitted; with several, pass it, or
   `add_lawful_basis()` raises `ValueError` rather than guess.

   If `LAWFUL_BASIS` (or `vcon.lawful_basis.lawful_basis` in YAML) is unset,
   this logs one warning per process and adds nothing — it does not raise
   and does not invent a basis. Set an invalid value and it raises
   `ValueError` at config-load time instead of silently building a bad vCon.
6. Pick a delivery mode in `config.yaml`: `delivery.mode: webhook` (generic
   HTTP + HMAC, the `webhook:` section) or `delivery.mode: conserver`
   (direct `POST {url}/vcon` to a vcon-server instance, the `conserver:`
   section — token header, `ingress_lists` query params). Both share the
   same retry/backoff/dead-letter-queue implementation in
   `webhook_delivery.py`, and both call `finalize_vcon()` on your vCon dict
   before serializing it — see the next point.
7. Call `finalize_vcon(v.vcon_dict)` on every finished vCon before you
   serialize or store it *outside* `WebhookDelivery`/`ConserverDelivery`
   (those two already call it for you inside `deliver()`). It strips empty
   `meta`/`metadata` placeholders that vcon-lib 0.9.6 leaves on every
   `Dialog` added via `add_dialog()` — real objects with real content are
   left alone; only the empty `{}` vcon-lib defaults are removed. Skipping
   this on a path that bypasses both delivery classes (e.g. writing
   straight to local storage) will produce a vCon that fails schema
   validation.
8. `encoding: "json"` bodies (draft-ietf-vcon-vcon-core-05, Attachment Content / Analysis Content): `body` is
   the raw JSON value (object/array/number/bool/null), never a
   `json.dumps()`'d string — `add_lawful_basis()` follows this already. Do
   the same for any other JSON-encoded attachment or analysis body you
   write. When *reading* a JSON body back (yours or one from an older -02
   vCon), use `json_body(attachment)` — it returns the value as-is if it's
   already a JSON value, or `json.loads()`s it first if it's a legacy
   string, so you don't need to special-case either shape.
9. If you don't need Prometheus — delete it and its dependency from `pyproject.toml`.
   (A `TranscriptionProvider` protocol and JWS signing were previously
   advertised in the README but never implemented — add them yourself if
   your adapter needs them, or ignore the now-corrected README note.)

## Step 4 — Verify spec compliance

Three test modules enforce spec compliance (draft-ietf-vcon-vcon-core-05).
**Keep them green.**

- `tests/test_vcon_builder.py` — smoke tests for the builder helpers,
  including `LawfulBasisConfig`, `add_lawful_basis()`, `describe_session()`, `finalize_vcon()`,
  and `json_body()`.
- `tests/test_spec_compliance.py` — validates a sample vCon (built with a
  lawful-basis attachment) against the vendored official JSON schema at
  `tests/schema/vcon_json_schema.json` (see `tests/schema/SOURCE.md` for
  where it came from and how to refresh it), plus the non-negotiables the
  schema alone doesn't fully enforce (no `mimetype`, attachments carry
  `purpose`/`start`/`party` plus `dialog` or `session`, `body` is a string unless
  `encoding: "json"` — then it must NOT be a string, catching accidental
  double-encoding — no empty `meta`/`metadata`/`group`/`redacted`). Its
  `assert_spec_compliant()` function is written to be copied verbatim into
  another vCon-writing repo's own tests.
- `tests/test_core05_examples.py` — validates the core-05 Appendix B examples
  (`tests/schema/examples/`) against the same schema. The CDDL (Appendix D)
  is vendored alongside as `tests/schema/vcon.cddl`.

```bash
uv pip install -e ".[dev]"
pytest
```

## Step 5 — Publish

1. Push to `github.com/vcon-dev/vcon-<name>-adapter`
2. Add the repo to the [vcon super repo](https://github.com/vcon-dev/vcon) as a submodule
3. When ready, publish to PyPI (CI does this on tag push if `PYPI_API_TOKEN` is set)

## Sessions, dialogs and events (core-05)

One Session per conversation. `new_vcon()` creates Session 0; fill it in and
hang everything else off it:

```python
from vcon.dialog import Dialog
from vcon.event import Event
from vcon.party import Party
from .vcon_builder import describe_session, new_vcon

v = new_vcon(subject="Support call")
v.add_party(Party(name="Caller", tel="+15555550100"))  # party 0
v.add_party(Party(name="Agent", tel="+15555550101"))  # party 1

# Receivers (the endpoints) live on the Session. First receiver is the
# implied originator; pass originator= only when it is someone else.
describe_session(v, start="2026-01-02T12:00:00Z", duration=60, receivers=[0, 1])

# Contributors (who spoke or wrote) live on the Dialog. session=0 lists the
# Dialog index on the Session.
v.add_dialog(
    Dialog(type="text", start="2026-01-02T12:00:05Z", parties=[0], body="Hello"), session=0
)

# Joins, leaves, mutes and transfers are Events, not party_history.
v.add_event(Event(type="join", time="2026-01-02T12:00:00Z", sessions=0, party=1))

# Attachments need party plus dialog or session.
v.add_attachment(
    purpose="call_metadata",
    body={"queue": "support"},
    encoding="json",
    mediatype="application/json",
    party=0,
    session=0,
)
```

A second related conversation (a transfer target, a callback) is another
`v.add_session(Session(...))`, linked from the first with a Session_Reference.
Once a vCon has more than one Session, every attachment must say which one.
Dialog types written are `recording`, `text` and `incomplete` only.
