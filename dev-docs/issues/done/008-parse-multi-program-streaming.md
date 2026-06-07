# 008 - plcc-parse: multi-program input, streaming output, and error recovery

**Type:** fix
**Date:** 2026-05-11

## Description

`plcc-parse` has several related limitations around how it handles input and
produces output.

### 1. Only one tree per source

A source file (or stdin stream) may contain more than one program in the
language. `plcc-parse` currently stops after the first program and does not
attempt to parse subsequent ones. It should repeatedly parse from the token
stream until input is exhausted, printing a tree for each complete program.

### 2. Multiple source arguments and `-` for stdin

Like `plcc-scan`, `plcc-parse` should accept multiple source file arguments
and treat `-` as stdin. Each source is parsed independently, producing one or
more trees per source. The same multi-program logic from (1) applies within
each source.

### 3. Output is batched instead of streamed

Output appears to be buffered and printed all at once when the process exits
rather than emitted as each tree is completed. Once a complete program has been
matched, its tree should be printed immediately. This matters for interactive
use and for downstream pipeline stages that want to process trees as they
arrive.

### 4. Syntax error recovery (needs design)

What should happen when a syntax error is detected mid-parse is not yet
decided. An initial hypothesis:

- In an interactive session (stdin is a TTY), flush the remainder of the
  current logical input unit (e.g. the current line or token run) and restart
  the parser, so the user can type a new program without restarting the
  command.
- In a non-interactive session (piped input or file), emit an error record and
  attempt to resume at the next recoverable boundary.

This needs more thought before implementation. Key questions:
- What is the right recovery boundary (line? statement? top-level rule attempt?)
- Should the error be emitted to stderr or as a structured record on stdout
  (consistent with how `plcc-scan` emits lex errors inline)?
- How does recovery interact with the multi-program loop from (1)?

## Notes

- Issues (1), (2), and (3) are relatively self-contained and can be
  implemented together.
- Issue (4) should be designed separately before implementation begins.
