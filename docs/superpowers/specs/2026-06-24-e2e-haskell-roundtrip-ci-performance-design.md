# Design: E2E Haskell Roundtrip CI Performance (Issue 110)

**Date:** 2026-06-24
**Issue:** [110 - e2e test 15: Haskell build roundtrip is too slow](../../../dev-docs/issues/110-e2e-haskell-build-test-performance.md)

## Problem

The Haskell emit-build-run roundtrip e2e test takes 4–5 minutes because `plcc-haskell-build` runs a cold `cabal build`. This makes the full e2e suite impractical to run locally and dominates CI wall time.

## Solution Overview

Three complementary changes:

1. **Split the Haskell bats file** — separate the slow roundtrip test from the fast emit test so each can be run independently.
2. **Parallelize CI jobs** — run all test tiers as independent parallel jobs, so the Haskell roundtrip's wall time is masked by other jobs running concurrently.
3. **Cache aggressively** — cache `.venv/`, the cabal store, and `dist-newstyle/` to minimize cold-build overhead.

## Bats Test Split

`tests/bats/e2e/haskell.bats` splits into two files:

**`tests/bats/e2e/haskell.bats`** (fast) — retains the "spec to model to emit produces expected files" test. `setup()` drops `cabal update` since cabal is not needed. Teardown unchanged.

**`tests/bats/e2e/haskell_roundtrip.bats`** (slow) — contains the "emit-build-run roundtrip" test. `setup()` retains `cabal update`. The output directory is configurable via `HASKELL_ROUNDTRIP_OUT_DIR` to support caching a fixed path in CI:

```bash
# In setup()
OUT_DIR="${HASKELL_ROUNDTRIP_OUT_DIR:-$(mktemp -d)}"

# In teardown()
rm -rf "$SPEC_DIR"
# Only remove OUT_DIR if it was a temp dir (not a cached CI path)
if [[ -z "${HASKELL_ROUNDTRIP_OUT_DIR:-}" ]]; then
    rm -rf "$OUT_DIR"
fi
```

When `HASKELL_ROUNDTRIP_OUT_DIR` is unset (local runs), behavior is unchanged — a temp dir is created and cleaned up. When set (CI), the fixed path persists so `dist-newstyle/` survives between runs.

## Local Scripts

| Script | Change |
|---|---|
| `bin/test/e2e.bash` | Add `! -name "haskell_roundtrip.bats"` exclusion alongside the existing `languages-java.bats` exclusion |
| `bin/test/e2e_haskell_roundtrip.bash` | **New.** Same structure as other tier scripts. Runs `tests/bats/e2e/haskell_roundtrip.bats` only. |
| `bin/test/functional.bash` | Unchanged. Already calls `e2e.bash`, which is now fast. |
| `bin/test/all.bash` | Add `e2e_haskell_roundtrip.bash` between `functional.bash` and `packaging.bash`. |

`bin/test/all.bash` sequential order: `functional.bash` → `e2e_haskell_roundtrip.bash` → `packaging.bash`.

Note: `languages-java.bats` is left as-is. It will migrate to the future `languages-ng` repo.

## CI Restructure

Replace the current sequential `unit-and-integration` job (which gates `languages-corpus` and `packaging`) with six fully independent parallel jobs. All are required checks; none has a `needs:` dependency.

| Job name | Script | Extra setup beyond Python |
|---|---|---|
| `units` | `bin/test/units.bash` | — |
| `commands` | `bin/test/commands.bash` | — |
| `integration` | `bin/test/integration.bash` | — |
| `e2e` | `bin/test/e2e.bash` | Java + languages repo clone (existing behavior) |
| `e2e-haskell-roundtrip` | `bin/test/e2e_haskell_roundtrip.bash` | cabal store cache + `dist-newstyle/` cache + `HASKELL_ROUNDTRIP_OUT_DIR` env var |
| `package` | `bin/test/packaging.bash` | `fetch-depth: 0` (existing requirement) |

Expected CI wall time: `max(units, commands, integration, e2e, e2e-haskell-roundtrip, package)`. On a warm cache, the Haskell roundtrip drops from 4–5 minutes to near-instant, so wall time is dominated by whichever other job is slowest (likely 1–3 minutes).

## Caches

All six jobs get the `.venv/` cache. The `e2e-haskell-roundtrip` job also gets the cabal store and `dist-newstyle/` caches.

### `.venv/` — all jobs

```yaml
- uses: actions/cache@v4
  with:
    path: .venv
    key: ${{ runner.os }}-venv-${{ hashFiles('pdm.lock') }}
```

### Cabal store — `e2e-haskell-roundtrip` only

Moved from the old `languages-corpus` job. Key unchanged:

```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.cabal/packages
      ~/.cabal/store
    key: ${{ runner.os }}-cabal-${{ hashFiles('src/plcc/lang/ext/haskell/emit.py') }}
    restore-keys: ${{ runner.os }}-cabal-
```

### `dist-newstyle/` — `e2e-haskell-roundtrip` only

New. Keyed on emit code, runtime files, and the roundtrip bats file (which embeds the test spec inline):

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/plcc-haskell-roundtrip
    key: ${{ runner.os }}-dist-newstyle-${{ hashFiles('src/plcc/lang/ext/haskell/emit.py', 'src/plcc/lang/ext/haskell/runtime/**', 'tests/bats/e2e/haskell_roundtrip.bats') }}
```

The job sets `HASKELL_ROUNDTRIP_OUT_DIR: ~/.cache/plcc-haskell-roundtrip` so the bats test uses this fixed path as `OUT_DIR`.

## Files Changed

- `tests/bats/e2e/haskell.bats` — remove `cabal update` from setup, remove roundtrip test
- `tests/bats/e2e/haskell_roundtrip.bats` — new file with roundtrip test and fixed-path support
- `bin/test/e2e.bash` — exclude `haskell_roundtrip.bats`
- `bin/test/e2e_haskell_roundtrip.bash` — new script
- `bin/test/all.bash` — add `e2e_haskell_roundtrip.bash`
- `.github/workflows/ci.yml` — replace two-job structure with six parallel jobs + new caches
