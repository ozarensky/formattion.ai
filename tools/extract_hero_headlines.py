#!/usr/bin/env python3
"""
extract_hero_headlines.py — landing-hero headline extractor.

Reads the Claude Design "typing hero" exports (bundled HTML, ~1 MB each: React +
Babel + a motion editor around ~10 KB of real content) and writes
`hero-headlines.json` — only the glyph outlines and where they sit. The exports'
own animation timing is ignored: the inline hero player in `index.html` types every
headline with one natural rhythm. The exports themselves are never deployed.

Outputs:
  - hero-headlines.json   (BUILD OUTPUT — never hand-edit; re-run this script)

Usage:
    python tools/extract_hero_headlines.py                 # reads ../branding/hero animations/
    python tools/extract_hero_headlines.py --src "<dir>"   # any folder of exports

Adding a headline: export it from Claude Design into the source folder, add its
spoken text to LABELS below, re-run, commit hero-headlines.json.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_SRC = ROOT.parent / "branding" / "hero animations"
OUT = ROOT / "hero-headlines.json"

# Screen-reader text per export (file stem → what the headline says). The exports
# hold outlines, not text, so this cannot be derived. Missing stems fall back to
# the file name.
LABELS: dict[str, str] = {
    "AI for the Trades Animation": "AI for the trades. Automation for the business.",
    "Automating the Paperwork Animation": "Automating the paperwork of British construction",
    "Construction Subcontractors Animation": "AI automation for construction subcontractors",
    "Digital Foundation Animation": "The digital foundation for construction subcontractors",
    "Hero 2 Typing Animation (Union Jack)": "Built for the trades that build Britain",
    "Operating System Animation": "The operating system for construction subcontractors",
    "People Who Build Britain Animation": "AI automation for the people who build Britain",
}

# The hero viewBox the site has always used (branding/SVG/hero.svg): first glyph
# at x≈2, cap top at y≈10. Every headline is translated onto that origin so the
# left edge stays aligned with `.chat-btn`.
ORIGIN_X = 2.0
ORIGIN_Y = 10.0
MIN_VIEWBOX = (1106.91, 163.58)

_ISLAND = r'<script type="__bundler/%s">\s*(.*?)\s*</script>'
_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtZz]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_ARITY = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "Z": 0}


# ──────────────────────────────────────────────────────────────────────
# Bundle unpacking
# ──────────────────────────────────────────────────────────────────────

def island(html: str, kind: str):
    m = re.search(_ISLAND % kind, html, re.DOTALL)
    if not m:
        raise ValueError(f"missing __bundler/{kind} block")
    return json.loads(m.group(1))


def bundle_sources(html: str) -> list[str]:
    """Decoded text of every small script in the bundle (skips React/Babel)."""
    out = []
    for entry in island(html, "manifest").values():
        if "javascript" not in entry["mime"] and "jsx" not in entry["mime"]:
            continue
        if len(entry["data"]) > 60_000:   # libraries, not authored content
            continue
        raw = base64.b64decode(entry["data"])
        if entry.get("compressed"):
            raw = gzip.decompress(raw)
        out.append(raw.decode("utf-8"))
    return out


def js_literal(src: str, name: str):
    """Value of `window.<name> = <literal>;` — tolerates unquoted keys and single quotes."""
    m = re.search(r"window\.%s\s*=\s*(.*?);\s*(?:\n|$)" % name, src, re.DOTALL)
    if not m:
        return None
    text = m.group(1).strip()
    try:
        return json.loads(text)
    except ValueError:
        text = re.sub(r"([{,]\s*)([A-Za-z_]\w*)\s*:", r'\1"\2":', text).replace("'", '"')
        return json.loads(text)


# ──────────────────────────────────────────────────────────────────────
# Path bounding boxes (exact for the curves Illustrator emits)
# ──────────────────────────────────────────────────────────────────────

def _cubic_extrema(p0: float, p1: float, p2: float, p3: float) -> list[float]:
    a = -p0 + 3 * p1 - 3 * p2 + p3
    b = 2 * (p0 - 2 * p1 + p2)
    c = -p0 + p1
    ts: list[float] = []
    if abs(a) < 1e-12:
        if abs(b) > 1e-12:
            ts.append(-c / b)
    else:
        disc = b * b - 4 * a * c
        if disc >= 0:
            root = math.sqrt(disc)
            ts += [(-b + root) / (2 * a), (-b - root) / (2 * a)]
    out = [p0, p3]
    for t in ts:
        if 0 < t < 1:
            u = 1 - t
            out.append(u * u * u * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t * t * t * p3)
    return out


def path_bbox(d: str) -> tuple[float, float, float, float]:
    if re.search(r"[Aa]", d):
        raise ValueError("arc commands are not supported")
    tokens = _TOKEN.findall(d)
    xs: list[float] = []
    ys: list[float] = []
    x = y = sx = sy = 0.0
    px = py = None          # previous control point, for S / T reflection
    i, cmd = 0, ""
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
        elif cmd in "Mm":   # implicit lineto after a moveto
            cmd = "L" if cmd == "M" else "l"
        up = cmd.upper()
        rel = cmd != up
        n = _ARITY[up]
        a = [float(t) for t in tokens[i:i + n]]
        i += n
        ox, oy = (x, y) if rel else (0.0, 0.0)
        if up == "Z":
            x, y, px, py = sx, sy, None, None
            continue
        if up == "H":
            nx, ny = a[0] + ox, y
        elif up == "V":
            nx, ny = x, a[0] + oy
        else:
            nx, ny = a[-2] + ox, a[-1] + oy
        if up in "CS":
            if up == "C":
                c1x, c1y, c2x, c2y = a[0] + ox, a[1] + oy, a[2] + ox, a[3] + oy
            else:
                c1x, c1y = (2 * x - px, 2 * y - py) if px is not None else (x, y)
                c2x, c2y = a[0] + ox, a[1] + oy
            xs += _cubic_extrema(x, c1x, c2x, nx)
            ys += _cubic_extrema(y, c1y, c2y, ny)
            px, py = c2x, c2y
        elif up in "QT":
            if up == "Q":
                qx, qy = a[0] + ox, a[1] + oy
            else:
                qx, qy = (2 * x - px, 2 * y - py) if px is not None else (x, y)
            # a quadratic is the cubic with both controls 2/3 of the way to q
            xs += _cubic_extrema(x, x + 2 / 3 * (qx - x), nx + 2 / 3 * (qx - nx), nx)
            ys += _cubic_extrema(y, y + 2 / 3 * (qy - y), ny + 2 / 3 * (qy - ny), ny)
            px, py = qx, qy
        else:
            xs.append(nx)
            ys.append(ny)
            px = py = None
        if up == "M":
            sx, sy = nx, ny
        x, y = nx, ny
    return min(xs), min(ys), max(xs), max(ys)


# ──────────────────────────────────────────────────────────────────────
# One export → one headline record
# ──────────────────────────────────────────────────────────────────────

def extract(path: pathlib.Path) -> dict:
    html = path.read_text(encoding="utf-8")
    sources = bundle_sources(html)

    data_src = next((s for s in sources if re.search(r"window\.HERO_GLYPHS\s*=", s)), None)
    if data_src is None:
        raise ValueError("not a typing-hero export (no HERO_GLYPHS)")

    glyphs = js_literal(data_src, "HERO_GLYPHS")
    layout = js_literal(data_src, "HERO_LAYOUT")
    suffix = js_literal(data_src, "HERO_SUFFIX")

    lines = [g["line"] for g in glyphs]
    if lines != sorted(lines) or set(lines) != {0, 1}:
        raise ValueError("expected two lines of glyphs, line one first")
    split = lines.count(0)

    # The caret is placed from measured outlines, not HERO_LAYOUT: the exports'
    # startX / lineTops / lineH are hand-set per file and drift (startX lands
    # 12-24 units inside the first glyph, lineH runs 56-62). Measured values keep
    # the caret identical across headlines, so the rotation has no jump.
    boxes = [path_bbox(g["d"]) for g in glyphs]
    left = min(b[0] for b in boxes)
    right = max(b[2] for b in boxes)
    tops = [min(b[1] for b in boxes[:split]), min(b[1] for b in boxes[split:])]
    # a line with no capital or ascender measures low — fall back to the export's value
    for n in (0, 1):
        if abs(tops[n] - layout["lineTops"][n]) > 8:
            print(f"  WARN   {path.name}: line {n + 1} has no cap-height glyph — caret top taken from HERO_LAYOUT")
            tops[n] = layout["lineTops"][n]
    bottom = max(b[3] for b in boxes)
    if suffix:
        right = max(right, boxes[-1][2] + suffix["gap"] + suffix["width"])

    stem = path.stem
    name = re.sub(r"\s+Animation\b", "", stem).strip()
    dx = round(ORIGIN_X - left, 2)
    dy = round(ORIGIN_Y - tops[0], 2)

    return {
        "name": name,
        "label": LABELS.get(stem, name),
        "shift": [dx, dy],
        "startX": round(left, 2),
        "lineTops": [round(t, 2) for t in tops],
        "split": split,
        "glyphs": [g["d"] for g in glyphs],
        "suffix": suffix,
        "_extent": [round(right + dx, 2), round(bottom + dy, 2)],
    }


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", type=pathlib.Path, default=DEFAULT_SRC,
                    help=f"folder of exported .html files (default: {DEFAULT_SRC})")
    args = ap.parse_args()

    files = sorted(args.src.glob("*.html"))
    if not files:
        sys.stderr.write(f"No .html exports found in {args.src}\n")
        return 1

    headlines = []
    for f in files:
        try:
            h = extract(f)
        except Exception as e:
            sys.stderr.write(f"  FAILED {f.name}: {e}\n")
            return 1
        print(f"  read   {h['name']:<34} {h['split']:>2}+{len(h['glyphs']) - h['split']:<2} glyphs  "
              f"{h['_extent'][0]:7.2f} wide{'  + ' + h['suffix']['kind'] if h['suffix'] else ''}")
        if f.stem not in LABELS:
            print(f"  WARN   {f.name}: no entry in LABELS — aria-label falls back to the file name")
        headlines.append(h)

    width = max([MIN_VIEWBOX[0]] + [h["_extent"][0] for h in headlines])
    height = max([MIN_VIEWBOX[1]] + [h["_extent"][1] for h in headlines])
    for h in headlines:
        for k in [k for k in h if k.startswith("_")]:
            del h[k]

    payload = {"viewBox": [round(width, 2), round(height, 2)], "headlines": headlines}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"\n  wrote  {OUT.name}  ({len(headlines)} headlines, {OUT.stat().st_size / 1024:.1f} KB, "
          f"viewBox 0 0 {payload['viewBox'][0]} {payload['viewBox'][1]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
