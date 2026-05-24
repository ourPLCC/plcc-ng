# First-Error-Only for plcc-parse and plcc-rep — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `plcc-parser-table` to pass all lex errors through, and make `ParseHandler` and `RepHandler` stop at the first error.

**Architecture:** Three targeted changes: `table_cli.py` emits every lex error record immediately (instead of keeping only the last), then `ParseHandler.feed()` and `RepHandler.feed()` each break after the first error record they encounter.

**Tech Stack:** Python, pytest (`bin/test/units.bash`)

---

> **Worktree:** All work goes in `.worktrees/first-error-wins` on branch `feat/first-error-wins`.
> Commands that operate on files run from inside the worktree. Git commands use `-C .worktrees/first-error-wins` or are run from that directory.
> The spec is at `docs/superpowers/specs/2026-05-24-first-error-wins-design.md`.

---

## File map

| File | Change |
|---|---|
| `src/plcc/parser/table_cli.py` | Replace `error_record` accumulation with immediate emit + boolean flag |
| `src/plcc/parser/table_cli_test.py` | Add two tests for all-lex-errors passthrough |
| `src/plcc/cmd/parse.py` | `break` after first error in `ParseHandler.feed()` |
| `src/plcc/cmd/parse_test.py` | Add one test: two errors → only first shown |
| `src/plcc/cmd/rep.py` | `break` after first error in `RepHandler.feed()` |
| `src/plcc/cmd/rep_test.py` | Add one test: two errors → only first shown |

---

## Task 1: All lex errors pass through `plcc-parser-table`

**Files:**
- Modify: `src/plcc/parser/table_cli_test.py`
- Modify: `src/plcc/parser/table_cli.py`

- [ ] **Step 1: Write two failing tests in `table_cli_test.py`**

Add these two tests at the end of `src/plcc/parser/table_cli_test.py`:

```python
def test_two_lex_errors_both_pass_through(capsys, monkeypatch):
    # Input: two lex error records (like 'ab' where both chars are unrecognized).
    # Before fix: only the last error (col 2) appears in output.
    # After fix: both errors appear, in order.
    err1 = {"kind": "error", "stage": "plcc-tokens",
            "message": "unrecognized character 'a'",
            "source": {"file": "-", "line": 1, "column": 1}}
    err2 = {"kind": "error", "stage": "plcc-tokens",
            "message": "unrecognized character 'b'",
            "source": {"file": "-", "line": 1, "column": 2}}
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        stdin_data = json.dumps(err1) + "\n" + json.dumps(err2) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        errors = [r for r in records if r.get("kind") == "error"]
        assert len(errors) == 2
        assert errors[0]["source"]["column"] == 1
        assert errors[1]["source"]["column"] == 2
    finally:
        os.unlink(ll1_file.name)


def test_first_lex_error_comes_first_in_output(capsys, monkeypatch):
    # The first unrecognized character must be the first error record emitted.
    err1 = {"kind": "error", "stage": "plcc-tokens",
            "message": "unrecognized character 'a'",
            "source": {"file": "-", "line": 1, "column": 1}}
    err2 = {"kind": "error", "stage": "plcc-tokens",
            "message": "unrecognized character 'b'",
            "source": {"file": "-", "line": 1, "column": 2}}
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        stdin_data = json.dumps(err1) + "\n" + json.dumps(err2) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        errors = [r for r in records if r.get("kind") == "error"]
        assert len(errors) >= 1
        assert errors[0]["source"]["column"] == 1
    finally:
        os.unlink(ll1_file.name)
```

- [ ] **Step 2: Run the new tests and confirm they fail**

```bash
bin/test/units.bash src/plcc/parser/table_cli_test.py::test_two_lex_errors_both_pass_through src/plcc/parser/table_cli_test.py::test_first_lex_error_comes_first_in_output -v
```

Expected: both FAIL — currently only one error (the last) is emitted.

- [ ] **Step 3: Fix `table_cli.py` — emit each lex error immediately**

In `src/plcc/parser/table_cli.py`, replace the `error_record` accumulation block.

Find this code (around line 52–70):

```python
    # Read all records from stdin; pass error records through unchanged.
    tokens = []
    error_record = None
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as e:
            verbose.emit_error({}, f"malformed token JSON: {e}")
            sys.exit(1)
        if record.get("kind") == "error":
            error_record = record
        else:
            tokens.append(record)

    if error_record is not None:
        print(json.dumps(error_record))
        sys.exit(0)
```

Replace with:

```python
    # Read all records from stdin; pass lex error records through immediately.
    tokens = []
    has_lex_error = False
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as e:
            verbose.emit_error({}, f"malformed token JSON: {e}")
            sys.exit(1)
        if record.get("kind") == "error":
            print(json.dumps(record), flush=True)
            has_lex_error = True
        else:
            tokens.append(record)

    if has_lex_error:
        sys.exit(0)
```

- [ ] **Step 4: Run the new tests and confirm they pass**

```bash
bin/test/units.bash src/plcc/parser/table_cli_test.py::test_two_lex_errors_both_pass_through src/plcc/parser/table_cli_test.py::test_first_lex_error_comes_first_in_output -v
```

Expected: both PASS.

- [ ] **Step 5: Run the full `table_cli_test.py` suite**

```bash
bin/test/units.bash src/plcc/parser/table_cli_test.py -v
```

Expected: all tests PASS. The existing `test_error_record_passes_through` test passes because one error still passes through.

