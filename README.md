# HK Disneyland — Live Wait Times

A clean, self-contained web dashboard that streams **live attraction wait times** for Hong Kong
Disneyland (rendered on a map + a sortable list), plus a full write-up of how a park app
actually transports that data.

Built from the ground up: an independent reimplementation of the concept, with no packing of
or derivation from the original app's source. The dashboard reads a **public, no-key park
wait-time feed** and decodes ride map coordinates from publicly distributed app data.

## What it does

- **Live wait times** for every attraction (50 rides), auto-refreshed every 60 seconds.
- **Status summary** cards: open count, closed count, average wait, busiest ride, refresh cadence.
- **Park map** with color-coded markers (green 0–30 / amber 31–60 / red 60+ / grey closed),
  placed using coordinates decoded from the platform's own public finder data.
- **Attraction list** sorted by wait time, with per-ride last-updated timestamps.

Verified against the live park feed — e.g. Iron Man Experience 30 min, Ant-Man & The Wasp:
Nano Battle! 45 min, Frozen Ever After 70 min at the same moment.

## Reports

- [`analysis/endpoint-architecture.html`](analysis/endpoint-architecture.html) — the full
  reverse-engineering write-up: the app's stack, the ride wait-time data model, the real
  transport (Couchbase Lite → Sync Gateway over Blip WebSocket), the secondary REST hosts
  that were discovered, and the three concrete usage scenarios. Self-contained single file.

## Run it

The page needs the feed served on its own origin (the feed's provider sends no CORS header),
so a tiny zero-dependency proxy is included:

```bash
python3 hkdl_server.py        # http://127.0.0.1:8000/
# or a different port:
python3 hkdl_server.py 8080
```

Then open <http://localhost:8000/>.

The single `index.html` also works opened directly in a browser — it will fall back through
public CORS relays when the proxy isn't running.

## Layout

```
index.html                 self-contained dashboard (map + list, inline Leaflet)
hkdl_server.py             stdlib-only proxy: serves index.html + /api/wait-times (CORS, 60s cache)
coords.json                ride name -> (lat, lng), decoded from public platform data
analysis/endpoint-architecture.html   the full endpoint & architecture write-up
```

## Data source & attribution

The live feed is the **Queue-Times Real Time API** (`/parks/31/queue_times.json`), a public,
5-minute mirror of the official park feed. Free to use; please display
[Powered by Queue-Times.com](https://queue-times.com/en-US) (the dashboard does).

## Not affiliated

This is an independent, non-commercial hobby project for personal, educational use. Not
affiliated with, endorsed by, or authorized by Disney or any park operator. No trademark
belongs to this project.