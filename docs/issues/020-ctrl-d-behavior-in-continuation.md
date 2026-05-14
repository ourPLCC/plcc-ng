# 020 - ^D behavior in continuation is surprising

**Type:** fix
**Date:** 2026-05-14

## Description

^D has two confusing behaviors when used during a multi-line (continuation)
input session.

### 1. ^D after partial text on a line does not submit

When the user presses ^D after typing text on a continuation line (without
pressing Enter first), nothing visibly happens. The terminal flushes the
partial line to the process without a newline; `readline()` returns the text
as a normal line, the buffer grows, and the `...` prompt reappears. The user
has to press Enter to complete the line, and even then the session continues
because the grammar still expects more input.

The user's mental model is: "^D means I am done — submit everything I have
typed." The actual behavior is: "^D flushes the partial line as if Enter were
pressed, then waits for more."

### 2. ^D on an empty continuation line immediately exits

When the user presses ^D on an empty `...` line, the session exits immediately.
The accumulated buffer is evaluated (if non-empty) and the loop breaks. This
is surprising in the middle of a multi-line entry: the user may have intended
"submit what I have" but instead gets an abrupt exit.

## Steps to Reproduce

Grammar:

```
skip WS '\s+'
token A 'a'
token AA 'aa'
token ID '\w+'
%
<prog> ::= <A> <AA> <ID>
```

Session (^D shown explicitly):

```
>>> a
... aa^D
... ^D
```

1. Type `a`, press Enter → `...` continuation appears (grammar needs `AA` and `ID`).
2. Type `aa`, press ^D (no Enter) → appears to do nothing; `...` prompt reappears.
3. Press Enter → `...` continuation again (grammar still needs `ID`; the `aa^D`
   flushed `aa` as a normal line, so the buffer is now `a\naa` — still
   incomplete).
4. Press ^D on the empty `...` line → session exits immediately.

Step 2 is surprise one; step 4 is surprise two.

## Desired behaviour

The right behavior for ^D in a continuation context needs design discussion, but
the student-friendly expectation is:

- **^D after partial text** — treat the partial text as a complete line (same as
  if Enter had been pressed) and then submit the accumulated buffer for
  evaluation, regardless of whether the grammar considers it complete.
- **^D on an empty continuation line** — submit the accumulated buffer for
  evaluation rather than exiting. Exiting on ^D makes sense at the top-level
  `>>>` prompt; inside a continuation the user is more likely trying to force
  evaluation of what they have.

## Notes

- The root of surprise (1) is how the terminal and `readline()` interact: ^D
  after partial input flushes the characters without a newline, so the code
  sees a normal (newline-less) line rather than EOF. A fix could detect a line
  without a trailing newline and treat it as a submit signal.
- The root of surprise (2) is that the `if not line: … break` path
  ([source_runner.py:52–55](../../src/plcc/cmd/source_runner.py#L52)) does not
  distinguish between ^D at the top-level prompt and ^D inside a continuation.
  Tracking whether a continuation is in progress would let the two cases behave
  differently.
- Related to issue [018](018-ctrl-d-exit-missing-newline.md): the exit triggered
  by step 4 also suffers from the missing-newline problem — the shell prompt
  appears on the same line as `...`.
- Same test grammar and session as issue [019](019-parse-error-not-student-friendly.md).
