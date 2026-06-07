# Interactive Session Design: Issues 016, 024, 025

**Date:** 2026-05-17
**Issues:** 016 (whitespace-only lines dropped), 024 (no diagnostic on premature EOF), 025 (attempt first line before continuation)
**Branch:** fix/interactive-session

---

## Context

`SourceRunner` drives two interactive modes:

- `SubmitOn.EOL` (`plcc-scan`): each line is fed to the handler immediately.
- `SubmitOn.EOF` (`plcc-parse`, `plcc-rep`): input accumulates until `^D`, then is fed all at once.

`feed(content, source)` runs content through a subprocess pipeline (e.g. `plcc-tokens | plcc-trees`) and returns `True` if any output was produced, `False` if output was empty ("need more input").

---

## Cross-cutting: rename `$` sentinel → `eof`

The EOF sentinel token is currently named `$`, a compiler-theory convention that is cryptic in user-facing output. It is renamed to `eof` throughout.

- `eof` is lowercase, which is not a legal PLCC token name (must be uppercase), so it is a permanently safe discriminator.
- The sentinel is still a real token with position (one past the last character on the last line) and empty lexeme.
- The change is mechanical: one emission site (`tokens_cli.py`), one loop guard (`table_cli.py`), and the internal sentinel in `predictive_parser.py`.

**Files:** `tokens_cli.py`, `predictive_parser.py`, `table_cli.py`, `scan.py` (filter update).

---

## Issue 016 — Whitespace-only lines silently dropped

### Problem

`_is_blank(line)` returns `True` for any line whose `.strip()` is empty, including whitespace-only lines like `b"  \n"`. These are silently dropped instead of being forwarded to the scanner.

A whitespace-only line is distinct from a truly blank line (`b"\n"`). Only the bare newline has a defined interactive role (submitting a pending buffer in `SubmitOn.EOL`); whitespace-only lines are content and should pass through.

### Fix

**`source_runner.py` — `_is_blank()`:**
```python
def _is_blank(self, line):
    return line == b"\n"
```

**`source_runner.py` — `_accumulate_only()`** (used by `SubmitOn.EOF`):
Remove the `if not buffer.strip()` guard that drops whitespace-only content. Always accumulate:
```python
def _accumulate_only(self, line, state):
    buffer = state.buffer + line
    return _InteractiveState(buffer=buffer, prompt=self._continuation)
```

### Behavior change

- `SubmitOn.EOL`: whitespace-only line (`b"  \n"`) now reaches `_accumulate_and_evaluate` and is fed to the scanner, which handles it per grammar rules. A bare newline (`b"\n"`) still force-submits the buffer as before.
- `SubmitOn.EOF`: whitespace-only line accumulates with the `...` prompt shown. Previously it was silently discarded and the `>>>` prompt was shown again.

---

## Issue 024 — Structured incomplete-input signal

### Problem

When the parser sees `eof` where a real token was expected (premature end of input), no diagnostic reaches the user. The session either silently re-prompts or shows "PLCC internal error".

### Design

Treat `eof` as a real token throughout the system. When parsing fails because `eof` was seen, the error record carries a `"found": "eof"` field. `ParseHandler` uses this field to distinguish "need more input" from "genuine error", and uses the `eof` parameter (added to `feed()`) to decide whether to signal continuation or show the error.

#### `predictive_parser.py`

`ParseError` gains a `found` field — the name of the token that was actually seen:
```python
class ParseError(Exception):
    def __init__(self, message, source=None, found=None):
        super().__init__(message)
        self.source = source or {}
        self.found = found
```

