# 061 - scanner-block-double-newline

**Type:** bug
**Date:** 2026-06-04

## Description

`Scanner._scanBlock` always injects a `\n` separator when concatenating subsequent lines into the block buffer (`buffer += '\n' + next_line.string`). However, `Line.string` is not normalized consistently across all line sources:

- `parse_from_string` (used in unit tests) calls `str.splitlines()`, which strips trailing newlines — so `Line.string` is `'foo'`.
- `parse_from_strings(file_iterator)` (used by `parse_from_file` and `tokens_cli._lines_from_stream`) yields raw lines from a file iterator, which **include** the trailing `\n` — so `Line.string` is `'foo\n'`.

This means in production file scanning the scanner injects an extra `\n`, producing doubled blank lines inside block token/skip lexemes. The unit tests do not catch this because they go through the normalizing `splitlines()` path.

## Steps to Reproduce

1. Create a source file with a block token spanning multiple lines, e.g.:
   ```
   <<<
   hello
   world
   >>>
   ```
2. Run `plcc-tokens` against a spec with `token BODY '<<<' '>>>'`.
3. Observe that the lexeme is `'\nhello\n\nworld\n\n'` instead of `'\nhello\nworld\n'`.

## Notes

The root cause is in the `lines` layer: `parse_from_strings` does not normalize its input the way `parse_from_string` does. The correct fix is to strip trailing newlines (and/or `\r\n`) from each string in `parse_from_strings`, making all `Line` sources consistent. A workaround in the scanner (e.g., "only add `\n` if buffer doesn't already end with one") would be fragile against `\r\n` line endings.

Discovered during review of issue-060 (block lexical rule implementation).
