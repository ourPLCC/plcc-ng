# plcc-scan Issues Design

**Date:** 2026-05-06
**Issues:** 003, 004, 002, 001 (implementation order)
**Scope:** `plcc-scan`, `plcc-parse`, `plcc-tokens`

## Overview

Four tracked issues improve `plcc-scan`'s usability as an interactive teaching tool. Each ships as a separate PR in the order below. `plcc-rep` is explicitly deferred from issues 004 and noted where relevant.

---

## Issue 003 — Brief usage message mentions `--help`

**Type:** fix  
**Files:** `src/plcc/cmd/scan.py`, `src/plcc/cmd/parse.py`, `src/plcc/cmd/rep.py`

Docopt prints only the `Usage:` section when invoked with wrong arguments. Users have no indication that `--help` provides more detail.

**Fix:** Append `Run '<command> --help' for more information.` to the docstring of all three Level 2 commands, above the `VERBOSE_OPTIONS` interpolation. All three commands get the same treatment for interface consistency.

**Tests:** One test per command (bats or unit) asserting the brief usage output contains the hint string.

---

## Issue 004 — Accept `-` as stdin

**Type:** feat  
**Files:** `src/plcc/cmd/scan.py`, `src/plcc/cmd/parse.py`  
**Deferred:** `plcc-rep` (its stdin handling is more complex due to tty-detection and interactive mode; deferred to a future issue)  
**Out of scope:** `--` end-of-options marker (deferred indefinitely)

The Unix convention of `-` as a filename meaning stdin is not currently supported.

**Fix:** Replace the input-reading loop in both commands with:

```python
for src in sources:
    if src == '-':
        input_data += sys.stdin.buffer.read()
    else:
        with open(src, "rb") as sf:
            input_data += sf.read()
if not sources:
    input_data = sys.stdin.buffer.read()
```

This allows `-` anywhere in the SOURCE list, interleaved with real files. Multiple `-` occurrences each read whatever remains in stdin (second gets EOF on a non-tty).

**Tests:** Bats tests for each command:

- `echo 'input' | cmd grammar -` produces same output as `echo 'input' | cmd grammar`
- `cmd grammar file1.txt - file2.txt` correctly processes file1, then stdin chunk, then file2

---

## Issue 002 — Continue scanning after unrecognized character

**Type:** fix  
**Files:** `src/plcc/tokens/tokens_cli.py`, `src/plcc/cmd/scan.py`

`plcc-tokens` currently exits on the first `LexError`. This prevents `plcc-scan` from showing tokens before or after a bad character — unhelpful for students diagnosing input.

The scanner layer (`src/plcc/scan/scanner.py`) already advances past bad characters and continues; only the CLI layer stops.

**Fix — `plcc-tokens`:** Add `--continue-on-error` flag. When passed:

- On `LexError`: emit the error, set `had_error = True`, continue scanning
- Exit 1 at the end if any errors occurred; exit 0 otherwise
- Default behavior (exit immediately on first error) is unchanged

`plcc-parse` and `plcc-rep` do not pass this flag — their behavior is unchanged, avoiding cascaded parse errors from a broken token stream.

**Fix — `plcc-scan`:** Pass `--continue-on-error` to `plcc-tokens`. Process stdout from `plcc-tokens` regardless of exit code (currently only processed on exit 0, so tokens emitted before an error are silently discarded).

**Exit code at the orchestrator level:** `plcc-scan` exits 0 even when lex errors occur. A lex error is a result (the student is learning how their lexer behaves), not a failure. Only genuine failures (e.g., file not found) produce a non-zero exit. This matches the existing bats test `plcc-scan exits 0 on lex error in source`.

**Tests — `tokens_cli_test.py`:**

- Valid input → all tokens printed, exit 0
- `--continue-on-error` + bad char mid-input → error emitted, remaining tokens printed, exit 1
- `--continue-on-error` + bad char only → error emitted, exit 1
- Bad char without flag → exits immediately on first error (existing behavior preserved)

**Tests — bats:** `plcc-scan` with input containing a bad char mid-stream prints tokens before and after the error.

---

## Issue 001 — Print tokens after each line (incremental output)

**Type:** feat  
**Files:** `src/plcc/cmd/scan.py`

`plcc-scan` uses `subprocess.run()` with `input=input_data`, buffering all input and waiting for `plcc-tokens` to finish before printing anything. Interactive use (no SOURCE args) is unusable as a result.

**Fix:** Switch to `subprocess.Popen()` and stream I/O:

- **Input:** SOURCE files are written to the subprocess stdin pipe in order (no need to buffer all files before starting the process). For interactive stdin (no SOURCE args, stdin is a tty), read one line at a time, write it to the subprocess, and read any resulting tokens before reading the next line.
- **Output:** Read `plcc-tokens` stdout with `readline()`, printing each token record as it arrives. `plcc-tokens` already flushes after each token, so output appears as soon as each line is scanned.
- Close `plcc-tokens` stdin when input is exhausted, then drain remaining output.
- The `--continue-on-error` flag (from issue 002) continues to be passed, ensuring errors don't terminate the subprocess mid-stream.

`plcc-parse` is unaffected (already uses Popen). `plcc-rep` is unaffected.

**Tests:** All existing bats tests must continue to pass. A new bats test verifies that with multi-line input, output arrives incrementally (this is hard to test deterministically; coverage relies primarily on the existing test suite passing with the new implementation).

---

## Deferred

- `plcc-rep` support for `-` as stdin (complex tty/interactive interaction; revisit when it comes up in review)
- `--` end-of-options marker for passing a file literally named `-`
