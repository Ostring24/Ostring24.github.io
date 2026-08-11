# Blog workflow. Five commands cover everything.
#
#   make new S=tech SLUG=my-post T="标题"   start a post
#   make serve                              preview at localhost:1313
#   make sync                               fill in missing front matter
#   make build                              production build into public/
#   make publish                            commit + push (Actions deploys)

.DEFAULT_GOAL := help
.PHONY: help new serve sync check build publish clean install-hooks

SHELL := /usr/bin/env bash

help:
	@echo ""
	@echo "  make new S=<section> SLUG=<slug> T=\"标题\""
	@echo "      Start a post. Sections: infra tech research solutions"
	@echo "      e.g. make new S=tech SLUG=qwen3-deep-dive T=\"Qwen3 深度解析\""
	@echo ""
	@echo "  make serve      Preview on http://localhost:1313 (drafts included)"
	@echo "  make sync       Fill in any missing title/date/summary"
	@echo "  make check      Report missing front matter without changing files"
	@echo "  make build      Production build into public/"
	@echo "  make publish    Commit and push; GitHub Actions deploys"
	@echo "  make clean      Remove build artifacts"
	@echo ""

new:
	@test -n "$(S)"    || { echo "usage: make new S=tech SLUG=my-post T=\"标题\""; exit 1; }
	@test -n "$(SLUG)" || { echo "usage: make new S=tech SLUG=my-post T=\"标题\""; exit 1; }
	@./scripts/new-post.sh "$(S)" "$(SLUG)" "$(T)"

serve:
	@hugo server -D --navigateToChanged --bind 127.0.0.1 --port 1313

sync:
	@python3 scripts/sync_frontmatter.py

check:
	@python3 scripts/sync_frontmatter.py --check

build: sync
	@rm -rf public resources
	@hugo --gc --minify
	@echo "built -> public/"

# sync first so a post written in a hurry still ships with complete metadata.
publish: sync
	@if git diff --quiet && git diff --cached --quiet; then \
		echo "nothing to publish"; exit 0; \
	fi
	@git add -A
	@git commit -m "$${M:-post: update content}"
	@git push
	@echo ""
	@echo "pushed. GitHub Actions is building:"
	@echo "  https://github.com/Ostring24/ostring.github.io/actions"

install-hooks:
	@git config core.hooksPath .githooks
	@echo "git hooks enabled (.githooks)"

clean:
	@rm -rf public resources .hugo_build.lock
	@echo "cleaned"
