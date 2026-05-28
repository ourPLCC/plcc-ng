# 039 — Level-2 Errors to Stdout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route user-facing language errors (parse, scan, semantic/interpreter) in `plcc-parse`, `plcc-rep`, and `plcc-scan` to stdout, reserving stderr for tool-level diagnostics only.

**Architecture:** A new `cmd/output.py` module introduces `print_user_error(message)` — a single function that prints to stdout. Its name encodes intent at every call site, making the stdout/stderr distinction self-documenting. `print_parse_error()` in `pipeline.py` and the interpreter error branch in `rep.py` switch to use it. `scan.py` also adopts it for consistency (no behaviour change).

**Tech Stack:** Python 3, pytest (via `bin/test/units.bash`), bats (via `bin/test/commands.bash`)

---

## File Map

| Action | Path | Purpose |
| --- | --- | --- |
| Create | `src/plcc/cmd/output.py` | `print_user_error()` helper |
| Create | `src/plcc/cmd/output_test.py` | Tests for the helper |
| Modify | `src/plcc/cmd/pipeline.py` | Use `print_user_error()` in `print_parse_error()` |
| Modify | `src/plcc/cmd/pipeline_test.py` | 5 tests: assert `out` instead of `err` |
| Modify | `src/plcc/cmd/rep.py` | Use `print_user_error()` for interpreter errors |
| Modify | `src/plcc/cmd/rep_test.py` | Fix broken parse/scan tests; add interpreter error test; rename tests |
| Modify | `src/plcc/cmd/scan.py` | Use `print_user_error()` (refactor, no behaviour change) |

---

## Task 1: Create `output.py` with `print_user_error()`

**Files:**

- Create: `src/plcc/cmd/output_test.py`
- Create: `src/plcc/cmd/output.py`

- [ ] **Step 1: Write the failing test**

Create `src/plcc/cmd/output_test.py`:

```python
from .output import print_user_error


def test_print_user_error_writes_to_stdout(capsys):
    print_user_error("scan error: bad token")
    out, err = capsys.readouterr()
    assert "scan error: bad token" in out
    assert err == ""


def test_print_user_error_does_not_write_to_stderr(capsys):
    print_user_error("any message")
    _, err = capsys.readouterr()
    assert err == ""
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && bin/test/units.bash src/plcc/cmd/output_test.py
```

