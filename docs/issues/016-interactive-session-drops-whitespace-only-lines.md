# 016 - Interactive session does not preserve whitespace-only lines

**Type:** fix
**Date:** 2026-05-14

## Description

When a line consisting entirely of whitespace (spaces or tabs) is entered in
an interactive session, it is not passed through to the scanner. The line is
silently dropped instead of being forwarded as input.

This matters when testing how a language handles whitespace. A language may
treat a whitespace-only line as meaningful — for example, as a blank separator
between declarations, or as a token in its own right — but the interactive
session makes it impossible to exercise that behavior.

## Steps to Reproduce

1. Define a grammar where whitespace is significant or where a whitespace-only
   line should produce a distinct token or trigger a parse event.
2. Start an interactive session (`plcc-scan` or the REPL equivalent).
3. Enter a line containing only spaces or tabs.
4. Observe that the line produces no output and is not forwarded to the scanner.

## Notes

- A blank line (no characters at all) has a defined role in the interactive
  session: it submits a pending multi-line buffer. A whitespace-only line is
  distinct from a blank line and should not trigger that behavior.
- The fix should preserve the existing blank-line-submits-buffer behavior
  (closed by issue 014) while allowing whitespace-only lines through.
- The scanner already handles whitespace according to the grammar; the problem
  is upstream, in the line-reading layer before the scanner sees the input.
