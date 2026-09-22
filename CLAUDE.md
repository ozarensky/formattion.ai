# formattion.ai — public site (`web page/`)

This folder is its own git repo (`origin` → github.com/ozarensky/formattion.ai, branch `main`). Every push to
`main` deploys to https://formattion.ai via Vercel. There is no JS build, no framework, no package.json.
`index.html` is the single source of truth; `tools/build_static.py` derives the crawlable pages from it.

You operate here as `for` (root `../CLAUDE.md`). Root operating rules apply: read `../branding/formattion-brand-guidelines_4.html`
before any visual change, escalate before any push, never `git add -A`.

## Layout

```
index.html            # THE source of truth: landing, services, news cards, article pages, privacy, chat widget, contact form
news/                 # BUILD OUTPUT — never hand-edit. news/index.html + news/<slug>/index.html per article
sitemap.xml           # BUILD OUTPUT — never hand-edit
images/               # about/, news/<slug>/image-1.jpg (+ image-2.jpg), services/, logo.svg, logo-email.png, landing-bg.jpg
robots.txt            # Allows search engines, blocks ~30 AI/dataset crawlers. Intentional.
.well-known/ai.txt    # Blanket AI-training opt-out. Intentional.
vercel.json           # cleanUrls, security headers, X-Robots-Tag noai/noimageai, cache rules. Intentional.
favicon.svg
tools/
  validate_index.py   # Read-only audit of index.html. Run before every push. Exit 0 = safe.
  build_static.py     # index.html → news/<slug>/index.html + news/index.html + sitemap.xml. Needs beautifulsoup4.
  sync_services.py    # Pull services from Google Sheet via n8n `service-sync` webhook, rewrite cards/pages, gen images (--force)
  generate_image.py   # Thin shim → ../../image generator/tools/generate_image.py (used by sync_services)
  seed_services_sheet.py  # One-off: seeded the services Google Sheet from the business plan. Historical.
service-sync.json     # n8n export of the service-sync workflow
branding/             # STALE copy of the brand guidelines — read ../branding/ instead
```

## Anatomy of index.html (exact names — grep for these)

- **News card:** `<a class="news-card" href="/news/<slug>/" onclick="if(!event.metaKey&&…){event.preventDefault();showPage('page-article-<slug>');}">`
  inside the `news-grid`. Newest first.
- **Article page:** `<div class="page" id="page-article-<slug>">` before `</body>`.
- **Service cards (clickable):** `<div class="service-cell" role="button">` between `<!-- SERVICES-CARDS-START -->` / `END`.
  `.service-card` is a *different* thing — feature-bullet blocks inside service/article pages. Do not confuse them.
- **Service pages:** `<div class="page" id="page-service-<name>">` between `<!-- SERVICES-PAGES-START -->` / `END`.
- **`articlePages` JS array** (near the bottom): the **reading-progress-bar whitelist**. It lists the article ids *and*
  `page-privacy` *and* every `page-service-*`. It is not an article registry. When adding an article, append its
  `page-article-<slug>` to it; never remove the other entries.
- **Routing:** hash-based SPA (`showPage()`, `pushState`, `hashchange`).
- **Backend calls:** `CHAT_WEBHOOK_URL` and `CONTACT_WEBHOOK_URL` POST to n8n Cloud (`ozarensky.app.n8n.cloud`). Public by design.
- **Landing hero:** inline SVG (`class="brand-slogan"`, source `../branding/SVG/hero.svg`) with every path `fill="var(--ink)"`.
  When inlining any brand SVG: strip xml header, `<defs><style>`, ids, `data-name`; keep `.brand-slogan` width in sync with `.chat-btn` offset.

## Adding a New Article

The news engine does this automatically (`../workflows/news engine/tools/publish_to_web.py`). Manually, follow
`../workflows/manual_article_add.md`. Either way the result must be:

### 1. News Card (top of `news-grid`)

```html
<!-- Card: [Article Title] — [Date] -->
<a class="news-card" href="/news/[slug]/"
   onclick="if(!event.metaKey&&!event.ctrlKey&&!event.shiftKey){event.preventDefault();showPage('page-article-[slug]');}"
   aria-label="Read: [Article Title]">
  <div class="news-card-image-zone">
    <img loading="lazy" decoding="async" class="news-card-img" src="images/news/[slug]/image-1.jpg" alt="[Article Title]">
    <div class="news-card-gradient"></div>
  </div>
  <div class="news-card-content">
    <div>
      <div class="news-card-eyebrow">[eyebrow label]</div>
      <div class="news-card-title">[Article Title]</div>
      <div class="news-card-desc">[One-line description]</div>
    </div>
    <div class="news-card-footer">
      <span class="news-card-date">[D Month YYYY]</span>
    </div>
  </div>
</a>
```

The card image MUST be `<img class="news-card-img">` pointing at `images/news/[slug]/image-1.jpg`, which must exist. No SVG placeholders.

### 2. Article Page (before `</body>`)

Copy the existing article page. The callout CTA is the `article-callout-btn` pill — never an inline link:

```html
<div class="article-callout">
  <p class="article-callout-text">[Callout text].</p>
  <button class="article-callout-btn" onclick="openChatWithContext('[Article Title]')">chat with us</button>
</div>
```

**NEVER** add a `← back to news` link inside the SPA article. The top-left `←` is the only back navigation.
The standalone `/news/<slug>/` page gets its own `← all news` header from the build script.

### 3. Images

`images/news/[slug]/image-1.jpg` (and optionally `image-2.jpg`). Generated only via the central image engine.

### 4. `articlePages`

Append `'page-article-[slug]'` to the array.

### 5. Validate, build, deploy

```bash
python tools/validate_index.py      # must print "All checks passed" and exit 0
python tools/build_static.py        # regenerates news/ and sitemap.xml
git add index.html images/news/[slug]/ news/ sitemap.xml
git commit -m "news: [Article Title]"
git push
```

Never use `git add -A`. Never push without the build step — the article would be invisible to search engines.

## SEO / scraping policy

- `robots.txt` blocks AI training crawlers (GPTBot, ClaudeBot, Google-Extended, PerplexityBot, CCBot, Bytespider, etc.) while allowing real search engines.
- `vercel.json` injects `X-Robots-Tag: noai, noimageai` and security headers on every response.
- Every page declares `noai, noimageai` in its `<meta name="robots">`.
- `.well-known/ai.txt` declares the AI training opt-out at the standard path.

Never weaken these signals without checking with Ion first. See `../workflows/seo_gsc_setup.md` for Search Console.

## Known quirks

- `sitemap.xml` `lastmod` for `/` is derived from `index.html`'s filesystem mtime; a fresh clone rebuilds it to the clone date. Harmless.
- `SHEET_ID` differs between `sync_services.py`, `seed_services_sheet.py` and the latter's docstring. `sync_services.py` is the one that matters; verify against the n8n `service-sync` workflow before running.
- `validate_index.py` was broken from 2026-05-11 (markup change) to 2026-09-22 (regex fix). If it ever reports 0 cards on a site that clearly has cards, the card markup changed again — fix the regex, don't bypass.
