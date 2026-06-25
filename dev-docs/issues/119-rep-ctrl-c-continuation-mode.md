# 119 - `^C` exits continuation mode in `plcc-rep` instead of canceling current input

**Type:** fix
**Date:** 2026-06-25

## Description

In `plcc-rep`, pressing `^C` while in continuation mode (showing `...` prompt) exits back to the top-level `>>>` prompt rather than simply canceling the current incomplete input and returning to `>>>`. A user reported this on macOS Terminal.

The desired behavior needs to be carefully considered: should `^C` cancel the current input and return to the top-level prompt (readline-style), exit the REPL entirely, or do something else?

## Notes

- Related: issue #085 (`plcc-rep` printed a `KeyboardInterrupt` stack trace on `^C` — now fixed). This is a separate behavioral question about what `^C` *should* do in continuation mode.
- In most REPLs (Python, Node, bash), `^C` during a partial/continuation input cancels that input and returns to a clean prompt without exiting the REPL.
- Decide the intended behavior first, then verify current behavior matches.
- May behave differently on Linux vs macOS — test both if possible.
