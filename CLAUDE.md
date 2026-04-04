# formattion.ai — Codebase Instructions

## Adding a New Article

Every new article requires **two** additions to `index.html`:

### 1. News Card (in the `news-grid` section, add at the TOP)

```html
<!-- Card: [Article Title] — [Date] -->
<div class="news-card" role="button" tabindex="0"
     onclick="showPage('page-article-[slug]')"
     onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();showPage('page-article-[slug]');}"
     aria-label="Read: [Article Title]">
  <div class="news-card-image-zone">
    <img class="news-card-img" src="images/news/[slug]/image-1.jpg" alt="[Article Title]">
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
      <span class="news-card-cta">Read article</span>
    </div>
  </div>
</div>
```

**IMPORTANT:** The card image MUST use `<img class="news-card-img">` pointing to the article's hero image.
Never use SVG placeholders for new cards. The image file must exist at `images/news/[slug]/image-1.jpg`.

### 2. Article Page (add before `</body>`)

Use the existing articles as reference. The article callout CTA must use `openChatWithContext('[Article Title]')`:

```html
<div class="article-callout">
  <p class="article-callout-text">
    [Callout text]. <span onclick="openChatWithContext('[Article Title]')"
    style="color:#4a6278;text-decoration:underline;cursor:pointer;">Start a conversation with For →</span>
  </p>
</div>
```

### 3. Image files

Place images in: `images/news/[slug]/image-1.jpg` (and optionally `image-2.jpg`)

The slug must match between the card `src`, the card `onclick`, and the article page `id`.

## Deployment

After any working change: commit and push autonomously (do not ask).