Expected: FAIL — `ModuleNotFoundError` or `ImportError` (file doesn't exist yet).

- [ ] **Step 3: Create `src/plcc/cmd/output.py`**

```python
def print_user_error(message):
    print(message, flush=True)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && bin/test/units.bash src/plcc/cmd/output_test.py
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && git add src/plcc/cmd/output.py src/plcc/cmd/output_test.py
git commit -m "feat(cmd): add print_user_error helper to encode stdout intent"
```

---

## Task 2: Fix `print_parse_error()` in `pipeline.py`

**Files:**

- Modify: `src/plcc/cmd/pipeline_test.py` (lines 167–202)
- Modify: `src/plcc/cmd/pipeline.py` (line 1 import block, line 23)

- [ ] **Step 1: Update the 5 failing tests in `pipeline_test.py`**

Change each of the five `print_parse_error` tests: replace `_, err = capsys.readouterr()` with `out, _ = capsys.readouterr()` and replace `assert "..." in err` with `assert "..." in out`.

The five tests start at lines 167, 175, 183, 191, 198. After editing, they look like:

```python
def test_print_parse_error_shows_location(capsys):
    record = {"kind": "error", "message": "bad char",
              "source": {"file": "foo.txt", "line": 3, "column": 7}}
    print_parse_error(record, default_stage="plcc-test")
    out, _ = capsys.readouterr()
    assert "plcc-test: foo.txt:3:7: error: bad char" in out


def test_print_parse_error_normalises_stdin_to_dash(capsys):
    record = {"kind": "error", "message": "oops",
              "source": {"file": "-", "line": 1, "column": 1}}
    print_parse_error(record, default_stage="plcc-test")
    out, _ = capsys.readouterr()
    assert "plcc-test: -:1:1: error: oops" in out


def test_print_parse_error_shows_stage_and_location_together(capsys):
    record = {"kind": "error", "stage": "plcc-tokens", "message": "unrecognized character 'a'",
              "source": {"file": "-", "line": 1, "column": 1}}
    print_parse_error(record, default_stage="plcc-parse")
    out, _ = capsys.readouterr()
    assert "plcc-tokens: -:1:1: error: unrecognized character 'a'" in out


def test_print_parse_error_uses_stage_when_no_location(capsys):
    record = {"kind": "error", "message": "bad", "stage": "plcc-tokens"}
    print_parse_error(record, default_stage="plcc-test")
    out, _ = capsys.readouterr()
    assert "plcc-tokens: error: bad" in out


def test_print_parse_error_uses_default_stage_when_no_stage_and_no_location(capsys):
    record = {"kind": "error", "message": "bad"}
    print_parse_error(record, default_stage="plcc-test")
    out, _ = capsys.readouterr()
    assert "plcc-test: error: bad" in out
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && bin/test/units.bash src/plcc/cmd/pipeline_test.py
```

Expected: 5 FAIL — the 5 `print_parse_error` tests assert `out` but code still writes to stderr.

- [ ] **Step 3: Update `pipeline.py`**

Add the import and change the `print` call in `print_parse_error()`.

At the top of `src/plcc/cmd/pipeline.py`, add to the import block:

```python
from .output import print_user_error
```

Change line 23 (the final print in `print_parse_error`):

```python
def print_parse_error(record, default_stage):
    src = record.get("source", {})
    message = record.get("message", "error")
    stage = record.get("stage", default_stage)
    loc = location_str(src)
    prefix = f"{stage}: {loc}" if loc else stage
    print_user_error(f"{prefix}: error: {message}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && bin/test/units.bash src/plcc/cmd/pipeline_test.py
```

Expected: all tests pass (including the 5 updated ones).

- [ ] **Step 5: Commit**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && git add src/plcc/cmd/pipeline.py src/plcc/cmd/pipeline_test.py
git commit -m "fix(parse): route parse/scan errors to stdout via print_user_error"
```

---

## Task 3: Fix `rep.py` interpreter errors and update `rep_test.py`

After Task 2, `pipeline.py` now routes parse/scan errors to stdout. This breaks several
`rep_test.py` tests that still assert those errors on `err`. This task fixes those tests,
renames them to match the new stream, and also fixes the separate interpreter error branch
in `rep.py`.

**Files:**

- Modify: `src/plcc/cmd/rep_test.py`
- Modify: `src/plcc/cmd/rep.py`

- [ ] **Step 1: Update the broken parse/scan error tests in `rep_test.py`**

Six tests need their stream changed from `err` to `out`. Four also need renaming.

**Lines 177–183** — rename and update:

```python
def test_feed_suppresses_output_for_eof_error_when_trial(monkeypatch, handler, capsys):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_eof_error_record("expected PLUS"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"1+\n", "-", eof=False)
    out, _ = capsys.readouterr()
    assert out == ""
```

**Lines 186–192** — rename and update:

```python
def test_feed_shows_output_for_eof_error_when_force_submit(monkeypatch, handler, capsys):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_eof_error_record("expected PLUS"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"1+\n", "-", eof=True)
    out, _ = capsys.readouterr()
    assert "expected PLUS" in out
```

**Lines 246–252** — rename and update:

```python
def test_feed_error_shows_location_in_stdout(monkeypatch, handler, capsys):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_error_record_with_source("bad char", file="-", line=1, col=1))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"@\n", "-")
    out, _ = capsys.readouterr()
    assert "-:1:1" in out
```

**Lines 255–262** — update stream only:

```python
def test_feed_error_renders_file_line_col(monkeypatch, handler, capsys):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_error_record_with_source("bad", file="foo.txt", line=3, col=7))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"bad\n", "-")
    out, _ = capsys.readouterr()
    assert "foo.txt:3:7" in out
    assert "bad" in out
```

**Lines 265–271** — update stream only:

```python
def test_feed_error_with_no_location_shows_stage(monkeypatch, handler, capsys):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_error_record("bad char", stage="plcc-tokens"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"@\n", "-")
    out, _ = capsys.readouterr()
    assert "plcc-tokens: error: bad char" in out
