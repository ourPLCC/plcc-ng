# 096 - Hoist test setup out of leaf scripts to avoid redundant installs

**Type:** chore
**Date:** 2026-06-17

## Description

`bin/test/functional.bash` calls several leaf scripts (`commands`, `integration`,
`e2e`, `units`). Each leaf script independently calls `pdm install` and
`bin/install/bats.bash`. Both are idempotent but not free — they run 3–4 times
on every full test suite invocation, adding unnecessary overhead.

## Desired Behavior

- Hoist `pdm install` and `bin/install/bats.bash` into `functional.bash` so
  they run exactly once per suite invocation.
- Guard the calls in the leaf scripts with a `SKIP_SETUP=1` env flag so
  existing callers of the leaf scripts directly still work without breaking.

## Notes

The `SKIP_SETUP=1` guard is the safer approach — it does not break existing
callers of the leaf scripts while letting `functional.bash` skip the redundant
setup. `functional.bash` sets `SKIP_SETUP=1` before invoking each leaf script.

See also: [[097-test-output-cache]]