- [ ] **Step 6: Commit**

```bash
git -C .worktrees/first-error-wins add src/plcc/parser/table_cli.py src/plcc/parser/table_cli_test.py
git -C .worktrees/first-error-wins commit -m "$(cat <<'EOF'
fix(parser): pass all lex errors through plcc-parser-table

Previously only the last lex error record was retained and emitted;
earlier errors were silently overwritten. Now all lex error records
are emitted immediately as they arrive.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: `ParseHandler` stops at the first error

**Files:**
- Modify: `src/plcc/cmd/parse_test.py`
- Modify: `src/plcc/cmd/parse.py`

- [ ] **Step 1: Write a failing test in `parse_test.py`**

Add this test at the end of `src/plcc/cmd/parse_test.py`:

```python
def test_feed_stops_at_first_error(monkeypatch, handler, capsys):
    # Two error records arrive (e.g. two lex errors from 'ab').
    # Only the first should be printed; the second is silently dropped.
    two_errors = (
        _error_record_with_source("first error", col=1) +
        _error_record_with_source("second error", col=2)
    )
    procs = iter([_proc(), _proc(stdout=two_errors)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"ab\n", "-")
    _, err = capsys.readouterr()
    assert "first error" in err
    assert "second error" not in err
```

- [ ] **Step 2: Run the new test and confirm it fails**

```bash
bin/test/units.bash src/plcc/cmd/parse_test.py::test_feed_stops_at_first_error -v
```

Expected: FAIL — currently both errors are printed.

- [ ] **Step 3: Add `break` to `ParseHandler.feed()` in `parse.py`**

In `src/plcc/cmd/parse.py`, find `ParseHandler.feed()`:

```python
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

Replace with:

```python
    def feed(self, content, source, eof=False):
        items = self._pipeline.run(content, eof)
        if items is None:
            return False
        for record, _ in items:
            if record.get("kind") == "error":
                print_parse_error(record, default_stage="plcc-parse")
                self.had_error = True
                break
            elif record.get("kind") == "tree":
                _print_tree(record, indent=0)
        return True
```

- [ ] **Step 4: Run the new test and confirm it passes**

```bash
bin/test/units.bash src/plcc/cmd/parse_test.py::test_feed_stops_at_first_error -v
```

Expected: PASS.

- [ ] **Step 5: Run the full `parse_test.py` suite**

```bash
bin/test/units.bash src/plcc/cmd/parse_test.py -v
```

Expected: all tests PASS. In particular, `test_feed_mixed_tree_and_error_renders_both` still passes because the tree arrives before the error and is rendered before the `break` fires.

- [ ] **Step 6: Commit**

```bash
git -C .worktrees/first-error-wins add src/plcc/cmd/parse.py src/plcc/cmd/parse_test.py
git -C .worktrees/first-error-wins commit -m "$(cat <<'EOF'
fix(parse): stop at first error in ParseHandler.feed()

Multiple error records (e.g. from several lex errors) are now
truncated to the first — students see one clear error to fix.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `RepHandler` stops at the first error

**Files:**
- Modify: `src/plcc/cmd/rep_test.py`
- Modify: `src/plcc/cmd/rep.py`

- [ ] **Step 1: Write a failing test in `rep_test.py`**

Add this test in `src/plcc/cmd/rep_test.py`, after the existing error-location tests:

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
    _, err = capsys.readouterr()
    assert "first error" in err
    assert "second error" not in err
```

- [ ] **Step 2: Run the new test and confirm it fails**

```bash
bin/test/units.bash src/plcc/cmd/rep_test.py::test_feed_stops_at_first_error -v
```

Expected: FAIL — currently both errors are printed.

- [ ] **Step 3: Add `break` to `RepHandler.feed()` in `rep.py`**

In `src/plcc/cmd/rep.py`, find `RepHandler.feed()`:

```python
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
                _read_response(self._interpreter.stdout, self._interpreter, self._verbose_format)
        return True
```

Replace with:

```python
    def feed(self, content, source, eof=False):
        items = self._pipeline.run(content, eof)
        if items is None:
            return False
        for record, raw in items:
            if record.get("kind") == "error":
                print_parse_error(record, default_stage="plcc-rep")
                break
            elif record.get("kind") == "tree":
                try:
                    self._interpreter.stdin.write(raw + b'\n')
                    self._interpreter.stdin.flush()
                except BrokenPipeError:
                    print('plcc-rep: interpreter exited unexpectedly', file=sys.stderr)
                    sys.exit(1)
                _read_response(self._interpreter.stdout, self._interpreter, self._verbose_format)
        return True
```

- [ ] **Step 4: Run the new test and confirm it passes**

```bash
bin/test/units.bash src/plcc/cmd/rep_test.py::test_feed_stops_at_first_error -v
```

Expected: PASS.

- [ ] **Step 5: Run the full `rep_test.py` suite**

```bash
bin/test/units.bash src/plcc/cmd/rep_test.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Run the full unit suite**

```bash
bin/test/units.bash
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git -C .worktrees/first-error-wins add src/plcc/cmd/rep.py src/plcc/cmd/rep_test.py
git -C .worktrees/first-error-wins commit -m "$(cat <<'EOF'
fix(rep): stop at first error in RepHandler.feed()

Mirrors the ParseHandler change: multiple error records are truncated
to the first so the interactive prompt shows one clear error to fix.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```
