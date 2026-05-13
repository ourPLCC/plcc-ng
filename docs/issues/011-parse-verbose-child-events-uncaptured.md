# 011 - plcc-parse verbose child events from ParseHandler subprocesses are uncaptured

**Type:** bug
**Date:** 2026-05-13

## Description

`plcc-parse` uses `child_flags_for_orchestrator()` when building the `plcc-tokens` and `plcc-tree`
subprocesses inside `ParseHandler.feed()`. When the user passes `-v`, those child processes emit
JSON verbose events to stderr. However, `ParseHandler` spawns the child processes with
`stderr=None` (inherited from the parent), so the raw JSON lines go directly to the terminal
without being reformatted through `VerboseContext.reformat_child_events()`.

The result is that `-v` output from `plcc-parse` mixes reformatted `plcc-make` events with raw
JSON event lines from `plcc-tokens` and `plcc-tree`, producing garbled output.

## Steps to Reproduce

```bash
echo "1" | plcc-parse -v
```

Observe raw `{"event":...}` JSON lines interspersed with formatted verbose output.

## Notes

The fix requires `ParseHandler` to capture `stderr=subprocess.PIPE` on both child processes,
collect the stderr bytes, and forward them through `verbose.reformat_child_events()` after
`tree_proc.communicate()` completes.

`ParseHandler` currently has no reference to a `VerboseContext`, so the fix also requires
threading the verbose context through to the handler (or having `main()` post-process the
child stderr).

The same issue likely affects `RepHandler` in `plcc-rep`.
