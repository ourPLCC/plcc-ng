# Design: mkdocs --strict warnings investigation, and the decision to decommission the dev-docs site

Issue: [dev-docs/issues/done/145-mkdocs-strict-warnings-cleanup.md](../issues/done/145-mkdocs-strict-warnings-cleanup.md)
Date: 2026-07-06

## Resolution summary

Issue #145 was filed to clean up the warnings blocking `mkdocs build -f
mkdocs-dev.yml --strict`. Investigation (below) found that roughly 70%
of the warnings (52 of 77) exist only because mkdocs' `docs_dir` is
scoped to `dev-docs/`, which structurally cannot resolve links to
`bin/`, `src/`, or repo-root files no matter how they're written —
confirmed by reading mkdocs 1.6.1's own source, not inferred.

Rather than rewrite ~20 files' worth of links to work around that
constraint, the decision was to decommission the dev-docs mkdocs site
entirely: it isn't providing enough value to justify the ongoing
maintenance cost, and there are no near-term plans to improve it. The
`dev-docs/` directory of markdown files stays exactly as it is — it's
the project's issue tracker, roadmap, and design-spec archive,
browsable directly on GitHub — only the mkdocs build/publish step for
it goes away.

The remaining ~25 warnings (stale `issues/NNN` links pointing at
issues that have since moved to `issues/done/`) are real broken links
on GitHub independent of mkdocs, so they're still worth fixing, just
not as part of a build-gating cleanup.

This issue closes with three follow-up issues filed instead of a
direct fix, ordered in `dev-docs/roadmap.md` under "Dev-docs cleanup":

1. **[#148](../issues/done/148-decommission-dev-docs-mkdocs-site.md)** — remove the mkdocs-dev.yml build/deploy pipeline and its published gh-pages content.
2. **[#149](../issues/done/149-fix-stale-issues-done-links.md)** — fix the stale `issues/NNN` → `issues/done/NNN` links (the investigation's "Bucket B", below), independent of #148.
3. **[#150](../issues/done/150-close-script-auto-fix-links.md)** — harden `bin/issues/close.bash` so #149's bug class doesn't recur on future closes.

## Investigation: what the 77 warnings actually were

`mkdocs build -f mkdocs-dev.yml --strict` aborted with 77 warnings (the
issue was filed at 74; the count moved because issue #147 was created
after). All 77 came from two structurally different root causes,
verified by running the build and cross-checking every flagged path
against the filesystem — not from the issue's original two-category
guess, which undercounted and mischaracterized one category.

**Bucket A — links to files outside `docs_dir` (`dev-docs/`), 52
warnings.** `docs_dir` is `dev-docs`, so any relative link to `bin/`,
`src/`, or repo-root files (`CONTRIBUTING.md`, `CLAUDE.md`, etc.) can
never resolve inside mkdocs's file collection, regardless of whether
the target actually exists on disk. Sources:

- `contributing.md` → `../bin/*.bash` (20)
- `plans/2026-05-21-stop-error-cascade.md` → `src/plcc/parser/table_cli*.py` (4) and `plans/2026-06-07-065-documentation.md` → `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `DCO-1.1.txt`, `LICENSES/...` (4) — real files confirmed to exist at their repo-root/`src/` locations (8 total)
- `plans/2026-06-07-066-initial-user-docs.md` → `tokens.md`, `grammar.md`, `code-generation.md`, `examples.md`, `language-guide/index.md`, `cli/index.md`, `changelog.md` (7) — this file is embedded draft content proposing pages for the (separate, top-level) `docs/` user-docs site, so none of its targets were ever going to resolve inside the `dev-docs` build regardless. Checked each against the repo: `docs/language-guide/examples.md`, `docs/language-guide/index.md`, and `docs/cli/index.md` exist (3 — genuine Bucket A, real files outside `docs_dir`). `tokens.md`, `grammar.md`, and `code-generation.md` were renamed during implementation to `docs/language-guide/lexical.md`/`syntactic.md`/`semantic.md`, and `changelog.md` was never built as its own page (`docs/whats-new.md` exists instead) — these 4 don't exist anywhere, on disk or GitHub.
- `specs/2026-05-30-050-rename-grammar-file-to-grammar-design.md` → `src/plcc/cmd/{make,scan,parse,rep,diagram}.py` (5)
- `issues/done/{013,014,018,020,021}*.md` → `../../src/plcc/cmd/source_runner.py` (6, one file has two such links)
- `issue-conventions.md` → `../bin/issues/*.bash` (3)
- `specs/2026-04-13-phase-1-walking-skeleton.md` → `CONTRIBUTING.md`, `CLAUDE.md` (2)
- `release-sop.md` → `../bin/release/extract-changelog.bash` (1)
- `issues/done/141-whats-new-user-release-notes.md` → `../../docs/superpowers/specs/2026-07-04-136-release-notes-unification-design.md` (1, confirmed this file exists on disk)

**Bucket B — stale or malformed intra-`dev-docs/` links, 23 warnings +
2 broken nav entries.**

- `specs/*.md` (18) and `v1.0-criteria.md` (2) link to `issues/NNN-*.md` for issues that have since closed and moved to `issues/done/NNN-*.md` (20 total). Verified: all distinct targets exist under `issues/done/`, none under `issues/`.
- Three genuine path bugs caused by files moving into `issues/done/` without their own relative links being adjusted for the new depth:
  - `issues/done/018-ctrl-d-exit-missing-newline.md` links to `done/013-ctrl-c-does-not-exit-interactive-shell.md` — but both files already live *inside* `issues/done/`, so the correct link is the bare sibling filename `013-ctrl-c-does-not-exit-interactive-shell.md`.
  - `issues/done/025-interactive-first-line-attempt-before-continuation.md` has the same bug pointing at `done/020-ctrl-d-behavior-in-continuation.md` → should be `020-ctrl-d-behavior-in-continuation.md`.
  - `issues/done/146-cut-v1.0.0-release.md` links to `../v1.0-criteria.md` — correct when the file lived at `issues/146-...md` (one level under `dev-docs/`), but wrong now that it's one level deeper at `issues/done/146-...md`; needs `../../v1.0-criteria.md`.
- `mkdocs-dev.yml`'s `nav:` has `Design Specs: specs/` and `Implementation Plans: plans/` — bare directory references. No nav-generation plugin is installed (only `search` and `include-markdown`), so mkdocs can't expand a directory into a section, and both entries fail to resolve to any file. Moot once #148 removes the build entirely.

Separately, mkdocs already emits an **INFO** (not WARNING) listing
every `dev-docs/` file excluded from `nav:` — this is the issue's
original "category 1" concern, but it never actually caused `--strict`
to fail.

## Why not just suppress the warnings

mkdocs 1.6.1's `validation.links.not_found` setting
(`mkdocs/structure/pages.py:467`, confirmed by reading the installed
package source) is a single global switch with no per-directory or
per-file scoping. Setting it to `ignore` would silence Bucket A, but
it would silence Bucket B just as completely — including any *future*
link that breaks because a doc moved. That would defeat the point of
a `--strict` build worth trusting, which is part of why decommissioning
the site (removing the constraint entirely) won out over configuring
around it.

## Why not symlink `bin/`/`src/` into `dev-docs/` instead

Also considered: mkdocs does follow symlinks when walking `docs_dir`
(`mkdocs/structure/files.py:550`, `followlinks=True`), so placing
symlinks to `bin/`, `src/`, etc. inside `dev-docs/` was a candidate
root-cause fix for Bucket A. Rejected because (a) several existing
links already have the wrong relative depth for their file's nesting
level independent of the `docs_dir` boundary, so a meaningful chunk of
file editing would survive anyway; (b) it would make mkdocs copy the
entire `bin/` and `src/` trees into the built site as static assets,
for no reason other than making a few dozen links resolve; (c) it does
nothing for Bucket B. Decommissioning subsumes all of Bucket A's
motivation without any of these costs.

## Out of scope (tracked in the follow-up issues instead)

- Fixing Bucket B's stale links and depth bugs — #149.
- Preventing Bucket B's bug class from recurring — #150.
- Removing the mkdocs-dev.yml build/deploy pipeline and its gh-pages content — #148.
- Wiring `mkdocs build --strict` into CI — moot; there's no longer a dev-docs strict build to wire in once #148 ships.
