# 093 - Incremental parsing in plcc-rep interactive mode

**Type:** feat
**Date:** 2026-06-15

## Description

Replace the current `SubmitOn.EOF` mode (where ^D submits accumulated input)
with an incremental parsing model that auto-detects complete statements and
handles ^D conventionally.

## Desired Behavior

After each line, the tool attempts to parse the accumulated input:

- If the input is a **complete statement** (it cannot be followed by additional
  tokens in the grammar): process it and return to the `>>>` prompt.
- If the input is **incomplete** (a valid prefix that could be extended by more
  tokens): show the `...` continuation prompt and wait for another line.

^D always exits the current context:

- At the `>>>` prompt: exits the REPL.
- At the `...` prompt: processes the accumulated input and returns to the `>>>`
  prompt.

## Notes

This mirrors how Python's interactive mode works: Python feeds each line to
`compile()` and distinguishes "unexpected EOF" (incomplete) from a real syntax
error or a complete statement.

Requires the generated parser to distinguish "unexpected end of input" from
"unexpected token" so plcc-rep can decide whether to show `...` or process.

This resolves the ^D dilemma: ^D always exits the current context (REPL or
continuation), satisfying the Linux convention that ^D exits. No special submit
chord is needed.
