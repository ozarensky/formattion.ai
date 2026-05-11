#!/usr/bin/env python3
"""
build_static.py — formattion.ai site builder.

Reads `index.html` and generates per-article static pages plus sitemap.xml.

Outputs:
  - news/<slug>/index.html  (one per article, fully indexable)
  - news/index.html         (news listing page)
  - sitemap.xml             (all URLs with lastmod)

Idempotent: safe to re-run on every deploy. The generated `news/` directory
is the build output — never hand-edit those files; edit `index.html`
and re-run this script.

Usage:
    python tools/build_static.py
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
import re
import sys
from html import escape as html_escape
from xml.sax.saxutils import escape as xml_escape

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write(
        "build_static.py requires beautifulsoup4. Install with:\n"
        "    pip install beautifulsoup4\n"
    )
    sys.exit(1)

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "index.html"
NEWS_DIR = ROOT / "news"
SITEMAP = ROOT / "sitemap.xml"
CANONICAL_BASE = "https://formattion.ai"


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def read_source() -> tuple[BeautifulSoup, str]:
    raw = SRC.read_text(encoding="utf-8")
    return BeautifulSoup(raw, "html.parser"), raw


def extract_inline_styles(raw_html: str) -> str:
    """Pull the first <style>...</style> block — the site's design system."""
    m = re.search(r"<style>(.*?)</style>", raw_html, re.DOTALL)
    return m.group(1) if m else ""


def slugify(article_id: str) -> str:
    return article_id.replace("page-article-", "", 1)


def parse_uk_date(text: str) -> _dt.date | None:
    text = text.strip()
    for fmt in ("%d %B %Y", "%d %b %Y"):
        try:
            return _dt.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def first_text(soup, selector: str, default: str = "") -> str:
    el = soup.select_one(selector)
    return el.get_text(" ", strip=True) if el else default


def absolute_image(src: str) -> str:
    if not src:
        return ""
    if src.startswith(("http://", "https://")):
        return src
    if src.startswith("/"):
        return CANONICAL_BASE + src
    return f"{CANONICAL_BASE}/{src}"


def truncate(text: str, limit: int = 158) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


# ──────────────────────────────────────────────────────────────────────
# Templates
# ──────────────────────────────────────────────────────────────────────

ARTICLE_SHELL_CSS = """
  /* Article shell — additions on top of site CSS */
  body.article-shell {
    overflow: auto;
    font-family: var(--sans);
    font-weight: 300;
    color: var(--ink);
    background: var(--bg);
  }
  .article-shell-header {
    position: sticky;
    top: 0;
    z-index: 100;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 18px 32px;
    background: var(--bg);
    border-bottom: 1px solid var(--dim);
  }
  .article-shell-header a {
    font-family: var(--mono);
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: lowercase;
    color: var(--ink);
    text-decoration: none;
  }
  .article-shell-header a:hover { color: var(--acc); }
  .article-shell-main {
    max-width: 900px;
    margin: 0 auto;
    padding: 60px 65px 80px;
  }
  .article-shell-main .page,
  .article-shell-main .page-inner {
    position: static;
    display: block;
    padding: 0;
    margin: 0;
    max-width: none;
    background: transparent;
  }
  .article-shell-footer {
    border-top: 1px solid var(--dim);
    padding: 32px;
    text-align: center;
    color: var(--muted);
    font-family: var(--mono);
    font-size: 12px;
    letter-spacing: 0.06em;
  }
  .article-shell-footer p { margin: 4px 0; }
  .article-shell-footer a { color: var(--ink); text-decoration: none; }
  .article-shell-footer a:hover { color: var(--acc); }
"""

