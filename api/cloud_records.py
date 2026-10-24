"""Per-user cloud record API backed by Supabase Auth and PostgREST.

The browser sends a Supabase access token. RLS on the table remains the
security boundary; this function never uses a service-role key.
"""
from http.server import BaseHTTPRequestHandler
from urllib.error import HTTPError, URLError
from urllib.parse import quote, parse_qs
from urllib.request import Request, urlopen
import json
import os
import re

MAX_BODY = 1_000_000
KEY_PATTERN = re.compile(r"^bit[A-Za-z0-9_]{0,120}$")


def _send(handler, status, body):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
    handler.end_headers()
    if status != 204:
        handler.wfile.write(data)


def _config():
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    anon = os.getenv("SUPABASE_ANON_KEY", "").strip()
    if not url or not anon or not url.startswith("https://"):
        raise RuntimeError("Cloud storage is not configured. Add SUPABASE_URL and SUPABASE_ANON_KEY.")
    return url, anon


def _request(url, anon, token, path, method="GET", payload=None, prefer=None):
    headers = {"apikey": anon, "Authorization": "Bearer " + token}
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if prefer:
        headers["Prefer"] = prefer
    req = Request(url + path, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=12) as response:
            raw = response.read(2_000_000).decode("utf-8")
            return response.status, json.loads(raw) if raw else None
    except HTTPError as exc:
        raw = exc.read(4000).decode("utf-8", errors="replace")
        if exc.code in (401, 403):
            raise PermissionError("Authentication failed or access was denied.") from exc
        raise ValueError("Supabase request failed (" + str(exc.code) + "): " + raw[:500]) from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("Could not reach Supabase. Check the project URL and network.") from exc


def _token(handler):
    value = handler.headers.get("Authorization", "")
    if not value.startswith("Bearer ") or len(value) < 20:
        raise PermissionError("Sign in first to sync project records.")
    return value[7:].strip()


def _valid_key(key):
    return isinstance(key, str) and bool(KEY_PATTERN.fullmatch(key)) and key != "bitBackupLastExportAt_v1"


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        _send(self, 204, {})

    def _run(self, method):
        try:
            url, anon = _config()
            token = _token(self)
            _request(url, anon, token, "/auth/v1/user")
            if method == "GET":
                path = "/rest/v1/project_records?select=record_key,record_value,updated_at&order=record_key.asc"
                _, rows = _request(url, anon, token, path)
                _send(self, 200, {"records": rows or []})
                return
            if method == "POST":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    _send(self, 400, {"detail": "Invalid Content-Length."})
                    return
                if length <= 0 or length > MAX_BODY:
                    _send(self, 413 if length > MAX_BODY else 400, {"detail": "Body must be between 1 byte and 1 MB."})
                    return
                try:
                    body = json.loads(self.rfile.read(length).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    _send(self, 400, {"detail": "Invalid JSON body."})
                    return
                if not isinstance(body, dict) or not isinstance(body.get("records"), list):
                    _send(self, 400, {"detail": "Expected a records array."})
                    return
                records = body["records"]
                if not records or len(records) > 250:
                    _send(self, 400, {"detail": "Provide between 1 and 250 records per sync."})
                    return
                clean = []
                for item in records:
                    if not isinstance(item, dict) or not _valid_key(item.get("record_key")) or "record_value" not in item:
                        _send(self, 400, {"detail": "Each record needs a valid bit-prefixed key and record_value."})
                        return
                    clean.append({"record_key": item["record_key"], "record_value": item["record_value"]})
                path = "/rest/v1/project_records?on_conflict=user_id,record_key"
                _, result = _request(url, anon, token, path, "POST", clean, "resolution=merge-duplicates,return=representation")
                _send(self, 200, {"saved": len(clean), "records": result or []})
                return
            if method == "DELETE":
                query = self.path.split("?", 1)[1] if "?" in self.path else ""
                record_key = parse_qs(query).get("key", [""])[0]
                if not _valid_key(record_key):
                    _send(self, 400, {"detail": "Provide a valid record key."})
                    return
                path = "/rest/v1/project_records?record_key=eq." + quote(record_key, safe="")
                _request(url, anon, token, path, "DELETE", prefer="return=minimal")
                _send(self, 200, {"deleted": True, "key": record_key})
                return
            _send(self, 405, {"detail": "Use GET, POST, or DELETE."})
        except PermissionError as exc:
            _send(self, 401, {"detail": str(exc)})
        except RuntimeError as exc:
            _send(self, 503, {"detail": str(exc)})
        except ValueError as exc:
            _send(self, 502, {"detail": str(exc)})
        except Exception:
            _send(self, 500, {"detail": "Unexpected cloud-record error. Check deployment logs."})

    def do_GET(self):
        self._run("GET")

    def do_POST(self):
        self._run("POST")

    def do_DELETE(self):
        self._run("DELETE")

    def log_message(self, format, *args):
        return
