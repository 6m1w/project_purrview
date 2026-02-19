"""Label API server for PurrView gallery.

Saves/loads cat identity labels for gallery frames.
Labels are stored in data/{date}/labels.json, separate from gallery_meta.jsonl.

Run:
    cd apps/worker
    python -m src.label_server

Endpoints (proxied by nginx at /api/labels):
    GET  /labels/{date}  — return labels for a date
    POST /labels         — save a label {date, filename, cats: [...]}
"""

from __future__ import annotations

import http.server
import json
from pathlib import Path
from urllib.parse import urlparse

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PORT = 8901


class LabelHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self) -> None:
        path = urlparse(self.path).path.strip("/")
        parts = path.split("/")

        # GET /labels/{date}
        if len(parts) == 2 and parts[0] == "labels":
            date = parts[1]
            labels_file = DATA_DIR / date / "labels.json"
            data = json.loads(labels_file.read_text()) if labels_file.exists() else {}
            self._json_response(data)
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path.strip("/")

        # POST /labels
        if path != "labels":
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length))

        date = body["date"]
        filename = body["filename"]
        cats: list[str] = body.get("cats", [])

        labels_file = DATA_DIR / date / "labels.json"

        # Load existing labels
        labels: dict[str, list[str]] = {}
        if labels_file.exists():
            labels = json.loads(labels_file.read_text())

        # Update: empty list means "no cat" (explicit), missing means unlabeled
        labels[filename] = cats

        # Atomic write
        tmp = labels_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(labels, ensure_ascii=False, indent=2))
        tmp.replace(labels_file)

        self._json_response({"ok": True, "total": len(labels)})

    def _json_response(self, data: dict | list) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[label-server] {self.client_address[0]} {args[0]}")


def main() -> None:
    server = http.server.HTTPServer(("127.0.0.1", PORT), LabelHandler)
    print(f"[label-server] Listening on 127.0.0.1:{PORT}")
    print(f"[label-server] Data dir: {DATA_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
