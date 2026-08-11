#!/usr/bin/env bash
#
# Start a new post as a page bundle, with front matter already filled in.
#
#   ./scripts/new-post.sh <section> <slug> ["标题"]
#   ./scripts/new-post.sh tech qwen3-next-deep-dive "Qwen3-Next 模型深度解析"
#
# The bundle layout is what makes images painless: drop a file next to
# index.md and reference it as ![说明](file.png) — no path prefix, no
# static/ directory, no broken links when the post is renamed.

set -euo pipefail

SECTIONS="infra tech research solutions"

die() { printf '\033[31merror:\033[0m %s\n' "$1" >&2; exit 1; }

usage() {
  cat >&2 <<EOF
usage: $0 [--private] <section> <slug> ["标题"]

  section     one of: $SECTIONS
  slug        URL segment, lowercase-with-hyphens, ASCII only
  标题         optional; defaults to the slug, edit it later in the file

  --private   never publish this post. Unlike draft, it is hidden from
              'make serve' too, and produces no page, no search entry,
              no RSS item and no tag page.
              NOTE: the repo is public, so the file is still readable on
              GitHub. This hides it from the site, not from the world.

example:
  $0 tech qwen3-next-deep-dive "Qwen3-Next 模型深度解析"
  $0 --private research my-notes "内部笔记"
EOF
  exit 1
}

PRIVATE=0
if [ "${1:-}" = "--private" ]; then
  PRIVATE=1
  shift
fi

[ $# -ge 2 ] || usage

SECTION="$1"
SLUG="$2"
TITLE="${3:-$SLUG}"

# Reject unknown sections rather than silently creating a new one — that is
# how this site ended up with seven sections, five of them unreachable.
case " $SECTIONS " in
  *" $SECTION "*) ;;
  *) die "unknown section '$SECTION'. Use one of: $SECTIONS" ;;
esac

[[ "$SLUG" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] \
  || die "slug must be lowercase ASCII words separated by hyphens (got '$SLUG')"

cd "$(git rev-parse --show-toplevel)"

DIR="content/posts/$SECTION/$SLUG"
[ -e "$DIR" ] && die "$DIR already exists"

mkdir -p "$DIR"

# RFC3339 wants the offset as +08:00. GNU date has %:z for this; BSD date
# (macOS) does not and emits a literal ":z", so build it from %z instead.
OFFSET="$(date +%z)"                        # e.g. +0800
DATE="$(date +%Y-%m-%dT%H:%M:%S)${OFFSET:0:3}:${OFFSET:3:2}"

if [ "$PRIVATE" = 1 ]; then
  cat > "$DIR/index.md" <<EOF
---
title: "$TITLE"
date: $DATE
private: true
tags: []
---

<!--
  private: true — this post is never published. 'make sync' expands it into
  the build-options block Hugo needs. It produces no page, no search entry, no RSS
  item and no tag page, and is hidden from 'make serve' too.

  To publish later: delete the 'private: true' line AND the build block,
  then set draft: false.

  WARNING: the GitHub repo is public, so this file is still readable at
  github.com/Ostring24/ostring.github.io. This hides the post from the
  site, not from the internet.
-->

EOF
else
  cat > "$DIR/index.md" <<EOF
---
title: "$TITLE"
date: $DATE
draft: true
summary: ""
tags: []
---

<!--
  draft: true keeps this off the site. Flip to false when ready.
  'make serve' previews drafts; the deployed build excludes them.

  Never want to publish it? Use 'private: true' instead of 'draft: true'
  (or create it with: ./scripts/new-post.sh --private ...).

  Images: drop the file in this folder, then reference it directly:
      ![架构图](arch.png)
  A cover image goes in front matter:
      cover:
        image: "cover.png"

  Leave summary/tags blank if you like — 'make sync' fills summary in from
  your first paragraph. Tags are worth writing by hand; see WRITING.md for
  the vocabulary already in use.
-->

EOF
fi

printf '\033[32mcreated\033[0m %s/index.md\n' "$DIR"
if [ "$PRIVATE" = 1 ]; then
  printf '  \033[33mprivate\033[0m — never published, and not shown by "make serve"\n'
  printf '  the repo is public, so the file is still readable on GitHub\n'
  printf '  to publish later: remove "private: true" and the build block\n'
else
  printf '  preview:  make serve\n'
  printf '  publish:  set draft: false, then make publish\n'
fi

if [ -n "${EDITOR:-}" ]; then
  "$EDITOR" "$DIR/index.md"
else
  printf '\n  (set $EDITOR to open new posts automatically)\n'
fi
