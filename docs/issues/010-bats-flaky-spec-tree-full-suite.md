# 010 - Intermittent bats failures for plcc-spec and plcc-tree in full commands suite

**Type:** test
**Date:** 2026-05-13

## Description

When running the full `bin/test/commands.bash` suite (167 tests), two tests occasionally fail:

- `plcc-spec trivial grammar outputs valid JSON` (plcc-spec.bats line 32)
- `plcc-tree passes error records through` (plcc-tree.bats line 43)

Both pass reliably when run in isolation:

```bash
bats tests/bats/commands/plcc-spec.bats tests/bats/commands/plcc-tree.bats
```

The `plcc-tree` failure is downstream: its `setup()` calls `plcc-spec` to build a `SPEC_JSON`, then pipes that into `plcc-ll1` to build `LL1_JSON`. If `plcc-spec` fails (or produces no output) during setup, `LL1_JSON` is invalid and the `plcc-tree` test that depends on it fails too.

## Steps to Reproduce

1. `cd .worktrees/source-runner` (or any worktree)
2. `bin/test/commands.bash`
3. Observe intermittent failures at test ~146 (`plcc-spec`) and ~166 (`plcc-tree`)
4. Re-run `bats tests/bats/commands/plcc-spec.bats tests/bats/commands/plcc-tree.bats` — both pass

## Notes

Likely cause: resource contention or temp-file exhaustion when 167 bats tests run in parallel or rapid succession. bats may be recycling temp-file names, or `mktemp` is hitting a limit. The `plcc-spec` test failure message is only `[ "$status" -eq 0 ]' failed` with no stderr capture, so the root cause is not yet confirmed.

Potential fixes:
- Add `--separate-stderr` to the `run plcc-spec` call and log stderr on failure for better diagnostics
- Check if bats parallelism settings are involved
- Verify `mktemp` behavior when many temp files are created in the same test run
