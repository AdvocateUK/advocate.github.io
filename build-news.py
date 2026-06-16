#!/usr/bin/env python3
"""
Build oddfruit news pages from Markdown posts.

Workflow:
  1. Add a Markdown file to news/posts/ using the front-matter format in news/posts/_template.md.
  2. Run: python3 build-news.py
  3. Commit and push the generated HTML.

Generated files:
  - news/<slug>.html for each Markdown post
  - news/index.html
  - feed.xml
  - the homepage Latest update panel in index.html
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Iterable

SITE_URL = "https://oddfruit.co.uk"
ROOT = Path(__file__).resolve().parent
POSTS_DIR = ROOT / "news" / "posts"
NEWS_DIR = ROOT / "news"
HOME_PAGE = ROOT / "index.html"
FEED = ROOT / "feed.xml"

MONTHS = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
}

@dataclass(frozen=True)
class Post:
    slug: str
    title: str
    date: datetime
    category: str
    summary: str
    lead: str
    image: str
    image_alt: str
    body_markdown: str
    featured: bool = False
    image_class: str = ""
    latest_title: str = ""
    cta_text: str = "Download INR Mate on the App Store →"
    cta_url: str = "https://apps.apple.com/gb/app/inr-mate/id6752260598"

    @property
    def pretty_date(self) -> str:
        return f"{self.date.day} {MONTHS[self.date.month]} {self.date.year}"

    @property
    def url(self) -> str:
        return f"{self.slug}.html"


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_post(path: Path) -> Post:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path} is missing YAML-style front matter")
    try:
        _, front, body = text.split("---", 2)
    except ValueError as exc:
        raise ValueError(f"{path} has incomplete front matter") from exc

    meta: dict[str, str] = {}
    for raw_line in front.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"Bad metadata line in {path}: {raw_line!r}")
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")

    required = ["title", "date", "category", "summary", "lead", "image", "image_alt"]
    missing = [key for key in required if not meta.get(key)]
    if missing:
        raise ValueError(f"{path} is missing required metadata: {', '.join(missing)}")

    slug = meta.get("slug") or path.stem
    date = datetime.strptime(meta["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)

    return Post(
        slug=slug,
        title=meta["title"],
        date=date,
        category=meta["category"],
        summary=meta["summary"],
        lead=meta["lead"],
        image=meta["image"],
        image_alt=meta["image_alt"],
        body_markdown=body.strip(),
        featured=parse_bool(meta.get("featured", "false")),
        image_class=meta.get("image_class", ""),
        latest_title=meta.get("latest_title", ""),
        cta_text=meta.get("cta_text", "Download INR Mate on the App Store →"),
        cta_url=meta.get("cta_url", "https://apps.apple.com/gb/app/inr-mate/id6752260598"),
    )


def inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[(.+?)\]\((https?://[^\s)]+)\)", r'<a class="text-link" href="\2">\1</a>', escaped)
    escaped = re.sub(r"\[(.+?)\]\(([^\s)]+)\)", r'<a class="text-link" href="\2">\1</a>', escaped)
    return escaped


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            blocks.append(f"        <p>{inline_markdown(' '.join(paragraph).strip())}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            items = "\n".join(f"          <li>{inline_markdown(item)}</li>" for item in list_items)
            blocks.append(f"        <ul>\n{items}\n        </ul>")
            list_items = []

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            flush_list()
            continue
        if stripped.startswith("### "):
            flush_paragraph(); flush_list()
            blocks.append(f"        <h3>{inline_markdown(stripped[4:].strip())}</h3>")
        elif stripped.startswith("## "):
            flush_paragraph(); flush_list()
            blocks.append(f"        <h2>{inline_markdown(stripped[3:].strip())}</h2>")
        elif stripped.startswith("- "):
            flush_paragraph()
            list_items.append(stripped[2:].strip())
        else:
            flush_list()
            paragraph.append(stripped)
    flush_paragraph()
    flush_list()
    return "\n\n".join(blocks)


def relative_asset_for_root(path: str) -> str:
    return path[3:] if path.startswith("../") else path


def absolute_url(path: str) -> str:
    if path.startswith("http"):
        return path
    clean = path[3:] if path.startswith("../") else path
    return f"{SITE_URL}/{clean.lstrip('/')}"


def render_header(active_news: bool = True) -> str:
    active = ' class="active" aria-current="page"' if active_news else ""
    return f'''  <header class="home-nav">
    <a class="wordmark" href="../index.html" aria-label="oddfruit home">
      <img class="wordmark-mark" src="../assets/oddfruit-mark.svg" alt="" aria-hidden="true">
      <img class="wordmark-text" src="../assets/oddfruit-logo.svg" alt="oddfruit">
    </a>
    <nav aria-label="Main navigation">
      <a href="../index.html">Home</a>
      <a href="../inrmate/">INR Mate</a>
      <a href="../inrmate/story/">Story</a>
      <a href="../inrmate/resources/">Resources</a>
      <a{active} href="../news/">News</a>
      <a href="../inrmate/privacy.html">Privacy</a>
      <a href="mailto:support@oddfruit.co.uk">Contact</a>
    </nav>
  </header>'''


def render_footer() -> str:
    return '''  <footer class="oddf-shared-footer">
    <div class="oddf-shared-footer__brand">
      <a class="oddf-shared-footer__wordmark" href="../index.html" aria-label="oddfruit home">
        <img class="oddf-shared-footer__mark" src="../assets/oddfruit-mark.svg" alt="" aria-hidden="true">
        <img class="oddf-shared-footer__text" src="../assets/oddfruit-logo.svg" alt="oddfruit">
      </a>
      <p>© 2026 oddfruit. INR Mate is for tracking and record keeping only.</p>
    </div>
    <nav class="oddf-shared-footer__nav" aria-label="Footer navigation">
      <a href="../index.html">Home</a>
      <a href="../inrmate/">INR Mate</a>
      <a href="../inrmate/story/">Story</a>
      <a href="../inrmate/resources/">Resources</a>
      <a href="../news/">News</a>
      <a href="../inrmate/privacy.html">Privacy</a>
      <a href="mailto:support@oddfruit.co.uk">Contact</a>
    </nav>
  </footer>'''


def render_post(post: Post) -> str:
    title = html.escape(post.title)
    summary = html.escape(post.summary)
    lead = html.escape(post.lead)
    image = html.escape(post.image)
    image_alt = html.escape(post.image_alt)
    og_image = html.escape(absolute_url(post.image))
    body_html = markdown_to_html(post.body_markdown)
    cta = ""
    if post.cta_text and post.cta_url:
        cta = f'\n\n        <p><a class="text-link" href="{html.escape(post.cta_url)}">{html.escape(post.cta_text)}</a></p>'
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — oddfruit News</title>
  <meta name="description" content="{summary}">
  <meta name="theme-color" content="#fbf7ec">
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link rel="icon" href="../favicon-32x32.png" sizes="32x32" type="image/png">
  <link rel="apple-touch-icon" href="../apple-touch-icon.png">
  <link rel="canonical" href="{SITE_URL}/news/{post.url}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{summary}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{SITE_URL}/news/{post.url}">
  <meta property="og:image" content="{og_image}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>
{render_header()}

  <main>
    <article class="article-page">
      <header class="article-header">
        <p class="eyebrow">{post.pretty_date} · {html.escape(post.category)}</p>
        <h1>{title}</h1>
        <p class="lead">{lead}</p>
      </header>

      <figure class="article-hero-image">
        <img src="{image}" alt="{image_alt}">
      </figure>

      <div class="article-card">
{body_html}{cta}

        <nav class="post-nav" aria-label="News post navigation">
          <a href="index.html">← Back to news</a>
          <a href="../inrmate/">Explore INR Mate →</a>
        </nav>
      </div>
    </article>
  </main>

{render_footer()}
</body>
</html>
'''


def render_news_card(post: Post, featured_post: bool = False) -> str:
    extra_article_class = " featured-news-post" if featured_post else ""
    image_class = f" news-post-{post.image_class}" if post.image_class else ""
    return f'''      <article class="news-post story-panel{extra_article_class}">
        <a href="{html.escape(post.url)}" aria-label="Read {html.escape(post.title)}">
          <img class="news-post-image{image_class}" src="{html.escape(post.image)}" alt="{html.escape(post.image_alt)}">
        </a>
        <div class="news-post-content">
          <div>
            <p class="eyebrow">{post.pretty_date}</p>
            <h2><a href="{html.escape(post.url)}">{html.escape(post.title)}</a></h2>
          </div>
          <p>{html.escape(post.summary)}</p>
          <p><a class="text-link" href="{html.escape(post.url)}">Read the update →</a></p>
        </div>
      </article>'''


def render_news_index(posts: list[Post], featured: Post) -> str:
    cards = "\n".join(render_news_card(post, post == featured) for post in posts)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>oddfruit News</title>
  <meta name="description" content="Development updates, release notes and INR Mate news from oddfruit.">
  <meta name="theme-color" content="#fbf7ec">
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link rel="icon" href="../favicon-32x32.png" sizes="32x32" type="image/png">
  <link rel="apple-touch-icon" href="../apple-touch-icon.png">
  <link rel="canonical" href="{SITE_URL}/news/">
  <meta property="og:title" content="oddfruit News">
  <meta property="og:description" content="Development updates, release notes and INR Mate news from oddfruit.">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{SITE_URL}/news/">
  <meta property="og:image" content="{SITE_URL}/assets/inrmate-icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>
{render_header()}

  <main>
    <section class="home-hero news-hero fade-in">
      <div class="hero-copy">
        <p class="eyebrow">news &amp; updates</p>
        <h1>Development updates from oddfruit.</h1>
        <p class="lead">Release notes, INR Mate progress and practical notes from a tiny app studio building tools for real-life routines.</p>
      </div>
      <div class="orb-card news-orb" aria-hidden="true">
        <img class="orbit-hero-logo" src="../assets/oddfruit-mark-white.svg" alt="">
        <p>small updates, properly kept</p>
      </div>
    </section>

    <section class="news-list" aria-label="Latest news posts">
{cards}
    </section>
  </main>

{render_footer()}
</body>
</html>
'''


def render_latest_panel(post: Post) -> str:
    title = html.escape(post.latest_title or post.title)
    image = html.escape(relative_asset_for_root(post.image))
    alt = html.escape(post.image_alt)
    return f'''    <section class="story-panel latest-update-panel">
      <div>
        <p class="eyebrow">latest update</p>
        <h2>{title}</h2>
      </div>
      <div class="latest-update-content">
        <a class="latest-update-image-link" href="news/{html.escape(post.url)}" aria-label="Read {html.escape(post.title)}">
          <img src="{image}" alt="{alt}" />
        </a>
        <div>
          <p>{html.escape(post.summary)}</p>
          <p><a href="news/{html.escape(post.url)}">Read the update →</a></p>
        </div>
      </div>
    </section>'''


def update_homepage(post: Post) -> None:
    html_text = HOME_PAGE.read_text(encoding="utf-8")
    replacement = render_latest_panel(post)
    pattern = re.compile(r"    <section class=\"story-panel latest-update-panel\">.*?    </section>", re.DOTALL)
    new_html, count = pattern.subn(replacement, html_text, count=1)
    if count != 1:
        raise RuntimeError("Could not find the homepage Latest update panel to replace")
    HOME_PAGE.write_text(new_html, encoding="utf-8")


def render_feed(posts: list[Post]) -> str:
    items = []
    for post in posts[:10]:
        items.append(f'''    <item>
      <title>{html.escape(post.title)}</title>
      <link>{SITE_URL}/news/{post.url}</link>
      <guid>{SITE_URL}/news/{post.url}</guid>
      <pubDate>{format_datetime(post.date)}</pubDate>
      <description>{html.escape(post.summary)}</description>
    </item>''')
    now = format_datetime(datetime.now(timezone.utc))
    return f'''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>oddfruit News</title>
    <link>{SITE_URL}/news/</link>
    <description>Development updates, release notes and INR Mate news from oddfruit.</description>
    <language>en-gb</language>
    <lastBuildDate>{now}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
'''


def load_posts() -> list[Post]:
    if not POSTS_DIR.exists():
        raise RuntimeError(f"Missing posts directory: {POSTS_DIR}")
    posts = [parse_post(path) for path in POSTS_DIR.glob("*.md") if not path.name.startswith("_")]
    if not posts:
        raise RuntimeError("No Markdown posts found in news/posts")
    return sorted(posts, key=lambda post: (post.date, post.slug), reverse=True)


def choose_featured(posts: list[Post]) -> Post:
    featured = [post for post in posts if post.featured]
    return featured[0] if featured else posts[0]


def main() -> None:
    posts = load_posts()
    featured = choose_featured(posts)
    NEWS_DIR.mkdir(exist_ok=True)

    for post in posts:
        (NEWS_DIR / post.url).write_text(render_post(post), encoding="utf-8")

    (NEWS_DIR / "index.html").write_text(render_news_index(posts, featured), encoding="utf-8")
    FEED.write_text(render_feed(posts), encoding="utf-8")
    update_homepage(featured)

    print(f"Built {len(posts)} news posts.")
    print(f"Homepage latest update: {featured.title}")


if __name__ == "__main__":
    main()
