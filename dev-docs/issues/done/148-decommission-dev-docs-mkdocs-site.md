# 148 - Decommission the dev-docs mkdocs site

**Type:** chore
**Date:** 2026-07-06

## Description

Stop building and publishing the dev-docs mkdocs site. Filed while
resolving #145 (mkdocs `--strict` warnings cleanup): investigation
showed that roughly 70% of the strict-build warnings (52 of 77) exist
solely because `docs_dir` is scoped to `dev-docs/`, which can never
resolve relative links to `bin/`, `src/`, or repo-root files no matter
how they're written — confirmed by reading mkdocs 1.6.1's own link
validation source (`mkdocs/structure/files.py:550`,
`mkdocs/structure/pages.py:467`). The site itself isn't providing
enough value to justify carrying that constraint indefinitely, so
remove the build instead of working around it.

The `dev-docs/` directory of markdown files is **not** going away — it
keeps being the project's issue tracker, roadmap, and design-spec
archive, browsable directly on GitHub exactly as `CONTRIBUTING.md` and
other repo-root docs already are. Only the mkdocs build/publish step
for it goes away.

Work:

- Remove `mkdocs-dev.yml`.
- Remove the "Build developer docs" and "Merge developer docs into
  gh-pages" steps from `.github/workflows/docs.yml` (steps 54-63 as of
  this writing) — keep the rest of that workflow (user-facing `docs/`
  site via `mike`) untouched.
- Remove the `mkdocs-dev.yml` path trigger from `.github/workflows/ci.yml`.
- Delete the three `include-markdown` shim files that exist only to
  feed the dev-docs site: `dev-docs/contributing.md`,
  `dev-docs/code-of-conduct.md`, `dev-docs/changelog.md`.
- Update `README.md`'s "Developer docs" link (currently
  `https://ourplcc.github.io/plcc-ng/dev-docs/`) to point at the
  `dev-docs/` tree on GitHub instead.
- Remove the already-published `dev-docs/` directory from the
  `gh-pages` branch, so old bookmarked links to the built site 404
  cleanly instead of silently serving an increasingly stale snapshot.

## Notes

- Full investigation and rationale: `dev-docs/specs/2026-07-06-145-mkdocs-strict-warnings-cleanup-design.md`.
- Does not touch the remaining ~25 warnings caused by stale
  `issues/NNN` links (tracked separately as #149) — those are real
  broken links on GitHub regardless of whether this site exists.
