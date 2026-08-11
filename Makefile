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
#
# The whole body is ONE shell invocation (trailing backslashes). Make runs each
# recipe line in a separate shell, so an `exit 0` on its own line only ends that
# line — the rest of the target still runs. That bug made an empty publish fall
# through to `git commit` and fail on a clean tree.
publish: sync
	@set -e; \
	branch=$$(git rev-parse --abbrev-ref HEAD); \
	if git diff --quiet && git diff --cached --quiet && \
	   [ -z "$$(git ls-files --others --exclude-standard)" ]; then \
		echo "nothing to commit — working tree is clean"; \
	else \
		git add -A; \
		git commit -m "$${M:-post: update content}"; \
	fi; \
	if [ -z "$$(git log origin/$$branch..$$branch 2>/dev/null)" ] && \
	   git rev-parse --verify --quiet origin/$$branch >/dev/null; then \
		echo "nothing new to push — $$branch matches origin"; \
	else \
		git push -u origin "$$branch"; \
	fi; \
	if [ "$$branch" != "main" ]; then \
		echo ""; \
		echo "NOTE: you are on '$$branch', not main."; \
		echo "      Deploys only trigger on pushes to main, so the live site"; \
		echo "      will not change until this branch is merged."; \
	else \
		echo ""; \
		echo "pushed. GitHub Actions is building:"; \
		echo "  https://github.com/Ostring24/ostring.github.io/actions"; \
	fi

install-hooks:
	@git config core.hooksPath .githooks
	@echo "git hooks enabled (.githooks)"

clean:
	@rm -rf public resources .hugo_build.lock
	@echo "cleaned"
