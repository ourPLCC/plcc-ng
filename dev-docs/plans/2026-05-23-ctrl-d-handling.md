# ^D Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change `SourceRunner` so that `^D` on an empty prompt warns before exiting, and `SubmitOn.EOF` mode never evaluates on Enter.

**Architecture:** Add `pending_exit: bool` to `_InteractiveState` to track the first `^D`-on-empty-prompt; split the `_is_eof` branch in `_process_line` to route empty-buffer `^D` through a new `_warn_then_exit` method; simplify the `SubmitOn.EOF` branch to pure accumulation by removing `_attempt_first_line`.

**Tech Stack:** Python, pytest, `bin/test/units.bash`

---

## File Map

- Modify: `src/plcc/cmd/source_runner.py` — all implementation changes
- Modify: `src/plcc/cmd/source_runner_test.py` — new tests, updated tests, deleted tests

---

## Task 1: Add `pending_exit` to `_InteractiveState`

**Files:**
- Modify: `src/plcc/cmd/source_runner.py:15-19`
- Modify: `src/plcc/cmd/source_runner_test.py`

- [ ] **Step 1: Write the failing tests**

Add these two tests to `source_runner_test.py`, after the existing `test_interactive_state_done_flag` test:

```python
def test_interactive_state_pending_exit_defaults_false():
    state = _InteractiveState(buffer=b"", prompt=">>> ")
    assert state.pending_exit is False


def test_interactive_state_pending_exit_can_be_set():
    state = _InteractiveState(buffer=b"", prompt=">>> ", pending_exit=True)
    assert state.pending_exit is True
```

- [ ] **Step 2: Run the tests and confirm they fail**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_interactive_state_pending_exit_defaults_false src/plcc/cmd/source_runner_test.py::test_interactive_state_pending_exit_can_be_set -v
```

Expected: `FAILED` — `_InteractiveState` has no `pending_exit` field.

- [ ] **Step 3: Add `pending_exit` to `_InteractiveState`**

In `src/plcc/cmd/source_runner.py`, replace the dataclass (lines 15–19):

```python
@dataclass
class _InteractiveState:
    buffer: bytes
    prompt: str
    done: bool = False
    pending_exit: bool = False
```

- [ ] **Step 4: Run the tests and confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_interactive_state_pending_exit_defaults_false src/plcc/cmd/source_runner_test.py::test_interactive_state_pending_exit_can_be_set -v
```

Expected: `PASSED`.

- [ ] **Step 5: Run the full unit suite to confirm no regressions**

```bash
bin/test/units.bash
```

Expected: all previously passing tests still pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
git commit -m "feat(source-runner): add pending_exit field to _InteractiveState"
```

---

## Task 2: Implement double-`^D` warning on empty prompt

**Files:**
- Modify: `src/plcc/cmd/source_runner.py:66-80` (`_process_line`), add `_warn_then_exit`
- Modify: `src/plcc/cmd/source_runner_test.py`

- [ ] **Step 1: Write the failing tests**

Add these three tests to `source_runner_test.py`, after the existing `test_ctrl_d_on_fresh_prompt_prints_newline` test:

```python
def test_first_ctrl_d_on_empty_prompt_prints_warning(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b""]))
    runner.run(["-"], RecordingHandler())
    _, err = capsys.readouterr()
    assert "(press ^D again to exit)" in err


def test_second_ctrl_d_on_empty_prompt_exits_without_feed(monkeypatch, runner):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b""]))
    handler = RecordingHandler()
    runner.run(["-"], handler)
    assert handler.calls == []


def test_input_after_ctrl_d_warning_clears_pending_exit(monkeypatch, runner):
    # ^D warns; user types a line (clears pending_exit); next ^D warns again instead
    # of exiting immediately. The presence of the feed call proves the session continued.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"", b"hello\n", b""]))
    handler = RecordingHandler(results=[True])
    runner.run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\n"
