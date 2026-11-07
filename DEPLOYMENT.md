# Deployment — HK-Disneyland-Wait-Time (ox dashboard)

The live dashboard runs on Jacky's **ox** host (dna), gated behind Authelia MFA, with a **same-origin nginx canary** substituting for the repo's stdlib proxy. This is the one place the deployment differs from the repository source.

## Live URL
- Dashboard: `https://ox.jackykeung.com/hkdl-wait-times/` — **behind Authelia MFA** (unauthenticated → 302 `auth.jackykeung.com/login`).
- Feed endpoint: `https://ox.jackykeung.com/hkdl-wait/api/wait-times`

## Deployed artifacts (on dna)
- Docroot: `/var/www/ox/hkdl-wait-times/index.html` (owned `www-data`).
- Backups kept: `index.html.bak.v1.0.20261011-212550`, `index.html.bak.v1.1.0.20261011-213351`.
- nginx canary config: `/etc/nginx/ox-hkdl-proxy.inc`, referenced from `/etc/nginx/sites-available/ox.jackykeung.com.conf` (`location = /hkdl-wait/...`).

## The one-line delta vs the repo (v1.1.1)
Deploying to ox substitutes the feed source so the page uses the nginx same-origin mirror instead of the python proxy (which only runs on `localhost`):

| In repo (`index.html`) | On ox (deployed `index.html`) |
|---|---|
| `{label:'park feed (proxy)', url:'/api/wait-times', wrap:false}` | `{label:'ox same-origin mirror', url:'/hkdl-wait/api/wait-times', wrap:false}` |

Everything else is byte-identical to repo HEAD v1.1.1 (verified: single-line diff, sha256 differs only by that line).

## nginx feed canary (`ox-hkdl-proxy.inc`)
```nginx
location = /hkdl-wait/api/wait-times {
    auth_request /authelia-verify;
    error_page 401 @authelia_redirect;
    proxy_pass https://queue-times.com/parks/31/queue_times.json;
    proxy_set_header Host queue-times.com;
    proxy_set_header User-Agent "Mozilla/5.0 (hkdl-wait-times-dashboard)";
    proxy_ssl_server_name on;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_cache_valid 200 60s;
    add_header Access-Control-Allow-Origin * always;
    add_header Cache-Control "public, max-age=60" always;
}
```
This makes the feed same-origin (queue-times sends no ACAO header, so the browser page can't fetch it directly without a proxy), rides the Authelia gate, and caches 60s to cut upstream hits.

## Notes
- The repo's standalone version runs `python3 hkdl_server.py` (stdlib-only proxy at `/api/wait-times`, 60s cache) for local dev. ox replaces that with the nginx canary — same data (queue-times `/parks/31/queue_times.json`), same 60s cadence.
- To redeploy after editing `index.html` in the repo: apply the single-line URL substitution above, then copy to `/var/www/ox/hkdl-wait-times/index.html` on dna. Keep a `index.html.bak.v<ver>.<ts>` backup.
- The dashboard auto-refreshes every 60s and renders ride pins immediately from the static `COORDS` table (v1.1.1 behaviour).