#!/usr/bin/env python3
"""
sync_services.py — Pull service content from n8n/Google Sheets and patch index.html.

Usage:
    python tools/sync_services.py

Prerequisites:
    - n8n workflow 'service-sync' must be live at ozarensky.app.n8n.cloud
    - index.html must contain the comment anchors:
        <!-- SERVICES-CARDS-START --> / <!-- SERVICES-CARDS-END -->
        <!-- SERVICES-PAGES-START --> / <!-- SERVICES-PAGES-END -->

After running, review index.html then:
    git add index.html images/services/
    git commit -m "services: sync from Google Sheets"
    git push
"""

import csv
import io
import os
import re
import shutil
import sys
import textwrap
import urllib.request

# ── Config ────────────────────────────────────────────────────────────────────

SHEET_ID  = "1Og0Aq8s2QIenNwM9oj5wyUI9oUKpkyBZj8oVpnje6oI"
TAB_NAME  = "Services"
INDEX_HTML = os.path.join(os.path.dirname(__file__), "..", "index.html")
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "images", "services")

CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    f"/export?format=csv&sheet={TAB_NAME}"
)

# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_services() -> list[dict]:
    print(f"Fetching sheet as CSV (no auth required) ...")
    with urllib.request.urlopen(CSV_URL, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(raw))
    services = []
    for row in reader:
        slug = row.get("slug", "").strip()
        if not slug:
            continue
        services.append({
            "slug":         slug,
            "number":       row.get("number", "").strip(),
            "card_eyebrow": row.get("card_eyebrow", "").strip(),
            "card_title":   row.get("card_title", "").strip(),
            "card_desc":    row.get("card_desc", "").strip(),
            "page_intro":   row.get("page_intro", "").strip(),
            "item1_title":  row.get("item1_title", "").strip(),
            "item1_desc":   row.get("item1_desc", "").strip(),
            "item1_tag1":   row.get("item1_tag1", "").strip(),
            "item1_tag2":   row.get("item1_tag2", "").strip(),
            "item2_title":  row.get("item2_title", "").strip(),
            "item2_desc":   row.get("item2_desc", "").strip(),
            "item2_tag1":   row.get("item2_tag1", "").strip(),
            "item2_tag2":   row.get("item2_tag2", "").strip(),
            "item3_title":  row.get("item3_title", "").strip(),
            "item3_desc":   row.get("item3_desc", "").strip(),
            "item3_tag1":   row.get("item3_tag1", "").strip(),
            "item3_tag2":   row.get("item3_tag2", "").strip(),
            "callout_text": row.get("callout_text", "").strip(),
            "image_prompt": row.get("image_prompt", "").strip(),
        })
    print(f"  {len(services)} service(s) received")
    return services

# ── Image generation ──────────────────────────────────────────────────────────

PLACEHOLDER_IMAGE = os.path.join(IMAGES_DIR, "placeholder.jpg")


def maybe_generate_image(slug: str, prompt: str) -> None:
    """Ensure an image exists for this slug: generate, or fall back to placeholder."""
    image_path = os.path.join(IMAGES_DIR, f"{slug}.jpg")
    if os.path.exists(image_path):
        print(f"  [image] {slug}.jpg exists — skipping generation")
        return

    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from generate_image import generate_image
        generate_image(slug, prompt, output_dir=IMAGES_DIR)
    except ImportError:
        pass

    # If still missing, copy placeholder so the page doesn't break
    if not os.path.exists(image_path):
        if os.path.exists(PLACEHOLDER_IMAGE):
            shutil.copy2(PLACEHOLDER_IMAGE, image_path)
            print(f"  [image] {slug}.jpg — copied from placeholder")
        else:
            print(f"  [image] {slug}.jpg missing and no placeholder found")

# ── HTML builders ─────────────────────────────────────────────────────────────

def build_card(s: dict) -> str:
    slug  = s["slug"]
    num   = s["number"]
    title = s["card_title"]
    desc  = s["card_desc"]
    img   = f"images/services/{slug}.jpg"

    return textwrap.dedent(f"""\
        <div class="service-cell" role="button" tabindex="0"
             onclick="showPage('page-service-{slug}')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();showPage('page-service-{slug}');}}">
          <div class="service-cell-image">
            <img src="{img}" alt="{title}">
          </div>
          <div class="service-cell-content">
            <div class="service-cell-label">{num}</div>
            <div class="service-cell-title">{title}</div>
            <div class="service-cell-body">{desc}</div>
          </div>
        </div>""")


