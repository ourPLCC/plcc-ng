# plcc-scan Multi-Line Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Switch `plcc-scan` from `SubmitOn.EOL` to `SubmitOn.EOF` so that block tokens spanning multiple lines work in interactive mode.

**Architecture:** One functional change in `scan.py` (swap `SubmitOn.EOL` for `SubmitOn.EOF`), one comment update in `source_runner.py`, and one new test in `scan_test.py`. No other files change.

**Tech Stack:** Python, pytest, `plcc.cmd.scan`, `plcc.cmd.source_runner`

---

### Task 1: Test that `main()` uses `SubmitOn.EOF`

**Files:**
- Modify: `src/plcc/cmd/scan_test.py`

- [ ] **Step 1: Write the failing test**

Open `src/plcc/cmd/scan_test.py`. After the existing imports add `SubmitOn` to the import line if it isn't there — the file already imports from `.scan`, so add a second import:

```python
from .source_runner import SubmitOn
```

Then add this test at the end of the file:

```python
def test_main_uses_eof_submit_mode(monkeypatch, tmp_path, capsys):
    build = tmp_path / "build"
    build.mkdir()
    (build / ".grammar").write_text(str(tmp_path / "grammar.plcc"))
    captured = {}
    def fake_runner(**kw):
        captured.update(kw)
        return type("R", (), {"run": lambda self, s, h: True})()
    monkeypatch.setattr(_scan_module, "SourceRunner", fake_runner)
    monkeypatch.setattr("plcc.cmd.scan.get_version", lambda: "0")
    run_main([])
    assert captured.get("submit_on") == SubmitOn.EOF
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /workspaces/plcc-ng/.worktrees/issue-063
python -m pytest src/plcc/cmd/scan_test.py::test_main_uses_eof_submit_mode -v
```

Expected: FAIL — `assert SubmitOn.EOL == SubmitOn.EOF`

### Task 2: Switch `scan.py` to `SubmitOn.EOF`

**Files:**
- Modify: `src/plcc/cmd/scan.py:168`

- [ ] **Step 1: Change `SubmitOn.EOL` to `SubmitOn.EOF`**

In `src/plcc/cmd/scan.py`, find line 168:

```python
    runner = SourceRunner(submit_on=SubmitOn.EOL)
```

Change it to:

```python
    runner = SourceRunner(submit_on=SubmitOn.EOF)
```

- [ ] **Step 2: Run the new test to verify it passes**

```bash
cd /workspaces/plcc-ng/.worktrees/issue-063
python -m pytest src/plcc/cmd/scan_test.py::test_main_uses_eof_submit_mode -v
```

Expected: PASS

- [ ] **Step 3: Run the full scan test suite**

```bash
cd /workspaces/plcc-ng/.worktrees/issue-063
python -m pytest src/plcc/cmd/scan_test.py -v
```

Expected: all tests pass

### Task 3: Update stale comment in `source_runner.py`

**Files:**
- Modify: `src/plcc/cmd/source_runner.py:11`

- [ ] **Step 1: Remove the `— plcc-scan` annotation**

In `src/plcc/cmd/source_runner.py`, find line 11:

```python
    EOL = "eol"   # each newline submits — plcc-scan
```

Change it to:

```python
    EOL = "eol"   # each newline submits
```

- [ ] **Step 2: Run the full test suite**

```bash
cd /workspaces/plcc-ng/.worktrees/issue-063
python -m pytest -q
```

Expected: same pass/fail counts as baseline (950 passing, 3 pre-existing failures in `make_test.py`)

### Task 4: Commit

- [ ] **Step 1: Commit all changes**

```bash
cd /workspaces/plcc-ng/.worktrees/issue-063
git add src/plcc/cmd/scan.py src/plcc/cmd/source_runner.py src/plcc/cmd/scan_test.py
git commit -m "feat(scan): switch to EOF submit mode for multi-line block token support

Fixes issue 063. plcc-scan now accumulates interactive input until ^D
before submitting to plcc-tokens, matching plcc-parse and plcc-rep.
Block tokens/skips that span multiple lines now work end-to-end.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```
