# oddfruit news workflow

News posts are now written in Markdown and converted to HTML with `build-news.py`.

## Add a new post

1. Copy `news/posts/_template.md`.
2. Rename it using a date and slug, for example:

   `news/posts/2026-07-01-new-feature.md`

3. Edit the metadata at the top of the file.
4. Write the post underneath the second `---` line.
5. From the site root, run:

   ```bash
   python3 build-news.py
   ```

6. Commit and push the generated changes.

## Homepage Latest update

The homepage chooses the post marked:

```yaml
featured: true
```

Only one post should normally have `featured: true`.

If no post is featured, the newest dated post is used automatically.

## Generated files

Do not manually edit these unless you really need to:

- `news/index.html`
- `news/*.html` article pages
- `feed.xml`
- the `Latest update` panel in `/index.html`

The next build will overwrite those sections.
