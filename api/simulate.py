"""Vercel serverless simulation endpoint; delegates to the shared PyADM1ODE adapter."""
from http.server import BaseHTTPRequestHandler
import json

from simulation_engine import run_simulation


def _send(handler, status, body):
    data = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(data)


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        _send(self, 204, {})

    def do_GET(self):
        _send(self, 405, {"detail": "Use POST /api/simulate with JSON input."})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            _send(self, 400, {"detail": "Invalid Content-Length header."})
            return
        if length <= 0 or length > 100000:
            _send(self, 413 if length > 100000 else 400, {"detail": "Request body must be between 1 byte and 100 KB."})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("The JSON body must be an object.")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            _send(self, 400, {"detail": "Invalid JSON body.", "error": str(exc)[:250]})
            return
        try:
            result = run_simulation(payload)
            _send(self, 200, result)
        except ValueError as exc:
            _send(self, 422, {"detail": str(exc)})
        except RuntimeError as exc:
            _send(self, 500, {"detail": str(exc)})
        except Exception:
            _send(self, 500, {"detail": "Unexpected simulation error. Check deployment logs; no heuristic result was substituted."})

    def log_message(self, format, *args):
        return
}
