# Harden `close.bash` to auto-fix links — design

Issue: [dev-docs/issues/150-close-script-auto-fix-links.md](../../../dev-docs/issues/150-close-script-auto-fix-links.md)
Date: 2026-07-06

## Problem

`bin/issues/close.bash` moves an issue file to `issues/done/` but doesn't touch any
links, so every future close recreates the bug class fixed in #149: other `dev-docs/`
files keep linking to the issue's old `issues/<name>` path, and any link inside the
moved file itself that climbs above `dev-docs/issues/` (e.g. to
`dev-docs/v1.0-criteria.md` or `src/...`) ends up one level short once the file is a
directory deeper. Issue #149 was the one-time cleanup of existing instances; this issue
is the preventive fix so it stops recurring on every future close.

## Decision summary

Two new passes in `close.bash`, inserted after the existing roadmap passes (milestone
checkbox rewrite, Open Issues entry removal — both unchanged) and before the final
`bin/issues/check.bash` call. Goal: after `close.bash` runs, every link broken by the
move is fixed, not just the roadmap's own.

### Pass 3 — external inbound links

Recursively grep `dev-docs/**/*.md` (excluding the file's own new location at
`issues/done/${basename}`, which Pass 4 owns) for the literal substring
`issues/${basename}`. For every match: `sed -i "s|issues/${basename}|issues/done/${basename}|g"`,
then `git add` the file. `roadmap.md` is included in this scan — it acts as a
catch-all safety net, not a special case; by the time Pass 3 runs, the existing roadmap
passes should already have removed or rewritten every reference, so no true match is
expected there in practice, but nothing excludes it.

This substitution is depth-agnostic: inserting `done/` between `issues/` and the
filename doesn't change how many `../` a referencing file needs, since `done/` is a
subdirectory of `issues/`, not a sibling. The grep is guarded with `|| true` so "no
matches" doesn't trip `set -e`.

### Pass 4 — internal outbound links

Applied only to the moved file (now at `issues/done/${basename}`). Three rules, keyed
off what immediately follows `](`, mutually exclusive by their leading characters:

1. **`](done/...)` → strip the `done/`.** The linked issue was already closed before
   this one, so it's now a true sibling in the same `issues/done/` directory.
2. **`](../...)` → prepend one more `../`.** The file is one directory deeper than
   before, so anything already climbing out of `issues/` (to another `dev-docs/` file,
   or further up to `src/`, etc.) needs an extra level.
3. **`](NNN-slug.md)` (bare, digit-led, no prefix) → prepend `../`.** Covers a link to a
   still-open sibling, which remains in `issues/` — one level up from the file's new
   location. Regex anchored on `[0-9]{3}-[^)]+\.md` right after `(` so it can't misfire
   on external URLs or anchors elsewhere in the body.

Each rule is one `sed -E` substitution; order among the three doesn't matter since the
patterns are disjoint by their first character after `(` (`d`, `.`, or a digit).

## Testing

Extend `tests/bats/commands/issues-close.bats`, which already has fixture conventions
for exercising `close.bash` against a throwaway git repo (issue files, `.next-id.txt`,
`roadmap.md`). New fixture additions and one `@test` per behavior:

- A second `dev-docs/` file (e.g. under a `specs/` subdirectory in the fixture) that
  links to the issue being closed via `issues/<name>` — asserts Pass 3 rewrites it to
  `issues/done/<name>`, and that an unrelated issue's link in the same file is
  untouched.
- An already-closed sibling issue file, linked from the body of the issue being closed
  via `[N](done/N-slug.md)` — asserts Pass 4 rule 1 strips the `done/` prefix in the
  moved file.
- A link in the closing issue's body that climbs above `issues/` (e.g.
  `[x](../some-other-doc.md)`) — asserts Pass 4 rule 2 prepends an extra `../`.
- A bare link in the closing issue's body to a still-open sibling (e.g.
  `[N](N-slug.md)`) — asserts Pass 4 rule 3 prepends `../`.

TDD order per CONTRIBUTING: extend the bats tests first, watch the new cases fail via
`bin/test/commands.bash tests/bats/commands/issues-close.bats`, then implement the two
passes in `close.bash`.

## Bookkeeping

Commits on this branch, in order:

1. `docs(specs)` — this design doc.
2. `test(issues)` — extend `issues-close.bats` with the new fixtures and cases
   (failing).
3. `feat(issues)` — Pass 3 and Pass 4 in `close.bash`.
4. `bin/issues/close.bash 150`; verify with `bin/issues/check.bash`.

The roadmap update on close is handled by `close.bash` itself. After the final commit
the branch is pushed; the user opens the PR.
