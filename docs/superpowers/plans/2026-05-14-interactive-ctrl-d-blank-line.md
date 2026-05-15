# Interactive ^D and blank-line fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix three bugs in `SourceRunner._run_interactive` (^D missing newline, ^D in continuation exits instead of submitting, blank-line submission silently discards) and refactor the method to a clean single-responsibility architecture.

**Architecture:** Five line types (interrupted, eof, partial-eof, blank, normal) are classified by predicate methods and dispatched to dedicated handler methods. Loop state is carried in an `_InteractiveState` dataclass. Each handler returns a new state rather than mutating variables in place.

**Tech Stack:** Python 3, pytest (`bin/test/units.bash`), dataclasses

**Working directory:** All work happens inside the worktree at `.worktrees/fix-interactive-ctrl-d-blank-line/` (relative to the repo root). `cd` there before starting. File paths in this plan are relative to that directory. Git commands should be run from inside the worktree (no `-C` flag needed).

---

### Task 1: Add `_InteractiveState` dataclass and predicate methods

**Files:**
- Modify: `src/plcc/cmd/source_runner.py`
- Modify: `src/plcc/cmd/source_runner_test.py`

- [ ] **Step 1: Write failing tests for `_InteractiveState` and the four predicates**

Add to `src/plcc/cmd/source_runner_test.py`. Update the existing import line:

```python
from .source_runner import SourceRunner, _InteractiveState
```

Then add this block at the end of the file:

```python
# --- _InteractiveState ---

def test_interactive_state_stores_buffer_and_prompt():
    state = _InteractiveState(buffer=b"hello", prompt=">>> ")
    assert state.buffer == b"hello"
    assert state.prompt == ">>> "
    assert state.done is False


def test_interactive_state_done_flag():
    state = _InteractiveState(buffer=b"", prompt=">>> ", done=True)
    assert state.done is True


# --- Predicate methods ---

def test_is_eof_true_for_empty_bytes(runner):
    assert runner._is_eof(b"") is True


def test_is_eof_false_for_nonempty(runner):
    assert runner._is_eof(b"hello\n") is False


def test_is_partial_eof_true_for_line_without_newline(runner):
    assert runner._is_partial_eof(b"partial") is True


def test_is_partial_eof_false_for_line_with_newline(runner):
    assert runner._is_partial_eof(b"complete\n") is False


def test_is_blank_true_for_newline_only(runner):
    assert runner._is_blank(b"\n") is True


def test_is_blank_true_for_spaces_and_newline(runner):
    assert runner._is_blank(b"  \n") is True


def test_is_blank_false_for_content_line(runner):
    assert runner._is_blank(b"hello\n") is False


def test_is_interrupted_true_for_none(runner):
    assert runner._is_interrupted(None) is True


def test_is_interrupted_false_for_bytes(runner):
    assert runner._is_interrupted(b"") is False
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py -v
```

Expected: failures with `ImportError` on `_InteractiveState` and `AttributeError` on the predicate methods.

- [ ] **Step 3: Add `_InteractiveState` and predicate methods to `source_runner.py`**

Add the import at the top of `src/plcc/cmd/source_runner.py`:

```python
import sys
from dataclasses import dataclass
```

Add the dataclass before the `SourceRunner` class:

```python
@dataclass
class _InteractiveState:
    buffer: bytes
    prompt: str
    done: bool = False
```

Add these methods to the `SourceRunner` class (after `_evaluate`):

```python
def _is_interrupted(self, line):
    return line is None

def _is_eof(self, line):
    return not line

def _is_partial_eof(self, line):
    return not line.endswith(b"\n")

def _is_blank(self, line):
    return not line.strip()
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
git commit -m "refactor(source-runner): add _InteractiveState and predicate methods"
```

---

### Task 2: Fix 018 — ^D exit prints a newline

**Files:**
- Modify: `src/plcc/cmd/source_runner.py` (one line in `_run_interactive`)
- Modify: `src/plcc/cmd/source_runner_test.py`

