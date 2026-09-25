# vcon-__ADAPTER_NAME__-adapter

> Adapter that converts **__SOURCE_PLATFORM__** events into [vCon](https://datatracker.ietf.org/doc/draft-ietf-vcon-vcon-core/) (Virtual Conversation) objects and delivers them to a [vCon server](https://github.com/vcon-dev/vcon-server) or other downstream consumer.

**Spec target:** IETF `draft-ietf-vcon-vcon-core-04`, vCon syntax `"0.4.0"`
(the syntax string is deprecated in -04 but kept for parser compatibility).

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
- `encoding: "json"` bodies are the raw JSON value, not a `json.dumps()` string (draft-ietf-vcon-vcon-core-04 §2.3.2); `json_body()` reads either shape back
- Lawful-basis attachments (`draft-howe-vcon-lawful-basis`) via `LawfulBasisConfig` + `add_lawful_basis()`
- Two delivery modes, selected by `delivery.mode`:
  - `webhook`: HMAC-SHA256 body signing (`X-Hub-Signature-256`), `Idempotency-Key` header, exponential-backoff retries, dead-letter queue
  - `conserver`: direct `POST {CONSERVER_URL}/vcon` to a vcon-server instance (`x-conserver-api-token` header, `ingress_lists` query params), same retry/backoff/DLQ machinery
- `/healthz` + Prometheus `/metrics` endpoints
- Configurable via YAML with `${ENV_VAR}` substitution

**Not implemented in this template** (remove this note once you've decided): a `TranscriptionProvider` protocol and optional JWS (RS256) signing of outgoing vCons were previously advertised here but never built. Add them yourself if your adapter needs them, or drop the mention.

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
- `VCON_WEBHOOK_URL` — where to POST vCons (`delivery.mode: webhook`)
- `VCON_WEBHOOK_HMAC_SECRET` — shared secret for body signing (`delivery.mode: webhook`)
- `CONSERVER_URL`, `CONSERVER_API_TOKEN` — target vcon-server and its API token (`delivery.mode: conserver`)

Optional lawful-basis env vars (see [USAGE.md](USAGE.md)):
`LAWFUL_BASIS`, `LAWFUL_BASIS_PURPOSE`, `LAWFUL_BASIS_JURISDICTION`,
`LAWFUL_BASIS_EXPIRATION`, `LAWFUL_BASIS_PROOF_MECHANISM`,
`LAWFUL_BASIS_PROOF_DESCRIPTION`. Unset means vCons are built with no
lawful-basis attachment — never default this in code.

## Test

```bash
pytest
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All vCon construction MUST pass the spec compliance checklist before merge.
