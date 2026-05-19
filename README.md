# vcon-__ADAPTER_NAME__-adapter

> Adapter that converts **__SOURCE_PLATFORM__** events into [vCon](https://datatracker.ietf.org/doc/draft-ietf-vcon-vcon-core/) (Virtual Conversation) objects and delivers them to a [vCon server](https://github.com/vcon-dev/vcon-server) or other downstream consumer.

**Spec target:** IETF `draft-ietf-vcon-vcon-core-02`, vCon syntax `"0.4.0"`.

[![Tests](https://github.com/vcon-dev/vcon-__ADAPTER_NAME__-adapter/actions/workflows/test.yml/badge.svg)](https://github.com/vcon-dev/vcon-__ADAPTER_NAME__-adapter/actions/workflows/test.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What this is

This repo was generated from [vcon-adapter-template](https://github.com/vcon-dev/vcon-adapter-template). Before publishing, do a global find-and-replace on:

| Placeholder | Replace with | Example |
|------------|--------------|---------|
| `__ADAPTER_NAME__` | kebab-case adapter slug | `signalwire` |
| `__ADAPTER_PACKAGE__` | snake_case Python package | `signalwire_adapter` |
| `__SOURCE_PLATFORM__` | human-readable platform name | `SignalWire` |

Then delete this section.

---

## Features

- Spec-compliant vCons (syntax `0.4.0`, `mediatype`, `base64url`, ISO-8601 UTC timestamps)
- Pluggable transcription via `TranscriptionProvider` protocol (WTF format in `analysis[]`)
- HMAC-SHA256 webhook body signing (`X-Hub-Signature-256`)
- Idempotent delivery (`Idempotency-Key` header = vCon UUID)
- Exponential-backoff retries with dead-letter queue
- Optional JWS signing (RS256) of each vCon before delivery
- `/healthz` + Prometheus `/metrics` endpoints
- Configurable via YAML with `${ENV_VAR}` substitution

---

## Install

```bash
# Using uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

## Run

```bash
cp config.example.yaml config.yaml
# edit config.yaml
python -m __ADAPTER_PACKAGE__
```

Or with Docker:

```bash
docker compose up
```

## Configuration

See [`config.example.yaml`](config.example.yaml) for all options.

Required env vars:
- `__ADAPTER_PACKAGE___API_KEY` — credentials for __SOURCE_PLATFORM__
- `VCON_WEBHOOK_URL` — where to POST vCons
- `VCON_WEBHOOK_HMAC_SECRET` — shared secret for body signing

## Test

```bash
pytest
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All vCon construction MUST pass the spec compliance checklist before merge.
