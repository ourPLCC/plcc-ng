# Test Output Cache — Design

**Issue:** 097
**Date:** 2026-06-18

## Overview

Add transparent output caching to all test scripts. When a test script is run,
it checks whether a valid cached result exists. On a hit it replays the cached
output and exits with the cached exit code. On a miss it runs the real command,
tees output to the cache, and exits with the live exit code. Caching is
invisible to callers — existing invocation patterns are unchanged.

## Architecture

One new sourced helper: `bin/test/_cache.bash`. Each of the seven existing test
scripts sources it and wraps its main command in a `run_cached` call. No other
files change except those seven scripts and the addition of
`bin/test/cache/stats.bash`.

`_cache.bash` is not executable and not meant to be run directly. The leading
underscore signals that it is a sourced helper, consistent with the convention
used elsewhere in `bin/`.

## The `run_cached` function

**Signature:** `run_cached <cache-file> <command> [args...]`

**Behavior:**

1. If `PLCC_NO_TEST_CACHE=1` is set, log a skip event and exec the command directly
   with no tee and no cache interaction.
2. Compute a cache key from `git status --porcelain` and `git rev-parse HEAD`.
   Compare against the key stored in `<cache-file>.meta`.
3. **Cache hit:** replay `<cache-file>` to stdout, exit with the cached exit
   code. Since stdout and stderr are merged into the cache file, all output
   comes back on stdout — acceptable for agent grep use; minor cosmetic
   difference for interactive runs.
4. **Cache miss:** run the command, tee stdout+stderr to `<cache-file>`, write
   a new `<cache-file>.meta`, exit with the live exit code.

**Sidecar file (`<cache-file>.meta`):** stores the cache key and exit code so
the cache file itself stays pure output — easy to grep without noise. Format:

```text
KEY=<git-status-hash>
EXIT=<exit-code>
```

**Fallback:** if the git commands fail (run outside a repo), if writing cache
files fails, or if the sidecar is missing or corrupt, `run_cached` falls back
to running the command uncached. Failures are silent — no crash, no noise.

## Per-script cache files

| Script | Cache file |
| --- | --- |
| `units.bash` | `/tmp/plcc-test-units.log` |
| `commands.bash` | `/tmp/plcc-test-commands.log` |
| `integration.bash` | `/tmp/plcc-test-integration.log` |
| `e2e.bash` | `/tmp/plcc-test-e2e.log` |
| `functional.bash` | `/tmp/plcc-test-functional.log` |
| `packaging.bash` | `/tmp/plcc-test-packaging.log` |
| `all.bash` | `/tmp/plcc-test-all.log` |

Scripts that call multiple sub-scripts (e.g. `functional.bash`) cache their
combined output as a unit — that is what agents grep.

## Cache invalidation

The cache key is the concatenation of `git status --porcelain` (working tree
changes relative to HEAD) and `git rev-parse HEAD` (current commit). The cache
is stale if either changes — a new commit, a staged change, or a modification
to a tracked file all invalidate it. This is the simplest git-status strategy;
switching to a different model (e.g. file-mtime) is a one-function change in
`_cache.bash`.

## Escape hatch

Setting `PLCC_NO_TEST_CACHE=1` bypasses the cache for that run entirely. The command
runs live and the cache is neither read nor written. The skip is still logged
(see Observability).

CI sets `PLCC_NO_TEST_CACHE=1` unconditionally — `/tmp` is ephemeral per job
so caching would always miss anyway, and this keeps CI logs free of cache
noise.

## Observability

On every invocation `run_cached` does two things:

1. **Stderr line:** `[cache hit] units`, `[cache miss] units`, or
   `[cache skip] units`. Immediately visible during normal runs.
2. **Stats log entry:** appends a timestamped line to
   `/tmp/plcc-test-cache-stats.log`:

   ```text
   2026-06-18T10:23:45 hit units
   ```

`bin/test/cache/stats.bash` reads the stats log and prints:

- Total runs, hits, misses, skips, and overall hit rate
- Per-script breakdown of the same counts

The stats log persists across runs until `/tmp` is cleared (reboot).
`stats.bash` handles a missing log gracefully (prints "no stats yet").

## Files changed

| File | Change |
| --- | --- |
| `bin/test/_cache.bash` | New sourced helper |
| `bin/test/cache/stats.bash` | New summary script |
| `bin/test/cache/clear.bash` | Remove all cached output files |
| `bin/test/cache/clear-stats.bash` | Remove the stats log |
| `bin/test/units.bash` | Source helper, wrap command in `run_cached` |
| `bin/test/commands.bash` | Source helper, wrap command in `run_cached` |
| `bin/test/integration.bash` | Source helper, wrap command in `run_cached` |
| `bin/test/e2e.bash` | Source helper, wrap command in `run_cached` |
| `bin/test/functional.bash` | Source helper, wrap command in `run_cached` |
| `bin/test/packaging.bash` | Source helper, wrap command in `run_cached` |
| `bin/test/all.bash` | Source helper, wrap command in `run_cached` |
| `.github/workflows/ci.yml` | Set `PLCC_NO_TEST_CACHE=1` on all test steps |
