# SafeGrid

Describe a change to a Google Sheet in plain English; get back Google Apps
Script you can read, run, and deploy in Google Workspace.

```
your sentence  ──►  SafeGrid  ──►  Apps Script  ──►  you paste + run it
```

SafeGrid never touches your spreadsheet. It writes the script; you review it
and run it yourself from the Apps Script editor.

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install anthropic groq
cp .env.example .env          # then put a key in .env
export $(grep -v '^#' .env | xargs)
.venv/bin/python mvp/app.py
```

Open **http://localhost:8000**, paste a spreadsheet link into your request, and
describe what you want done.

## Example

> In `https://docs.google.com/spreadsheets/d/…/edit` — highlight every row
> where the email address column is blank.

SafeGrid returns a short summary of what the script will do, the script itself,
and the four steps to run it.

## How it works

**Finding the target spreadsheet** is a plain regex over your request, not a
job handed to the model. A regex cannot mistype an ID, and a wrong ID would
point the generated script at the wrong workbook. A Sheets URL or a bare file
ID both match.

- ID found → the script uses `SpreadsheetApp.openById(...)`
- No ID → the script uses `getActiveSpreadsheet()` and runs wherever you paste it

**Writing the script** is the model's job, under a system prompt that enforces
the conventions that keep generated scripts safe on real data: resolve columns
by header text rather than by position, read and write in bulk to stay inside
the Apps Script execution limit, and never delete anything the request did not
ask for.

**Nothing is executed.** The output is text until a person reads it and clicks
Run. That review step is deliberate — see [Scope](#scope).

## Configuration

One API key, set in `.env`:

| variable | |
|---|---|
| `GROQ_API_KEY` | Groq, via [console.groq.com](https://console.groq.com) |
| `ANTHROPIC_API_KEY` | Anthropic, via [console.anthropic.com](https://console.anthropic.com) |

The provider is chosen from whichever key is set. Optional overrides:
`SAFEGRID_PROVIDER`, `GROQ_MODEL`, `ANTHROPIC_MODEL`.

## Requirements

Python 3.10+ and one API key. No database, no build step, no framework — the
server is Python's standard library.

## Tests

```bash
.venv/bin/python -m unittest mvp.test_generate -v
```

Runs offline with no API key: the model client is stubbed, so what is under
test is spreadsheet resolution, request shaping, and code extraction.

## Deploying a generated script

1. Spreadsheet → **Extensions → Apps Script**
2. Paste over `Code.gs`, Save
3. Pick the function from the dropdown, **Run**
4. On first run Google asks you to authorise. Read the scopes before accepting.

To version scripts rather than paste them, use
[clasp](https://github.com/google/clasp). Its `.clasprc.json` holds a live
OAuth token and is gitignored.

## Scope

The model writes the JavaScript directly, and your review is what stands
between a bad generation and your data. That is a deliberate tradeoff for a
tool this size, and the failure it accepts is worth naming: a script that looks
plausible and is subtly wrong. Run generated scripts against a copy of your
data before running them against the real thing.

## Security

`.gitignore` covers `.env`, Google credentials (`credentials.json`,
`token.json`, `service-account*.json`, `client_secret*.json`), clasp's
`.clasprc.json`, private keys, and anything matching `api_key*` / `*_secret*` /
`*_token*`. Generated scripts are ignored too, since they can embed real
spreadsheet IDs.

The server binds to `127.0.0.1` only, and request logging records the method
and path but not request contents.

Copy `.env.example` to `.env`. Never commit `.env`.
