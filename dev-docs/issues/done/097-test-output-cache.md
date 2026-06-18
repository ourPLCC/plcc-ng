# 097 - Cache test output to a temp file for agent grep

**Type:** chore
**Date:** 2026-06-17

## Description

Agents working on test failures often call a test script multiple times to grep
different slices of output (failures, specific test names, counts). Each call
re-runs the full suite, wasting time when the output has not changed.

## Desired Behavior

Add `bin/test/run.bash` — a thin wrapper around the existing test scripts that
tees all output (stdout + stderr) to a predictable temp file:

```text
/tmp/plcc-test-output.log
```

Agents can then grep the cached file instead of re-running. The cache is
implicitly invalidated whenever the suite is intentionally re-run via
`bin/test/run.bash`.

## Notes

- The wrapper should pass through all arguments to the underlying script so
  existing invocation patterns still work.
- The cache path should be fixed and predictable so agents can depend on it
  without needing to discover it.
- No explicit cache invalidation is needed — re-running the wrapper overwrites
  the file.

See also: [[096-test-setup-deduplication]]