COPY_PROTECTION_JS = """
(function installCopyProtection() {
  var ALLOW_SELECTORS = 'input, textarea, [contenteditable="true"]';
  function isInAllowedField(target) {
    try { return target && target.closest && target.closest(ALLOW_SELECTORS); }
    catch (e) { return false; }
  }
  document.addEventListener('contextmenu', function(e) {
    if (isInAllowedField(e.target)) return;
    e.preventDefault();
  });
  ['copy', 'cut'].forEach(function(evt) {
    document.addEventListener(evt, function(e) {
      if (isInAllowedField(e.target)) return;
      var sel = (window.getSelection && window.getSelection().toString()) || '';
      if (!sel) return;
      var watermark = '\\n\\n— formattion.ai — © formattion.ai. Source: ' + location.href;
      try {
        if (e.clipboardData) {
          e.clipboardData.setData('text/plain', sel + watermark);
          e.preventDefault();
        }
      } catch (err) {}
    });
  });
  document.addEventListener('keydown', function(e) {
    if (isInAllowedField(e.target)) return;
    var k = (e.key || '').toLowerCase();
    var blocked =
      e.key === 'F12' ||
      (e.ctrlKey && e.shiftKey && ['i', 'j', 'c'].indexOf(k) !== -1) ||
      (e.metaKey && e.altKey && ['i', 'j', 'c'].indexOf(k) !== -1) ||
      (e.ctrlKey && k === 'u') ||
      (e.ctrlKey && k === 's') ||
      (e.ctrlKey && k === 'p') ||
      (e.metaKey && k === 'u') ||
      (e.metaKey && k === 's') ||
      (e.metaKey && k === 'p');
    if (blocked) e.preventDefault();
  });
  document.addEventListener('dragstart', function(e) {
    if (e.target && e.target.tagName === 'IMG') e.preventDefault();
  });
})();
"""

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title_esc} — formattion.ai</title>
  <meta name="description" content="{description_esc}" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1, noai, noimageai" />
  <meta name="googlebot" content="index, follow, noai, noimageai" />
  <link rel="canonical" href="{canonical}" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <link rel="apple-touch-icon" href="/favicon.svg" />
  <meta name="theme-color" content="#F4EFE6" />
  <meta property="og:title" content="{title_esc}" />
  <meta property="og:description" content="{description_esc}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:type" content="article" />
  <meta property="og:image" content="{og_image}" />
  <meta property="og:locale" content="en_GB" />
  <meta property="article:published_time" content="{date_iso}" />
  <meta property="article:author" content="formattion.ai" />
  <meta property="article:section" content="{category_esc}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{title_esc}" />
  <meta name="twitter:description" content="{description_esc}" />
  <meta name="twitter:image" content="{og_image}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Infant:ital,wght@0,300;1,300;1,400&family=DM+Mono:wght@300;400&family=Inter:wght@300;400&display=swap" rel="stylesheet" />
  <script type="application/ld+json">{article_jsonld}</script>
  <script type="application/ld+json">{breadcrumb_jsonld}</script>
  <style>{styles}</style>
  <style>{shell_css}</style>
</head>
<body class="article-shell">
  <header class="article-shell-header">
    <a href="/news/" aria-label="Back to all news">← all news</a>
    <a href="/" aria-label="formattion.ai home">formattion.ai</a>
  </header>
  <main class="article-shell-main">
    {article_html}
  </main>
  <footer class="article-shell-footer">
    <p>© formattion.ai — AI automation for UK construction subcontractors.</p>
    <p><a href="/">home</a> · <a href="/news/">news</a> · <a href="/#contact">free operations audit</a></p>
  </footer>
  <script>{copy_js}</script>
