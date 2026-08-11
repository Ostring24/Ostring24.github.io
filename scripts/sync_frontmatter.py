#!/usr/bin/env python3
"""Fill in missing front matter for Hugo posts.

Design rules, in order of importance:

1. NEVER overwrite a field the author wrote by hand. This script only fills
   blanks. Run it a hundred times and the second run is a no-op.
2. NEVER touch git state. The script this replaces ran `git restore
   content/posts` after every build, which silently ate uncommitted work.
3. Dates come from git history, not filesystem mtime. mtime is reset by any
   checkout, which is why every post on the live site claimed 2025-11-28.

Fields it can infer:

  title       first `# ` heading, stripped of bold markers and inline HTML.
              The heading is then removed from the body, so the page does not
              render its title twice.
  date        first commit that added the file; today for uncommitted files.
  lastmod     most recent commit touching the file (only if already tracked).
  summary     first real prose paragraph, truncated on a sentence boundary.
  draft       false.

`tags` is deliberately never inferred. Auto-tagging produces near-duplicate
vocabulary that quietly wrecks the tag index; two or three by hand is better.

There is no `categories` field: the section directory under content/posts/
already expresses that grouping, and a category term sharing a section's name
makes site.GetPage ambiguous, which breaks the theme's menu.

Usage:
    python3 scripts/sync_frontmatter.py [paths...]   # default: content/posts
    python3 scripts/sync_frontmatter.py --check      # exit 1 if work is needed
"""

import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

CONTENT_ROOT = Path("content/posts")
TZ = timezone(timedelta(hours=8))

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---[ \t]*\n?", re.DOTALL)
H1_RE = re.compile(r"^#[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)

SUMMARY_MAX = 90


# --------------------------------------------------------------- text helpers

def clean_title(raw: str) -> str:
    """Strip the markdown and HTML debris that leaked into titles.

    Real examples from this repo:
        '**苹果WWDC 2025 前瞻**'
        '<span id="page-39-0"></span>**人工智能会对哪些人造成最大的伤害...**'
    """
    t = raw.strip()
    t = re.sub(r"<[^>]+>", "", t)            # inline HTML (<span id=...></span>)
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)   # bold
    t = re.sub(r"__(.+?)__", r"\1", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", t)  # italics
    t = re.sub(r"`(.+?)`", r"\1", t)         # inline code
    t = re.sub(r"\[(.+?)\]\([^)]*\)", r"\1", t)  # links -> text
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def strip_markdown(text: str) -> str:
    """Reduce a paragraph to plain prose for use as a summary."""
    t = text
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)   # images
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)  # links
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[*_`>#]+", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def is_prose(line: str) -> bool:
    """True if the line looks like a sentence rather than structure."""
    s = line.strip()
    if not s:
        return False
    # tables, headings, quotes, lists, code fences, html, images, hrules
    if s[0] in "|#>-*+<!=" or s.startswith("```"):
        return False
    if re.match(r"^\d+[.)]\s", s):
        return False
    return len(strip_markdown(s)) >= 12


def make_summary(body: str) -> str | None:
    for raw_line in body.split("\n"):
        if not is_prose(raw_line):
            continue
        text = strip_markdown(raw_line)
        if not text:
            continue
        if len(text) <= SUMMARY_MAX:
            return text
        # Prefer cutting at a sentence end so the card does not read as truncated.
        window = text[:SUMMARY_MAX]
        for stop in "。！？.!?；;":
            idx = window.rfind(stop)
            if idx >= SUMMARY_MAX // 2:
                return window[: idx + 1]
        return window.rstrip() + "…"
    return None


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


# ---------------------------------------------------------------- git helpers

def git_date(path: Path, first: bool) -> str | None:
    """ISO date of the first (or last) commit touching path."""
    cmd = ["git", "log", "--format=%aI", "-1"]
    if first:
        cmd += ["--diff-filter=A", "--follow"]
    cmd += ["--", str(path)]
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        ).stdout.strip()
    except OSError:
        return None
    return out or None


# ------------------------------------------------------------------ main work

def split_front_matter(text: str) -> tuple[str | None, str]:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


def has_key(front: str, key: str) -> bool:
    return re.search(rf"^{key}\s*:", front, re.MULTILINE) is not None


def process(path: Path, apply: bool = True) -> list[str]:
    """Return the list of fields that were (or would be) added."""
    original = path.read_text(encoding="utf-8")
    front, body = split_front_matter(original)
    front = front if front is not None else ""
    added: list[str] = []

    # -- title ---------------------------------------------------------------
    h1_match = H1_RE.search(body)
    h1_text = clean_title(h1_match.group(1)) if h1_match else None

    if not has_key(front, "title"):
        if h1_text:
            front += f"\ntitle: {yaml_quote(h1_text)}"
            added.append("title")
            body = body[: h1_match.start()] + body[h1_match.end():]
            body = body.lstrip("\n")
    else:
        # Title exists; drop a body H1 that merely repeats it so the page does
        # not show the same heading twice. (The old theme papered over this
        # with a client-side string comparison.)
        existing = re.search(r"^title\s*:\s*(.+)$", front, re.MULTILINE)
        if existing and h1_text:
            current = existing.group(1).strip().strip('"\'')
            if clean_title(current) == h1_text:
                body = body[: h1_match.start()] + body[h1_match.end():]
                body = body.lstrip("\n")
                added.append("dedup-h1")

    # -- date ----------------------------------------------------------------
    if not has_key(front, "date"):
        d = git_date(path, first=True) or datetime.now(TZ).isoformat(timespec="seconds")
        front += f"\ndate: {d}"
        added.append("date")

    if not has_key(front, "lastmod"):
        d = git_date(path, first=False)
        if d:
            front += f"\nlastmod: {d}"
            added.append("lastmod")

    # -- summary -------------------------------------------------------------
    if not has_key(front, "summary") and not has_key(front, "description"):
        s = make_summary(body)
        if s:
            front += f"\nsummary: {yaml_quote(s)}"
            added.append("summary")

    # -- draft ---------------------------------------------------------------
    if not has_key(front, "draft"):
        front += "\ndraft: false"
        added.append("draft")

    if not added:
        return []

    rebuilt = "---\n" + front.strip("\n") + "\n---\n\n" + body.lstrip("\n")
    if apply and rebuilt != original:
        path.write_text(rebuilt, encoding="utf-8")
    return added


def iter_posts(targets: list[str]) -> list[Path]:
    roots = [Path(t) for t in targets] if targets else [CONTENT_ROOT]
    files: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix == ".md":
            files.append(root)
        elif root.is_dir():
            # is_file() matters: this repo has a directory literally named
            # "m2_confusion.md", which rglob happily returns.
            files.extend(sorted(p for p in root.rglob("*.md") if p.is_file()))
    out = []
    for f in files:
        # Inside a leaf bundle only index.md is a page; siblings are resources.
        if f.name != "index.md" and (f.parent / "index.md").exists():
            continue
        out.append(f)
    return out


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_only = "--check" in sys.argv

    if not CONTENT_ROOT.exists():
        print(f"error: run from the repo root ({CONTENT_ROOT} not found)", file=sys.stderr)
        return 2

    touched = 0
    for path in iter_posts(args):
        added = process(path, apply=not check_only)
        if added:
            touched += 1
            print(f"  {path}: +{', '.join(added)}")

    if check_only:
        if touched:
            print(f"\n{touched} file(s) need front matter. Run: make sync")
            return 1
        print("front matter is complete")
        return 0

    print(f"\nupdated {touched} file(s)" if touched else "nothing to do")
    return 0


if __name__ == "__main__":
    sys.exit(main())
