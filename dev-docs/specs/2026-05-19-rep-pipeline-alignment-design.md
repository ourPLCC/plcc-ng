# Design: Align plcc-rep with plcc-parse and extract shared pipeline

**Date:** 2026-05-19
**Branch:** rep

---

## Problem

`plcc-rep` drifted from `plcc-parse` and developed a bug: typing an incomplete
expression (e.g. `1+`) in the interactive REPL printed an immediate
`error: unexpected end of input` instead of showing the `...` continuation
prompt. The root cause was that `RepHandler.feed()` lacked the EOF-error
detection that `ParseHandler` already had, and used the wrong submit mode.

While aligning the two files, we found that `feed()` in both handlers shares
~35 lines of identical pipeline logic (subprocess setup, record collection, and
the EOF-error gate) that is worth consolidating.

---

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Submit mode for rep | `SubmitOn.EOF` | Matches parse; first-line trial gives immediate feedback; matches the proven-correct pattern |
| Alignment strategy | Replace rep.py with parse.py baseline, add rep-specific pieces back | Less error-prone than parallel edits; diff shows exactly what rep needs |
| Extract pipeline? | Yes — `TreePipeline` class | ~35 lines of identical logic including the subtle EOF gate; strong argument for a single copy |
| Extract `_location_str`? | Yes — rides along with `TreePipeline` | Free when pipeline.py already exists; no standalone cost |
| Include scan? | No | scan runs one process (plcc-tokens only), has no EOF-error concept; structurally different |

---

## Phase 1 — rep.py alignment (done)

Starting from `parse.py` as the known-good baseline, the following rep-specific
pieces were added back:

- `__doc__` / `--tool` argument
- `interpreter` subprocess (`plcc-lang-run`)
- `_resolve_tool()`, `_read_response()`, `_render_record()`
- `RepHandler` tree handling: write raw JSON bytes to interpreter, read response
- `plcc-make` without `--through=parse` (full build)
- No `had_error` tracking (a REPL does not exit non-zero because one expression failed)

Changes relative to the old `rep.py`:

| | Old | New |
|---|---|---|
| Submit mode | `SubmitOn.EOL` | `SubmitOn.EOF` |
| EOF-error detection | none | `only_eof_errors` gate (return `False` silently when `eof=False`) |
| `child_flags` | not passed to subprocesses | forwarded to `plcc-tokens` and `plcc-trees` |
| Error format | bare `error: <msg>` | `file:line:col: error: <msg>` with stage-name fallback |

### New tests in `rep_test.py`

| Test | What it verifies |
|---|---|
| `test_feed_returns_false_for_eof_only_error_when_trial` | `eof=False` + EOF error → `False` |
| `test_feed_returns_true_for_eof_only_error_when_force_submit` | `eof=True` + EOF error → `True` |
| `test_feed_suppresses_stderr_for_eof_error_when_trial` | no stderr printed when `eof=False` |
| `test_feed_shows_stderr_for_eof_error_when_force_submit` | error printed when `eof=True` |
| `test_feed_returns_true_for_genuine_error_regardless_of_eof` | genuine error always → `True` |
| `test_feed_passes_child_flags_to_subprocesses` | `child_flags` appear in both `Popen` calls |
| `test_feed_error_shows_location_in_stderr` | stdin error renders `-:line:col` |
| `test_feed_error_renders_file_line_col` | file error renders `file:line:col` |
| `test_feed_error_with_no_location_shows_stage` | locationless error renders `stage: error: msg` |

---

## Phase 2 — `TreePipeline` extraction (planned)

### New file: `src/plcc/cmd/pipeline.py`

Three exports:

```python
def _location_str(source) -> str | None:
    """Return 'file:line:col', or None if line/col missing."""
    # Normalises "-" / "<stdin>" / "" to "-"


def print_parse_error(record, default_stage: str) -> None:
    """Print a parse/lex error record to stderr with location or stage prefix."""
    src = record.get("source", {})
    message = record.get("message", "error")
    loc = _location_str(src)
    if loc:
        print(f"{loc}: error: {message}", file=sys.stderr)
    else:
        stage = record.get("stage", default_stage)
        print(f"{stage}: error: {message}", file=sys.stderr)


class TreePipeline:
    """Runs plcc-tokens | plcc-trees and classifies the output."""

    def __init__(self, spec_path: str, ll1_path: str, child_flags=None): ...

    def run(self, content: bytes, eof: bool = False) \
            -> list[tuple[dict, bytes]] | None:
        """Run the pipeline.

        Returns None  — only EOF errors and eof=False; caller shows '...'
        Returns list  — (record_dict, raw_bytes) pairs ready to dispatch
        """
```

