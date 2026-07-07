# 151 - Migrate docs/superpowers/ into dev-docs/

**Issue:** [151](../issues/done/151-migrate-superpowers-docs-to-dev-docs.md)

## Goal

`docs/superpowers/specs/` (50 files) and `docs/superpowers/plans/` (51
files) hold the same kind of per-issue brainstorming design docs and
implementation plans that `dev-docs/specs/` and `dev-docs/plans/`
already hold — two parallel locations for the same artifact type.
Migrate both directories into `dev-docs/` via `git mv`, fix every link
the move touches, and remove the now-empty `docs/superpowers/`.

This was actually planned once before:
`dev-docs/plans/2026-06-07-065-documentation.md` lists this exact
`git mv` as a task, but it was never carried out for `specs/`/`plans/`
(only `docs/issues/` → `dev-docs/issues/` happened). New files kept
landing in `docs/superpowers/` by copy-pattern-matching ever since,
which is what grew it to 101 files.

No filename collisions exist between the source and destination
directories, so `git mv docs/superpowers/specs/*.md dev-docs/specs/`
and the equivalent for `plans/` apply cleanly.

## Link breakage discovered

A repo-wide investigation (grepping for `docs/superpowers` as both a
literal string and inside markdown link syntax) turned up three tiers
of link breakage tied to this move, beyond the simple `git mv`:

**Tier 1 — links that work today, break purely from the depth change.**
`docs/superpowers/{specs,plans}/` is 3 levels deep; `dev-docs/{specs,plans}/`
is 2. Every correctly-working `../../../dev-docs/...` style link in the
moving files needs rebasing. Two external files also link *into* a file
being moved and need fixing for the same reason:
`docs/superpowers/plans/2026-07-04-136-release-notes-unification.md:394`
and `dev-docs/issues/done/141-whats-new-user-release-notes.md:14`, both
linking to `2026-07-04-136-release-notes-unification-design.md`.

**Tier 2 — links already broken today for unrelated reasons.** Several
plans use `../commands/plcc-X.md`, `../guide/Y.md`, `../v1.0-criteria.md`,
or `../bin/release/Z.bash`, which resolve to nonexistent
`docs/superpowers/{commands,guide,bin}/` paths — these should be
`../../cli/commands/`, `../../cli/guide/`, `../../dev-docs/v1.0-criteria.md`,
and `../../bin/release/` (paths correct for the *old* location; see
remap rules below for the new one). A few plans already use the correct
`../../cli/commands/...` form, so this is a pre-existing inconsistency,
not something the move introduces.

**Tier 3 — stale issue-reference links.** ~30 issue-reference links in
these files point at `dev-docs/issues/NNN-*.md` for issues that have
since closed and moved to `dev-docs/issues/done/NNN-*.md` — often under
a different slug than the link guessed (e.g. a link says
`084-make-no-banner-the-default-print-banner-to-stderr-with-v.md` but
the real file is `084-no-banner-default.md`). This is the same bug
class fixed in #149, which explicitly excluded `docs/superpowers/`
because it was "frozen historical" at the time; that exclusion no
longer applies since this issue is moving the directory out from under
that label.

All three tiers will be fixed as part of this issue.

## Approach

A one-off Python script (used for this migration only, not committed
to `bin/`) does the rewrite in one pass, followed by an automated
verification pass — chosen over hand-editing ~100 files individually,
since the transform is fully formulaic and a script can check every
link it touches rather than relying on spot-checks.

**1. Build lookup tables:**
- Issue index: every file under `dev-docs/issues/` and
  `dev-docs/issues/done/`, keyed by leading issue number, mapped to its
  current path.
- Tier-2 remap table for the known-wrong prefixes:
  `docs/superpowers/commands/` → `docs/cli/commands/`,
  `docs/superpowers/guide/` → `docs/cli/guide/`,
  `docs/superpowers/v1.0-criteria.md` → `dev-docs/v1.0-criteria.md`,
  `docs/superpowers/bin/release/` → `bin/release/`.

**2. For every markdown link in each moving file** (plus the 2 known
external files), resolve it against the file's *current* location to a
root-relative target, then:
- If the target falls under `docs/superpowers/specs/` or
  `docs/superpowers/plans/`, rewrite the prefix to `dev-docs/specs/` or
  `dev-docs/plans/`.
- If the target matches `dev-docs/issues/...`, look it up by number in
  the issue index and replace with the canonical current path (handles
  both the open→done drift and slug renames).
- Apply the Tier-2 table for the other known-wrong prefixes.
- Recompute the relative path from the file's *new* location (one
  level shallower than before) and rewrite the link in place.

Links that match none of the above (plain HTTP links, in-page anchors,
same-directory sibling links) are left untouched.

**3. Move the directories:**
```bash
git mv docs/superpowers/specs/*.md dev-docs/specs/
git mv docs/superpowers/plans/*.md dev-docs/plans/
rmdir docs/superpowers/specs docs/superpowers/plans docs/superpowers
```

## Verification

- Every relative markdown link inside `dev-docs/specs/*.md` and
  `dev-docs/plans/*.md` that was broken by this move (one of the three
  tiers above) resolves to a file that exists on disk — the
  authoritative check that all three tiers were actually fixed, not
  just mechanically transformed. Pre-existing broken links unrelated
  to `docs/superpowers` (e.g. references to doc pages that were never
  written) predate this move and are out of scope; a plain `--verify`
  pass will still report them.
- `grep -rn '](.*docs/superpowers' . --include='*.md'` (excluding
  `.git`) turns up no *live* markdown link into the removed directory
  — every hit it does return is either the greedy pattern spanning
  past a real link into unrelated trailing prose, or this issue's own
  plan/design docs quoting the old path as illustration. Neither is a
  dead link. A plain string grep for `docs/superpowers` is not the
  acceptance test: it also matches legitimate historical prose
  (elsewhere in this document included) describing the directory as a
  past fact, which correctly stays unchanged.
- `bin/issues/check.bash` still passes.
- `bin/test/units.bash` stays green (docs-only change; confirms no
  unrelated regression).

## Out of scope

If the issue-index lookup can't resolve some link (a typo'd issue
number that never existed, not a close-rename), it's left untouched
and called out in the commit rather than guessed at. A plain-string
repo-wide grep for `docs/superpowers` does surface hits outside the
files this plan directly touches — CHANGELOG.md, and prior plans/specs
that describe the directory as history (`moved from docs/superpowers/`,
"frozen historical records", and similar) — all confirmed to be
accurate historical prose, not stray dead links, so no follow-up issue
is expected. This finishes cleanup that #149/#150 already established,
scoped to exactly the files this move touches.
