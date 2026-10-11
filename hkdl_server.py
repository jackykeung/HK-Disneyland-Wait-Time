#!/usr/bin/env python3
"""Hong Kong Disneyland live wait-times dashboard.

Serves a self-contained dashboard page at http://localhost:8000/ and proxies
the live wait-time feed (Queue-Times Real Time API, which mirrors Disney's own
park feed) at /api/wait-times with permissive CORS and a 60s cache.

Why a proxy: queue-times.com sends no Access-Control-Allow-Origin header, so a
browser page cannot fetch it directly. This tiny server bridges that so the
dashboard can be a single plain HTML file that live-streams.

Zero dependencies (stdlib only). Python 3.8+.

Usage:
    python3 hkdl_server.py
Then open http://localhost:8000/
"""
import json
import ssl
import time
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
FEED = "https://queue-times.com/parks/31/queue_times.json"
CACHE_SECONDS = 60

_cache = {"t": 0.0, "data": None, "err": None, "status": 200}


def _ssl_ctx():
    """Build a TLS context that trusts certifi's bundle (this host lacks the
    system CA store that browsers/curl use, so urllib raises
    SSLCertVerificationError unless we point it at a real bundle)."""
    ctx = ssl.create_default_context()
    try:
        import certifi
        ctx.load_verify_locations(cafile=certifi.where())
    except Exception:
        # fall back to system store; if that also fails, degrade and continue
        pass
    return ctx


_CTX = _ssl_ctx()


def fetch_feed(force=False):
    now = time.time()
    if not force and _cache["data"] is not None and (now - _cache["t"]) < CACHE_SECONDS:
        return _cache
    try:
        req = urllib.request.Request(FEED, headers={
            "User-Agent": "Mozilla/5.0 (live-wait-times-dashboard)",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=12, context=_CTX) as r:
            data = r.read()
        _cache.update(t=now, data=data, err=None, status=200)
    except Exception as e:  # network/geo/ratelimit -> keep last good data, report err
        _cache.update(t=now, err=str(e), status=502)
    return _cache


def read_html():
    p = BASE / "index.html"
    return p.read_bytes() if p.exists() else b"<h1>index.html not found</h1>"


class Handler(BaseHTTPRequestHandler):
    server_version = "HKDLDashboard/1.0"

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/index.html"):
            body = read_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/wait-times":
            c = fetch_feed()
            self.send_response(c["status"])
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._cors()
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(c["data"]) if c["data"] else 0))
            self.end_headers()
            self.wfile.write(c["data"] or b"{}")
        else:
            self.send_response(404)
            self._cors()
            self.end_headers()
            self.wfile.write(b"404")

    def log_message(self, *a):
        pass


def main():
    HOST, PORT = "127.0.0.1", 8000
    import sys
    if len(sys.argv) == 2:
        PORT = int(sys.argv[1])
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Hong Kong Disneyland wait-times dashboard: http://{HOST}:{PORT}/")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()