```

**Lines 308–320** — update stream only:

```python
def test_feed_stops_at_first_error(monkeypatch, handler, capsys):
    # Two error records arrive. Only the first should be printed.
    h, _ = handler
    two_errors = (
        _error_record_with_source("first error", col=1) +
        _error_record_with_source("second error", col=2)
    )
    procs = iter([_proc(), _proc(stdout=two_errors)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"ab\n", "-")
    out, _ = capsys.readouterr()
    assert "first error" in out
    assert "second error" not in out
```

- [ ] **Step 2: Add a new test for the interpreter error branch**

The `_render_record()` function in `rep.py` handles output from the student's interpreter. Its `error` branch currently writes to stderr. Add a test that asserts it goes to stdout. Append this to `rep_test.py`:

```python
def test_render_record_interpreter_error_writes_to_stdout(capsys):
    record = {"kind": "error", "type": "TypeError", "message": "bad value"}
    _rep_module._render_record(record, "text")
    out, err = capsys.readouterr()
    assert "TypeError" in out
    assert "bad value" in out
    assert err == ""
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && bin/test/units.bash src/plcc/cmd/rep_test.py
```

Expected: the new `test_render_record_interpreter_error_writes_to_stdout` test FAILs (`err` contains the message, not `out`). The six updated parse/scan tests should now PASS (pipeline.py already routes to stdout).

- [ ] **Step 4: Update `rep.py`**

Add the import and change the error branch in `_render_record()`.

At the top of `src/plcc/cmd/rep.py`, add to the import block (alongside the existing `from .pipeline import ...` line):

```python
from .output import print_user_error
```

Change the `error` branch in `_render_record()` (currently line 187):

```python
def _render_record(record, verbose_format):
    if verbose_format == 'json':
        print(json.dumps(record))
        return
    if record['kind'] == 'result':
        value = record.get('value')
        if value is not None:
            print(value)
    elif record['kind'] == 'error':
        print_user_error(f"error: {record.get('type')}: {record.get('message')}")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && bin/test/units.bash src/plcc/cmd/rep_test.py
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && git add src/plcc/cmd/rep.py src/plcc/cmd/rep_test.py
git commit -m "fix(rep): route interpreter/semantic errors to stdout via print_user_error"
```

---

## Task 4: Update `scan.py` for consistency

`scan.py` already prints errors to stdout via a plain `print()`. This task replaces it with
`print_user_error()` to make the intent explicit. No behaviour change — existing tests pass
before and after.

**Files:**

- Modify: `src/plcc/cmd/scan.py`

- [ ] **Step 1: Run the scan tests to establish baseline**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && bin/test/units.bash src/plcc/cmd/scan_test.py
```

Expected: all tests pass.

- [ ] **Step 2: Update `scan.py`**

Add the import at the top of `src/plcc/cmd/scan.py`:

```python
from .output import print_user_error
```

In `_render_record()`, replace the error branch (currently `print(f"{loc}: error: {message}", flush=True)`):

```python
def _render_record(record, show_skips, show_line, show_attempts):
    kind = record.get("kind")

    if kind == "error":
        loc = _location_str(record.get("source", {}))
        message = record.get("message", "unrecognized character")
        print_user_error(f"{loc}: error: {message}")
        return
    # ... rest of function unchanged
```

Note: remove the `flush=True` from the error branch — `print_user_error` uses the default
(unbuffered when stdout is a TTY; line-buffered otherwise). The existing token/skip branches
keep their own `flush=True` calls — leave those unchanged.

- [ ] **Step 3: Run tests to verify they still pass**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && bin/test/units.bash src/plcc/cmd/scan_test.py
```

Expected: all tests pass (no behaviour change).

- [ ] **Step 4: Commit**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && git add src/plcc/cmd/scan.py
git commit -m "refactor(scan): use print_user_error for scan errors (intent, no behaviour change)"
```

---

## Task 5: Full test suite verification

- [ ] **Step 1: Run the full unit test suite**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && bin/test/units.bash
```

Expected: all tests pass.

- [ ] **Step 2: Run the command-level bats tests**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && bin/test/commands.bash
```

Expected: all tests pass. (No bats tests assert user-facing errors on `$stderr`, so no bats changes are needed.)

- [ ] **Step 3: Run the full functional suite**

```bash
cd /workspaces/plcc-ng/.worktrees/039 && bin/test/functional.bash
```

Expected: all tests pass.
