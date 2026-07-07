# Design: Shared SourceRunner for plcc-scan, plcc-parse, plcc-rep

**Date:** 2026-05-12

## Problem

`plcc-scan`, `plcc-parse`, and `plcc-rep` share a common CLI pattern: they accept source files on the command line, fall back to stdin when none are given (or when `-` is listed), and need to behave consistently in interactive sessions. Currently each command reimplements this logic independently, producing an inconsistent user experience:

- `plcc-rep` already shows a `>>> ` prompt and detects TTY interactivity; `plcc-scan` and `plcc-parse` do not.
- The planned `plcc-scan` TTY hint (issue 005) would add _some_ feedback for scan but still leave parse unaddressed.
- Source file name metadata in token records is handled differently across commands.

The goal is a single shared component that all three commands use for source routing, TTY detection, hint/prompt display, and interactive input accumulation.

---

## Design

### `SourceRunner` (`src/plcc/cmd/source_runner.py`)

A new `SourceRunner` class owns all source I/O behavior. Each command constructs a `SourceRunner` and passes it a `SourceHandler` — an object with one method:

```python
def feed(self, content: bytes, source: str) -> bool:
    ...
```

`True` means the pipeline produced output (tree, tokens, result, or error) — the runner resets the accumulation buffer and shows a fresh `>>>` prompt. `False` means no output yet — the runner keeps accumulating and shows `...`.

#### Source routing

| Source | Behavior |
|--------|----------|
| Filename argument | Read file content, call `feed(content, filename)` once |
| No arguments | Treat as `["-"]` |
| `"-"` with non-TTY stdin | Read all of stdin, call `feed(content, "-")` once |
| `"-"` with TTY stdin | Enter interactive loop (see below) |

Multiple sources are processed in order. A mix of files and `-` is valid.

#### Interactive loop

When stdin is a TTY, the runner:

1. Prints the hint once to stderr: `Enter input. Press ^D (EOF) when done.`
2. Shows `>>> ` prompt, reads a line, appends to an accumulation buffer, calls `feed(buffer, "-")`.
3. If `feed` returns `True`: clears the buffer, shows `>>> ` again.
4. If `feed` returns `False`: shows `... ` and reads another line.
5. **`^D` with non-empty buffer**: submits the buffer via `feed(buffer, "-")`, then exits the loop (EOF is a terminal state — the session ends).
6. **`^D` with empty buffer**: exits the loop immediately.
7. **`^C` (KeyboardInterrupt)**: clears the buffer and returns to `>>> ` without exiting.

#### `^D` semantics and LL1 grammars

For grammars where the start symbol is a single expression or statement, `plcc-tree` emits a tree as soon as the start symbol is complete and the token buffer is empty — so pressing `Enter` after a complete expression triggers output and the `>>>` prompt returns naturally. `^D` is only needed to signal end-of-input for `<stmt>+`-style top-level grammars, where the parser cannot know whether more statements will follow. In that case `^D` submits the accumulated program and ends the session, which is the correct behavior (multi-statement programs are better run as files).

---

### Changes to `plcc-tokens` (`src/plcc/tokens/tokens_cli.py`)

Add `--source-name=<label>` flag. When present, this label replaces `"-"` as the file annotation for all lines read from stdin. This allows `ScanHandler` to pipe file content while preserving the original filename in token location metadata (e.g. `foo.txt:3:1` instead of `-:3:1`).

No other behavior changes to `plcc-tokens`.

---

### Changes to `plcc-tree` (`src/plcc/tree/tree_cli.py`)

Two additions to support the streaming control signal:

1. **Mid-stream emit**: when the LL1 parser completes the start symbol derivation and the token buffer is empty (no remaining tokens from the current input chunk), emit the tree record immediately without waiting for stdin to close.

2. **Incomplete-EOF error**: when stdin closes (EOF) and the parser has not yet completed the start symbol, emit `{"kind": "error", "message": "unexpected end of input", ...}` to stdout.