- [ ] **Step 1: Write a failing test**

Add to `src/plcc/cmd/source_runner_test.py`:

```python
def test_ctrl_d_on_fresh_prompt_prints_newline(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b""]))
    runner.run(["-"], RecordingHandler())
    _, err = capsys.readouterr()
    # Prompt is ">>> " (no newline); ^D should add one so the shell lands on a new line
    assert err.endswith(">>> \n")
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_ctrl_d_on_fresh_prompt_prints_newline -v
```

Expected: FAIL — `err` ends with `">>> "` (no trailing newline).

- [ ] **Step 3: Add `print(file=sys.stderr)` in the `if not line:` branch**

In `_run_interactive`, change:

```python
        if not line:                          # ^D
            if buffer:
                self._evaluate(handler, buffer)
            break
```

to:

```python
        if not line:                          # ^D
            print(file=sys.stderr)
            if buffer:
                self._evaluate(handler, buffer)
            break
```

- [ ] **Step 4: Run all tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
git commit -m "fix(source-runner): ^D exit prints newline before returning to shell (018)"
```

---

### Task 3: Fix 020a — ^D in continuation submits buffer instead of exiting

**Files:**
- Modify: `src/plcc/cmd/source_runner.py`
- Modify: `src/plcc/cmd/source_runner_test.py`

- [ ] **Step 1: Write a failing test**

Add to `src/plcc/cmd/source_runner_test.py`:

```python
def test_ctrl_d_in_continuation_submits_and_continues(monkeypatch, runner):
    # Setup: line1 fails (continuation), then ^D on empty "..." → should submit and
    # continue (not exit), then line2 succeeds, then final ^D exits.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"", b"world\n", b""]))
    handler = RecordingHandler(results=[False, True, True])
    runner.run(["-"], handler)
    # With fix: ^D in continuation submits buffer and loops — "world\n" is processed.
    # Without fix: ^D exits immediately after submitting — "world\n" is never read.
    assert len(handler.calls) == 3
    assert handler.calls[2][0] == b"world\n"
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_ctrl_d_in_continuation_submits_and_continues -v
```

Expected: FAIL — `len(handler.calls)` is 2, not 3 (loop exits after ^D).

- [ ] **Step 3: Update the `if not line:` branch to distinguish continuation from fresh prompt**

Change:

```python
        if not line:                          # ^D
            print(file=sys.stderr)
            if buffer:
                self._evaluate(handler, buffer)
            break
```

to:

```python
        if not line:                          # ^D
            print(file=sys.stderr)
            if buffer:
                self._evaluate(handler, buffer)
                buffer = b""
                prompt = self._prompt
            else:
                break
```

- [ ] **Step 4: Run all tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
git commit -m "fix(source-runner): ^D in continuation submits buffer instead of exiting (020)"
```

---

### Task 4: Fix 020b — ^D after partial text force-submits

**Files:**
- Modify: `src/plcc/cmd/source_runner.py`
- Modify: `src/plcc/cmd/source_runner_test.py`

**Background:** When the user presses ^D after typing text (without Enter), the terminal flushes the partial bytes to the process without a trailing `\n`. `readline()` returns the partial content as a bytes object with no newline. Currently this is treated as a normal line and stays in continuation if evaluation fails. The fix: detect the missing newline and force-submit.

- [ ] **Step 1: Write a failing test**

Add to `src/plcc/cmd/source_runner_test.py`:

```python
def test_ctrl_d_after_partial_text_force_submits(monkeypatch, runner):
    # "hello\n" fails → continuation.
    # "world" (no \n, simulates ^D after text) → should force-submit buffer+"world".
    # Without fix: "world" treated as normal line; evaluate fails; then ^D (020a fix)
    #   submits the same buffer again — 3 calls total.
    # With fix: "world" detected as partial-eof, force-submitted — 2 calls total.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world", b""]))
    handler = RecordingHandler(results=[False, False])
    runner.run(["-"], handler)
    assert len(handler.calls) == 2
    assert handler.calls[1][0] == b"hello\nworld"
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_ctrl_d_after_partial_text_force_submits -v
```

