# formattion.ai

Public marketing site for FORMATTION AI LTD. Static HTML, no build framework, deployed to Vercel on every push to `main`.

- `index.html` — the whole site (SPA with hash routing). Single source of truth.
- `tools/build_static.py` — generates crawlable `/news/<slug>/` pages and `sitemap.xml` from `index.html`. Run before every commit that touches an article.
- `tools/validate_index.py` — structural audit of `index.html`. Run before every push.

Operator instructions, article template and deploy checklist: see `CLAUDE.md`.

Requires Python 3.11+ and `beautifulsoup4` for the build script.
