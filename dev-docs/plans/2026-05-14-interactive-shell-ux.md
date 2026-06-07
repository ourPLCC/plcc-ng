# Interactive Shell UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `^C` to exit the interactive shell (or clear a mistyped line) and make a blank line during continuation submit the accumulated input as EOF.

**Architecture:** Both changes live entirely in `SourceRunner._run_interactive` and a new `SourceRunner._evaluate` helper in `src/plcc/cmd/source_runner.py`. Input-phase `KeyboardInterrupt` is handled in the loop's own `try/except`; evaluation-phase `KeyboardInterrupt` is handled inside `_evaluate`. This keeps the two behaviors structurally isolated with no shared flag.

**Tech Stack:** Python 3, pytest. Tests use `monkeypatch` and custom fake stdin objects. Run tests with `bin/test/units.bash`.

---

### Task 1: Update existing ^C test — empty buffer should exit 130

The existing test `test_ctrl_c_clears_buffer_and_continues` raises `KeyboardInterrupt` when the buffer is empty and expects the loop to continue. The new behaviour is `sys.exit(130)`. Rename and update it to assert the exit.

**Files:**
- Modify: `src/plcc/cmd/source_runner_test.py`

- [ ] **Step 1: Replace the existing test**

In `src/plcc/cmd/source_runner_test.py`, find `test_ctrl_c_clears_buffer_and_continues` (near the bottom of the file) and replace it entirely with:

```python
def test_ctrl_c_with_empty_buffer_exits_130(monkeypatch, runner):
    class ImmediateInterrupt:
        isatty = lambda self: True

        @property
        def buffer(self):
            return self

        def readline(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(sys, "stdin", ImmediateInterrupt())
    with pytest.raises(SystemExit) as exc_info:
        runner.run(["-"], RecordingHandler())
    assert exc_info.value.code == 130
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_ctrl_c_with_empty_buffer_exits_130 -v
```

Expected: **FAIL** — current code does not call `sys.exit(130)`, it just resets and continues.

---

### Task 2: Add failing tests — ^C with buffer and ^C during evaluation

**Files:**
- Modify: `src/plcc/cmd/source_runner_test.py`

- [ ] **Step 1: Add test for ^C with a non-empty buffer**

Append after `test_ctrl_c_with_empty_buffer_exits_130`:

```python
def test_ctrl_c_with_buffer_clears_and_continues(monkeypatch, runner, capsys):
    class InterruptAfterLine:
        def __init__(self):
            self._calls = 0

        isatty = lambda self: True

        @property
        def buffer(self):
            return self

        def readline(self):
            self._calls += 1
            if self._calls == 1:
                return b"partial\n"   # builds the buffer
            if self._calls == 2:
                raise KeyboardInterrupt  # ^C with non-empty buffer
            if self._calls == 3:
                return b"hello\n"
            return b""

    monkeypatch.setattr(sys, "stdin", InterruptAfterLine())
    handler = RecordingHandler(results=[False, True])
    runner.run(["-"], handler)
    _, err = capsys.readouterr()
    assert "KeyboardInterrupt" in err
    # buffer was cleared by ^C; next feed sees only "hello\n"
    assert handler.calls[-1][0] == b"hello\n"
```

- [ ] **Step 2: Add test for ^C during handler.feed()**

Append after the previous test:

```python
def test_ctrl_c_during_evaluation_exits_130(monkeypatch, runner):
    class InterruptingHandler:
        def feed(self, content, source):
            raise KeyboardInterrupt

    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
    with pytest.raises(SystemExit) as exc_info:
        runner.run(["-"], InterruptingHandler())
    assert exc_info.value.code == 130
```

- [ ] **Step 3: Run both new tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_ctrl_c_with_buffer_clears_and_continues src/plcc/cmd/source_runner_test.py::test_ctrl_c_during_evaluation_exits_130 -v
```

Expected: **FAIL** — current code doesn't print "KeyboardInterrupt" and doesn't exit on evaluation interrupt.

---

### Task 3: Add failing test — blank line during continuation submits buffer with newline

**Files:**
- Modify: `src/plcc/cmd/source_runner_test.py`

- [ ] **Step 1: Add the test**

Append after `test_interactive_empty_line_on_fresh_prompt_does_not_call_feed`:

```python
def test_blank_line_during_continuation_submits_buffer_with_newline(monkeypatch, runner):
    # line1 returns False (continuation), blank line submits buffer + blank line
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"line1\n", b"\n", b""]))
    handler = RecordingHandler(results=[False, True])
    runner.run(["-"], handler)
    assert handler.calls[1][0] == b"line1\n\n"
```

- [ ] **Step 2: Run to confirm it fails**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_blank_line_during_continuation_submits_buffer_with_newline -v
```

Expected: **FAIL** — current code skips blank lines regardless of buffer state.

- [ ] **Step 3: Commit the three failing tests**

```bash
git add src/plcc/cmd/source_runner_test.py
git commit -m "test(source-runner): add failing tests for issues 013 and 014"
```

---

### Task 4: Implement new `_run_interactive` and `_evaluate`

**Files:**
- Modify: `src/plcc/cmd/source_runner.py`

- [ ] **Step 1: Replace `_run_interactive` and add `_evaluate`**

Open `src/plcc/cmd/source_runner.py`. Replace the existing `_run_interactive` method (lines 34–59) with the following two methods. Leave the rest of the file untouched.

```python
    def _run_interactive(self, handler):
        print(self._hint, file=sys.stderr)
        buffer = b""
        prompt = self._prompt
        while True:
            try:
                print(prompt, end="", flush=True, file=sys.stderr)
                line = sys.stdin.buffer.readline()
            except KeyboardInterrupt:
                print(file=sys.stderr)
                if buffer:
                    print("KeyboardInterrupt", file=sys.stderr)
                    buffer = b""
                    prompt = self._prompt
                else:
                    sys.exit(130)
                continue

            if not line:                          # ^D
                if buffer:
                    self._evaluate(handler, buffer)
                break
            elif not line.strip():                # blank line
                if buffer:
                    self._evaluate(handler, buffer + line)
                    buffer = b""
                    prompt = self._prompt
            else:                                 # normal line
                buffer += line
                if self._evaluate(handler, buffer):
                    buffer = b""
                    prompt = self._prompt
                else:
                    prompt = self._continuation

    def _evaluate(self, handler, content):
        try:
            return handler.feed(content, "-")
        except KeyboardInterrupt:
            print(file=sys.stderr)
            sys.exit(130)
```

- [ ] **Step 2: Run all source_runner tests**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py -v
```

Expected: **all PASS**.

- [ ] **Step 3: Run the full unit suite to check for regressions**

```bash
bin/test/units.bash
```

Expected: **all PASS**.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/cmd/source_runner.py
git commit -m "fix(source-runner): ^C exits or clears buffer; blank line submits continuation"
```

---

### Task 5: Run command-level tests

The interactive path is exercised by `plcc-scan`, `plcc-parse`, and `plcc-rep`. Run their bats suites to catch any regressions.

**Files:** none changed — verification only.

- [ ] **Step 1: Run the commands test suite**

```bash
bin/test/commands.bash
```

Expected: **all PASS**.

- [ ] **Step 2: If all pass, close out**

No further action needed. If any test fails, investigate before proceeding — do not skip.
