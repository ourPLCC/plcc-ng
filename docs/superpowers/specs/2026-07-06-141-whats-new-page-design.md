# What's New page (issue 141) — design

**Date:** 2026-07-06
**Issue:** [141 - whats-new-user-release-notes](../../../dev-docs/issues/141-whats-new-user-release-notes.md)

## Problem

The user docs have no user-facing release narrative. `docs/changelog.md`
republishes the developer-grade CHANGELOG.md, which tells users nothing
about what changed *for them* or why it matters. The issue-136 design
(Part 2) agreed the shape of the fix: a hand-curated `docs/whats-new.md`,
with the changelog page moving to the dev-docs site. This spec designs the
page and its first entry.

## Decisions

Explored during brainstorming (2026-07-06):

1. **This issue lands before the v1.0 release, not after.** The first
   entry greets users at the v1.0 announcement, so the page (and the
   changelog move) must be in place when v1.0 is cut. The only
   release-dependent detail — the entry's date — is deferred to issue
   112's release checklist.
2. **First entry speaks to PLCC veterans first.** Highlights are framed
   as "what's different/better than PLCC," matching the issue-136 spec's
   "especially relative to PLCC." Newcomers still benefit, but
   comparisons anchor the story.
3. **Themed prose sections, not a bullet list.** Each highlight is a
   `###` section of 2–4 sentences ending in links into the user docs.
   A flat bullet list was rejected as changelog-shaped — the thing this
   page exists to not be.
4. **Grammar-analysis tooling (`plcc-ll1`, `plcc-parser-table`) is not a
   first-entry highlight.** Extensibility, the docs site itself, and an
   honest breaking-changes/gaps section are in.
5. **Installation is framed as "native install simplified"** (one
   `pip install` vs PLCC's shell-script setup). It is *not* framed as
   replacing Docker/DevContainers — container options will still be
   offered.
6. **The CLI highlight leads with the three daily drivers**
   (`plcc-scan`, `plcc-parse`, `plcc-rep`; no separate compile step),
   with the composable lower-level commands (per-language
   `emit`/`build`/`run`) as the "workbench underneath."
7. **The closing section leads with breaking changes** (spec syntax is
   not backwards compatible; the migration guide walks through every
   change), with the "features not yet in PLCC-ng" pointer as a closing
   sentence, not the headline.

## Page skeleton — `docs/whats-new.md`

A short standing preamble, the pickup marker, then entries newest-first:

```markdown
# What's New

Curated highlights of what's changed in PLCC-ng and why it matters
to you. For the full commit-level history, see
[GitHub Releases](https://github.com/ourPLCC/plcc-ng/releases).

<!-- last-covered: v1.0.0 -->

## 2026-07-XX — PLCC-ng v1.0.0
...
```

- The marker records where the next drafting session picks up
  (per the issue-136 Part 2 process).
- The marker says `v1.0.0` from day one: the entry is written *as* the
  v1.0 entry. Any 0.x releases landing between merge and the 1.0 cut are
  covered by the tour anyway.
- `2026-07-XX` is a deliberate placeholder. Issue 112's notes gain a
  release-checklist line: "set the What's New entry date and confirm the
  version stamp."

## First entry content

An intro paragraph, then seven themed sections, ordered biggest wins
first, caveat last. Every claim must have a user-docs page to link to.

1. **Intro paragraph** — PLCC-ng reaches 1.0; a tour of what's new
   relative to [PLCC](https://github.com/ourPLCC/plcc); migrating a
   course? start with the migration guide.
2. **Four target languages** — PLCC generated Java only; PLCC-ng
   generates scanners, parsers, and interpreters in Python, Java,
   Haskell, and JavaScript. → Language Guide.
3. **Simpler native installation** — a single `pip install plcc-ng`
   replaces PLCC's shell-script installation. → Installation.
4. **Three commands, and a workbench underneath** — day-to-day use is
   `plcc-scan`, `plcc-parse`, and `plcc-rep`: tokenize, see the parse
   tree, or run the language interactively, with no separate compile
   step. Underneath, composable lower-level commands (per-language
   `emit`/`build`/`run`) expose each pipeline stage. → author-facing
   commands + under-the-hood guides.
5. **Diagrams from your spec** — class diagrams generated from the
   grammar via `plcc-diagram`. → author-facing commands (visualization)
   / diagram-extensions guide.
6. **Built to extend** — language, parser, and diagram extension
   points. → the three extension guides.
7. **A real documentation site** — language guide, CLI reference for
   every command, instructor guide. → docs index / instructor guide.
8. **Spec syntax has changed — not backwards compatible** — PLCC spec
   files need updating (regex flavor, nonterminal casing, captured-field
   syntax, and more); the migration guide walks through every change.
   Closing sentence points at the migration guide's "Features not yet in
   PLCC-ng" section so veterans know the gaps before switching.

Drafting process per issue-136 Part 2: AI drafts, the human review before
merge is the quality gate; user-facing claims must be verified against
the docs pages they link to.

## Nav changes and the changelog move

- **`mkdocs.yml`:** add `What's New: whats-new.md` directly after
  `Home`; remove the `Changelog: changelog.md` nav entry. Delete
  `docs/changelog.md`.
- **`mkdocs-dev.yml`:** add a `Changelog` nav entry (after `Home`,
  before `Contributing`) backed by a new `dev-docs/changelog.md` that
  includes `../CHANGELOG.md` — using the dev config's `{! ... !}`
  include-markdown tags, not the user site's `{% %}` tags.

## Out of scope

- Cutting the v1.0 release (issue 112).
- Automation of entry drafting (towncrier-style tooling was rejected in
  issue 136; the cadence and process are conventions, not code).
- Changes to CHANGELOG.md generation or GitHub Release notes (issue 136
  Part 1, already landed).

## Verification

- `pdm run mkdocs build` (user site) and
  `pdm run mkdocs build --config-file mkdocs-dev.yml` (dev site) both
  succeed with no new warnings — matching the builds CI runs
  (`docs.yml` deploys the user site via mike and builds the dev site
  with the same command).
- The removed changelog page no longer appears in the user site nav;
  the dev site renders the changelog content.
- `bin/issues/check.bash` passes after the close commit.

## Implementation shape

1. `docs/whats-new.md` with preamble, marker, and drafted first entry.
2. `mkdocs.yml` nav: add What's New, remove Changelog; delete
   `docs/changelog.md`.
3. `dev-docs/changelog.md` + `mkdocs-dev.yml` nav entry.
4. Release-checklist line added to issue 112's notes.
5. Human review of the entry text (the quality gate).
6. Close issue 141 via `bin/issues/close.bash` as the final commit.
