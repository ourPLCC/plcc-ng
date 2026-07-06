# 145 - Clean up mkdocs build --strict warnings in dev-docs

**Type:** docs
**Date:** 2026-07-06

## Description

`mkdocs build -f mkdocs-dev.yml --strict` currently fails with 74
warnings. Discovered while adding `dev-docs/v1.0-criteria.md` for
issue #112 — the new page introduces zero new warnings, but the
pre-existing count means the dev-docs site can't be strict-built
clean, and CI/local builds silently tolerate broken links.

The warnings fall into two categories:

1. **Pages missing from `mkdocs-dev.yml` nav** — `roadmap.md`,
   `issues/index.md`, `issues/TEMPLATE.md`, and every file under
   `issues/done/` and `issues/*.md`. These are intentionally excluded
   from the published nav (they're working files, not end-user
   pages), so this category likely needs `not_in_nav:` entries in
   `mkdocs-dev.yml` rather than actual nav additions — or the plugin
   config needs a documented reason these are expected.
2. **Broken relative links in `dev-docs/specs/*.md`** — many older
   design-spec docs link to `../../issues/NNN-*.md` or
   `../issues/NNN-*.md` for issues that have since moved to
   `issues/done/NNN-*.md` when they were closed. The links were never
   updated to point at the new location.

## Steps to Reproduce

1. `export PATH="$(git rev-parse --show-toplevel)/.venv/bin:${PATH}"`
2. `mkdocs build -f mkdocs-dev.yml --strict`
3. Observe "Aborted with 74 warnings in strict mode!"

## Notes

- Not urgent — the non-strict build succeeds and the dev-docs site
  deploys fine today. This is a hygiene issue, not a broken deploy.
- Once fixed, consider wiring `mkdocs build --strict` into CI (or a
  `bin/docs/` script) so this doesn't silently regress again.
- Related but out of scope: issue #112's v1.0 criteria doc
  (`dev-docs/v1.0-criteria.md`) and the audit that surfaced this.
