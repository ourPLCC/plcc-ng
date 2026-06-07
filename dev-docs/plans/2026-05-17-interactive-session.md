# Interactive Session Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix three interactive-mode bugs — whitespace-only lines dropped (016), no diagnostic on premature EOF (024), first line not tried before entering continuation (025) — and rename the `$` token sentinel to `eof` as the enabling cross-cut.

**Architecture:** The `$` → `eof` rename threads through the token emitter, the parser, and the two handler classes. Issues 024 and 025 add an `eof` flag to `feed()` so that `ParseHandler` can distinguish "trial" from "force-submit" and suppress or surface the incomplete-input error accordingly. Issue 016 is a narrower `_is_blank` predicate fix.

**Tech Stack:** Python 3, pytest, `bin/test/units.bash` for the TDD inner loop, `bin/test/commands.bash` and `bin/test/integration.bash` for final verification.

---

## File map

| File | Change |
|---|---|
| `src/plcc/tokens/tokens_cli.py` | Emit `"eof"` sentinel instead of `"$"` |
| `src/plcc/tokens/tokens_cli_sentinel_test.py` | Update `"$"` → `"eof"` assertions and test names |
| `src/plcc/parser/predictive_parser.py` | Rename internal SENTINEL; `ParseError` gains `found`; remove `"$"` special cases |
| `src/plcc/parser/predictive_parser_test.py` | Add tests for `found` field |
| `src/plcc/parser/table_cli.py` | Update loop guard; add `found` to error records |
| `src/plcc/parser/table_cli_test.py` | Update `_sentinel()` helper; add `found: "eof"` test |
| `src/plcc/cmd/scan.py` | Update sentinel filter; `feed()` gains `eof` param (ignored) |
| `src/plcc/cmd/parse.py` | `feed()` gains `eof`; return `False` for eof-only errors when trial |
| `src/plcc/cmd/parse_test.py` | Add tests for eof-aware `feed()` logic |
| `src/plcc/cmd/source_runner.py` | Fix `_is_blank`; fix `_accumulate_only`; add `_attempt_first_line`; pass `eof` in `_evaluate` |
| `src/plcc/cmd/source_runner_test.py` | Update `RecordingHandler`; update broken tests; add trial-mode tests |

---

## Task 1: Rename the `$` sentinel to `eof` in `tokens_cli`

**Files:**
- Modify: `src/plcc/tokens/tokens_cli.py:65`
- Modify: `src/plcc/tokens/tokens_cli_sentinel_test.py`

- [ ] **Step 1: Run failing baseline — confirm existing sentinel tests pass before any change**

```bash
bin/test/units.bash src/plcc/tokens/tokens_cli_sentinel_test.py -v
```
Expected: all three tests PASS (baseline).

- [ ] **Step 2: Update tests to expect `"eof"` — they fail now**

In `src/plcc/tokens/tokens_cli_sentinel_test.py`, replace the three test bodies:

```python
def test_tokens_emits_eof_sentinel_at_eof(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
    run_main(['/spec.json'])
    out, _ = capsys.readouterr()
    records = [json.loads(l) for l in out.strip().splitlines() if l]
    last = records[-1]
    assert last["kind"] == "token"
    assert last["name"] == "eof"
    assert last["lexeme"] == ""


def test_tokens_eof_sentinel_has_source(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
    run_main(['/spec.json'])
    out, _ = capsys.readouterr()
    records = [json.loads(l) for l in out.strip().splitlines() if l]
    last = records[-1]
    assert "source" in last


def test_tokens_eof_sentinel_on_empty_input(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO(''))
    run_main(['/spec.json'])
    out, _ = capsys.readouterr()
    records = [json.loads(l) for l in out.strip().splitlines() if l]
    assert len(records) == 1
    assert records[0]["name"] == "eof"
```

- [ ] **Step 3: Run — confirm the three sentinel tests FAIL**

```bash
bin/test/units.bash src/plcc/tokens/tokens_cli_sentinel_test.py -v
```
Expected: FAIL with `AssertionError: assert '$' == 'eof'`.