All raise sites pass `found=tok["name"]` (the bad token's name). Because `eof` is now a regular token, no special-case branches are needed for EOF detection — the parser treats it like any other unexpected token.

The internal `SENTINEL` in `parse()` is renamed to use `"eof"` as its name (safety fallback; in practice `plcc-tokens` always provides the real `eof` token).

#### `table_cli.py`

Error records include `"found"` when set:
```python
record = {
    "kind": "error",
    "message": str(e),
    "stage": "plcc-parser-table",
    "source": e.source,
}
if e.found:
    record["found"] = e.found
```

#### `parse.py` — `ParseHandler.feed(content, source, eof=False)`

Gains an `eof` parameter. After collecting all records:

- If any tree was produced → return `True`.
- If any error has `found != "eof"` (genuine error) → return `True`.
- If all errors have `found == "eof"` (premature EOF, no tree):
  - `eof=False` (trial) → return `False` (enter continuation mode, no output shown).
  - `eof=True` (force-submit) → return `True` (errors are already printed to stderr, session continues).

#### `scan.py` — `ScanHandler.feed(content, source, eof=False)`

Gains `eof` parameter, ignores it, always returns `True`. Updates sentinel filter from `"$"` to `"eof"`.

---

## Issue 025 — Attempt first line before entering continuation mode

### Problem

In `SubmitOn.EOF` mode, every line accumulates without being processed until `^D`. This means even a self-contained single-line expression like `1 + 2` requires `^D` to produce output.

### Design

At the `>>>` prompt (empty buffer), the first line is tried immediately by calling `feed()` with `eof=False`. If it produces output (tree or genuine error), the session returns to `>>>`. If it produces no output (premature EOF), the shell enters `...` continuation mode and accumulates further input until `^D`.

```
>>> 1 + 2        → trial → tree → show result → >>>
>>> 1 +          → trial → eof error, eof=False → feed returns False → ...
... 2
... ^D           → force-submit → tree → show result → >>>
>>> 1 + ^D       → partial-EOF force-submit → eof error, eof=True → show error → >>>
>>> bad          → trial → lex error (found != "eof") → show error → >>>
```

Once in `...` mode, behavior is unchanged: lines accumulate, `^D` force-submits.

#### `source_runner.py`

`_process_line()` — new branch for `SubmitOn.EOF` with empty buffer:
```python
if self._submit_on == SubmitOn.EOF:
    if not state.buffer:
        return self._attempt_first_line(handler, line, state)
    return self._accumulate_only(line, state)
```

New `_attempt_first_line()`:
```python
def _attempt_first_line(self, handler, line, state):
    if self._evaluate(handler, line, eof=False):
        return _InteractiveState(buffer=b"", prompt=self._prompt)
    return _InteractiveState(buffer=line, prompt=self._continuation)
```

`_evaluate()` passes `eof` to the handler:
```python
result = handler.feed(content, "-", eof=eof)
```

The existing `if eof and result is False: sys.exit(1)` is retained as a safety net for genuine internal errors (unreachable in normal use with the new `ParseHandler` logic).

---

## File change summary

| File | Change |
|---|---|
| `tokens_cli.py` | Emit `"eof"` sentinel instead of `"$"` |
| `predictive_parser.py` | Rename sentinel; `ParseError` gains `found`; remove `== "$"` special cases |
| `table_cli.py` | Update sentinel check; add `"found"` to error records |
| `source_runner.py` | Fix `_is_blank`, `_accumulate_only`; add `_attempt_first_line`; pass `eof` in `_evaluate` |
| `parse.py` | `ParseHandler.feed` gains `eof`; checks `found == "eof"` to signal continuation |
| `scan.py` | `ScanHandler.feed` gains `eof` (ignored); update sentinel filter |

---

## Testing notes

- `predictive_parser_test.py`: update sentinel references; add test that a premature-EOF `ParseError` has `found == "eof"`.
- `table_cli_test.py`: add test that an incomplete-input error record has `"found": "eof"`.
- `parse_test.py`: add test that `feed()` returns `False` for `eof`-only errors when `eof=False`, and `True` when `eof=True`.
- `source_runner_test.py`: add tests for `_attempt_first_line` — trial succeeds, trial fails (continuation), whitespace-only line behavior.
- `scan_test.py`: verify `$` → `eof` filter update.
- Bats integration tests: update any `$` sentinel references.