Expected: FAIL — `len(handler.calls)` is 3, not 2.

- [ ] **Step 3: Add the partial-eof branch in `_run_interactive`**

In `_run_interactive`, after the `if not line:` block and before the `elif not line.strip():` block, add:

```python
        elif not line.endswith(b"\n"):        # ^D after partial text
            print(file=sys.stderr)
            buffer += line
            self._evaluate(handler, buffer)
            buffer = b""
            prompt = self._prompt
```

The full `_run_interactive` should now read:

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

        if not line:                          # ^D on empty line
            print(file=sys.stderr)
            if buffer:
                self._evaluate(handler, buffer)
                buffer = b""
                prompt = self._prompt
            else:
                break
        elif not line.endswith(b"\n"):        # ^D after partial text
            print(file=sys.stderr)
            buffer += line
            self._evaluate(handler, buffer)
            buffer = b""
            prompt = self._prompt
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
```

- [ ] **Step 4: Run all tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
git commit -m "fix(source-runner): ^D after partial text force-submits buffer (020)"
```

---

### Task 5: Refactor to clean architecture (fixes 021)

All three bugs are now fixed. This task refactors `_run_interactive` into the designed clean architecture: `_InteractiveState`-returning handler methods, `_process_line` dispatch, and `_read_line`/`_print_hint` helpers. Issue 021 is fixed by passing `eof=True` to `_evaluate` on all three force-submit paths; `_evaluate` exits with a PLCC internal error if the handler returns `False` on a forced submission.

**Note:** The original plan said "no behavior changes" for this task and treated 021 as documentation-only. That was revised during implementation: the force-submit paths now check the handler's return value and exit with an error rather than silently discarding input.

**Files:**
- Modify: `src/plcc/cmd/source_runner.py` (full replacement of `_run_interactive` and addition of handler methods)
- Modify: `src/plcc/cmd/source_runner_test.py` (add 021 tests)

- [ ] **Step 1: Add 021 tests**

Add to `src/plcc/cmd/source_runner_test.py`:

```python
def test_blank_line_submission_resets_to_fresh_prompt_when_evaluate_succeeds(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"\n", b""]))
    handler = RecordingHandler(results=[False, True])
    runner.run(["-"], handler)
    _, err = capsys.readouterr()
    assert err.count(">>> ") >= 2


def test_blank_line_force_submit_exits_with_error_when_handler_rejects(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"\n"]))
    handler = RecordingHandler(results=[False, False])
    with pytest.raises(SystemExit) as exc_info:
        runner.run(["-"], handler)
    assert exc_info.value.code == 1
    _, err = capsys.readouterr()
    assert "PLCC internal error" in err


def test_ctrl_d_in_continuation_force_submit_exits_with_error_when_handler_rejects(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
    handler = RecordingHandler(results=[False, False])
    with pytest.raises(SystemExit) as exc_info:
        runner.run(["-"], handler)
    assert exc_info.value.code == 1
    _, err = capsys.readouterr()
    assert "PLCC internal error" in err


def test_partial_eof_force_submit_exits_with_error_when_handler_rejects(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world"]))
    handler = RecordingHandler(results=[False, False])
    with pytest.raises(SystemExit) as exc_info:
        runner.run(["-"], handler)
    assert exc_info.value.code == 1
    _, err = capsys.readouterr()
    assert "PLCC internal error" in err
```

- [ ] **Step 2: Run new tests**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py -v
```

Expected: all pass. The first test verifies the prompt resets on a successful force-submit. The other three verify that a handler returning `False` on a forced submission produces a PLCC internal error and exits.

- [ ] **Step 3: Replace `source_runner.py` with the full clean implementation**

Replace the entire contents of `src/plcc/cmd/source_runner.py` with:

```python
import sys
from dataclasses import dataclass

