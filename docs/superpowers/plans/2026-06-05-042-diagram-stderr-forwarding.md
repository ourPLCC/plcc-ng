# 042 Diagram Orchestrator stderr Forwarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring `plcc-diagram`'s stderr forwarding in line with every other orchestrator in the codebase by replacing four raw `sys.stderr.buffer.write()` calls with `VerboseContext.parse_child_events` + `reformat_child_events`.

**Architecture:** One file changes (`src/plcc/cmd/diagram.py`): swap `child_flags()` for `child_flags_for_orchestrator(min_level=0)` and replace each raw binary write with the decode → parse → reformat pattern already used by `make.py`, `parse.py`, and `rep.py`.

**Tech Stack:** Python, pytest, existing `VerboseContext` API in `src/plcc/verbose.py`.

---

### Task 1: Test — plain-text child stderr is forwarded

**Files:**
- Modify: `src/plcc/cmd/diagram_test.py`

The four subprocess stubs in the existing tests all return `m.stderr = b''`. Add three new tests for the stderr-forwarding behaviour. Start with the simplest: plain-text (non-JSON) bytes from a child should appear on `sys.stderr`.

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/cmd/diagram_test.py`:

```python
def test_make_plain_text_stderr_forwarded(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 1
        m.stderr = b'plcc-make: something went wrong\n'
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main(['--no-banner'])

    _, err = capsys.readouterr()
    assert 'plcc-make: something went wrong' in err
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
cd /workspaces/plcc-ng/.worktrees/042-diagram-stderr-forwarding
python -m pytest src/plcc/cmd/diagram_test.py::test_make_plain_text_stderr_forwarded -v
```

Expected: FAIL — the raw buffer write doesn't go through capsys's stderr capture.

- [ ] **Step 3: Commit the failing test**

```bash
git add src/plcc/cmd/diagram_test.py
git commit -m "test(diagram): add failing test for plain-text stderr forwarding"
```

---

### Task 2: Implement — replace child_flags and all four raw writes

**Files:**
- Modify: `src/plcc/cmd/diagram.py`

Replace the one `child_flags` assignment and all four `sys.stderr.buffer.write()` blocks.

- [ ] **Step 1: Replace `child_flags` (line 62)**

Change:
```python
child_flags = verbose.child_flags()
```
To:
```python
child_flags = verbose.child_flags_for_orchestrator(min_level=0)
```

- [ ] **Step 2: Replace the `make_result` stderr write (lines 70–71)**

Change:
```python
    if make_result.stderr:
        sys.stderr.buffer.write(make_result.stderr)
```
To:
```python
    events = verbose.parse_child_events(make_result.stderr.decode('utf-8', errors='replace'))
    verbose.reformat_child_events(events)
```

- [ ] **Step 3: Replace the `emit_result` stderr write (lines 90–91)**

Change:
```python
    if emit_result.stderr:
        sys.stderr.buffer.write(emit_result.stderr)
```
To:
```python
    events = verbose.parse_child_events(emit_result.stderr.decode('utf-8', errors='replace'))
    verbose.reformat_child_events(events)
```

- [ ] **Step 4: Replace the `build_result` stderr write (lines 101–102)**

Change:
```python
    if build_result.stderr:
        sys.stderr.buffer.write(build_result.stderr)
```
To:
```python
    events = verbose.parse_child_events(build_result.stderr.decode('utf-8', errors='replace'))
    verbose.reformat_child_events(events)
```

- [ ] **Step 5: Replace the `run_result` stderr write (lines 110–111)**

Change:
```python
    if run_result.stderr:
        sys.stderr.buffer.write(run_result.stderr)
```
To:
```python
    events = verbose.parse_child_events(run_result.stderr.decode('utf-8', errors='replace'))
    verbose.reformat_child_events(events)
```

- [ ] **Step 6: Run the failing test from Task 1 — it should pass now**

```bash
python -m pytest src/plcc/cmd/diagram_test.py::test_make_plain_text_stderr_forwarded -v
```

Expected: PASS

- [ ] **Step 7: Run the full diagram test file to confirm no regressions**

```bash
python -m pytest src/plcc/cmd/diagram_test.py -v
```

Expected: all tests PASS

- [ ] **Step 8: Commit**

```bash
git add src/plcc/cmd/diagram.py
git commit -m "refactor(diagram): use VerboseContext parse/reformat for child stderr"
```

---

### Task 3: Test — JSONL events are reformatted through the parent's verbose context

**Files:**
- Modify: `src/plcc/cmd/diagram_test.py`

When `-v --verbose-format=text` is active, a JSONL event from a child should be
rendered as `stage: event: message` text, not as a raw JSON string.

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/cmd/diagram_test.py`:

```python
import json

def test_make_jsonl_stderr_reformatted_as_text(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    event = json.dumps({
        "stage": "plcc-make",
        "time": 0,
        "event": "started",
        "message": "building"
    })

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 1
        m.stderr = (event + '\n').encode()
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main(['-v', '--verbose-format=text', '--no-banner'])

    _, err = capsys.readouterr()
    assert 'plcc-make: started: building' in err
    assert event not in err  # raw JSON must NOT appear
```

- [ ] **Step 2: Run to confirm it passes (implementation already done in Task 2)**

```bash
python -m pytest src/plcc/cmd/diagram_test.py::test_make_jsonl_stderr_reformatted_as_text -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/plcc/cmd/diagram_test.py
git commit -m "test(diagram): verify JSONL child events are reformatted as text"
```

---

### Task 4: Test — empty child stderr produces no output

**Files:**
- Modify: `src/plcc/cmd/diagram_test.py`

`parse_child_events('')` is a no-op; confirm nothing is written to stderr when a child
produces no output.

- [ ] **Step 1: Write the test**

Add to `src/plcc/cmd/diagram_test.py`:

```python
def test_empty_child_stderr_produces_no_output(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 1
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main(['--no-banner'])

    _, err = capsys.readouterr()
    assert err == ''
```

- [ ] **Step 2: Run to confirm it passes**

```bash
python -m pytest src/plcc/cmd/diagram_test.py::test_empty_child_stderr_produces_no_output -v
```

Expected: PASS

- [ ] **Step 3: Run the full test suite**

```bash
bin/test/python.bash
```

Expected: all tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/plcc/cmd/diagram_test.py
git commit -m "test(diagram): verify empty child stderr produces no output"
```
