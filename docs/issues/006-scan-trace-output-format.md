# 006 - Improve plcc-scan --trace output format

**Type:** fix
**Date:** 2026-05-11

## Description

The output of `plcc-scan --trace` (and `--show-skips`, `--show-attempts`,
`--show-regex`) is hard to read. Several formatting improvements are needed:

1. **Add a heading before the matching-rules block.** There is currently no
   label separating the source-line/cursor from the list of rule attempts.
   Add a heading such as `Candidates:` (or `Matching Rules:`, `attempts:`,
   etc.) immediately before the indented list.

2. **Reduce indentation of matching rules.** The current indentation is
   deeper than necessary. Bring it closer to the left margin to reduce
   horizontal noise.

3. **Remove the asterisk marking the winning rule.** The winner is already
   identified by its position in the token line that follows; the `*` prefix
   adds clutter without adding information.

4. **Add a blank line after each match event.** Each token's block (source
   line + cursor + candidates + token line) runs directly into the next.
   A blank line between blocks improves scannability.

5. **Remove regex from the match/token event line.** Under `--trace` the
   regex already appears in the candidates list. Printing it again on the
   token line is redundant. Keep the regex only in the candidates list.

6. **Move SKIPPED to the front of the line and rename it SKIP.** The current
   format places `SKIPPED` at the end (`-:1:3 WS ' ' SKIPPED`). Putting the
   disposition at the front makes it easier to filter or scan visually.
   Use the shorter `SKIP` rather than `SKIPPED`.

## Notes

- Changes affect `--show-skips`, `--show-line`, `--show-attempts`,
  `--show-regex`, and `--trace` (which enables all four).
- Bats tests that assert on the current format will need updating alongside
  the implementation.
