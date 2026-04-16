#!/usr/bin/env python3
"""
Hardin Local — Email collection API (local dev server)
Stores newsletter signups in SQLite. Serves on port 8766.
Production: replace with Cloudflare Worker + D1.
"""

import json
import sqlite3
import re
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer

DB_PATH = "/home/philtaul/data/hardin-local-emails.db"
PORT = 8766

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            source_page TEXT,
            subscribed_at TEXT NOT NULL,
            ip_address TEXT
        )
    """)
    conn.commit()
    conn.close()
    print(f"Database ready at {DB_PATH}")

def is_valid_email(email):
    return bool(re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email))

class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json_response(self, status, data):
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/subscribe":
            self._json_response(404, {"error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            self._json_response(400, {"error": "Invalid JSON"})
            return

        email = (body.get("email") or "").strip().lower()
        source = (body.get("source") or "unknown").strip()

        if not email or not is_valid_email(email):
            self._json_response(400, {"error": "Invalid email address"})
            return

        ip = self.client_address[0]
        now = datetime.now(timezone.utc).isoformat()

        try:
            with sqlite3.connect(DB_PATH, timeout=5) as conn:
                conn.execute(
                    "INSERT INTO subscribers (email, source_page, subscribed_at, ip_address) VALUES (?, ?, ?, ?)",
                    (email, source, now, ip)
                )
                conn.commit()
            print(f"[+] New subscriber: {email} (from {source})")
            self._json_response(200, {"ok": True, "message": "Subscribed"})
        except sqlite3.IntegrityError:
            self._json_response(200, {"ok": True, "message": "Already subscribed"})
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def do_GET(self):
        if self.path != "/subscribers":
            self._json_response(404, {"error": "Not found"})
            return

        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            rows = conn.execute(
                "SELECT email, source_page, subscribed_at FROM subscribers ORDER BY subscribed_at DESC"
            ).fetchall()
        self._json_response(200, {
            "count": len(rows),
            "subscribers": [{"email": r[0], "source": r[1], "date": r[2]} for r in rows]
        })

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")

if __name__ == "__main__":
    init_db()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Email API running on http://localhost:{PORT}")
    print(f"  POST /subscribe  — add email")
    print(f"  GET  /subscribers — list all")
    print()
    server.serve_forever()
