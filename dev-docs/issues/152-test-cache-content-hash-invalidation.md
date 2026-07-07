# 152 - test-cache-content-hash-invalidation

**Type:** fix
**Date:** 2026-07-07

## Description

`bin/test/_cache.bash`'s `_cache_key()` hashes `git rev-parse HEAD` plus
`git status --porcelain` — i.e. *which* paths are dirty, not their
*content*. Editing a file that is already dirty from a prior edit does not
change the dirty-file list, so the cache key stays the same and a stale,
pre-edit result gets replayed as if it were fresh.

Fix: fold content into the key, e.g. `git diff HEAD` (covers tracked
changes, staged and unstaged) plus the contents of untracked files (via
`git ls-files --others --exclude-standard`), hashed alongside the existing
`HEAD` + `status --porcelain`. Genuinely-unchanged state still hits the
cache; any content change — even to an already-dirty file — always misses.

## Steps to Reproduce

1. Run any `bin/test/*.bash` script once (cache miss, writes cache + meta).
2. Edit a file that was *already* dirty before that run (don't change
   which files are dirty, just their content) — e.g. fix a bug in a file
   you'd already started editing.
3. Run the same test script again without `PLCC_NO_TEST_CACHE=1`.
4. Observe `[cache hit]` and the *pre-edit* output/exit code, even though
   the file on disk now differs.

## Notes

- Hit this twice in one session while working issue #150: once directly,
  once inside `bin/test/functional.bash`'s internal `commands` sub-run.
  Both times the cached result showed a failing test that the on-disk code
  had already fixed; bypassing with `PLCC_NO_TEST_CACHE=1` confirmed the
  fix was real and the cache was stale.
- Also worth noting (separate, lower-priority issue — not this one):
  `bin/test/commands.bash <path-to-one-bats-file>` doesn't actually filter
  to that file, it runs the entire `commands` tier regardless of the
  argument. That's *why* cache misses are expensive and worth avoiding,
  but it's an independent gap from the staleness bug this issue is about.
- TDD: extend the existing cache-behavior bats tests (the ones covering
  `cache miss`/`cache hit`/`stale cache: reruns command when git state
  changes`, currently in `tests/bats/commands/`) with a case for "content
  changes on an already-dirty file invalidate the cache."