HINT = "Enter input. Press ^D (EOF) when done."
PROMPT = ">>> "
CONTINUATION = "... "


@dataclass
class _InteractiveState:
    buffer: bytes
    prompt: str
    done: bool = False


class SourceRunner:
    def __init__(self, hint=HINT, prompt=PROMPT, continuation=CONTINUATION):
        self._hint = hint
        self._prompt = prompt
        self._continuation = continuation

    def run(self, sources, handler):
        """Run handler over sources. Returns False if any non-interactive feed
        signalled incomplete input (handler returned False); True otherwise."""
        effective = sources if sources else ["-"]
        completed = True
        for source in effective:
            if source == "-":
                if sys.stdin.isatty():
                    self._run_interactive(handler)
                else:
                    content = sys.stdin.buffer.read()
                    if handler.feed(content, "-") is False:
                        completed = False
            else:
                with open(source, "rb") as f:
                    content = f.read()
                if handler.feed(content, source) is False:
                    completed = False
        return completed

    def _run_interactive(self, handler):
        self._print_hint()
        state = _InteractiveState(buffer=b"", prompt=self._prompt)
        while not state.done:
            line = self._read_line(state.prompt)
            state = self._process_line(handler, line, state)

    def _print_hint(self):
        print(self._hint, file=sys.stderr)

    def _read_line(self, prompt):
        print(prompt, end="", flush=True, file=sys.stderr)
        try:
            return sys.stdin.buffer.readline()
        except KeyboardInterrupt:
            return None

    def _process_line(self, handler, line, state):
        if self._is_interrupted(line):
            return self._clear_buffer_or_exit(state)
        if self._is_eof(line):
            return self._exit_or_submit_accumulated_buffer(handler, state)
        if self._is_partial_eof(line):
            return self._force_submit_including_partial_line(handler, line, state)
        if self._is_blank(line):
            return self._force_submit_accumulated_buffer(handler, line, state)
        return self._accumulate_and_evaluate(handler, line, state)

    def _is_interrupted(self, line):
        return line is None

    def _is_eof(self, line):
        return not line

    def _is_partial_eof(self, line):
        return not line.endswith(b"\n")

    def _is_blank(self, line):
        return not line.strip()

    def _clear_buffer_or_exit(self, state):
        print(file=sys.stderr)
        if state.buffer:
            print("KeyboardInterrupt", file=sys.stderr)
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        sys.exit(130)

    def _exit_or_submit_accumulated_buffer(self, handler, state):
        print(file=sys.stderr)
        if state.buffer:
            self._evaluate(handler, state.buffer)
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        return _InteractiveState(buffer=b"", prompt=self._prompt, done=True)

    def _force_submit_including_partial_line(self, handler, line, state):
        print(file=sys.stderr)
        self._evaluate(handler, state.buffer + line)
        return _InteractiveState(buffer=b"", prompt=self._prompt)

    def _force_submit_accumulated_buffer(self, handler, line, state):
        if state.buffer:
            self._evaluate(handler, state.buffer + line)
        return _InteractiveState(buffer=b"", prompt=self._prompt)

    def _accumulate_and_evaluate(self, handler, line, state):
        buffer = state.buffer + line
        if self._evaluate(handler, buffer):
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        return _InteractiveState(buffer=buffer, prompt=self._continuation)

    def _evaluate(self, handler, content):
        try:
            return handler.feed(content, "-")
        except KeyboardInterrupt:
            print(file=sys.stderr)
            sys.exit(130)
```

- [ ] **Step 4: Run all unit tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
git commit -m "refactor(source-runner): extract _process_line and handler methods; make 021 force-submit explicit"
```

---

### Task 6: Run commands tests

- [ ] **Step 1: Run the commands test suite**

```bash
bin/test/commands.bash
```

Expected: all tests pass.

- [ ] **Step 2: If any failures, investigate and fix before proceeding**

Failures here indicate a CLI contract regression. Check the failing bats test output for the specific command and input/output mismatch.