- [ ] **Step 4: Update `tokens_cli.py` to emit `"eof"`**

In `src/plcc/tokens/tokens_cli.py` line 65, change:
```python
    print(json.dumps({"kind": "token", "name": "$", "lexeme": "", "source": last_source}), flush=True)
```
to:
```python
    print(json.dumps({"kind": "token", "name": "eof", "lexeme": "", "source": last_source}), flush=True)
```

- [ ] **Step 5: Run — confirm the three sentinel tests PASS**

```bash
bin/test/units.bash src/plcc/tokens/tokens_cli_sentinel_test.py -v
```
Expected: all three PASS.

- [ ] **Step 6: Run all units to surface any other breakage**

```bash
bin/test/units.bash
```
Expected: failures in `table_cli_test.py` (uses `_sentinel()` with `"$"`) and `scan.py` filter — those are fixed in Tasks 2 and 3.

- [ ] **Step 7: Commit**

```bash
git -C .worktrees/interactive-session add src/plcc/tokens/tokens_cli.py src/plcc/tokens/tokens_cli_sentinel_test.py
git -C .worktrees/interactive-session commit -m "feat(tokens): emit 'eof' sentinel instead of '\$' [skip ci]"
```

---

## Task 2: Update `table_cli` loop guard and `scan` filter

**Files:**
- Modify: `src/plcc/parser/table_cli.py:74`
- Modify: `src/plcc/parser/table_cli_test.py:189-191`
- Modify: `src/plcc/cmd/scan.py:113`

- [ ] **Step 1: Update `_sentinel()` helper in `table_cli_test.py`**

In `src/plcc/parser/table_cli_test.py` line 191, change:
```python
def _sentinel(line=1, col=1, file="-"):
    return {"kind": "token", "name": "$", "lexeme": "",
            "source": {"file": file, "line": line, "column": col}}
```
to:
```python
def _sentinel(line=1, col=1, file="-"):
    return {"kind": "token", "name": "eof", "lexeme": "",
            "source": {"file": file, "line": line, "column": col}}
```

- [ ] **Step 2: Run `table_cli_test.py` — confirm failures resolve**

```bash
bin/test/units.bash src/plcc/parser/table_cli_test.py -v
```
Expected: some tests that pass `_sentinel()` to the parser may now fail because `table_cli.py` still checks `!= "$"`.

- [ ] **Step 3: Update loop guard in `table_cli.py`**

In `src/plcc/parser/table_cli.py` line 74, change:
```python
    while cursor < len(tokens) and tokens[cursor]["name"] != "$":
```
to:
```python
    while cursor < len(tokens) and tokens[cursor]["name"] != "eof":
```

- [ ] **Step 4: Update sentinel filter in `scan.py`**

In `src/plcc/cmd/scan.py` line 113, change:
```python
            if record.get("name") == "$":
```
to:
```python
            if record.get("name") == "eof":
```

- [ ] **Step 5: Run all units — confirm no new failures**

```bash
bin/test/units.bash
```
Expected: PASS for `table_cli_test.py` and any scan-related tests. Any remaining failures should only be in `predictive_parser_test.py` related to `found` (not yet added).

- [ ] **Step 6: Commit**

```bash
git -C .worktrees/interactive-session add \
    src/plcc/parser/table_cli.py \
    src/plcc/parser/table_cli_test.py \
    src/plcc/cmd/scan.py
git -C .worktrees/interactive-session commit -m "fix(parser,scan): update sentinel guard and filter from '\$' to 'eof' [skip ci]"
```

---

## Task 3: Add `found` to `ParseError` and remove `"$"` special cases

**Files:**
- Modify: `src/plcc/parser/predictive_parser.py`
- Modify: `src/plcc/parser/predictive_parser_test.py`

The `predictive_parser.py` currently has two special-case branches for `"$"`:
1. `expect()` at line 73: `if tok["name"] == "$":` — raises a different message.
2. `_parse_regular()` at line 102: `if lookahead == "$":` — raises a different message.

