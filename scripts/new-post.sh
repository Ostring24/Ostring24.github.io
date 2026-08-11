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
usage: $0 <section> <slug> ["标题"]

  section   one of: $SECTIONS
  slug      URL segment, lowercase-with-hyphens, ASCII only
  标题       optional; defaults to the slug, edit it later in the file

example:
  $0 tech qwen3-next-deep-dive "Qwen3-Next 模型深度解析"
EOF
  exit 1
}

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

printf '\033[32mcreated\033[0m %s/index.md\n' "$DIR"
printf '  preview:  make serve\n'
printf '  publish:  set draft: false, then make publish\n'

if [ -n "${EDITOR:-}" ]; then
  "$EDITOR" "$DIR/index.md"
else
  printf '\n  (set $EDITOR to open new posts automatically)\n'
fi