```

- [ ] **Step 2: Run the tests and confirm they fail**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_first_ctrl_d_on_empty_prompt_prints_warning src/plcc/cmd/source_runner_test.py::test_second_ctrl_d_on_empty_prompt_exits_without_feed src/plcc/cmd/source_runner_test.py::test_input_after_ctrl_d_warning_clears_pending_exit -v
```

Expected: `FAILED` — `_warn_then_exit` does not exist yet.

- [ ] **Step 3: Add `_warn_then_exit` and split `_is_eof` in `_process_line`**

In `src/plcc/cmd/source_runner.py`, replace `_process_line` (lines 66–80):

```python
    def _process_line(self, handler, line, state):
        if self._is_interrupted(line):
            return self._clear_buffer_or_exit(state)
        if self._is_eof(line):
            if state.buffer:
                return self._exit_or_submit_accumulated_buffer(handler, state)
            return self._warn_then_exit(state)
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

Add `_warn_then_exit` after `_clear_buffer_or_exit` (after line 110):

```python
    def _warn_then_exit(self, state):
        print(file=sys.stderr)
        if state.pending_exit:
            return _InteractiveState(buffer=b"", prompt=self._prompt, done=True)
        print("(press ^D again to exit)", file=sys.stderr)
        return _InteractiveState(buffer=b"", prompt=self._prompt, pending_exit=True)
```

- [ ] **Step 4: Run the new tests and confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_first_ctrl_d_on_empty_prompt_prints_warning src/plcc/cmd/source_runner_test.py::test_second_ctrl_d_on_empty_prompt_exits_without_feed src/plcc/cmd/source_runner_test.py::test_input_after_ctrl_d_warning_clears_pending_exit -v
```

Expected: `PASSED`.

- [ ] **Step 5: Run the full unit suite to confirm no regressions**

```bash
bin/test/units.bash
```

Expected: all previously passing tests still pass. `_tty_stdin([b""])` produces two empty reads from `BytesIO`, so existing tests that pass a single `b""` implicitly exercise both `^D` presses and still pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
git commit -m "feat(source-runner): warn on first ^D on empty prompt, exit on second"
```

---

## Task 3: `SubmitOn.EOF` — pure accumulation, no Enter evaluation

**Files:**
- Modify: `src/plcc/cmd/source_runner.py:66-80` (`_process_line`), delete `_attempt_first_line`
- Modify: `src/plcc/cmd/source_runner_test.py` — add new tests, update 5, delete 3

### Step 1: Write the new failing tests

- [ ] **Step 1: Write the failing tests**

Add these two tests to `source_runner_test.py`, in the `SubmitOn enum and EOF mode` section:

```python
def test_eof_mode_enter_accumulates_both_lines(monkeypatch):
    # Enter never calls feed; only ^D submits. Both lines must arrive in one call.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"line1\n", b"line2\n", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"line1\nline2\n"


def test_eof_mode_blank_line_accumulates(monkeypatch):
    # Blank Enter accumulates in buffer; ^D submits everything.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"\n", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\n\n"
```

- [ ] **Step 2: Run the failing tests and confirm they fail**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_eof_mode_enter_accumulates_both_lines src/plcc/cmd/source_runner_test.py::test_eof_mode_blank_line_accumulates -v
```

Expected: `FAILED` — currently Enter evaluates on the first line in EOF mode.

- [ ] **Step 3: Simplify `_process_line` and delete `_attempt_first_line`**

In `src/plcc/cmd/source_runner.py`, replace `_process_line`:

```python
    def _process_line(self, handler, line, state):
        if self._is_interrupted(line):
            return self._clear_buffer_or_exit(state)
        if self._is_eof(line):
            if state.buffer:
                return self._exit_or_submit_accumulated_buffer(handler, state)
            return self._warn_then_exit(state)
        if self._is_partial_eof(line):
            return self._force_submit_including_partial_line(handler, line, state)
        if self._submit_on == SubmitOn.EOF:
            return self._accumulate_only(line, state)
        # SubmitOn.EOL
        if self._is_blank(line):
            return self._force_submit_accumulated_buffer(handler, line, state)
        return self._accumulate_and_evaluate(handler, line, state)
```

