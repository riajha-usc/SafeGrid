# The MVP

One job: turn a sentence into Apps Script for a named spreadsheet.

## Files

| file | lines | what it does |
|---|---|---|
| `generate.py` | 147 | Finds the spreadsheet in the request, asks Claude for the script, pulls the code out of the reply |
| `app.py` | 86 | Serves the page and one endpoint. Standard library only |
| `index.html` | 170 | The UI |
| `test_generate.py` | 12 tests | Runs offline with the SDK stubbed |

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install anthropic
cp .env.example .env && $EDITOR .env
export $(grep -v '^#' .env | xargs)
.venv/bin/python mvp/app.py            # http://localhost:8000
```

## Test it

```bash
.venv/bin/python -m unittest mvp.test_generate -v
```

No API key needed — the Anthropic client is stubbed, so what's under test is
our half: finding the spreadsheet, shaping the request, extracting the code.

## How it works

**Finding the target spreadsheet** is a regex over the request text, not a job
given to the model. A regex cannot mistype an ID, and a wrong ID would point
the generated script at somebody else's workbook. A Sheets URL or a bare
44-character file ID both match; anything shorter is treated as prose.

- ID found → the script uses `SpreadsheetApp.openById('...')`
- No ID → the script uses `getActiveSpreadsheet()` and runs wherever it's pasted

**Writing the script** is the model's job. The system prompt in `generate.py`
carries the rules that matter for this workbook family: resolve columns by
header text rather than by number (staff insert columns without warning), bulk
`getValues()`/`setValues()` rather than per-row calls (the 6-minute execution
limit), and never delete anything that wasn't explicitly asked for.

**Nothing here runs the generated code.** It's text on a page until a person
reads it and clicks Run in the Apps Script editor. That review step is what the
MVP relies on in place of automated verification.

## Deploying what it generates

1. Spreadsheet → **Extensions → Apps Script**
2. Paste over `Code.gs`, Save
3. Pick the function from the dropdown, **Run**
4. First run only: Google asks you to authorise. Read the scopes before accepting.

To version the script instead of pasting, use
[clasp](https://github.com/google/clasp) — `clasp push`. Its `.clasprc.json`
holds a live OAuth token and is already gitignored.

## What this deliberately does not do

The model writes the JavaScript directly, and the only thing between a bad
generation and your spreadsheet is you reading it. That is a real tradeoff, and
it is the right one for an MVP — but it is worth knowing which failure it
accepts: a subtly wrong script that looks plausible.

The machinery that closes that gap is already built and is being held back
from this cut so the MVP stays small:

| | |
|---|---|
| operation grammar | the model picks an operation and fills enum arguments; it never writes code |
| deterministic codegen | Apps Script rendered from fixed templates, byte-identical per plan |
| approval gates | anything that sends mail stops for a human checksum |
| privacy firewall | blocks student IDs, phone numbers, pay from outbound email |
| workbook registry | schema for the three master workbooks, generated from the real files |
| 141 tests | including 23 that execute the Apps Script against a mock SpreadsheetApp |

The natural first thing to land is the registry, so the model gets the real
column names instead of inferring them from the request.
