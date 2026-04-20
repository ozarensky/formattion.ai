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

import os
import sys
import json
import textwrap
import urllib.request

# ── Config ────────────────────────────────────────────────────────────────────

N8N_WEBHOOK = "https://ozarensky.app.n8n.cloud/webhook/service-sync"
INDEX_HTML   = os.path.join(os.path.dirname(__file__), "..", "index.html")
IMAGES_DIR   = os.path.join(os.path.dirname(__file__), "..", "images", "services")

# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_services() -> list[dict]:
    print(f"Fetching from {N8N_WEBHOOK} ...")
    with urllib.request.urlopen(N8N_WEBHOOK, timeout=15) as resp:
        data = json.loads(resp.read())
    services = data.get("services", [])
    print(f"  {len(services)} service(s) received")
    return services

# ── Image generation ──────────────────────────────────────────────────────────

def maybe_generate_image(slug: str, prompt: str) -> None:
    """Call the image generation tool if the image doesn't already exist."""
    image_path = os.path.join(IMAGES_DIR, f"{slug}.jpg")
    if os.path.exists(image_path):
        print(f"  [image] {slug}.jpg exists — skipping generation")
        return

    try:
        # Import from the same tools/ directory
        sys.path.insert(0, os.path.dirname(__file__))
        from generate_image import generate_image
        generate_image(slug, prompt, output_dir=IMAGES_DIR)
    except ImportError:
        print(f"  [image] generate_image.py not found — skipping {slug}")

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