</body>
</html>
"""

NEWS_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>From the field — formattion.ai news</title>
  <meta name="description" content="Perspectives on automation, operational systems, and what's changing in the UK construction subcontract sector." />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, noai, noimageai" />
  <meta name="googlebot" content="index, follow, noai, noimageai" />
  <link rel="canonical" href="{base}/news/" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <link rel="apple-touch-icon" href="/favicon.svg" />
  <meta name="theme-color" content="#F4EFE6" />
  <meta property="og:title" content="From the field — formattion.ai news" />
  <meta property="og:description" content="Perspectives on automation, operational systems, and what's changing in the UK construction subcontract sector." />
  <meta property="og:url" content="{base}/news/" />
  <meta property="og:type" content="website" />
  <meta property="og:image" content="{base}/og.png" />
  <meta property="og:locale" content="en_GB" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Infant:ital,wght@0,300;1,300;1,400&family=DM+Mono:wght@300;400&family=Inter:wght@300;400&display=swap" rel="stylesheet" />
  <script type="application/ld+json">{{
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "From the field — formattion.ai news",
    "url": "{base}/news/",
    "inLanguage": "en-GB",
    "isPartOf": {{ "@type": "WebSite", "name": "formattion.ai", "url": "{base}/" }}
  }}</script>
  <style>{styles}</style>
  <style>{shell_css}</style>
</head>
<body class="article-shell">
  <header class="article-shell-header">
    <a href="/" aria-label="formattion.ai home">← home</a>
    <a href="/" aria-label="formattion.ai home">formattion.ai</a>
  </header>
  <main class="article-shell-main">
    <h1 class="page-title news-page-title">From the field.</h1>
    <div class="page-body">
      <p>Perspectives on automation, operational systems, and what's changing in the subcontract trades sector.</p>
    </div>
    <div class="page-divider"></div>
    <div class="news-grid">
      {cards_html}
    </div>
  </main>
  <footer class="article-shell-footer">
    <p>© formattion.ai — AI automation for UK construction subcontractors.</p>
    <p><a href="/">home</a> · <a href="/news/">news</a> · <a href="/#contact">free operations audit</a></p>
  </footer>
  <script>{copy_js}</script>
</body>
</html>
"""


# ──────────────────────────────────────────────────────────────────────
# Builders
# ──────────────────────────────────────────────────────────────────────

def build_article(article_el, styles: str) -> dict:
    article_id = article_el.get("id", "")
    slug = slugify(article_id)
    if not slug:
        raise ValueError(f"Could not derive slug from id='{article_id}'")

    title = first_text(article_el, ".article-page-title", "formattion.ai article")
    intro = first_text(article_el, ".article-intro", "")
    description = truncate(intro, 158)

    meta_el = article_el.select_one(".article-meta")
    spans = meta_el.find_all("span") if meta_el else []
    date_text = spans[0].get_text(strip=True) if spans else ""
    category = spans[1].get_text(strip=True) if len(spans) > 1 else ""
    date_iso = ""
    parsed = parse_uk_date(date_text)
    if parsed:
        date_iso = parsed.isoformat()

    hero = article_el.select_one(".article-hero img")
    image_src = hero.get("src", "") if hero else ""
    og_image = absolute_image(image_src) or f"{CANONICAL_BASE}/og.png"

    canonical = f"{CANONICAL_BASE}/news/{slug}/"

    inner = article_el.select_one(".page-inner")
    # rewrite relative image paths so they resolve from the site root, not /news/<slug>/
    if inner:
        for img in inner.find_all("img"):
            src = img.get("src", "")
            if src and not src.startswith(("http://", "https://", "/")):
                img["src"] = "/" + src
    inner_html = inner.decode_contents() if inner else article_el.decode_contents()

    article_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "image": og_image,
        "datePublished": date_iso or _dt.date.today().isoformat(),
        "dateModified": date_iso or _dt.date.today().isoformat(),
        "author": {"@type": "Organization", "name": "formattion.ai", "url": f"{CANONICAL_BASE}/"},
        "publisher": {
            "@type": "Organization",
            "name": "formattion.ai",
            "url": f"{CANONICAL_BASE}/",
            "logo": {"@type": "ImageObject", "url": f"{CANONICAL_BASE}/favicon.svg"},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "inLanguage": "en-GB",
        "articleSection": category,
    }, ensure_ascii=False, indent=2)

    breadcrumb_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "formattion.ai", "item": f"{CANONICAL_BASE}/"},
            {"@type": "ListItem", "position": 2, "name": "News", "item": f"{CANONICAL_BASE}/news/"},
            {"@type": "ListItem", "position": 3, "name": title, "item": canonical},
        ],
    }, ensure_ascii=False, indent=2)

    page_html = ARTICLE_TEMPLATE.format(
        title_esc=html_escape(title, quote=True),
        description_esc=html_escape(description, quote=True),
        canonical=canonical,
        og_image=og_image,
        date_iso=date_iso,
        category_esc=html_escape(category, quote=True),
        base=CANONICAL_BASE,
        article_jsonld=article_jsonld,
        breadcrumb_jsonld=breadcrumb_jsonld,
        styles=styles,
        shell_css=ARTICLE_SHELL_CSS,
        article_html=inner_html,
        copy_js=COPY_PROTECTION_JS,
    )

    target_dir = NEWS_DIR / slug
    target_dir.mkdir(parents=True, exist_ok=True)
    out_file = target_dir / "index.html"
    out_file.write_text(page_html, encoding="utf-8")

    return {
        "slug": slug,
        "title": title,
        "description": description,
        "date_text": date_text,
        "date_iso": date_iso or _dt.date.today().isoformat(),
        "category": category,
        "image": image_src,
        "canonical": canonical,
    }


