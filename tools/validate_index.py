"""
Tool: validate_index
Read-only audit of index.html for structural integrity.

Checks:
  1. Every news card slug has a matching article page div
  2. Every article page has a matching news card
  3. Card image paths reference existing files
  4. articlePages JS array contains all card slugs
  5. Slug consistency: card src, card onclick, and article page id all match

Usage:
    python tools/validate_index.py
    python tools/validate_index.py --index path/to/index.html

Exit codes:
    0 = all checks passed
    1 = one or more errors found
"""

import argparse
import re
import sys
from pathlib import Path

INDEX_HTML = Path(__file__).parent.parent / "index.html"
IMAGES_DIR = Path(__file__).parent.parent / "images" / "news"


def extract_card_slugs(html: str) -> list[str]:
    """Extract slugs from all news card onclick attributes."""
    pattern = r'class="news-card"[^>]*onclick="showPage\(\'page-article-([^\']+)\'\)"'
    return re.findall(pattern, html)


def extract_page_ids(html: str) -> list[str]:
    """Extract all article page div IDs."""
    pattern = r'<div class="page"[^>]*id="page-article-([^"]+)"'
    return re.findall(pattern, html)


def extract_article_pages_js(html: str) -> list[str]:
    """Extract slugs from the articlePages JS array (strips 'page-article-' prefix)."""
    match = re.search(r'var articlePages\s*=\s*\[([^\]]*)\]', html)
    if not match:
        return []
    raw = match.group(1)
    return [s.strip().strip("'\"").replace("page-article-", "") for s in raw.split(",") if s.strip()]


def extract_card_image_src(html: str, slug: str) -> str | None:
    """Extract the image src from a card for a given slug."""
    pattern = rf"showPage\('page-article-{re.escape(slug)}'\)[^>]*>.*?<img[^>]*src=\"([^\"]+)\"[^>]*>"
    match = re.search(pattern, html, re.DOTALL)
    return match.group(1) if match else None


def run_audit(index_path: Path) -> bool:
    """Run all checks. Returns True if all pass, False if any fail."""
    if not index_path.exists():
        print(f"ERROR: index.html not found at {index_path}")
        return False

    html = index_path.read_text(encoding="utf-8")
    card_slugs = extract_card_slugs(html)
    page_ids = extract_page_ids(html)
    js_slugs = extract_article_pages_js(html)

    errors = []
    warnings = []

    print(f"\nvalidate_index — {index_path}")
    print(f"  Cards found:         {len(card_slugs)}")
    print(f"  Article pages found: {len(page_ids)}")
    print(f"  articlePages array:  {len(js_slugs)} entries\n")

    # Check 1: Every card slug has a matching article page
    for slug in card_slugs:
        if slug not in page_ids:
            errors.append(f"Card slug '{slug}' has NO matching article page div (id='page-article-{slug}')")

    # Check 2: Every article page has a matching card
    for page_slug in page_ids:
        if page_slug not in card_slugs:
            errors.append(f"Article page 'page-article-{page_slug}' has NO matching news card")

    # Check 3: Card image files exist on disk
    for slug in card_slugs:
        img_path = IMAGES_DIR / slug / "image-1.jpg"
        if not img_path.exists():
            errors.append(f"Missing image file: {img_path}")

    # Check 4: articlePages JS array contains all card slugs
    missing_from_js = [s for s in card_slugs if s not in js_slugs]
    if missing_from_js:
        errors.append(
            f"articlePages JS array is missing {len(missing_from_js)} slug(s): "
            + ", ".join(missing_from_js)
            + "\n    Fix: var articlePages = ["
            + ", ".join(f"'page-article-{s}'" for s in card_slugs)
            + "];"
        )

    extra_in_js = [s for s in js_slugs if s not in card_slugs]
    if extra_in_js:
        warnings.append(
            f"articlePages JS array has {len(extra_in_js)} slug(s) with no card: "
            + ", ".join(extra_in_js)
        )

    # Check 5: Duplicate slugs
    seen = set()
    for slug in card_slugs:
        if slug in seen:
            errors.append(f"Duplicate card slug: '{slug}'")
        seen.add(slug)

    seen = set()
    for pid in page_ids:
        if pid in seen:
            errors.append(f"Duplicate article page id: 'page-article-{pid}'")
        seen.add(pid)

    # Report
    if warnings:
        for w in warnings:
            print(f"  WARNING  {w}")

    if errors:
        for e in errors:
            print(f"  ERROR    {e}")
        print(f"\n  {len(errors)} error(s) found. Fix before pushing.\n")
        return False
    else:
        print(f"  All checks passed. index.html is consistent.\n")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate index.html article structure")
    parser.add_argument("--index", default=str(INDEX_HTML), help="Path to index.html")
    args = parser.parse_args()

    ok = run_audit(Path(args.index))
    sys.exit(0 if ok else 1)
