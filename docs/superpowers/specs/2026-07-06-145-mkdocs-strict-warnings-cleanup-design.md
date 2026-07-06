# Design: Clean up mkdocs build --strict warnings in dev-docs

Issue: [dev-docs/issues/145-mkdocs-strict-warnings-cleanup.md](../../../dev-docs/issues/145-mkdocs-strict-warnings-cleanup.md)
Date: 2026-07-06

## Problem

`mkdocs build -f mkdocs-dev.yml --strict` currently aborts with 77 warnings (the issue was filed at 74; the count moved because issue #147 was created after). All 77 come from two structurally different root causes, verified by running the build and cross-checking every flagged path against the filesystem — not from the issue's original two-category guess, which undercounted and mischaracterized one category.

**Bucket A — links to files outside `docs_dir` (`dev-docs/`), 52 warnings.** `docs_dir` is `dev-docs`, so any relative link to `bin/`, `src/`, or repo-root files (`CONTRIBUTING.md`, `CLAUDE.md`, etc.) can never resolve inside mkdocs's file collection, regardless of whether the target actually exists on disk. Sources:

- `contributing.md` → `../bin/*.bash` (20)
- `plans/*.md` → `src/plcc/...`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `DCO-1.1.txt`, `LICENSES/...` (15)
- `specs/2026-05-30-050-rename-grammar-file-to-grammar-design.md` → `src/plcc/cmd/{make,scan,parse,rep,diagram}.py` (5)
- `issues/done/{013,014,018,020,021}*.md` → `../../src/plcc/cmd/source_runner.py` (6, one file has two such links)
- `issue-conventions.md` → `../bin/issues/*.bash` (3)
- `specs/2026-04-13-phase-1-walking-skeleton.md` → `CONTRIBUTING.md`, `CLAUDE.md` (2)
- `release-sop.md` → `../bin/release/extract-changelog.bash` (1)
- `issues/done/141-whats-new-user-release-notes.md` → `../../docs/superpowers/specs/2026-07-04-136-release-notes-unification-design.md` (1, confirmed this file exists on disk)

**Bucket B — stale or malformed intra-`dev-docs/` links, 23 warnings + 2 broken nav entries.**

- `specs/*.md` (18) and `v1.0-criteria.md` (2) link to `issues/NNN-*.md` for issues that have since closed and moved to `issues/done/NNN-*.md` (20 total). Verified: all distinct targets exist under `issues/done/`, none under `issues/`.
- Three genuine path bugs caused by files moving into `issues/done/` without their own relative links being adjusted for the new depth:
  - `issues/done/018-ctrl-d-exit-missing-newline.md` links to `done/013-ctrl-c-does-not-exit-interactive-shell.md` — but both files already live *inside* `issues/done/`, so the correct link is the bare sibling filename `013-ctrl-c-does-not-exit-interactive-shell.md`.
  - `issues/done/025-interactive-first-line-attempt-before-continuation.md` has the same bug pointing at `done/020-ctrl-d-behavior-in-continuation.md` → should be `020-ctrl-d-behavior-in-continuation.md`.
  - `issues/done/146-cut-v1.0.0-release.md` links to `../v1.0-criteria.md` — correct when the file lived at `issues/146-...md` (one level under `dev-docs/`), but wrong now that it's one level deeper at `issues/done/146-...md`; needs `../../v1.0-criteria.md`.
- `mkdocs-dev.yml`'s `nav:` has `Design Specs: specs/` and `Implementation Plans: plans/` — bare directory references. No nav-generation plugin is installed (only `search` and `include-markdown`), so mkdocs can't expand a directory into a section, and both entries fail to resolve to any file.

Separately, mkdocs already emits an **INFO** (not WARNING) listing every `dev-docs/` file excluded from `nav:` — this is the issue's original "category 1" concern, but it doesn't actually cause `--strict` to fail and needs no change.

## Why not just suppress the warnings

mkdocs 1.6.1's `validation.links.not_found` setting (`mkdocs/structure/pages.py:467`, confirmed by reading the installed package source) is a single global switch with no per-directory or per-file scoping. Setting it to `ignore` would silence Bucket A, but it would silence Bucket B just as completely — including any *future* link that breaks because a doc moved. That defeats the issue's actual goal (a `--strict` build worth trusting), so Bucket A is fixed by rewriting content instead of relaxing validation.

## Plan

1. **Bucket A: rewrite outside-`docs_dir` links to absolute GitHub URLs.**
   Replace each relative link (e.g. `../bin/test/units.bash`, `src/plcc/cmd/source_runner.py#L56`) with `https://github.com/ourPLCC/plcc-ng/blob/main/<path>[#L<n>]`, preserving any `#L<n>` line anchors. Files touched: `dev-docs/contributing.md`, `dev-docs/issue-conventions.md`, `dev-docs/release-sop.md`, `dev-docs/plans/*.md` (5 files), `dev-docs/specs/2026-04-13-phase-1-walking-skeleton.md`, `dev-docs/specs/2026-05-30-050-rename-grammar-file-to-grammar-design.md`, `dev-docs/issues/done/{013,014,018,020,021,141}*.md` (6 files).

2. **Bucket B: fix stale/malformed intra-doc links.**
   - In each affected `dev-docs/specs/*.md` and `dev-docs/v1.0-criteria.md`, change `issues/NNN-*.md` (or `../issues/NNN-*.md`, `../../issues/NNN-*.md` depending on nesting depth) to the equivalent path under `issues/done/`.
   - In `dev-docs/issues/done/018-ctrl-d-exit-missing-newline.md` and `dev-docs/issues/done/025-interactive-first-line-attempt-before-continuation.md`, change `done/013-...`/`done/020-...` to `013-...`/`020-...`.
   - In `dev-docs/issues/done/146-cut-v1.0.0-release.md`, change `../v1.0-criteria.md` to `../../v1.0-criteria.md`.

3. **Fix the two broken nav entries.**
   Add `dev-docs/specs/index.md` and `dev-docs/plans/index.md` — short landing stubs (one paragraph: what the directory is for, note that individual documents are browsable via GitHub/the site search). Change `mkdocs-dev.yml`'s nav to point at `specs/index.md` and `plans/index.md` instead of the bare directory strings.

4. **Harden `bin/issues/close.bash` against recurrence.**
   Two distinct adjustments needed, both surfaced by this cleanup:
   - After moving the issue file to `dev-docs/issues/done/`, grep `dev-docs/` for links *to* the old `issues/<old-name>` path (from other files) and rewrite them to `issues/done/<old-name>` — this is the 20-warning pattern from specs/v1.0-criteria.md.
   - Also rewrite any relative links *within* the moved file itself that climb upward past `dev-docs/issues/` (e.g. `../v1.0-criteria.md`, `../../src/...`) by prepending one more `../`, since the file is now one directory level deeper — this is the `146-cut-v1.0.0-release.md` bug pattern.
   Both will keep recurring every time an issue closes unless the close script closes the loop on both.

5. **Out of scope (follow-up issue):** wiring `mkdocs build --strict` into CI. Filed separately since a CI change carries its own review/testing risk independent of this content cleanup.

## Testing

- After steps 1–3: re-run `mkdocs build -f mkdocs-dev.yml --strict` and confirm it exits 0 with no warnings.
- After step 4: add a bats test (in `tests/bats/commands/` alongside existing `bin/issues/*.bash` coverage, or wherever `close.bash` is currently tested) that closes a fixture issue referenced from a fixture spec doc, and asserts the spec doc's link is rewritten to point at `issues/done/`.
- Run `bin/test/units.bash` after any script changes to confirm no regressions.

## Out of scope

- Wiring `mkdocs build --strict` into CI (separate follow-up issue).
- Any further nav restructuring beyond the two broken entries.
- Freezing outside-`docs_dir` links to a specific commit SHA rather than `main` — accepted trade-off; these become ordinary external links and will only be caught by *browsing*, not by `--strict`, if the referenced file is later renamed.
