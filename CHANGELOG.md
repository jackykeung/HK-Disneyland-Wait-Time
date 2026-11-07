# Changelog

All notable changes to the HK-Disneyland-Wait-Time dashboards.

## [2.0.0] — 2026-11-07
### Added
- **Crowd heatmap layer** (`index.v2.html`): a weighted heat overlay on the park map where each ride's heat weight is its current wait time (normalised to HEAT_MAX = 60 min). Gradient cool (short wait / low crowd) -> hot (long wait / high crowd). Re-computed on every 60 s refresh with the live feed.
- Show/hide toggle ("Crowd heatmap") + a gradient legend (Low -> High · wait) rendered over the map.
- Self-contained: the Leaflet.heat / simpleheat plugin (MIT) is inlined, so the page stays a single file with no CDN/CSP dependency.
- `build_v2.py`: reproducible build script that emits `index.v2.html` from `index.html` (v1) with the heat feature injected.

### Notes
- The original dashboard (`index.html`, v1.1.1) is unchanged. v2 lives alongside it at a separate URL and is also behind the Authelia gate.
- Weight model: a ride with a 0-min wait is excluded (no crowd); 60+ min is full heat. A closed ride contributes nothing.

## [1.1.1] — 2026-10-11
### Fixed
- The map now always shows ride pins. Previously markers were drawn only after a successful feed fetch, so an unreachable feed (or a closed park with the external CORS relays down) rendered an empty map. `drawBasePins()` renders all rides from the static `COORDS` table as grey dots immediately, recoloured by live data when it arrives.

## [1.1.0] — 2026-10-11
### Changed
- Map coordinates corrected. The app's finder database stores coordinates on a translated origin, so decoded positions sat ~1.1 km northeast of the real attraction. Corrected `coords.json` by applying the reference-frame offset (−0.0028° lat, −0.0120° lng), verified against the resort centroid (~90 m) and landmark checkpoints (~9 m).

## [1.0.0] — 2026-10-11
### Added
- Initial release: live wait-time dashboard (map + sortable list + status cards, 60 s refresh), stdlib-only CORS/60 s-cache proxy, decoded ride coordinates, and the endpoint-architecture write-up.