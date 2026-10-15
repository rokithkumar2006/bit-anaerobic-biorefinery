"""Vercel serverless health endpoint for the BIT biorefinery API."""
from http.server import BaseHTTPRequestHandler
import json
import importlib.metadata


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
        try:
            version = importlib.metadata.version("pyadm1")
            installed = True
        except importlib.metadata.PackageNotFoundError:
            version = None
            installed = False
        _send(self, 200, {
            "status": "ok",
            "engine": "PyADM1ODE/ADM1da" if installed else "model-package-not-installed",
            "engine_version": version,
            "model_integrated": installed,
            "simulation_executed": False,
        })

    def do_OPTIONS(self):
        _send(self, 204, {})

    def log_message(self, format, *args):
        return
}
