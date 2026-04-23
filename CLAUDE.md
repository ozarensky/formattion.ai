# Agent Instructions

You're working inside the **WAT framework** (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution. That separation is what makes this system reliable.

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases
- Written in plain language, the same way you'd brief someone on your team

**Layer 2: Agents (The Decision-Maker)**
- This is your role. You're responsible for intelligent coordination.
- Read the relevant workflow, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed
- You connect intent to execution without trying to do everything yourself
- Example: If you need to pull data from a website, don't attempt it directly. Read `workflows/scrape_website.md`, figure out the required inputs, then execute `tools/scrape_single_site.py`

**Layer 3: Tools (The Execution)**
- Python scripts in `tools/` that do the actual work
- API calls, data transformations, file operations, database queries
- Credentials and API keys are stored in `.env`
- These scripts are consistent, testable, and fast

**Why this matters:** When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, you stay focused on orchestration and decision-making where you excel.

## How to Operate

**1. Look for existing tools first**
Before building anything new, check `tools/` based on what your workflow requires. Only create new scripts when nothing exists for that task.

**2. Learn and adapt when things fail**
When you hit an error:
- Read the full error message and trace
- Fix the script and retest (if it uses paid API calls or credits, check with me before running again)
- Document what you learned in the workflow (rate limits, timing quirks, unexpected behavior)
- Example: You get rate-limited on an API, so you dig into the docs, discover a batch endpoint, refactor the tool to use it, verify it works, then update the workflow so this never happens again

**3. Keep workflows current**
Workflows should evolve as you learn. When you find better methods, discover constraints, or encounter recurring issues, update the workflow. That said, don't create or overwrite workflows without asking unless I explicitly tell you to. These are your instructions and need to be preserved and refined, not tossed after one use.

## The Self-Improvement Loop

Every failure is a chance to make the system stronger:
1. Identify what broke
2. Fix the tool
3. Verify the fix works
4. Update the workflow with the new approach
5. Move on with a more robust system

This loop is how the framework improves over time.

## File Structure

**What goes where:**
- **Deliverables**: Final outputs go to cloud services (Google Sheets, Slides, etc.) where I can access them directly
- **Intermediates**: Temporary processing files that can be regenerated

**Directory layout:**
```
.tmp/           # Temporary files (scraped data, intermediate exports). Regenerated as needed.
tools/          # Python scripts for deterministic execution
workflows/      # Markdown SOPs defining what to do and how
.env            # API keys and environment variables (NEVER store secrets anywhere else)
credentials.json, token.json  # Google OAuth (gitignored)
```

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
    </div>
  </div>
</div>
```

**IMPORTANT:** The card image MUST use `<img class="news-card-img">` pointing to the article's hero image.
Never use SVG placeholders for new cards. The image file must exist at `images/news/[slug]/image-1.jpg`.

### 2. Article Page (add before `</body>`)

Use the existing articles as reference. The article callout CTA uses the `article-callout-btn` pill button — never an inline link or span:

```html
<div class="article-callout">
  <p class="article-callout-text">[Callout text].</p>
  <button class="article-callout-btn" onclick="openChatWithContext('[Article Title]')">chat with us</button>
</div>
```

**NEVER** add a `← back to news` link or any other back navigation inside an article. The `←` arrow in the top-left corner is the only navigation back.

### 3. Image files

Place images in: `images/news/[slug]/image-1.jpg` (and optionally `image-2.jpg`)

The slug must match between the card `src`, the card `onclick`, and the article page `id`.

## Deployment

After adding or updating articles: stage only the changed files, commit, and push.

```bash
git add index.html images/news/[slug]/
git commit -m "news: [Article Title]"
git push
```

Never use `git add -A` — only stage the files that were intentionally changed.



**Core principle:** Local files are just for processing. Anything I need to see or use lives in cloud services. Everything in `.tmp/` is disposable.

## Bottom Line

You sit between what I want (workflows) and what actually gets done (tools). Your job is to read instructions, make smart decisions, call the right tools, recover from errors, and keep improving the system as you go.

Stay pragmatic. Stay reliable. Keep learning.
