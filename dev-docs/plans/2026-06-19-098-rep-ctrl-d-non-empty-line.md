# 098 — ^D on Non-Empty Line Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the regression where pressing ^D on a non-empty line at the `>>>` prompt requires a second ^D before `plcc-rep` processes the input.

**Architecture:** One-line change in `SourceRunner._read_line` — replace `readline()` with `read1(65536)`. `readline()` blocks on real TTYs after a partial-line ^D flush because it waits for a second `read()` to return `b""` before returning. `read1(N)` makes exactly one OS `read()` call and returns immediately. The rest of `_process_line` is already correct. The test infrastructure uses `BytesIO`-based helpers and custom buffer classes that define `readline()`; these must be updated to define `read1()` instead so the tests match the method the production code calls.

**Tech Stack:** Python 3.14, pytest. Run tests with `python -m pytest src/plcc/cmd/source_runner_test.py -v` from the worktree root.

## Global Constraints

- Work entirely in `/workspaces/plcc-ng/.worktrees/issue-098` on branch `issue-098`. Never commit to `main`.
- TDD: write failing tests first, implement minimally, verify pass, commit.
- `docs(...)` commit subjects must end with `[skip ci]`.
- Commit footer for every commit:
  ```
  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  ```

---

### Task 1: Fix `_read_line` and update test infrastructure

**Files:**
- Modify: `src/plcc/cmd/source_runner.py` — `_read_line` method (~line 49)
- Modify: `src/plcc/cmd/source_runner_test.py` — `_tty_stdin` helper and three custom buffer classes

**Interfaces:**
- `SourceRunner._read_line(prompt)` continues to return `bytes | None` (unchanged contract).
- The change is internal: `sys.stdin.buffer.read1(65536)` instead of `sys.stdin.buffer.readline()`.

- [ ] **Step 1: Write the failing test and update `_tty_stdin`**

In `src/plcc/cmd/source_runner_test.py`, replace the `_tty_stdin` helper with a version whose buffer defines `read1()` instead of relying on `BytesIO.readline()`. Then add the 098 regression test.

Replace `_tty_stdin` (currently around line 85):

```python
def _tty_stdin(lines):
    """Simulate canonical TTY: each read1() call returns the next item from lines."""
    _iter = iter(lines)

    class _TtyBuffer:
        def read1(self, n=-1):
            try:
                return next(_iter)
            except StopIteration:
                return b""

    return SimpleNamespace(isatty=lambda: True, buffer=_TtyBuffer())
```

Add this new test after `test_ctrl_d_empty_buffer_prints_newline` (around line 141):

```python
def test_ctrl_d_partial_line_at_top_level_prompt_force_submits(monkeypatch, runner):
    # 098 regression: at >>>, type "hello" then ^D (no Enter) — force-submit immediately.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello", b""]))
    handler = RecordingHandler(results=[b""])
    runner.run(["-"], handler)
    assert handler.calls == [(b"hello", "-")]
    assert handler.eof_flags == [True]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest src/plcc/cmd/source_runner_test.py -v`

Expected: multiple failures with `AttributeError: '_TtyBuffer' object has no attribute 'readline'` — this confirms `_read_line` currently calls `readline()` and the new mock correctly exposes the mismatch.

- [ ] **Step 3: Fix `_read_line` in `source_runner.py`**

In `src/plcc/cmd/source_runner.py`, replace the body of `_read_line`:

```python
def _read_line(self, prompt):
    try:
        print(prompt, end="", flush=True, file=sys.stderr)
        return sys.stdin.buffer.read1(65536)
    except KeyboardInterrupt:
        return None
```

- [ ] **Step 4: Update the three custom buffer classes in the test file**

Three tests in `source_runner_test.py` define inner classes with a `readline()` method. Replace each `readline` with `read1`:

**`ImmediateInterrupt`** (around line 181, inside `test_ctrl_c_with_empty_buffer_exits_130`):
```python
class ImmediateInterrupt:
    isatty = lambda self: True

    @property
    def buffer(self):
        return self

    def read1(self, n=-1):
        raise KeyboardInterrupt
```

**`InterruptAfterLine`** (around line 197, inside `test_ctrl_c_with_buffer_clears_and_continues`):
```python
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
            return b"partial\n"
        if self._calls == 2:
            raise KeyboardInterrupt
        if self._calls == 3:
            return b"hello\n"
        return b""
```

**`EOFInContinuation`** (around line 262, inside `test_ctrl_d_in_continuation_submits_and_continues`):
```python
class EOFInContinuation:
    def __init__(self):
        self._calls = 0

    isatty = lambda self: True

    @property
    def buffer(self):
        return self

    def read1(self, n=-1):
        self._calls += 1
        if self._calls == 1:
            return b"hello\n"
        if self._calls == 2:
            return b""
        if self._calls == 3:
            return b"world\n"
        return b""
```

- [ ] **Step 5: Run all tests to verify they pass**

Run: `python -m pytest src/plcc/cmd/source_runner_test.py -v`

Expected: 25 passed (24 existing + 1 new), 0 failures.

- [ ] **Step 6: Run the full unit suite to check for regressions**

Run: `bin/test/units.bash`

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
git commit -m "$(cat <<'EOF'
fix(098): replace readline with read1 so one ^D submits partial line

On a real TTY in canonical mode, readline() blocks after the first ^D
flushes buffered content because it loops calling read() until it sees
a newline or an empty read. A second ^D was required to produce the
empty read that caused readline() to return. read1(65536) makes exactly
one OS read() call and returns immediately with whatever was flushed.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review

**Spec coverage:**
- Root cause (readline blocks, needs second ^D) → addressed by Task 1 Step 3. ✓
- Correct behavior (partial line force-submitted immediately) → covered by new test. ✓
- All three `_process_line` paths (Enter, partial-line ^D, empty ^D) → `_tty_stdin` update + existing tests. ✓
- Out-of-scope items (other methods, pipeline, grammar, docs) → not touched. ✓

**Placeholder scan:** None found.

**Type consistency:** `read1(65536)` in production code; `read1(self, n=-1)` in all three custom buffer classes. The `n` parameter is accepted and ignored, matching `BytesIO.read1()` behavior. Consistent throughout.
