# 014 - Blank line should end a multi-line (continuation) input

**Type:** feat
**Date:** 2026-05-14

## Description

When the interactive shell (`plcc-rep`) is waiting for more input (showing the
`... ` continuation prompt), pressing Enter on a blank line should submit the
accumulated buffer for evaluation.

Currently a blank line during continuation is treated as more input and the
`... ` prompt reappears, giving users no keyboard-based way to submit a
multi-line expression short of ^D (which also exits the shell).

## Steps to Reproduce

1. Run `plcc-rep` with a grammar that accepts multi-line input.
2. Type a partial expression that leaves the parser wanting more (continuation
   prompt appears).
3. Press Enter on a blank line.

**Expected:** the accumulated input is submitted for evaluation.

**Actual:** the `... ` prompt reappears; input is not submitted.

## Notes

The relevant loop is in `SourceRunner._run_interactive`
([src/plcc/cmd/source_runner.py:34](../../src/plcc/cmd/source_runner.py#L34)).
The current blank-line guard (line 46) only fires on a fresh `>>> ` prompt, not
during continuation.

Whether ^D also ends a continuation (vs. exiting the shell) is left to the
implementer — whichever keeps the protocol simpler is fine.
