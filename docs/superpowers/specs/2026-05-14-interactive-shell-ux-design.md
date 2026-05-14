# Interactive Shell UX Design

**Date:** 2026-05-14
**Issues:** 013 (^C exits interactive shell), 014 (blank line submits multiline input)
**Branch:** interactive-shell-ux

## Scope

Both issues are fixed entirely inside `_run_interactive` in
`src/plcc/cmd/source_runner.py`. No changes to any handler or caller.

## Background: how the interactive loop works

`SourceRunner._run_interactive` accumulates typed lines into a `buffer`. On
every Enter it feeds the **entire buffer** to the handler via `handler.feed(buffer,
"-")`. Each `feed()` call spawns a fresh subprocess pipeline (e.g.
`plcc-tokens | plcc-tree`) and waits for it to finish before returning. The
handler returns `True` if the buffer parsed successfully, `False` if the parse
is incomplete.

Because the full buffer is re-fed each time and each call creates fresh
subprocesses, **all three handlers are stateless between calls**:

- `ScanHandler` — always returns `True`; continuation mode never activates.
- `ParseHandler` — returns `False` only after the fresh `plcc-tokens`/`plcc-tree`
  pair has already exited with no output. No dangling processes on `False`.
- `RepHandler` — same stateless parse phase as `ParseHandler`. The long-lived
  interpreter subprocess is only written to after a successful parse (a `True`
  return path). On a `False` return the interpreter is untouched.

This means clearing the buffer on `^C` during input is always safe: the next
`feed()` call starts from a clean slate with no handler state to reset.

## Issue 014 — blank line submits multiline input

**Desired behaviour:** when the continuation prompt (`...`) is showing and the
user presses Enter on a blank line, submit the accumulated buffer for evaluation.

**Change:** in the blank-line branch, check whether `buffer` is non-empty. If so,
append the blank line to the buffer (treating it as an EOF signal) and feed the
result. If the buffer is empty, continue silently as today.

```text
blank line received
├── buffer non-empty → feed(buffer + line); reset buffer and prompt
└── buffer empty     → skip silently (existing behaviour)
```

## Issue 013 — ^C behavior

**Desired behaviour (Python-style):**

| Situation | Result |
| --- | --- |
| `^C` while blocking on `readline()`, buffer empty | `sys.exit(130)` |
| `^C` while blocking on `readline()`, buffer non-empty | clear buffer, print `KeyboardInterrupt` to stderr, reprompt |
| `^C` while `handler.feed()` is running (evaluation) | `sys.exit(130)` |

The distinction between "during input" and "during evaluation" is tracked with
a boolean flag `evaluating` set to `True` immediately before each `handler.feed()`
call and implicitly `False` at the top of each loop iteration.

**Why exit on evaluation interrupt?** The long-lived interpreter subprocess in
`RepHandler` accumulates user session state (variables, objects). There is no
safe way to interrupt an in-flight evaluation and resume that state. A clean
exit with code 130 is the honest answer. For `plcc-scan` and `plcc-parse`, whose
handlers are purely synchronous, evaluation interrupts are rare but the same
exit behaviour is appropriate.

**Why Python-style two-press for input?** Clearing a mistyped or misstarted line
with `^C` is a universal interactive shell convention. A single `^C` exit would
force the user to retype everything if they accidentally pressed Enter too early.

## Implementation sketch

```python
def _run_interactive(self, handler):
    print(self._hint, file=sys.stderr)
    buffer = b""
    prompt = self._prompt
    while True:
        evaluating = False
        try:
            print(prompt, end="", flush=True, file=sys.stderr)
            line = sys.stdin.buffer.readline()
            if not line:                          # ^D / EOF
                if buffer:
                    handler.feed(buffer, "-")
                break
            if not line.strip():
                if buffer:                        # blank line in continuation → submit
                    evaluating = True
                    result = handler.feed(buffer + line, "-")
                    if result:
                        buffer = b""
                        prompt = self._prompt
                    else:
                        prompt = self._continuation
                continue                           # blank on fresh prompt → skip
            buffer += line
            evaluating = True
            result = handler.feed(buffer, "-")
            if result:
                buffer = b""
                prompt = self._prompt
            else:
                prompt = self._continuation
        except KeyboardInterrupt:
            print(file=sys.stderr)
            if not evaluating and buffer:         # ^C clearing a mistyped line
                print("KeyboardInterrupt", file=sys.stderr)
                buffer = b""
                prompt = self._prompt
            else:                                 # ^C on empty prompt or during eval
                sys.exit(130)
```

## Testing

Unit tests in `src/plcc/cmd/source_runner_test.py` (existing file). No new bats
tier needed — the interactive path is impractical to drive via bats.

Cases to cover:

- `^C` with empty buffer → process exits 130
- `^C` with non-empty buffer during input → buffer cleared, loop continues,
  `KeyboardInterrupt` printed to stderr
- `^C` during `handler.feed()` (mock raises `KeyboardInterrupt`) → exits 130
- Blank line on fresh prompt → skipped (existing behaviour preserved)
- Blank line during continuation → buffer submitted, prompt reset
