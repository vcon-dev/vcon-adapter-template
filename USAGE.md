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
   add_lawful_basis(v, config.lawful_basis, granted_at=granted_at, party=0, dialog=0)
   ```

   If `LAWFUL_BASIS` (or `vcon.lawful_basis.lawful_basis` in YAML) is unset,
   this logs one warning per process and adds nothing — it does not raise
   and does not invent a basis. Set an invalid value and it raises
   `ValueError` at config-load time instead of silently building a bad vCon.
6. Pick a delivery mode in `config.yaml`: `delivery.mode: webhook` (generic
   HTTP + HMAC, the `webhook:` section) or `delivery.mode: conserver`
   (direct `POST {url}/vcon` to a vcon-server instance, the `conserver:`
   section — token header, `ingress_lists` query params). Both share the
   same retry/backoff/dead-letter-queue implementation in
   `webhook_delivery.py`.
7. If you don't need Prometheus — delete it and its dependency from `pyproject.toml`.
   (A `TranscriptionProvider` protocol and JWS signing were previously
   advertised in the README but never implemented — add them yourself if
   your adapter needs them, or ignore the now-corrected README note.)

## Step 4 — Verify spec compliance

Two test modules enforce spec compliance. **Keep them green.**

- `tests/test_vcon_builder.py` — smoke tests for the builder helpers,
  including `LawfulBasisConfig` and `add_lawful_basis()`.
- `tests/test_spec_compliance.py` — validates a sample vCon (built with a
  lawful-basis attachment) against the vendored official JSON schema at
  `tests/schema/vcon_json_schema.json` (see `tests/schema/SOURCE.md` for
  where it came from and how to refresh it), plus the non-negotiables the
  schema alone doesn't fully enforce (no `mimetype`, attachments carry
  `purpose`/`start`/`party`/`dialog`, every `body` is a string, no empty
  `meta`/`metadata`/`group`/`redacted`). Its `assert_spec_compliant()`
  function is written to be copied verbatim into another vCon-writing
  repo's own tests.

```bash
uv pip install -e ".[dev]"
pytest
```

## Step 5 — Publish

1. Push to `github.com/vcon-dev/vcon-<name>-adapter`
2. Add the repo to the [vcon super repo](https://github.com/vcon-dev/vcon) as a submodule
3. When ready, publish to PyPI (CI does this on tag push if `PYPI_API_TOKEN` is set)