After this task: both branches are removed. All `ParseError` raises pass `found=tok["name"]` (or `found=lookahead`). Because `"eof"` is a real token, no special-casing is needed.

- [ ] **Step 1: Write failing tests for the `found` field**

Add to the end of `src/plcc/parser/predictive_parser_test.py`:

```python
def test_parse_error_found_is_set_for_wrong_terminal():
    with pytest.raises(ParseError) as exc_info:
        parse(_TRIVIAL_LL1, [_tok("PLUS", "+")])
    assert exc_info.value.found == "PLUS"


def test_parse_error_found_is_eof_for_premature_end_of_input():
    # Grammar: program → NUM PLUS NUM; tokens: [NUM] — hits EOF before PLUS
    with pytest.raises(ParseError) as exc_info:
        parse(_ADDITION_LL1, [_tok("NUM", "1")])
    assert exc_info.value.found == "eof"


def test_parse_error_found_is_none_by_default():
    e = ParseError("something went wrong")
    assert e.found is None
```

- [ ] **Step 2: Run — confirm new tests FAIL**

```bash
bin/test/units.bash src/plcc/parser/predictive_parser_test.py -v -k "test_parse_error_found"
```
Expected: FAIL with `AttributeError: 'ParseError' object has no attribute 'found'`.

- [ ] **Step 3: Update `ParseError` and all raise sites in `predictive_parser.py`**

Replace the entire `ParseError` class and update `expect()` and `_parse_regular()` in `src/plcc/parser/predictive_parser.py`:

```python
class ParseError(Exception):
    def __init__(self, message, source=None, found=None):
        super().__init__(message)
        self.source = source or {}
        self.found = found
```

Replace `expect()` (lines 70-82):
```python
    def expect(sym):
        tok = current()
        if tok["name"] != sym:
            raise ParseError(
                f"expected {sym!r}, got {tok['name']!r}",
                source=tok["source"],
                found=tok["name"],
            )
        return advance()
```

Replace the `production is None` block in `_parse_regular()` (lines 101-110):
```python
        if production is None:
            raise ParseError(
                f"unexpected {lookahead!r}, no production for {sym!r}",
                source=current()["source"],
                found=lookahead,
            )
```

Also rename the internal sentinel on line 60:
```python
    SENTINEL = {"name": "eof", "lexeme": "", "source": {"file": "", "line": 0, "column": 0}}
```

- [ ] **Step 4: Run — confirm new tests PASS**

```bash
bin/test/units.bash src/plcc/parser/predictive_parser_test.py -v
```
Expected: all PASS including the three new `found` tests.

- [ ] **Step 5: Run all units**

```bash
bin/test/units.bash
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git -C .worktrees/interactive-session add \
    src/plcc/parser/predictive_parser.py \
    src/plcc/parser/predictive_parser_test.py
git -C .worktrees/interactive-session commit -m "fix(parser): add found field to ParseError; remove \$ special cases [skip ci]"
```

---

## Task 4: Add `found` to error records in `table_cli`

**Files:**
- Modify: `src/plcc/parser/table_cli.py:95-104`
- Modify: `src/plcc/parser/table_cli_test.py`

- [ ] **Step 1: Write a failing test for `found: "eof"` in incomplete-input error records**

Add to the end of `src/plcc/parser/table_cli_test.py`:

```python
def test_incomplete_input_error_record_has_found_eof(capsys, monkeypatch):
    # Grammar: program → NUM PLUS NUM; tokens: [NUM, eof] — incomplete input
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_ADDITION_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        tokens = [_tok("NUM", "1"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        err_records = [r for r in records if r.get("kind") == "error"]
        assert len(err_records) >= 1
        assert err_records[0].get("found") == "eof"
    finally:
        os.unlink(ll1_file.name)
```

- [ ] **Step 2: Run — confirm new test FAILS**

```bash
bin/test/units.bash src/plcc/parser/table_cli_test.py::test_incomplete_input_error_record_has_found_eof -v
```
Expected: FAIL with `AssertionError: assert None == 'eof'`.

