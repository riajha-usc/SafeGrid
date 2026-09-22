# mvp/

The application. Four source files.

| file | lines | |
|---|---|---|
| `generate.py` | 211 | Resolves the target spreadsheet, calls the model, extracts the code |
| `app.py` | 86 | Serves the page and one endpoint; standard library only |
| `index.html` | 179 | The UI |
| `test_generate.py` | 19 tests | Runs offline with the model client stubbed |

Setup, configuration, and deployment are in the [top-level README](../README.md).

## Request flow

```
POST /api/generate  {query}
        │
        ├─ find_spreadsheet_id()   regex over the request text
        ├─ build_user_message()    pins the script to that spreadsheet
        ├─ _call_groq() | _call_anthropic()
        └─ CODE_FENCE_RE           pulls the script out of the reply
        │
        ▼
{provider, model, spreadsheet_id, explanation, code}
```

`generate.py` is the only file that knows which provider is in use. `app.py`,
the UI, and the tests all see the same response shape either way, so adding a
provider touches one function.

## Extending it

**A new provider** — add a `_call_<name>()` returning the reply text, and a
branch in `resolve_provider()`. Nothing else changes.

**Different script conventions** — edit `SYSTEM` in `generate.py`. That prompt
is where the rules about header lookup, bulk reads and writes, and not deleting
data are enforced.

**Tighter guarantees** — the current design lets the model write JavaScript
freely. Constraining it to a fixed set of operations, with the script rendered
from templates rather than generated, would remove the class of failure
described under [Scope](../README.md#scope) at the cost of flexibility.
