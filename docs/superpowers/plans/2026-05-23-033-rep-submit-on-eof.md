# 033 — plcc-rep switch to SubmitOn.EOF Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Switch `plcc-rep` interactive input from EOL mode (Enter submits) to EOF mode (^D submits), matching `plcc-parse`.

**Architecture:** One line changes in `rep.py`. A new test in `rep_test.py` captures the `SubmitOn` argument passed to `SourceRunner` during `main()` to lock in the intended mode. All existing tests pass unchanged because they use pipe (non-interactive) mode, which is unaffected by `SubmitOn`.

**Tech Stack:** Python, pytest, `plcc.cmd.rep`, `plcc.cmd.source_runner`

---

## Task 1: Change `plcc-rep` to use `SubmitOn.EOF`

**Files:**

- Modify: `src/plcc/cmd/rep.py:120`
- Modify: `src/plcc/cmd/rep_test.py`

- [ ] **Step 1: Confirm the baseline tests pass**

Run from the worktree root (`.worktrees/feat/rep-submit-on-eof/`):

```bash
bin/test/units.bash src/plcc/cmd/rep_test.py
```

Expected: all tests pass.

- [ ] **Step 2: Write a failing test**

Add this test to `src/plcc/cmd/rep_test.py` (after the existing imports and before the first test):

```python
import json as _json
from unittest.mock import MagicMock as _MagicMock
import plcc.cmd.rep as _rep_module


def test_main_uses_eof_submit_mode(monkeypatch, tmp_path):
    """plcc-rep interactive mode must submit on ^D, not Enter (SubmitOn.EOF)."""
    monkeypatch.chdir(tmp_path)
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("")
    build = tmp_path / "build"
    build.mkdir()
    spec = {"semantics": [{"tool": "calc", "language": "python"}]}
    (build / "spec.json").write_text(_json.dumps(spec))
    (build / "ll1.json").write_text("{}")

    captured = {}

    def capturing_runner(submit_on, **kwargs):
        captured["submit_on"] = submit_on
        m = _MagicMock()
        m.run.return_value = True
        return m

    monkeypatch.setattr(_rep_module, "SourceRunner", capturing_runner)
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: _MagicMock(returncode=0, stderr=b""),
    )
    monkeypatch.setattr(
        "subprocess.Popen",
        lambda *a, **kw: _MagicMock(stdin=_MagicMock(), wait=_MagicMock()),
    )

    _rep_module.main(["--grammar-file=grammar.plcc", "--tool=calc"])

    from .source_runner import SubmitOn
    assert captured["submit_on"] is SubmitOn.EOF
```

- [ ] **Step 3: Run the test to confirm it fails**

```bash
bin/test/units.bash src/plcc/cmd/rep_test.py::test_main_uses_eof_submit_mode -v
```

Expected: FAIL — `assert captured["submit_on"] is SubmitOn.EOF` fails because the current value is `SubmitOn.EOL`.

- [ ] **Step 4: Make the one-line change**

In `src/plcc/cmd/rep.py`, line 120, change:

```python
runner = SourceRunner(submit_on=SubmitOn.EOL)
```

to:

```python
runner = SourceRunner(submit_on=SubmitOn.EOF)
```

- [ ] **Step 5: Run the new test to confirm it passes**

```bash
bin/test/units.bash src/plcc/cmd/rep_test.py::test_main_uses_eof_submit_mode -v
```

Expected: PASS.

- [ ] **Step 6: Run the full unit suite**

```bash
bin/test/units.bash
```

Expected: all tests pass.

- [ ] **Step 7: Run commands and e2e tests**

```bash
bin/test/commands.bash && bin/test/e2e.bash
```

Expected: all tests pass. (These tests all use pipe/file mode, which is unaffected by `SubmitOn`.)

- [ ] **Step 8: Commit**

```bash
git add src/plcc/cmd/rep.py src/plcc/cmd/rep_test.py
git commit -m "feat(rep): switch to SubmitOn.EOF — ^D submits, Enter accumulates"
```