Both fit the existing JSONL output protocol — no format changes are needed upstream or downstream.

---

### `ScanHandler` (`src/plcc/cmd/scan.py`)

Each `feed(content, source)` call:

1. Spawns a fresh `plcc-tokens <spec> --source-name=<source> -` subprocess with `content` piped to its stdin.
2. Reads all JSONL token records from stdout, renders each via `_render_record`.
3. Returns `True` unconditionally — every content chunk tokenizes completely; scan has no continuation concept.

---

### `ParseHandler` (`src/plcc/cmd/parse.py`)

Each `feed(content, source)` call:

1. Spawns a fresh `plcc-tokens <spec> -` piped into `plcc-tree --ll1=<ll1>`, with `content` sent to tokens' stdin.
2. Reads stdout for a tree or error record.
3. Returns `True` if any record was produced; `False` if stdout was empty (incomplete parse — more input needed).

---

### `RepHandler` (`src/plcc/cmd/rep.py`)

`RepHandler` is structurally `ParseHandler` plus an evaluation step. The long-lived interpreter process is started once when `main()` begins and kept alive for the session so that state (variable bindings, etc.) persists across evaluations.

Each `feed(content, source)` call:

1. Spawns a fresh `plcc-tokens | plcc-tree` pipeline with `content` piped in (identical to `ParseHandler`).
2. If `plcc-tree` produces **no output** (incomplete parse): return `False` immediately. The interpreter is not contacted — its state is unchanged. This is the load-bearing guarantee: partial attempts are invisible to the interpreter.
3. If `plcc-tree` produces a tree: write the tree line to the interpreter's stdin, read its response, print the result or error, and return `True`.

---

### Module layout

```
src/plcc/cmd/
    source_runner.py       ← new: SourceRunner class + SourceHandler protocol
    source_runner_test.py  ← new: unit tests (monkeypatched, no subprocesses)
    scan.py                ← add ScanHandler; replace IO loop with SourceRunner
    scan_test.py           ← add handler unit tests
    parse.py               ← add ParseHandler; replace IO loop with SourceRunner
    parse_test.py          ← new: handler unit tests
    rep.py                 ← add RepHandler; replace IO loop with SourceRunner
    rep_test.py            ← new: handler unit tests
src/plcc/tokens/
    tokens_cli.py          ← add --source-name flag + tests
src/plcc/tree/
    tree_cli.py            ← add streaming emit + incomplete-EOF error + tests
```

---

## Testing

### Unit tests (`pytest`)

- **`source_runner_test.py`**: covers source routing (file, non-TTY stdin, TTY stdin), accumulation across multiple `feed()` calls, `^C` reset, `^D` with non-empty buffer, `^D` with empty buffer, and multiple `-` sources. All via monkeypatching — no subprocesses.
- **`scan_test.py`**: covers `ScanHandler.feed()` in isolation — verifies `plcc-tokens` is invoked with correct `--source-name`, and that `True` is always returned.
- **`parse_test.py`**: covers `ParseHandler.feed()` — verifies `True` when output produced, `False` when stdout empty.
- **`rep_test.py`**: covers `RepHandler.feed()` — verifies interpreter interaction and return values.
- **`tokens_cli_test.py`**: add tests for `--source-name` label override.
- **`tree_cli_test.py`**: add tests for mid-stream emit and incomplete-EOF error.

### Bats command tests

Existing bats tests for `plcc-scan`, `plcc-parse`, and `plcc-rep` cover the end-to-end CLI contract (stdin/stdout/exit-code) and require no structural changes — the external behavior is preserved.

---

## Supersedes

The planned TTY hint for `plcc-scan` (issue 005 / `dev-docs/plans/2026-05-12-scan-tty-hint.md`) is subsumed by this design. The hint and prompt behavior specified there is now owned by `SourceRunner` and applies uniformly to all three commands. Issue 005 should be closed in favour of this work.
