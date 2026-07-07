# ^C Always Exits in Interactive Mode (issue #119) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `^C` always exit with code 130 in the interactive REPL loop, regardless of whether there is buffered input.

**Architecture:** `SourceRunner._clear_buffer_or_exit` currently branches on buffer state; we collapse both branches to `sys.exit(130)` and rename the method to `_handle_interrupt` to reflect its new, singular purpose. The call site in `_process_line` is updated to match.

**Tech Stack:** Python, pytest

## Global Constraints

- Run unit tests with: `bin/test/units.bash`
- Commit messages must follow the existing style (imperative subject, no period, ≤ 72 chars)
- Docs-only commits: add `[skip ci]` to the subject line (not applicable here — this is code)

---

### Task 1: Replace the buffer-clearing ^C path with immediate exit

**Files:**
- Modify: `src/plcc/cmd/source_runner.py`
- Test: `src/plcc/cmd/source_runner_test.py`

**Interfaces:**
- Produces: `SourceRunner._handle_interrupt(self)` — prints a newline to stderr and calls `sys.exit(130)`
- Produces: `SourceRunner._process_line` calls `self._handle_interrupt()` instead of `self._clear_buffer_or_exit(state)`

- [ ] **Step 1: Replace the existing ^C-with-buffer test with the correct assertion**

Open `src/plcc/cmd/source_runner_test.py`. Find `test_ctrl_c_with_buffer_clears_and_continues` (around line 213). Replace the entire function with:

```python
def test_ctrl_c_with_buffer_exits_130(monkeypatch, runner):
    class InterruptAfterLine:
        def __init__(self):
            self._calls = 0

        isatty = lambda self: True

        @property
        def buffer(self):
            return self

        def read1(self, n=-1):
            self._calls += 1
            if self._calls == 1:
                return b"partial\n"   # builds the buffer
            raise KeyboardInterrupt   # ^C with non-empty buffer

    monkeypatch.setattr(sys, "stdin", InterruptAfterLine())
    handler = RecordingHandler(results=[b"partial\n"])
    with pytest.raises(SystemExit) as exc_info:
        runner.run(["-"], handler)
    assert exc_info.value.code == 130
```

- [ ] **Step 2: Run the new test to verify it fails**

```
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_ctrl_c_with_buffer_exits_130
```

Expected: FAIL — the test exits 130 but the current code does not exit when the buffer is non-empty; it returns an `_InteractiveState`. The test runner will see `SystemExit` not raised.

- [ ] **Step 3: Update `source_runner.py` — rename method and remove the branch**

Open `src/plcc/cmd/source_runner.py`.

Replace:
```python
    def _clear_buffer_or_exit(self, state):
        print(file=sys.stderr)
        if state.buffer:
            print("KeyboardInterrupt", file=sys.stderr)
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        sys.exit(130)
```

With:
```python
    def _handle_interrupt(self):
        print(file=sys.stderr)
        sys.exit(130)
```

Then update the call site in `_process_line`. Replace:
```python
        if line is None:
            return self._clear_buffer_or_exit(state)
```

With:
```python
        if line is None:
            self._handle_interrupt()
```

- [ ] **Step 4: Run the full unit suite to verify everything passes**

```
bin/test/units.bash
```

Expected: all tests pass, 0 failures. The new test `test_ctrl_c_with_buffer_exits_130` passes. The old `test_ctrl_c_with_empty_buffer_exits_130` still passes unchanged.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
git commit -m "fix: ^C always exits 130 in interactive mode, even in continuation (#119)"
```