- [ ] **Step 3: Update the `ParseError` handler in `table_cli.py`**

In `src/plcc/parser/table_cli.py`, find the `except ParseError as e:` block (lines 95-104) and replace:

```python
        except ParseError as e:
            record = {
                "kind": "error",
                "message": str(e),
                "stage": "plcc-parser-table",
                "source": e.source,
            }
            if e.found:
                record["found"] = e.found
            verbose.emit_error(e.source, str(e))
            print(json.dumps(record), flush=True)
            cursor += 1
```

Also update the `not attempted` branch's `except ParseError as e:` block (lines 113-120):

```python
        except ParseError as e:
            record = {
                "kind": "error",
                "message": str(e),
                "stage": "plcc-parser-table",
                "source": e.source,
            }
            if e.found:
                record["found"] = e.found
            print(json.dumps(record), flush=True)
```

- [ ] **Step 4: Run — confirm the new test PASSES**

```bash
bin/test/units.bash src/plcc/parser/table_cli_test.py -v
```
Expected: all PASS.

- [ ] **Step 5: Run all units**

```bash
bin/test/units.bash
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git -C .worktrees/interactive-session add \
    src/plcc/parser/table_cli.py \
    src/plcc/parser/table_cli_test.py
git -C .worktrees/interactive-session commit -m "fix(parser): add found field to parse error records in table_cli [skip ci]"
```

---

## Task 5: `ParseHandler.feed` gains `eof` flag; `ScanHandler.feed` gains `eof` (ignored)

**Files:**
- Modify: `src/plcc/cmd/parse.py`
- Modify: `src/plcc/cmd/scan.py`
- Modify: `src/plcc/cmd/parse_test.py`

**Logic for `ParseHandler.feed(content, source, eof=False)`:**

