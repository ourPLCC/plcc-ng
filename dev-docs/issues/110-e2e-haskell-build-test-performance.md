# 110 - e2e test 15: Haskell build roundtrip is too slow

**Type:** perf
**Date:** 2026-06-24

## Description

E2e test 15 (`tests/bats/e2e/haskell.bats` — "haskell pipeline: emit-build-run roundtrip") takes approximately 4–5 minutes to complete. It calls `plcc-haskell-build`, which runs `cabal build` and compiles the generated Haskell code from scratch. This makes the e2e suite impractical to run locally and slows CI.

## Notes

- The slow step is `plcc-haskell-build` / `cabal build`. Haskell compilation is inherently expensive, especially without a warm build cache.
- Two directions to explore:
  1. **Speed it up** — cache the cabal store across test runs (e.g., persist `~/.cabal` or the `dist-newstyle` directory in CI and locally). A warm cache could cut the compile step to seconds.
  2. **Test differently** — split the test. Keep a fast unit/integration test that verifies the emitted `.hs` files are syntactically correct (e.g., `ghc -fno-code`) without doing a full `cabal build`, and promote the full roundtrip to a separate, explicitly slow suite that only runs in CI on a schedule or on demand.
- Either way, the fast e2e suite should not include a multi-minute compile step.