def build_detail_page(s: dict) -> str:
    slug  = s["slug"]
    num   = s["number"]
    title = s["card_title"]
    intro = s["page_intro"]
    img   = f"images/services/{slug}.jpg"

    items_html = ""
    for i in (1, 2, 3):
        item_title = s.get(f"item{i}_title", "")
        item_desc  = s.get(f"item{i}_desc", "")
        tag1       = s.get(f"item{i}_tag1", "")
        tag2       = s.get(f"item{i}_tag2", "")
        items_html += textwrap.dedent(f"""\
            <div class="article-item">
              <div>
                <div class="article-item-title">{item_title}</div>
                <p class="article-item-desc">{item_desc}</p>
              </div>
              <div class="article-item-date">{tag1}<br>{tag2}</div>
            </div>
""")

    callout = s.get("callout_text", "")

    return textwrap.dedent(f"""\
  <div class="page" id="page-service-{slug}">
    <div class="page-inner">
      <div class="article-hero">
        <img src="{img}" alt="{title}">
      </div>
      <div class="page-eyebrow">services — {num}</div>
      <h1 class="article-page-title">{title}</h1>
      <p class="article-intro">{intro}</p>
{items_html}\
      <div class="article-callout">
        <p class="article-callout-text">{callout}</p>
        <button class="article-callout-btn" onclick="showPage('page-contact')">book a free audit</button>
      </div>
    </div>
  </div>""")

# ── Patch index.html ──────────────────────────────────────────────────────────

def patch_article_pages(html: str, services: list[dict]) -> str:
    """Rewrite the articlePages JS array, keeping non-service entries and adding new service slugs."""
    match = re.search(r"(var articlePages\s*=\s*\[)([^\]]*?)(\];)", html)
    if not match:
        print("  [warn] articlePages array not found — skipping")
        return html

    existing_raw = match.group(2)
    existing = re.findall(r"'([^']+)'", existing_raw)

    # Keep only non-service entries
    non_service = [p for p in existing if not p.startswith("page-service-")]

    # Append new service slugs
    service_entries = [f"page-service-{s['slug']}" for s in services]

    all_entries = non_service + service_entries
    new_array = ", ".join(f"'{e}'" for e in all_entries)
    replacement = f"{match.group(1)}{new_array}{match.group(3)}"
    return html[:match.start()] + replacement + html[match.end():]


def patch(html: str, start_marker: str, end_marker: str, new_content: str) -> str:
    start = html.find(start_marker)
    end   = html.find(end_marker)
    if start == -1 or end == -1:
        raise ValueError(f"Markers not found: '{start_marker}' / '{end_marker}'")
    end += len(end_marker)
    return html[:start] + start_marker + "\n" + new_content + "\n        " + end_marker + html[end:]


def update_index(services: list[dict]) -> None:
    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    # Build cards block (indented to match the services-grid context)
    cards_html = "\n".join(
        textwrap.indent(build_card(s), "        ")
        for s in services
    )

    # Build detail pages block
    pages_html = "\n\n".join(build_detail_page(s) for s in services)

    html = patch(html,
                 "<!-- SERVICES-CARDS-START -->",
                 "<!-- SERVICES-CARDS-END -->",
                 cards_html)

    html = patch(html,
                 "<!-- SERVICES-PAGES-START -->",
                 "<!-- SERVICES-PAGES-END -->",
                 "\n" + pages_html + "\n  ")

    html = patch_article_pages(html, services)

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"index.html updated — {len(services)} service(s) written")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    services = fetch_services()
    if not services:
        print("No services returned — aborting.")
        sys.exit(1)

    os.makedirs(IMAGES_DIR, exist_ok=True)

    for s in services:
        slug   = s["slug"]
        prompt = s.get("image_prompt", "")
        print(f"Processing: {slug}")
        maybe_generate_image(slug, prompt)

    update_index(services)
    print("\nDone. Review changes in index.html, then:")
    print("  git add index.html images/services/")
    print('  git commit -m "services: sync from Google Sheets"')
    print("  git push")


if __name__ == "__main__":
    main()