1. Collect all JSONL records from the pipeline output.
2. If no records → return `False`.
3. Classify: `any_tree`, `any_genuine_error` (kind==error, found≠"eof"), `only_eof_errors` (no tree, no genuine error).
4. If `only_eof_errors` and `eof=False` → return `False` (trial: don't show incomplete-input error).
5. Otherwise → print all records to stdout/stderr as before → return `True`.

- [ ] **Step 1: Add a helper and new tests to `parse_test.py`**

Add a helper and tests to the end of `src/plcc/cmd/parse_test.py`:

```python
def _eof_error_record(msg="unexpected end of input: expected 'PLUS'",
                      stage="plcc-parser-table", line=1, col=1):
    return json.dumps({
        "kind": "error", "message": msg, "stage": stage,
        "found": "eof",
        "source": {"file": "-", "line": line, "column": col},
    }).encode() + b"\n"


def test_feed_returns_false_for_eof_only_error_when_trial(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_eof_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert handler.feed(b"1+\n", "-", eof=False) is False


def test_feed_returns_true_for_eof_only_error_when_force_submit(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_eof_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert handler.feed(b"1+\n", "-", eof=True) is True


def test_feed_suppresses_stderr_for_eof_error_when_trial(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_eof_error_record("expected PLUS"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"1+\n", "-", eof=False)
    _, err = capsys.readouterr()
    assert err == ""


def test_feed_shows_stderr_for_eof_error_when_force_submit(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_eof_error_record("expected PLUS"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"1+\n", "-", eof=True)
    _, err = capsys.readouterr()
    assert "expected PLUS" in err


def test_feed_returns_true_for_genuine_error_regardless_of_eof_param(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_error_record("bad token"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    # _error_record has no "found" field → genuine error → always True
    assert handler.feed(b"@\n", "-", eof=False) is True
```

- [ ] **Step 2: Run — confirm new tests FAIL**

```bash
bin/test/units.bash src/plcc/cmd/parse_test.py -v -k "eof"
```
Expected: FAIL (`TypeError: feed() got an unexpected keyword argument 'eof'` or similar).

- [ ] **Step 3: Rewrite `ParseHandler.feed` in `parse.py`**

Replace the `feed` method in `src/plcc/cmd/parse.py`:

```python
    def feed(self, content, source, eof=False):
        tokens_proc = subprocess.Popen(
            ["plcc-tokens", self._spec_path, "-"] + self._child_flags,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
        )
        tree_proc = subprocess.Popen(
            ["plcc-trees", f"--ll1={self._ll1_path}"] + self._child_flags,
            stdin=tokens_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=None,
        )
        tokens_proc.stdout.close()
        tokens_proc.stdin.write(content)
        tokens_proc.stdin.close()
        tree_out, _ = tree_proc.communicate()
        tokens_proc.wait()

        records = []
        for raw in tree_out.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            records.append(json.loads(raw))

        if not records:
            return False

        any_tree = any(r.get("kind") == "tree" for r in records)
        any_genuine_error = any(
            r.get("kind") == "error" and r.get("found") != "eof"
            for r in records
        )
        only_eof_errors = not any_tree and not any_genuine_error

        if only_eof_errors and not eof:
            return False

        for record in records:
            if record.get("kind") == "error":
                src = record.get("source", {})
                message = record.get("message", "error")
                loc = _location_str(src)
                if loc:
                    print(f"{loc}: error: {message}", file=sys.stderr)
                else:
                    stage = record.get("stage", "plcc-parse")
                    print(f"{stage}: error: {message}", file=sys.stderr)
                self.had_error = True
            elif record.get("kind") == "tree":
                _print_tree(record, indent=0)

        return True
```

Also add `eof=False` to `ScanHandler.feed` in `src/plcc/cmd/scan.py`:

```python
    def feed(self, content, source, eof=False):
```
(No other changes — `eof` is accepted but ignored; `ScanHandler` always returns `True`.)

- [ ] **Step 4: Run — confirm all `parse_test.py` tests PASS**

```bash
bin/test/units.bash src/plcc/cmd/parse_test.py -v
```
Expected: all PASS (existing tests unaffected because error records without `found` field are classified as genuine errors).

- [ ] **Step 5: Run all units**

```bash
bin/test/units.bash
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git -C .worktrees/interactive-session add \
    src/plcc/cmd/parse.py \
    src/plcc/cmd/scan.py \
    src/plcc/cmd/parse_test.py
git -C .worktrees/interactive-session commit -m "fix(parse,scan): feed() gains eof flag; ParseHandler returns False for eof-only errors on trial [skip ci]"
```

---

## Task 6: Fix Issue 016 — whitespace-only lines silently dropped

**Files:**
- Modify: `src/plcc/cmd/source_runner.py:89-96`
- Modify: `src/plcc/cmd/source_runner_test.py`

Current `_is_blank` returns `True` for any line whose `.strip()` is empty, including `b"  \n"`. Fix: only a bare newline is blank.

Current `_accumulate_only` drops whitespace-only buffers. Fix: always accumulate.

- [ ] **Step 1: Write a failing test for `_is_blank` and accumulation**

In `src/plcc/cmd/source_runner_test.py`, locate `test_is_blank_true_for_spaces_and_newline` (line 269) and change it:

```python
def test_is_blank_false_for_whitespace_only_line(runner):
    assert runner._is_blank(b"  \n") is False
```

Also add a new test after `test_eof_mode_blank_line_accumulates_without_feed`:

```python
def test_eof_mode_whitespace_only_line_accumulates(monkeypatch):
    # whitespace-only line is not blank — it accumulates in EOF mode
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"  \n", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"  \n"
```

Note: this test references `_eof_runner()` with a handler that has `eof` param (updated in Task 7). For now the test may error on the `feed()` signature mismatch — that's expected and fixed in Task 7. Skip running this new test until Task 7 by running only the `_is_blank` test in Step 2.

- [ ] **Step 2: Run — confirm `_is_blank` test FAILS**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_is_blank_false_for_whitespace_only_line -v
```
Expected: FAIL with `assert True is False`.

- [ ] **Step 3: Fix `_is_blank` in `source_runner.py`**

In `src/plcc/cmd/source_runner.py`, change `_is_blank` (line 89-90):

```python
    def _is_blank(self, line):
        return line == b"\n"
```

- [ ] **Step 4: Fix `_accumulate_only` in `source_runner.py`**

In `src/plcc/cmd/source_runner.py`, replace `_accumulate_only` (lines 92-96):

```python
    def _accumulate_only(self, line, state):
        buffer = state.buffer + line
        return _InteractiveState(buffer=buffer, prompt=self._continuation)
```

- [ ] **Step 5: Run — confirm `_is_blank` test PASSES**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_is_blank_false_for_whitespace_only_line -v
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git -C .worktrees/interactive-session add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
git -C .worktrees/interactive-session commit -m "fix(source-runner): whitespace-only lines are not blank; _accumulate_only always accumulates (016) [skip ci]"
```

---

## Task 7: Issue 025 — `_attempt_first_line`: try first line before continuation

**Files:**
- Modify: `src/plcc/cmd/source_runner.py`
- Modify: `src/plcc/cmd/source_runner_test.py`

**New behavior for `SubmitOn.EOF` at `>>>` (empty buffer):**
- Blank line → skip (no feed).
- Non-blank line → trial: `feed(line, eof=False)`.
  - Returns `True` → complete; stay at `>>>`.
  - Returns `False` → incomplete; enter `...` continuation.

**Lines while in `...` (non-empty buffer):** unchanged — always `_accumulate_only`.

- [ ] **Step 1: Update `RecordingHandler` to accept `eof` kwarg**

In `src/plcc/cmd/source_runner_test.py`, update the `RecordingHandler.feed` signature:

```python
class RecordingHandler:
    """Captures feed() calls for assertions."""
    def __init__(self, results=None):
        self._results = iter(results or [])
        self.calls = []

    def feed(self, content, source, eof=False):
        self.calls.append((content, source))
        try:
            return next(self._results)
        except StopIteration:
            return True
```

- [ ] **Step 2: Write new tests for trial-mode behavior**

Add at the end of `src/plcc/cmd/source_runner_test.py`:

```python
def test_eof_mode_first_line_calls_feed_immediately(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\n"


def test_eof_mode_trial_succeeds_resets_to_prompt(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    _, err = capsys.readouterr()
    assert err.count(">>> ") >= 1
    assert "... " not in err


def test_eof_mode_trial_fails_enters_continuation(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
    handler = RecordingHandler(results=[False, True])
    _eof_runner().run(["-"], handler)
    _, err = capsys.readouterr()
    assert "... " in err


def test_eof_mode_blank_first_line_is_skipped(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"\n", b""]))
    handler = RecordingHandler()
    _eof_runner().run(["-"], handler)
    assert handler.calls == []


def test_eof_mode_second_line_accumulates_not_retried(monkeypatch):
    # first line → trial fails → continuation; second line accumulates (not retried)
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world\n", b""]))
    handler = RecordingHandler(results=[False, True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 2
    assert handler.calls[0][0] == b"hello\n"
    assert handler.calls[1][0] == b"hello\nworld\n"
```

- [ ] **Step 3: Run — confirm new tests FAIL**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py -v -k "test_eof_mode_first_line or test_eof_mode_trial or test_eof_mode_blank_first or test_eof_mode_second"
```
Expected: FAIL (old code never calls feed on the first line in EOF mode).

- [ ] **Step 4: Add `_attempt_first_line` and update `_process_line` and `_evaluate` in `source_runner.py`**

Replace `_process_line` (lines 66-78):

```python
    def _process_line(self, handler, line, state):
        if self._is_interrupted(line):
            return self._clear_buffer_or_exit(state)
        if self._is_eof(line):
            return self._exit_or_submit_accumulated_buffer(handler, state)
        if self._is_partial_eof(line):
            return self._force_submit_including_partial_line(handler, line, state)
        if self._submit_on == SubmitOn.EOF:
            if not state.buffer:
                return self._attempt_first_line(handler, line, state)
            return self._accumulate_only(line, state)
        # SubmitOn.EOL
        if self._is_blank(line):
            return self._force_submit_accumulated_buffer(handler, line, state)
        return self._accumulate_and_evaluate(handler, line, state)
```

Add `_attempt_first_line` after `_accumulate_only`:

```python
    def _attempt_first_line(self, handler, line, state):
        if self._is_blank(line):
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        if self._evaluate(handler, line, eof=False):
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        return _InteractiveState(buffer=line, prompt=self._continuation)
```

Update `_evaluate` (line 129):

```python
    def _evaluate(self, handler, content, eof=False):
        try:
            result = handler.feed(content, "-", eof=eof)
        except KeyboardInterrupt:
            print(file=sys.stderr)
            sys.exit(130)
        if eof and result is False:
            print("PLCC internal error: forced submission was not accepted by the handler.", file=sys.stderr)
            sys.exit(1)
        return result
```

- [ ] **Step 5: Run — confirm new tests PASS**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py -v -k "test_eof_mode_first_line or test_eof_mode_trial or test_eof_mode_blank_first or test_eof_mode_second"
```
Expected: all PASS.

- [ ] **Step 6: Update tests whose behavior changed**

Four existing tests break because the old code accumulated without calling `feed`; the new code trials the first line. Update them:

Replace `test_eof_mode_ctrl_d_with_buffer_calls_feed` (tests that ^D submits accumulated buffer):
```python
def test_eof_mode_ctrl_d_with_buffer_calls_feed(monkeypatch):
    # first line trial fails → continuation; second line accumulates; ^D force-submits
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world\n", b""]))
    handler = RecordingHandler(results=[False, True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 2
    assert handler.calls[0][0] == b"hello\n"
    assert handler.calls[1][0] == b"hello\nworld\n"
```

Replace `test_eof_mode_blank_line_accumulates_without_feed` (blank line behavior now depends on buffer state):
```python
def test_eof_mode_blank_line_accumulates_during_continuation(monkeypatch):
    # first line trial fails → continuation; blank line accumulates; ^D submits all
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"\n", b""]))
    handler = RecordingHandler(results=[False, True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 2
    assert handler.calls[0][0] == b"hello\n"
    assert handler.calls[1][0] == b"hello\n\n"
```

Replace `test_eof_mode_continuation_prompt_shown_after_first_line` (continuation prompt requires trial to return False):
```python
def test_eof_mode_continuation_prompt_shown_after_failed_trial(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
    handler = RecordingHandler(results=[False, True])
    _eof_runner().run(["-"], handler)
    _, err = capsys.readouterr()
    assert "... " in err
```

Replace `test_eof_mode_partial_eof_submits_partial_line` (partial EOF during continuation):
```python
def test_eof_mode_partial_eof_force_submits_buffer_plus_partial(monkeypatch):
    # first line trial fails → continuation; partial-EOF force-submits buffer + partial text
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world", b""]))
    handler = RecordingHandler(results=[False, True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 2
    assert handler.calls[0][0] == b"hello\n"
    assert handler.calls[1][0] == b"hello\nworld"
```

- [ ] **Step 7: Run all source_runner tests**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py -v
```
Expected: all PASS.

- [ ] **Step 8: Run all units**

```bash
bin/test/units.bash
```
Expected: all PASS.

- [ ] **Step 9: Commit**

```bash
git -C .worktrees/interactive-session add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
git -C .worktrees/interactive-session commit -m "feat(source-runner): trial first line before entering continuation mode (025) [skip ci]"
```

---

## Task 8: Verify with command and integration tests

- [ ] **Step 1: Run command-level bats tests**

```bash
bin/test/commands.bash
```
Expected: PASS. If any test checks for `$` in token output, update the bats test to expect `eof`.

- [ ] **Step 2: Run integration tests**

```bash
bin/test/integration.bash
```
Expected: PASS. Any `"$"` sentinel references in integration bats would need to be updated to `"eof"`.

- [ ] **Step 3: Commit any bats fixes, then tag the branch as ready**

```bash
git -C .worktrees/interactive-session log --oneline -8
```

Review the commit log. If everything looks clean, the branch is ready for PR.
