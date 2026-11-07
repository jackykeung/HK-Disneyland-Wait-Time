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
'  .hlegend{display:flex;align-items:center;gap:8px;font-size:11.5px;color:#9aa8bd;flex-wrap:wrap}\n'
'  .hleg{display:flex;align-items:center;gap:4px;white-space:nowrap}\n'
'  .hsw{width:15px;height:15px;border-radius:5px;display:inline-block;border:1px solid rgba(0,0,0,.25)}\n'
'  </style>\n'
'  <div class="htool">\n'
'    <label class="htoggle"><input type="checkbox" id="heatToggle" checked> Crowd heatmap</label>\n'
'    <div class="hlegend">\n'
'      <span class="hleg"><span class="hsw" style="background:#ffffff"></span>Not operating</span>\n'
'      <span class="hleg"><span class="hsw" style="background:#2fd083"></span>&lt;15</span>\n'
'      <span class="hleg"><span class="hsw" style="background:#e8d63a"></span>15-30</span>\n'
'      <span class="hleg"><span class="hsw" style="background:#f5872a"></span>30-40</span>\n'
'      <span class="hleg"><span class="hsw" style="background:#e23c3c"></span>40-60</span>\n'
'      <span class="hleg"><span class="hsw" style="background:#7a0f0f"></span>60+</span>\n'
'      <span class="hleg" style="opacity:.75">min wait</span>\n'
'    </div>\n'
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
  const t=document.getElementById('heatToggle');
  if(t) t.addEventListener('change',function(e){
    if(!heat) return;
    if(e.target.checked){ if(!map.hasLayer(heat)) heat.addTo(map); }
    else { if(map.hasLayer(heat)) map.removeLayer(heat); }
  });
})();""" + a, 1)

# NOTE: keep SOURCES as-is in the source; deployment substitutes the feed URL.
# Default first source stays '/api/wait-times' for the local dev proxy.

# ---- 7. BAND COLOUR SCHEME (user-defined thresholds) ----
# white = not operating; green 1-15; yellow 15-30; orange 30-40; red 40-60; dark red >=60
# (0-min open ride treated as green — confirmed with user)
BCOL = '''

/* Crowd band colour (user thresholds):
   not operating => white; <15 green; 15-30 yellow; 30-40 orange (30=orange);
   40-60 red; >=60 dark red. A 0-min open ride is green (least crowded). */
function bcol(w, open){
  if(open===false || w==null || w===undefined) return '#ffffff';
  if(w<15) return '#2fd083';
  if(w<30) return '#e8d63a';
  if(w<40) return '#f5872a';
  if(w<60) return '#e23c3c';
  return '#7a0f0f';
}
function band(w, open){ const c=bcol(w,open); return (c==='#ffffff')?{key:'closed',col:c}:{key:'band',col:c}; }
'''
a = must("function colFor(c){ return c==='open'?'#2fd083':(c==='mid'?'#f5b942':(c==='long'?'#f26d6d':'#5b6675')); }")
src = src.replace(a, BCOL + "\n" + a, 1)

# marker dot colour + a visible ring for white (closed) dots
a = must("    const col=colFor(p.cls);")
src = src.replace(a, "    const col=bcol(p.wait,p.open);", 1)
a = must("    const mk=L.circleMarker([lat,lng],{radius:9,color:'#fff',weight:1.5,fillColor:col,fillOpacity:.92});")
src = src.replace(a, "    const brd=col==='#ffffff'?'#8a94a6':'#fff';\n    const mk=L.circleMarker([lat,lng],{radius:9,color:brd,weight:1.5,fillColor:col,fillOpacity:.92});", 1)

# list pills -> band colour (tinted bg + coloured text); closed ride = grey pill
a = must("    const c=waitClass(r.wait_time);\n    const st=r.is_open?'open':'closed';")
src = src.replace(a, "    const c=bcol(r.wait_time,r.is_open);\n    const st=r.is_open?'open':'closed';", 1)
a = must("<span class=\"pill ${c}\">${r.is_open&&r.wait_time>0?r.wait_time+'m':(r.is_open?'0m':'—')}</span>")
src = src.replace(a, "<span class=\"pill\" style=\"background:${c==='#ffffff'?'#eef1f5':'#'+c.slice(1)+'22'};color:${c==='#ffffff'?'#8a94a6':c}\">${r.is_open&&r.wait_time>0?r.wait_time+'m':(r.is_open?(r.wait_time===0?'0m':r.wait_time+'m'):'—')}</span>", 1)

# heat gradient anchors aligned to band boundaries (wait 15/30/40/60 => /60)
a = must("gradient:{0.15:'#2b6cff',0.35:'#3ac6d0',0.55:'#7bd04a',0.75:'#f5b942',0.9:'#f28c28',1:'#ff3d3d'}")
src = src.replace(a, "gradient:{0.25:'#2fd083',0.5:'#e8d63a',0.67:'#f5872a',0.85:'#e23c3c',1:'#7a0f0f'}", 1)

open(OUT, "w").write(src)
print(f"wrote {OUT}  ({orig_size} -> {len(src)} bytes)")

import re
assert "function bcol" in src, "bcol missing"
assert "bcol(p.wait,p.open)" in src, "marker not wired to band"
assert "bcol(r.wait_time,r.is_open)" in src, "pill not wired to band"
assert "0.25:'#2fd083'" in src, "heat gradient not aligned"
print("sanity: band colours (markers + pills + heat) OK")