# Design: Scan token output file provenance

**Date:** 2026-05-07
**Issue:** [002-scan-tokens-missing-file-info](../issues/done/002-scan-tokens-missing-file-info.md)

## Problem

`plcc-scan` output omits the source filename from token lines. When input spans
multiple files (or a mix of files and stdin) there is no way to tell which file a
token came from. Errors already include the filename; tokens do not — an
inconsistency this design closes.

Root cause: `plcc-scan` pipes all source content into `plcc-tokens` stdin.
`plcc-tokens` labels every line `file='<stdin>'`, so the JSONL records carry no
real provenance, and `plcc-scan`'s `_location_str` suppresses `<stdin>` from the
output.

## Design

### Part 1 — `plcc-tokens` gains `[SOURCE ...]` arguments

**New usage:**

```
plcc-tokens [options] SPEC_JSON [SOURCE ...]
```

- If no SOURCE files are given, reads stdin and labels every line `file='-'`.
- If SOURCE files are given, opens them in order using two private helpers:
  `_lines_from_sources` (iterates files, handling `-` as stdin) and
  `_lines_from_stream` (enumerates lines from an open stream).

The `_read_stdin_as_lines()` helper in `tokens_cli.py` is removed and replaced
by these helpers. `scan.source.Source` is intentionally **not** reused here:
`Source` calls `line.strip()` which removes leading whitespace and would corrupt
column numbers in source code.

No changes to `jsonl_formatter.py` or the token JSON schema — both already emit
and require `source.file` / `pos.file`.

### Part 2 — `plcc-scan` passes SOURCE args through instead of piping content

Currently `plcc-scan` opens each source file itself and feeds bytes into
`plcc-tokens` stdin via a `_feed_input` thread. After this change it passes its
SOURCE arguments (or `["-"]` when none are given) directly to `plcc-tokens` as
command-line arguments. `plcc-tokens` opens the files itself. The feed thread
and the stdin pipe to `plcc-tokens` are removed.

`_location_str` in `scan.py` is simplified to always emit `file:line:col` — the
file is now always meaningful (a real path or `-`).

### Data flow

**Before:**

```
plcc-scan opens files
  → pipes bytes into plcc-tokens stdin
  → plcc-tokens labels every line file='<stdin>'
  → scan.py _location_str suppresses file, outputs line:col
```

**After:**

```
plcc-scan passes source filenames as CLI args to plcc-tokens
  → plcc-tokens uses Source to open files, labels lines with actual path or '-'
  → scan.py _location_str always outputs file:line:col
```

## Output format

Token line: `file:line:col NAME 'lexeme'`
Error line: `file:line:col: error: message 'char'`

Named file example:
```
input.txt:1:1 NUM '42'
```

Stdin example (`plcc-scan grammar.plcc` or `plcc-scan grammar.plcc -`):
```
-:1:1 NUM '42'
```

## Tests to update

| Location | Current expectation | New expectation |
|---|---|---|
| `tests/bats/commands/plcc-scan.bats` line 37 | `^1:1 NUM '42'$` | `^-:1:1 NUM '42'$` |
| `src/plcc/tokens/tokens_cli_test.py` line 60 | `'file': '<stdin>'` | `'file': '-'` |

## New tests to add

- `plcc-tokens` with a named file arg produces records with `source.file` set to
  that filename.
- `plcc-scan` with a named SOURCE file includes the filename in token output.
- `plcc-scan` with `-` as SOURCE shows `-` as the file in output.
- `plcc-tokens` with no SOURCE args reads stdin and labels lines `file='-'`.

## Files changed

| File | Change |
|---|---|
| `src/plcc/tokens/tokens_cli.py` | Accept `[SOURCE ...]`; use `Source`; remove `_read_stdin_as_lines` |
| `src/plcc/tokens/tokens_cli_test.py` | Update `file='<stdin>'` → `file='-'`; add file-arg tests |
| `src/plcc/cmd/scan.py` | Pass SOURCE args to `plcc-tokens`; remove feed thread and stdin pipe; simplify `_location_str` |
| `tests/bats/commands/plcc-scan.bats` | Update format assertion; add filename-in-output tests |
| `tests/bats/commands/plcc-tokens.bats` | Add file-arg tests |
