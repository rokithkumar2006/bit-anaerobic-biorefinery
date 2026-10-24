"""Expose only public Supabase project settings to the browser."""
from http.server import BaseHTTPRequestHandler
import json
import os


def _send(handler, status, body):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(data)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
        anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
        if not url or not anon_key:
            _send(self, 200, {"configured": False})
            return
        if not url.startswith("https://"):
            _send(self, 503, {"configured": False, "detail": "SUPABASE_URL must use HTTPS."})
            return
        _send(self, 200, {"configured": True, "url": url, "anonKey": anon_key})

    def do_OPTIONS(self):
        _send(self, 204, {})

    def log_message(self, format, *args):
        return
