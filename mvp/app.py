"""
app.py — the web UI.

A single-file HTTP server on the standard library: no framework, nothing to
configure. It serves one page and one endpoint.

    python3 mvp/app.py        then open http://localhost:8000

Binds to 127.0.0.1 only. The generated script can carry a real spreadsheet id,
and the request carries whatever the staff member typed, so neither should be
reachable from the network during development.
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mvp.generate import GenerationError, generate  # noqa: E402

HERE = Path(__file__).resolve().parent
HOST, PORT = "127.0.0.1", 8000
MAX_BODY = 100_000          # a request is a sentence, not a payload


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: dict) -> None:
        self._send(code, json.dumps(payload).encode(), "application/json")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        else:
            self._json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/api/generate":
            self._json(404, {"error": "Not found"})
            return

        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            self._json(413, {"error": "Request too long."})
            return

        try:
            query = json.loads(self.rfile.read(length) or b"{}").get("query", "")
        except json.JSONDecodeError:
            self._json(400, {"error": "Malformed request body."})
            return

        try:
            self._json(200, generate(query))
        except GenerationError as exc:
            # Expected failures — a missing key, a vague request. These are
            # for the person to read and act on, so they go to the UI as-is.
            self._json(400, {"error": str(exc)})
        except Exception as exc:                      # noqa: BLE001
            self.log_error("unexpected: %r", exc)
            self._json(500, {"error": "Something went wrong. Check the server log."})

    def log_message(self, fmt, *args):
        # Default logging echoes the full request line. Keep it to the verb and
        # path so a pasted spreadsheet id never lands in the terminal scrollback.
        sys.stderr.write(f"{self.command} {self.path.split('?')[0]}\n")


def main():
    print(f"Ops-Hubs MVP running at http://{HOST}:{PORT}  (ctrl-c to stop)")
    try:
        HTTPServer((HOST, PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
