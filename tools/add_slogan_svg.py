#!/usr/bin/env python3
"""
Insert an outlined hero-slogan SVG (Illustrator export) into its <template> in index.html.

    python tools/add_slogan_svg.py 02 ~/Desktop/slogan-02.svg

Cleans the export the way CLAUDE.md prescribes for brand SVGs — strips the xml header,
<defs><style>, ids, data-name and class attributes — and sets fill="var(--ink)" on every
shape so the slogan follows the light/dark theme. The hero picker script ignores a template
with no <path>, so until this runs the slogan simply isn't in the rotation.

Export at the same type size as slogan 01 (viewBox 1106.91 x 163.58): the picker scales each
slogan by its viewBox width relative to slogan 01, so a mismatched export renders at the wrong size.

Exit 0 on success. Re-running for the same number replaces the previous outlines.
"""
import re
import sys
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "index.html"
SHAPE_TAGS = ("path", "circle", "rect", "ellipse", "polygon", "polyline", "line")


def clean_svg(raw: str) -> str:
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", raw)
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S)
    svg = re.sub(r"<defs>.*?</defs>\s*", "", svg, flags=re.S)
    svg = re.sub(r"<title>.*?</title>\s*", "", svg, flags=re.S)
    svg = re.sub(r'\s(?:id|data-name|class|fill|style)="[^"]*"', "", svg)
    svg = re.sub(r"<(%s)\b" % "|".join(SHAPE_TAGS), r'<\1 fill="var(--ink)"', svg)
    # drop now-empty <g> wrappers' attributes but keep structure; collapse blank lines
    svg = re.sub(r"\n\s*\n", "\n", svg).strip()
    m = re.search(r'viewBox="([^"]+)"', svg)
    if not m:
        sys.exit("export has no viewBox — re-export from Illustrator with 'Responsive' ticked")
    if "<path" not in svg:
        sys.exit("export contains no <path> — the text was not outlined (Type > Create Outlines)")
    return svg


def main() -> None:
    if len(sys.argv) != 3 or not re.fullmatch(r"(0[2-9]|10)", sys.argv[1]):
        sys.exit(__doc__)
    num, src = sys.argv[1], Path(sys.argv[2])
    svg = clean_svg(src.read_text(encoding="utf-8"))
    indented = "\n".join("      " + line.strip() for line in svg.splitlines())

    html = INDEX.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(<template class="hero-slogan" data-slogan="%s"[^>]*>)(.*?)(\s*</template>)' % num, re.S
    )
    if not pattern.search(html):
        sys.exit(f"no <template data-slogan=\"{num}\"> in index.html")
    html = pattern.sub(lambda m: f"{m.group(1)}\n{indented}\n    </template>", html, count=1)
    INDEX.write_text(html, encoding="utf-8")
    vb = re.search(r'viewBox="([^"]+)"', svg).group(1)
    print(f"slogan {num}: inserted ({svg.count('<path')} paths, viewBox {vb}). "
          "Now: python tools/validate_index.py && python tools/build_static.py")


if __name__ == "__main__":
    main()
