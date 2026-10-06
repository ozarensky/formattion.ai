#!/usr/bin/env python3
"""
build_hero_embed.py — self-contained typed headline for other pages (the platform log-in page).

Reads `hero-headlines.json` and writes one HTML file that previews on its own and contains an
embeddable block: an <svg> plus an inline script with the glyph data baked in (no fetch, no
other files). On every page load it picks one headline at random, types it with the site's
natural rhythm, then stops with the caret blinking. Nothing rotates and nothing is deleted.

Usage:
    python tools/build_hero_embed.py                       # → ../branding/hero animations/formattion-typed-headline.html
    python tools/build_hero_embed.py --out "<file.html>"   # anywhere else as well

Embedding: copy everything between EMBED START and EMBED END into the page. The headline takes
its colour from the surrounding text colour (currentColor) and is 100% of its container's width.
The Union Jack suffix is not drawn by this player (dropped on request, 2026-10-06).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from extract_hero_headlines import path_bbox  # noqa: E402

DATA = ROOT / "hero-headlines.json"
DEFAULT_OUT = ROOT.parent / "branding" / "hero animations" / "formattion-typed-headline.html"

PLAYER = r"""
(function () {
  var DATA = __DATA__;
  var NS = 'http://www.w3.org/2000/svg';
  var BLINK = 2 / 2.2;              // caret blink period, seconds
  var INTRO = BLINK * 1.5;          // caret alone on the empty line before the first key
  var CARET_W = 3, CARET_H = 56;
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function jitter(i) { return ((Math.sin(i * 12.9898) * 43758.5453) % 1 + 1) % 1; }   // deterministic 0..1
  function el(name, attrs, parent) {
    var node = document.createElementNS(NS, name);
    for (var k in attrs) node.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(node);
    return node;
  }
  function setAttr(node, name, value) { if (node.getAttribute(name) !== value) node.setAttribute(name, value); }
  function blinkStyle() {
    if (document.getElementById('fm-typed-style')) return;
    var st = document.createElement('style');
    st.id = 'fm-typed-style';
    st.textContent = '@keyframes fm-typed-blink{0%,49%{opacity:1}50%,100%{opacity:0}}';
    document.head.appendChild(st);
  }

  function mount(svg, index) {
    var h = DATA.headlines[index], G = h.glyphs.length, split = h.split, i;
    svg.setAttribute('viewBox', '0 0 ' + DATA.viewBox[0] + ' ' + DATA.viewBox[1]);
    svg.setAttribute('aria-label', h.label);
    var title = svg.querySelector('title') || el('title', {}, svg);
    title.textContent = h.label;
    var g = el('g', { fill: 'currentColor', transform: 'translate(' + h.shift[0] + ' ' + h.shift[1] + ')' }, svg);
    var paths = [], boxes = [];
    for (i = 0; i < G; i++) {
      paths.push(el('path', { d: h.glyphs[i], opacity: 0 }, g));
      boxes.push({ x: h.boxes[i][0], r: h.boxes[i][1], y: h.boxes[i][2], h: h.boxes[i][3] });   // measured at build time
    }
    var caret = el('rect', { width: CARET_W, height: CARET_H, opacity: 0 }, g);

    var wordStart = {}, avg = 0, n = 0;
    for (i = 1; i < G; i++) if (i !== split) { avg += boxes[i].x - boxes[i - 1].r; n++; }
    avg /= Math.max(1, n);
    for (i = 1; i < G; i++) if (i !== split && boxes[i].x - boxes[i - 1].r > avg * 2.5) wordStart[i] = true;
    function isStop(j) { var b = boxes[j]; return b.h < 12 && b.r - b.x < 12; }

    // Natural typing: keys 55–115 ms apart; a new word costs the space bar plus a beat;
    // a full stop or the line break takes a breath. Same rhythm as formattion.ai.
    function rnd(i, k) { return jitter(index * 31 + i * 3 + k); }
    var t = INTRO, times = [], spaceAt = [], line2Start = 0;
    for (i = 0; i < G; i++) {
      var key = 0.055 + rnd(i, 0) * 0.06;
      if (i === split) { line2Start = t + 0.3 + rnd(i, 1) * 0.12; t = line2Start + 0.22 + rnd(i, 2) * 0.1; }
      else if (wordStart[i]) { spaceAt[i] = t + key; t += key + 0.07 + rnd(i, 1) * 0.09 + (isStop(i - 1) ? 0.3 : 0); }
      else if (i > 0) { t += key + (rnd(i, 2) > 0.94 ? 0.12 : 0); }
      times.push(t);
    }
    var typedEnd = t;

    function draw(T) {
      var last = -1;
      for (i = 0; i < G; i++) if (T >= times[i]) last = i;
      for (i = 0; i < G; i++) setAttr(paths[i], 'opacity', i <= last ? '1' : '0');
      var line = last < split ? 0 : 1;
      var cx = last < 0 ? h.startX : boxes[last].r + 5;
      if (last === split - 1) { if (T >= line2Start) { cx = h.startX; line = 1; } }
      else if (last >= 0 && last < G - 1 && T >= spaceAt[last + 1]) cx = boxes[last + 1].x - 6;
      var on = true;
      if (last < 0) on = Math.floor(T / (BLINK / 2)) % 2 === 0;   // blinking on the empty line
      setAttr(caret, 'x', String(cx));
      setAttr(caret, 'y', String(h.lineTops[line]));
      setAttr(caret, 'opacity', on ? '1' : '0');
    }
    function rest() {                 // typed: hand the blink to CSS and stop the frame loop
      blinkStyle();
      caret.style.animation = 'fm-typed-blink ' + BLINK + 's linear infinite';
    }

    if (reduceMotion) { draw(typedEnd + 1); caret.setAttribute('opacity', '0'); return; }
    var T = 0, lastTs = 0;
    function frame(ts) {
      T += lastTs ? Math.min((ts - lastTs) / 1000, 0.1) : 0;   // capped: time in a background tab is not replayed
      lastTs = ts;
      draw(T);
      if (T >= typedEnd) { rest(); return; }
      requestAnimationFrame(frame);
    }
    draw(0);
    requestAnimationFrame(frame);
  }

  var nodes = document.querySelectorAll('svg.fm-typed-headline:not([data-ready])');
  for (var k = 0; k < nodes.length; k++) {
    nodes[k].setAttribute('data-ready', '');
    mount(nodes[k], Math.floor(Math.random() * DATA.headlines.length));   // one random headline per page load
  }
})();
"""

PAGE = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>formattion — typed headline</title>
<style>
  body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #F4EFE6; color: #000; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
  .demo {{ width: min(900px, calc(100vw - 80px)); }}
  @media (prefers-color-scheme: dark) {{ body {{ background: #000; color: #F4EFE6; }} }}
</style>
</head>
<body>
<div class="demo">
<!-- ══ EMBED START — copy everything from here to EMBED END into the page. ══
     One headline is picked at random each time the page loads, typed, then left with the caret blinking.
     Colour comes from the surrounding text colour (currentColor): set `color` on a parent for light / dark.
     Width is 100% of the container; size the container, not the svg.
     Built by web page/tools/build_hero_embed.py — do not hand-edit. -->
<svg class="fm-typed-headline" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{first_label}" style="display:block;width:100%;height:auto;overflow:visible"><title>{first_label}</title></svg>
<script>{player}</script>
<!-- ══ EMBED END ══ -->
</div>
</body>
</html>
"""


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    data = json.loads(DATA.read_text(encoding="utf-8"))
    headlines = []
    for h in data["headlines"]:
        boxes = [path_bbox(d) for d in h["glyphs"]]
        headlines.append({
            "label": h["label"],
            "shift": h["shift"],
            "startX": h["startX"],
            "lineTops": h["lineTops"],
            "split": h["split"],
            "glyphs": h["glyphs"],
            # x, right, y, height — so the player never needs getBBox (works inside hidden containers)
            "boxes": [[round(b[0], 1), round(b[2], 1), round(b[1], 1), round(b[3] - b[1], 1)] for b in boxes],
        })
        print("  " + h["label"] + ("  (flag dropped)" if h.get("suffix") else ""))

    payload = json.dumps({"viewBox": data["viewBox"], "headlines": headlines}, separators=(",", ":"), ensure_ascii=False)
    html = PAGE.format(first_label=headlines[0]["label"], player=PLAYER.replace("__DATA__", payload).strip("\n"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"\n  wrote  {args.out}  ({args.out.stat().st_size / 1024:.1f} KB, {len(headlines)} headlines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
