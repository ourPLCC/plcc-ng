# 098 - ^D on a non-empty line requires a second ^D to take effect

**Type:** fix
**Date:** 2026-06-18

## Description

In `plcc-rep`'s interactive mode, pressing ^D while there is text on the
current line has no immediate effect. A second ^D is required before the
input is processed. This is non-standard behavior.

## Steps to Reproduce

1. Run `plcc-rep -s spec.plcc`
2. At the `>>>` prompt, type some input (do not press Enter)
3. Press ^D

## Observed

Nothing happens. A second ^D is required to process the input.

## Desired Behavior

Standard terminal ^D semantics: ^D on a non-empty line flushes the line
to the application without a trailing newline character. `plcc-rep` should
treat this flushed input as it would any other line — appending it to the
accumulated input buffer — and then process the buffer with EOF, as if the
user had pressed Enter followed by ^D on an empty line.

## Notes

This is standard POSIX ^D behavior: the terminal sends whatever is buffered
to the reading process immediately, without a newline. The application sees
the partial line as data followed by EOF. `plcc-rep` should handle this
case the same way it handles ^D on an empty line (i.e. process accumulated
input and return to `>>>` or exit, depending on context).

See also: [[093-incremental-parsing-repl]]
