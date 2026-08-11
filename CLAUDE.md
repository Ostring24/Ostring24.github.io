# CLAUDE.md

Hugo blog, theme **PaperMod** (git submodule), deployed by GitHub Actions.
Content is ~95% long-form Chinese; UI chrome is English.

Full authoring docs: **[WRITING.md](WRITING.md)**.

## Layout

```
content/posts/<section>/<slug>/index.md   every post is a leaf bundle
  sections: infra | tech | research | solutions
assets/css/extended/cjk.css               CJK typography overrides
scripts/sync_frontmatter.py               fills missing front matter
scripts/new-post.sh                       scaffolds a post bundle
.githooks/pre-commit                      runs sync on staged content
```

## Commands

```bash
make new S=tech SLUG=my-post T="标题"
make serve      # localhost:1313, drafts included
make sync       # fill missing front matter
make check      # report only, exit 1 if incomplete (CI gate)
make build
make publish
```

## Rules

- **Every post is a page bundle** (`<slug>/index.md`), never a loose `.md`.
  Images live beside `index.md` and are referenced by bare filename.
  Non-bundle posts break relative image paths — that was a real bug here.
- **Never write a `categories:` field.** The taxonomy was removed: it mapped
  1:1 onto sections, and a category term sharing a section's name makes
  `site.GetPage` ambiguous and breaks the theme's menu.
- **Don't hand-write front matter** when creating posts; `make new` plus
  `sync_frontmatter.py` handle it. `sync` only fills blanks and never
  overwrites author-written values, so it is safe to re-run.
- **Reuse existing tags** (see WRITING.md for the vocabulary). New spellings
  of an existing concept fragment the tag index.
- `hasCJKLanguage = true` in hugo.toml is load-bearing — without it Hugo
  counts words by whitespace and every Chinese post reports "1 min".
- Never reintroduce a build step that runs `git restore`. The old `fire.sh`
  did, and it silently discarded uncommitted work.

## Deploy

Push to `main` → `.github/workflows/hugo.yml` builds and deploys.
Build output is not committed; `docs/` and `public/` are gitignored.
