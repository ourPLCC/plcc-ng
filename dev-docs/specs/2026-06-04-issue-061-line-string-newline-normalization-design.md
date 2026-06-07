# Design: Issue 061 — Line.string Newline Normalization

**Date:** 2026-06-04
**Issue:** [061-scanner-block-double-newline](../../issues/061-scanner-block-double-newline.md)

## Problem

`Scanner._scanBlock` injects `'\n'` between lines when building a block lexeme
(`buffer += '\n' + next_line.string`). In production, `Line.string` already
includes the trailing `\n` from the file iterator, so the injection produces
double newlines. In unit tests, `parse_from_string` uses `str.splitlines()`
which strips trailing newlines, so tests pass without revealing the bug.

The deeper issue is that the scanner needs to see newline characters so that
rules like `token NEWLINE '\n'` can match them. The production path (file
iterator via `parse_from_strings`) already provides this. The test path
(`parse_from_string` via `splitlines()`) accidentally discards them.

## Invariant

`Line.string` carries the source text of the line **including its trailing
line ending (`\n`)**, except for the final line of a source that has no
trailing newline. Line endings are normalized: `\r\n` and bare `\r` both
become `\n`. Mid-line `\r` is left as-is.

This invariant makes `Line.string` a faithful, normalized slice of the source
stream across all input paths (file, string, string list).

## Changes

### 1. `parse_from_strings.py` — normalize line endings

`parse_from_strings` is the single funnel all `Line` construction flows
through. Normalize each string's trailing line ending before yielding:

```python
def parse_from_strings(strings, file=None, startLineNumber=1):
    for i, string in enumerate(strings, start=startLineNumber):
        if string.endswith('\r\n'):
            string = string[:-2] + '\n'
        elif string.endswith('\r'):
            string = string[:-1] + '\n'
        yield Line(string=string, file=file, number=i)
```

`parse_from_file` opens files in text mode, so Python already converts `\r\n`
to `\n` on all platforms; the normalization here is a safety net for strings
passed programmatically.

### 2. `parse_from_string.py` — preserve line endings

Change `splitlines()` to `splitlines(keepends=True)` so the string path
produces Lines with the same trailing `\n` as the file path:

```python
def parse_from_string(string, file=None, startLineNumber=1):
    return parse_from_strings(string.splitlines(keepends=True), file=file, startLineNumber=startLineNumber)
```

The normalization in `parse_from_strings` handles any `\r\n` or `\r` that
`splitlines(keepends=True)` preserves.

### 3. `scanner.py` `_scanBlock` — remove `'\n'` injection

Remove the explicit `'\n' +` from both buffer-accumulation sites. The newline
is already present in `next_line.string`:

```python
# close found on a subsequent line
buffer += next_line.string[:m.start()]

# close not yet found
buffer += next_line.string
```

The opening-line contribution (`buffer = line.string[start:]`) naturally ends
with `\n` when the open delimiter is not the last character on its line, so
concatenation is seamless.

## Test Updates

### `parse_from_string_test.py` (parseLines tests)

Expected `Line` values for lines that carry a newline gain `\n` in their
`string` field. Examples:

- `Line('one', 1, None)` for `parseLines('one\n')` → `Line('one\n', 1, None)`
- `Line('', 1, None)` for `parseLines('\n')` → `Line('\n', 1, None)`
- `Line('one', 1, None), Line('two', 2, None)` for `parseLines('one\ntwo')` →
  `Line('one\n', 1, None), Line('two', 2, None)`

Lines without a trailing newline are unaffected.

### `scanner_test.py`

**Block-token tests:** Tests that append a trailing `\n` to input strings
(e.g. `'<<<hello>>>\n'`) now cause the scanner to attempt matching `'\n'`
after the close delimiter. Fix by trimming the trailing `\n` from inputs in
tests that are not specifically testing newline handling (e.g.
`'<<<hello>>>'`). Tests that already include a whitespace skip rule are
unaffected.

**LexError slice tests:** `Line.string` is now one character longer for lines
that had a trailing `\n`. Result-slice indices in tests that count characters
need adjusting (e.g. `results[0:10]` → `results[0:11]`).

**New tests to add:**

1. A `token NEWLINE '\n'` rule matches each line ending when input comes
   through `parse_from_strings` with raw file-style strings (exercises the
   previously-untested production path and confirms newlines are visible to the
   scanner).

2. A block token spanning multiple lines produces the correct (non-doubled)
   lexeme when scanned via `parse_from_strings` with raw newline-bearing
   strings (regression test for the original bug).

## Non-changes

- `Line` remains a plain frozen dataclass. Normalization lives in
  `parse_from_strings`, not in `Line.__post_init__`.
- `parse_from_file` is unchanged. Text-mode `open()` already normalizes
  `\r\n`; the `parse_from_strings` guard is belt-and-suspenders.
- Mid-line `\r` characters are not touched.
