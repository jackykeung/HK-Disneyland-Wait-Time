#!/usr/bin/env python3
"""
Build HK-Disneyland-Wait-Time v2.0.0 — add a crowd-heatmap layer over the map.

Feature: a weighted heat overlay (Leaflet.heat / simpleheat, inlined) where each
ride point's heat weight = its current wait time (normalised to HEAT_MAX min).
Gradient: cool (short wait / low crowd) -> hot (long wait / high crowd). A
show/hide toggle + gradient legend are added. Everything else in v1 is unchanged.

Run:  python3 build_v2.py   -> writes index.v2.html  (then check with a browser)
"""
import os, sys, hashlib

here = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(here, "index.html")          # v1.1.1 source (unchanged)
PLUGIN = open("/tmp/leaflet-heat.js").read().strip()
OUT = os.path.join(here, "index.v2.html")

src = open(SRC).read()
orig_size = len(src)

def must(anchor, count=1):
    assert src.count(anchor) == count, f"anchor not unique/absent ({src.count(anchor)}): {anchor[:60]}"
    return anchor

# ---- 1. inline the heat plugin as raw JS inside the app block (no nested <script> tags) ----
PLUG = '\n/* simpleheat + L.heatLayer (c) 2014 Vladimir Agafonkin, MIT (crowd heat overlay) */\n' + PLUGIN + '\n'
a = must("\nconst COORDS = {")
src = src.replace(a, PLUG + a, 1)

# ---- 2. toolbar: heat toggle + gradient legend (with its own inline <style>) ----
TOOL = (
'  <style>\n'
'  .htool{display:flex;align-items:center;gap:16px;margin:10px 0 0;flex-wrap:wrap}\n'
'  .htoggle{font-size:13.5px;color:#cfd7e3;display:flex;align-items:center;gap:6px;cursor:pointer;user-select:none}\n'
'  .htoggle input{transform:scale(1.15);cursor:pointer}\n'
'  .hlegend{display:flex;align-items:center;gap:7px;font-size:11.5px;color:#9aa8bd}\n'
'  .hgrad{width:150px;height:12px;border-radius:6px;background:linear-gradient(90deg,#2b6cff,#3ac6d0,#7bd04a,#f5b942,#f28c28,#ff3d3d)}\n'
'  </style>\n'
'  <div class="htool">\n'
'    <label class="htoggle"><input type="checkbox" id="heatToggle" checked> Crowd heatmap</label>\n'
'    <div class="hlegend">Low<div class="hgrad"></div>High &middot; wait</div>\n'
'  </div>\n'
)
a = must("  <div class=\"layout\">")
src = src.replace(a, TOOL + a, 1)

# ---- 3. state vars ----
a = must("let map=null, markers={}, oldLayers=new Map();")
src = src.replace(a, a + "\nlet heat=null;\nconst HEAT_MAX=60; // wait (min) that maps to the hottest colour", 1)

# ---- 4. updateHeat(pts) before init() ----
HEAT = '''

function updateHeat(pts){
  if(!map) return;
  const dat=[];
  pts.forEach(p=>{
    if(!p.coords||!p.open) return;
    const w=Math.min(1,Math.max(0,(p.wait||0)/HEAT_MAX));
    if(w>0) dat.push([p.coords[0],p.coords[1],w]);
  });
  if(!heat){
    heat=L.heatLayer(dat,{radius:22,blur:20,maxZoom:18,minOpacity:.35,
      gradient:{0.15:'#2b6cff',0.35:'#3ac6d0',0.55:'#7bd04a',0.75:'#f5b942',0.9:'#f28c28',1:'#ff3d3d'}});
    heat.addTo(map);
  } else {
    heat.setLatLngs(dat);
  }
  const htg=document.getElementById('heatToggle');
  if(htg && !htg.checked && map.hasLayer(heat)) map.removeLayer(heat);
}
'''
a = must("function init(){")
src = src.replace(a, HEAT + "\n" + a, 1)

# ---- 5. call updateHeat(pts) at the end of updateMap() ----
a = must("""  if(latlngs.length){
    map.fitBounds(L.latLngBounds(latlngs),{padding:[48,48],maxZoom:17});
  }
}""")
src = src.replace(a, """  if(latlngs.length){
    map.fitBounds(L.latLngBounds(latlngs),{padding:[48,48],maxZoom:17});
  }
  updateHeat(pts);
}""", 1)

# ---- 6. toggle listener + feed URL for the ox same-origin canary ----
a = must("\ninit();")
src = src.replace(a, """
(function(){
  const t=document.getElementById('heatToggle'), g=document.querySelector('.hlegend');
  if(t) t.addEventListener('change',function(e){
    if(!heat) return;
    if(e.target.checked){ if(!map.hasLayer(heat)) heat.addTo(map); if(g) g.style.display='flex'; }
    else { if(map.hasLayer(heat)) map.removeLayer(heat); if(g) g.style.display='none'; }
  });
})();""" + a, 1)

# NOTE: keep SOURCES as-is in the source; deployment substitutes the feed URL.
# Default first source stays '/api/wait-times' for the local dev proxy.

open(OUT, "w").write(src)
print(f"wrote {OUT}  ({orig_size} -> {len(src)} bytes)")

# quick sanity
import re
assert "L.heatLayer" in src, "plugin missing"
assert src.count("updateHeat(pts)") >= 2, "updateHeat not wired"
assert "id=\"heatToggle\"" in src, "toggle missing"
print("sanity: plugin + updateHeat(pts) + toggle OK")