Delete the entire `_attempt_first_line` method (lines 98–103 in the original file):

```python
    # DELETE THIS METHOD ENTIRELY:
    def _attempt_first_line(self, handler, line, state):
        if self._is_blank(line):
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        if self._evaluate(handler, line, eof=False):
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        return _InteractiveState(buffer=line, prompt=self._continuation)
```

- [ ] **Step 4: Run the new tests and confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/source_runner_test.py::test_eof_mode_enter_accumulates_both_lines src/plcc/cmd/source_runner_test.py::test_eof_mode_blank_line_accumulates -v
```

Expected: `PASSED`.

- [ ] **Step 5: Run the full unit suite to identify which existing tests now fail**

```bash
bin/test/units.bash 2>&1 | grep FAILED
```

Expected failures (tests that relied on `_attempt_first_line` behavior):
- `test_eof_mode_trial_succeeds_resets_to_prompt`
- `test_eof_mode_blank_first_line_is_skipped`
- `test_eof_mode_second_line_accumulates_not_retried`
- `test_eof_mode_ctrl_d_with_buffer_calls_feed`
- `test_eof_mode_blank_line_accumulates_during_continuation`
- `test_eof_mode_continuation_prompt_shown_after_failed_trial`
- `test_eof_mode_partial_eof_force_submits_buffer_plus_partial`
- `test_eof_mode_trial_fails_enters_continuation`

- [ ] **Step 6: Delete the three tests whose behavior is gone**

In `source_runner_test.py`, delete these three test functions entirely:

```python
# DELETE:
def test_eof_mode_trial_succeeds_resets_to_prompt(monkeypatch, capsys):
    ...

# DELETE:
def test_eof_mode_blank_first_line_is_skipped(monkeypatch):
    ...

# DELETE:
def test_eof_mode_second_line_accumulates_not_retried(monkeypatch):
    ...
```

Reason: `test_eof_mode_trial_succeeds_resets_to_prompt` tested that the first Enter in EOF mode reset to `">>> "` on success — Enter now always shows `"... "`. `test_eof_mode_blank_first_line_is_skipped` tested that blank Enter was ignored — it now accumulates. `test_eof_mode_second_line_accumulates_not_retried` tested a two-call sequence that no longer exists.

- [ ] **Step 7: Update the five tests whose assertions need adjusting**

Replace each of the following in `source_runner_test.py`:

**`test_eof_mode_ctrl_d_with_buffer_calls_feed`** — now one call, all content at once:

```python
def test_eof_mode_ctrl_d_with_buffer_calls_feed(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world\n", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\nworld\n"
```

**`test_eof_mode_blank_line_accumulates_during_continuation`** — now one call:

```python
def test_eof_mode_blank_line_accumulates_during_continuation(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"\n", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\n\n"
```

**`test_eof_mode_continuation_prompt_shown_after_failed_trial`** — rename; Enter now always shows continuation:

```python
def test_eof_mode_enter_shows_continuation_prompt(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    _, err = capsys.readouterr()
    assert "... " in err
```

**`test_eof_mode_partial_eof_force_submits_buffer_plus_partial`** — now one call:

```python
def test_eof_mode_partial_eof_force_submits_buffer_plus_partial(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\nworld"
```

**`test_eof_mode_trial_fails_enters_continuation`** — rename; Enter accumulates, `^D` submits:

```python
def test_eof_mode_enter_then_ctrl_d_submits(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\n"
```

- [ ] **Step 8: Run the full unit suite and confirm all tests pass**

```bash
bin/test/units.bash
```

Expected: all tests pass, zero failures.

- [ ] **Step 9: Commit**

```bash
git add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
git commit -m "feat(source-runner): EOF mode accumulates on Enter, only ^D submits"
```