`TreePipeline.run()` encapsulates:
1. Subprocess pipeline: `plcc-tokens | plcc-trees`
2. Record collection into `(record, raw_bytes)` pairs
3. EOF-error gate:
   - No records → `None`
   - Only EOF errors and `eof=False` → `None`
   - Otherwise → list (may include error records)

### `ParseHandler` after extraction

```python
class ParseHandler:
    def __init__(self, spec_path, ll1_path, child_flags):
        self._pipeline = TreePipeline(spec_path, ll1_path, child_flags)
        self.had_error = False

    def feed(self, content, source, eof=False):
        items = self._pipeline.run(content, eof)
        if items is None:
            return False
        for record, _ in items:
            if record.get("kind") == "error":
                print_parse_error(record, default_stage="plcc-parse")
                self.had_error = True
            elif record.get("kind") == "tree":
                _print_tree(record, indent=0)
        return True
```

### `RepHandler` after extraction

```python
class RepHandler:
    def __init__(self, spec_path, ll1_path, interpreter, verbose_format,
                 child_flags=None):
        self._pipeline = TreePipeline(spec_path, ll1_path, child_flags)
        self._interpreter = interpreter
        self._verbose_format = verbose_format

    def feed(self, content, source, eof=False):
        items = self._pipeline.run(content, eof)
        if items is None:
            return False
        for record, raw in items:
            if record.get("kind") == "error":
                print_parse_error(record, default_stage="plcc-rep")
            elif record.get("kind") == "tree":
                try:
                    self._interpreter.stdin.write(raw + b'\n')
                    self._interpreter.stdin.flush()
                except BrokenPipeError:
                    print('plcc-rep: interpreter exited unexpectedly', file=sys.stderr)
                    sys.exit(1)
                _read_response(self._interpreter.stdout, self._verbose_format)
        return True
```

### New file: `src/plcc/cmd/pipeline_test.py`

Tests for `TreePipeline.run()`:
- empty output → `None`
- EOF-only error + `eof=False` → `None`
- EOF-only error + `eof=True` → list with error record
- genuine error + `eof=False` → list (not suppressed)
- tree record → list with tree record + raw bytes preserved
- `child_flags` forwarded to both subprocesses

Tests for `print_parse_error`:
- record with source → `file:line:col: error: msg` on stderr
- record without source → `stage: error: msg` on stderr
- default_stage used when record has no `stage` field

### Tests in parse_test.py and rep_test.py after extraction

Pipeline-internal tests (EOF gate, subprocess mechanics, error formatting) move to
`pipeline_test.py`. Handler tests keep the `subprocess.Popen` mock or switch to
injecting a mock `TreePipeline`; either approach is valid.

---

## Files modified

| File | Change |
|---|---|
| `src/plcc/cmd/rep.py` | Phase 1 (done); Phase 2 handler shrinks |
| `src/plcc/cmd/rep_test.py` | Phase 1 new tests (done); Phase 2 tests adjust |
| `src/plcc/cmd/parse.py` | Phase 2: handler shrinks, `_location_str` removed |
| `src/plcc/cmd/parse_test.py` | Phase 2: pipeline tests move to pipeline_test.py |
| `src/plcc/cmd/pipeline.py` | Phase 2: new |
| `src/plcc/cmd/pipeline_test.py` | Phase 2: new |

---

## Commit plan

```
fix(rep): align with plcc-parse — EOF errors, submit mode, child_flags, location format
refactor(cmd): extract TreePipeline shared pipeline logic from parse and rep
```

Both commits land on the `rep` branch.

---

## Verification

```bash
cd .worktrees/rep
bin/test/units.bash src/plcc/cmd/   # all green after each commit
```
