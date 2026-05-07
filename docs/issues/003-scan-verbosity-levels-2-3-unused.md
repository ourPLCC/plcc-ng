# 003 - Verbosity levels 2 and 3 produce no more output than level 1

**Type:** feat
**Date:** 2026-05-07

## Description

`plcc-scan` accepts a `--verbose` / `-v` flag, but verbosity levels 2 and 3
produce output identical to level 1. The levels are wired up but not
meaningfully differentiated.

What useful information could levels 2 and 3 expose is an open design question.
Candidates include (but are not limited to):

- Which regex patterns were attempted and in what order before a match or error.
- The raw matched text alongside the token name and position.
- Timing or performance counters per file or per token.
- The full token struct (all fields) rather than the summary line.

## Notes

Verbosity controls what is printed, not how it is printed. File information
(issue [002](002-scan-tokens-missing-file-info.md)) is part of the default
output at level 0 and is unaffected by verbosity.
