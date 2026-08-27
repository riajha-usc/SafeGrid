# Ops-Hubs Compiler

Describe a change to a Google Sheet in plain English; get back Apps Script you
can read, run, and deploy in Google Workspace.

```
your sentence  ──►  Claude  ──►  Apps Script  ──►  you paste + run it
```

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install anthropic
cp .env.example .env          # then put your key in .env
export $(grep -v '^#' .env | xargs)
.venv/bin/python mvp/app.py
```

Open **http://localhost:8000**, paste your spreadsheet link into the request,
and describe what you want done.

## What's here

| path | |
|---|---|
| `mvp/` | **The MVP.** Four files, ~530 lines. Start here. |

That is the whole repo for now. A later phase — operation grammar,
deterministic codegen, approval gates, a multi-workbook registry — is built but
deliberately kept out of this cut; see [mvp/README.md](mvp/README.md) for what
it adds and when it becomes worth landing.

## Requirements

Python 3.10+, an Anthropic API key. Node is optional (only the archived test
suite uses it).

## Secrets

`.gitignore` covers `.env`, Google credentials (`credentials.json`,
`token.json`, `service-account*.json`), clasp's `.clasprc.json`, private keys,
and anything matching `*_secret*` / `*_token*` / `api_key*`. Generated scripts
are ignored too, since they can embed real spreadsheet IDs.

Copy `.env.example` to `.env`. Never commit `.env`.
