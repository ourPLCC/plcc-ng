# 189 - Adopt the languages-ng issue-system shape: issues never move, status is frontmatter

**Type:** chore
**Date:** 2026-08-11

<!--
Classify by user-facing impact, not by whether something was "broken".
`fix` and `feat` bump the release version (see [tool.semantic_release]
in pyproject.toml); reserve them for changes to the shipped package
(src/). A bug in a test, script, or CI workflow (bin/, tests/,
.github/) is still a bug, but it's not user-facing — classify it
`test` or `chore` instead so it doesn't spin the version. `docs` is for
documentation content, and never bumps the version either way.
-->

## Description

The `languages-ng` repo's issue system is a fork of this one, evolved
under use, and it has diverged in three deliberate ways. This proposes
adopting that shape here. The three are separable; only the first is
load-bearing.

### 1. Issues never move; `closed:` is the status

Today a close does `git mv` into [issues/done/](done/), so an issue's path
changes exactly once in its life — and every link written before that
moment goes stale. Issue
[#149](done/149-fix-stale-issues-done-links.md) was the one-time cleanup of
~23 such links; issue [#150](done/150-close-script-auto-fix-links.md) then
built link-rewriting into `close.bash` so the class would stop recurring.

**It did not stop recurring. There are 14 broken links in `issues/done/`
right now** (command in Steps to Reproduce). They come in two shapes, and
both are structural rather than bugs in the rewriting:

- **Links that go stale on a *later* close** (8 of the 14). When #179
  closed, `close.bash` correctly rewrote its bare sibling link
  `176-integration-tier-has-no-arbno-coverage.md` to
  `../176-integration-tier-has-no-arbno-coverage.md` — correct at that
  moment, because #176 was still open in `issues/`. Then #176 closed and
  moved. Closing #176 rewrites occurrences of the literal string
  `issues/176-…` across `dev-docs/`, but #179's link now reads `../176-…`,
  which does not contain `issues/`, so it is missed. Every close
  invalidates links written by earlier closes, and no rewriting rule keyed
  on the closing issue's own path can see them.

- **Depth rewrites applied to already-wrong paths** (6 of the 14). #150's
  blanket "add one more `../` to anything climbing out of `issues/`" cannot
  tell a correct relative path from an incorrect one. #157 was filed with
  `[issues/TEMPLATE.md](../TEMPLATE.md)` — already wrong by one level — and
  the close deepened it to `../../TEMPLATE.md`, still wrong. The five
  `../../src/plcc/cmd/source_runner.py` links in #013/#014/#018/#020/#021
  are the same shape from before #150 landed.

Under the languages-ng shape none of this exists. A link to an issue is
`issues/NNN-slug.md` from the day it is filed until forever, no file ever
changes depth, and `close.bash` touches no links at all — its
[close.bash](../../bin/issues/close.bash) counterpart is *shorter* than
ours despite doing strictly more validation, because roughly 40 lines of
link surgery are simply gone.

Closed state moves into the frontmatter instead:

```yaml
closed: 2026-08-11
```

Empty while open, a date once closed. Their `check.bash` guards the
regression directly:

```bash
if [[ -d "${ISSUES_DIR}/done" ]]; then
    fail "${ISSUES_DIR}/done exists; status is a 'closed:' date, not a directory"
fi
```

### 2. YAML frontmatter instead of `**Type:**` / `**Date:**`

```yaml
---
type: chore
target: this repo
opened: 2026-07-31
closed:
---
```

Two gains over our bold-label lines. First, **we currently record no close
date at all** — our `**Date:**` is the filing date, and when an issue
closed survives only in git history and in which directory the file landed
in. `opened` + `closed` puts the issue's whole lifespan in the file.
Second, it is machine-readable: their `check.bash` validates that the block
is well-formed, that all four keys are present, and that both dates parse.
Ours can validate none of that.

The block is deliberately **flat scalars, one key per line** — no nesting,
no lists, no multi-line values — precisely so `grep` and `awk` suffice and
no YAML dependency enters `bin/`:

```bash
grep -l '^closed: [0-9]' dev-docs/issues/[0-9]*.md   # closed
grep -L '^closed: [0-9]' dev-docs/issues/[0-9]*.md   # open
```

### 3. A `target:` field

Names the repository an issue is actually about, defaulting to `this repo`,
so a defect found here but belonging to another repo can be filed here
without pretending it is ours. This is the weakest of the three for us:
languages-ng needs it because it is downstream of this repo and
accumulates upstream findings, whereas we are usually the upstream. It is
not worthless — issues [#160](160-concurrent-plcc-build-dir-race.md)
and [#161](161-rename-plcc-rep-to-plcc-eval.md) were hand-migrated
from `ourPLCC/plcc-ng-demo`, and adjacent repos (`plcc-ng-demo`,
`plcc-ng-devcontainer`) could use the same treatment — but it is easily
dropped without affecting (1) or (2).

## Steps to Reproduce

The 14 currently-broken links, from the repository root:

```bash
for f in dev-docs/issues/done/*.md; do
  grep -o '](\.\.[^)]*)' "$f" | tr -d '()' | sed 's/^]//' | while read -r l; do
    [ -e "$(dirname "$f")/$l" ] || echo "$f -> $l"
  done
done
```

Every hit is inside `issues/done/`, and every one is a consequence of the
file having moved.

## Notes

**Migration sketch** — one branch, mechanical, but not small:

1. `git mv dev-docs/issues/done/*.md dev-docs/issues/` (177 files; 9 are
   already open, for 186 total). Note that IDs 035, 039, and 043 each name
   two different files from before `.next-id.txt` existed — the slugs
   differ so there is no filename collision, but anything keyed on ID alone
   should be checked.
2. Convert all 186 files' `**Type:**`/`**Date:**` headers to frontmatter,
   mapping `Date:` → `opened:`. Backfill `closed:` from each file's close
   commit date (`git log --diff-filter=R --follow`); spot-check rather than
   trust it, since some closes were amended or batched.
3. Un-rewrite the links #150 rewrote — the exact inverse of its rules:
   `../NNN-slug.md` → `NNN-slug.md` for sibling issues, and one fewer `../`
   on paths climbing out of `issues/`. Fix the 14 broken ones by hand while
   in there.
4. Port [check.bash](../../bin/issues/check.bash) from languages-ng (frontmatter
   validators, the `done/` guard, checkbox-vs-`closed` agreement) and delete
   `close.bash`'s link-rewriting block.
5. Trim `tests/bats/commands/issues-close.bats` — most of its 126 lines
   exercise link rewriting that will no longer exist — and add coverage for
   the `closed:` fill-in.
6. Update [issue-conventions.md](../issue-conventions.md) and
   [CLAUDE.md](../../CLAUDE.md).

**Honest cost.** One directory holding 186 files, 177 of them closed, is
worse to browse than 9-plus-an-archive. languages-ng has 38 issues total,
so it has not felt this yet. The mitigation is the `grep -L` one-liner
above (their conventions document it for exactly this reason) plus the fact
that the roadmap already lists precisely the open set. Worth deciding
deliberately, because it is the one real thing being traded away for the
link stability.

**Timing.** Now is unusually cheap: `roadmap.md` currently has no milestone
sections, and milestone links are the other place the move rule bites (ours
must be repointed at `done/` on close; theirs never change). Doing this
before the next milestone list is written avoids the conversion entirely.

Filed after hand-migrating issues
[#185](185-rep-parses-each-source-independently.md)–[#188](188-follow-set-omits-nullable-tail.md)
from languages-ng, which is what surfaced the divergence between the two
systems.