def build_news_index(articles: list[dict], styles: str) -> None:
    cards = []
    for art in articles:
        img_src = art["image"] if art["image"].startswith("/") else f"/{art['image']}"
        cards.append(
            f"""<a class="news-card-link" href="/news/{art['slug']}/" style="display:block;text-decoration:none;color:inherit;">
        <div class="news-card" role="article" aria-label="Read: {html_escape(art['title'], quote=True)}">
          <div class="news-card-image-zone">
            <img loading="lazy" decoding="async" class="news-card-img" src="{img_src}" alt="{html_escape(art['title'], quote=True)}">
            <div class="news-card-gradient"></div>
          </div>
          <div class="news-card-content">
            <div>
              <div class="news-card-eyebrow">{html_escape(art['category'])}</div>
              <div class="news-card-title">{html_escape(art['title'])}</div>
              <div class="news-card-desc">{html_escape(art['description'])}</div>
            </div>
            <div class="news-card-footer">
              <span class="news-card-date">{html_escape(art['date_text'])}</span>
            </div>
          </div>
        </div>
      </a>"""
        )

    out = NEWS_DIR / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        NEWS_INDEX_TEMPLATE.format(
            base=CANONICAL_BASE,
            styles=styles,
            shell_css=ARTICLE_SHELL_CSS,
            cards_html="\n".join(cards),
            copy_js=COPY_PROTECTION_JS,
        ),
        encoding="utf-8",
    )


def build_sitemap(articles: list[dict]) -> None:
    today = _dt.date.today().isoformat()
    src_mtime = _dt.date.fromtimestamp(SRC.stat().st_mtime).isoformat()

    urls = [
        (f"{CANONICAL_BASE}/", src_mtime, "1.0", "weekly"),
        (f"{CANONICAL_BASE}/news/", today, "0.8", "weekly"),
    ]
    for art in sorted(articles, key=lambda a: a["date_iso"], reverse=True):
        urls.append((art["canonical"], art["date_iso"], "0.7", "monthly"))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, priority, changefreq in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{xml_escape(loc)}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append(f"    <changefreq>{changefreq}</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    SITEMAP.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def main() -> int:
    if not SRC.exists():
        sys.stderr.write(f"Source not found: {SRC}\n")
        return 1

    soup, raw = read_source()
    styles = extract_inline_styles(raw)

    article_els = soup.select('div.page[id^="page-article-"]')
    if not article_els:
        sys.stderr.write("No articles found in index.html (expected <div class=\"page\" id=\"page-article-*\">).\n")
        return 1

    # force UTF-8 stdout so Windows cp1252 doesn't choke on titles with em dashes
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    NEWS_DIR.mkdir(exist_ok=True)
    articles = []
    for el in article_els:
        info = build_article(el, styles)
        articles.append(info)
        print(f"  built  news/{info['slug']}/  -  {info['title']}")

    build_news_index(articles, styles)
    print(f"  built  news/index.html  (listing {len(articles)} article(s))")

    build_sitemap(articles)
    print(f"  built  sitemap.xml  ({len(articles) + 2} URLs)")

    print(f"\nDone. {len(articles)} article(s) regenerated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
