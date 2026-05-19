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
5. If you don't need transcription, JWS signing, or Prometheus — delete those features and their dependencies from `pyproject.toml`

## Step 4 — Verify spec compliance

The smoke tests in `tests/test_vcon_builder.py` enforce the spec compliance checklist. **Keep them green.**

```bash
uv pip install -e ".[dev]"
pytest
```

## Step 5 — Publish

1. Push to `github.com/vcon-dev/vcon-<name>-adapter`
2. Add the repo to the [vcon super repo](https://github.com/vcon-dev/vcon) as a submodule
3. When ready, publish to PyPI (CI does this on tag push if `PYPI_API_TOKEN` is set)
