# 046 - No sticky grammar: --grammar-file doesn't persist across commands

**Type:** feat
**Date:** 2026-05-28

## Description

When working with a non-default grammar file, specifying `--grammar-file=X` on one
command has no effect on subsequent commands. Each command independently defaults to
`grammar.plcc` if `--grammar-file` is omitted. There is no way to say "I am now
working on `a.plcc`" and have all subsequent `plcc-*` commands use `a.plcc`
automatically.

This leads to silent mismatch: a student specifies `--grammar-file=a.plcc` for a scan
or parse step, then runs `plcc-rep` without the flag, and the REPL silently builds and
runs `grammar.plcc` instead of `a.plcc` — with no indication that the wrong grammar
is in use.

## Steps to Reproduce

```
plcc-scan --grammar-file=a.plcc   # scans a.plcc
plcc-rep                           # silently builds and runs grammar.plcc, not a.plcc
```

The student expected `plcc-rep` to continue working with `a.plcc`. There is no error
or warning to signal the switch.

## Notes

**Proposed model — sticky grammar:**

Treat `build/` as tied to a specific grammar file. Store the last-used grammar path
in `build/` (e.g. `build/.grammar`). When any command runs without `--grammar-file`,
it reads that stored path instead of defaulting to `grammar.plcc`. When `--grammar-file`
is explicitly given and differs from the stored path, wipe `build/` entirely and
rebuild from scratch with the new grammar.

Expected behavior after the change:

```
plcc-scan --grammar-file=a.plcc   # stores a.plcc as active grammar, scans
plcc-rep                           # reads build/.grammar → a.plcc, builds and runs a.plcc
plcc-rep --grammar-file=b.plcc    # detects grammar change, wipes build/, rebuilds b.plcc
plcc-rep                           # reads build/.grammar → b.plcc
```

**Also consider:** renaming `--grammar-file` to `--grammar` (shorter, more natural).

**Supersedes:** issue 038, which described a symptom of the same root cause.
