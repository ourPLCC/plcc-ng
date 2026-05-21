# Fix Verbose Child Events Uncaptured in plcc-parse and plcc-rep

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capture stderr from `plcc-tokens` and `plcc-trees` subprocesses inside `TreePipeline` and reformat their verbose JSON events through `VerboseContext`, so `plcc-parse -v` and `plcc-rep -v` produce clean human-readable output instead of raw JSON mixed with formatted lines.

**Architecture:** Thread an optional `VerboseContext` into `TreePipeline.__init__`. Switch both child `Popen` calls from `stderr=None` to `stderr=subprocess.PIPE`. After `communicate()`, collect both stderrs and call `verbose.reformat_child_events()` — but only when returning real records; suppress events silently on the eof-probe early-return. `ParseHandler` and `RepHandler` gain a matching `verbose=None` param that they forward to `TreePipeline`. `main()` in both commands passes the already-constructed `VerboseContext`.

**Tech Stack:** Python 3, pytest, `bin/test/units.bash` (TDD inner loop)

---

## File Map

| File | Change |
| --- | --- |
| `src/plcc/cmd/_test_helpers.py` | Add `stderr=b""` param to `_proc()`; set `p.stderr` and update `communicate` return |
| `src/plcc/cmd/pipeline.py` | `TreePipeline.__init__` gains `verbose=None`; `run()` uses `stderr=PIPE` and reformats on success |
| `src/plcc/cmd/pipeline_test.py` | Three new tests for verbose capture, suppression, and no-verbose default |
| `src/plcc/cmd/parse.py` | `ParseHandler.__init__` gains `verbose=None`; `main()` passes it |
| `src/plcc/cmd/parse_test.py` | One new smoke test confirming verbose threads through |
| `src/plcc/cmd/rep.py` | `RepHandler.__init__` gains `verbose=None`; `main()` passes it |
| `src/plcc/cmd/rep_test.py` | One new smoke test confirming verbose threads through |

---

## Task 1: Extend `_proc()` test helper with stderr support

**Files:**

- Modify: `src/plcc/cmd/_test_helpers.py`

`_proc()` currently has no `.stderr` attribute and `communicate()` always returns `b""` as the second element. After `TreePipeline` changes, `tokens_proc.stderr.read()` and `tree_proc.communicate()` (which returns `(stdout, stderr)`) both need to work on the mock.

- [ ] **Step 1: Open `_test_helpers.py` and update `_proc()`**

  Replace:

  ```python
  def _proc(stdout=b"", returncode=0):
      p = SimpleNamespace(returncode=returncode)
      p.communicate = lambda: (stdout, b"")
      p.wait = lambda: None
      p.stdin = io.BytesIO()
      p.stdout = io.BytesIO(stdout)
      return p
  ```

  With:

  ```python
  def _proc(stdout=b"", returncode=0, stderr=b""):
      p = SimpleNamespace(returncode=returncode)
      p.communicate = lambda: (stdout, stderr)
      p.wait = lambda: None
      p.stdin = io.BytesIO()
      p.stdout = io.BytesIO(stdout)
      p.stderr = io.BytesIO(stderr)
      return p
  ```

  The default `stderr=b""` keeps all existing call sites unchanged.

- [ ] **Step 2: Confirm existing tests still pass**

  ```bash
  bin/test/units.bash src/plcc/cmd/pipeline_test.py src/plcc/cmd/parse_test.py src/plcc/cmd/rep_test.py
  ```

  Expected: all green, no failures.

- [ ] **Step 3: Commit**

  ```bash
  git add src/plcc/cmd/_test_helpers.py
  git commit -m "test(cmd): extend _proc() helper with stderr support"
  ```

---

## Task 2: `TreePipeline` captures and reformats verbose child events

**Files:**

- Modify: `src/plcc/cmd/pipeline_test.py`
- Modify: `src/plcc/cmd/pipeline.py`

This is the core fix. Write the failing test first, then implement.

- [ ] **Step 1: Write the failing test in `pipeline_test.py`**

  Add this import at the top of the file alongside existing imports:

  ```python
  from plcc.verbose import VerboseContext
  ```

  Add this test:

  ```python
  def test_run_reformats_child_verbose_events_when_verbose_set(monkeypatch, capsys):
      verbose = VerboseContext("test", None, level=1, fmt="text")
      tokens_stderr = (
          b'{"stage": "plcc-tokens", "event": "started", "message": "tokenizing"}\n'
      )
      procs = iter([
          _proc(stderr=tokens_stderr),
          _proc(stdout=_tree_record(), stderr=b""),
      ])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      p = TreePipeline(spec_path="s", ll1_path="l", verbose=verbose)
      p.run(b"1\n")
      _, err = capsys.readouterr()
      assert "plcc-tokens: started: tokenizing" in err
  ```

- [ ] **Step 2: Run the test to confirm it fails**

  ```bash
  bin/test/units.bash src/plcc/cmd/pipeline_test.py::test_run_reformats_child_verbose_events_when_verbose_set
  ```

  Expected: FAIL — `TreePipeline.__init__` does not accept `verbose`.

- [ ] **Step 3: Implement the fix in `pipeline.py`**

  Replace the full `TreePipeline` class with:

  ```python
  class TreePipeline:
      """Runs plcc-tokens | plcc-trees and classifies the output."""

      def __init__(self, spec_path, ll1_path, child_flags=None, verbose=None):
          self._spec_path = spec_path
          self._ll1_path = ll1_path
          self._child_flags = child_flags or []
          self._verbose = verbose

      def run(self, content, eof=False):
          """Run the pipeline.

          Returns None  — need more input (no records, or only EOF errors with eof=False).
          Returns list  — list of (record_dict, raw_bytes) pairs ready to dispatch.
          """
          tokens_proc = subprocess.Popen(
              ["plcc-tokens", self._spec_path, "-"] + self._child_flags,
              stdin=subprocess.PIPE,
              stdout=subprocess.PIPE,
              stderr=subprocess.PIPE,
          )
          tree_proc = subprocess.Popen(
              ["plcc-trees", f"--ll1={self._ll1_path}"] + self._child_flags,
              stdin=tokens_proc.stdout,
              stdout=subprocess.PIPE,
              stderr=subprocess.PIPE,
          )
          tokens_proc.stdout.close()
          tokens_proc.stdin.write(content)
          tokens_proc.stdin.close()
          tree_out, tree_err = tree_proc.communicate()
          tokens_proc.wait()
          # Note: if tokens_proc wrote >64 KB to stderr before tree_proc.communicate()
          # drained it, this read could deadlock. Verbose output is a handful of JSON
          # lines (~300 bytes per run), so this is not a practical risk.
          tokens_err = tokens_proc.stderr.read()

          records = []
          raws = []
          for raw in tree_out.splitlines():
              raw = raw.strip()
              if not raw:
                  continue
              records.append(json.loads(raw))
              raws.append(raw)

          if not records:
              return None  # suppress events: pipeline will re-run with more input

          any_tree = any(r.get("kind") == "tree" for r in records)
          any_genuine_error = any(
              r.get("kind") == "error" and r.get("found") != "eof"
              for r in records
          )
          only_eof_errors = not any_tree and not any_genuine_error

          if only_eof_errors and not eof:
              return None  # suppress events: pipeline will re-run with more input

          if self._verbose:
              # tokens runs upstream; concatenate in pipeline order for roughly
              # chronological display
              combined = tokens_err + tree_err
              events = self._verbose.parse_child_events(
                  combined.decode("utf-8", errors="replace")
              )
              self._verbose.reformat_child_events(events)

          return list(zip(records, raws))
  ```

- [ ] **Step 4: Run the new test to confirm it passes**

  ```bash
  bin/test/units.bash src/plcc/cmd/pipeline_test.py::test_run_reformats_child_verbose_events_when_verbose_set
  ```

  Expected: PASS.

- [ ] **Step 5: Run all pipeline tests to confirm nothing regressed**

  ```bash
  bin/test/units.bash src/plcc/cmd/pipeline_test.py
  ```

  Expected: all green.

- [ ] **Step 6: Commit**

  ```bash
  git add src/plcc/cmd/pipeline.py src/plcc/cmd/pipeline_test.py
  git commit -m "fix(cmd): capture child stderr in TreePipeline and reformat verbose events"
  ```

---

## Task 3: Verify eof-probe suppression and no-verbose default

**Files:**

- Modify: `src/plcc/cmd/pipeline_test.py`

Two more tests to pin the suppression behavior and the `verbose=None` default.

- [ ] **Step 1: Add two tests to `pipeline_test.py`**

  ```python
  def test_run_suppresses_child_verbose_events_on_eof_probe(monkeypatch, capsys):
      verbose = VerboseContext("test", None, level=1, fmt="text")
      tokens_stderr = (
          b'{"stage": "plcc-tokens", "event": "started", "message": "tokenizing"}\n'
      )
      procs = iter([
          _proc(stderr=tokens_stderr),
          _proc(stdout=_eof_error_record(), stderr=b""),
      ])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      p = TreePipeline(spec_path="s", ll1_path="l", verbose=verbose)
      result = p.run(b"1+\n", eof=False)
      assert result is None
      _, err = capsys.readouterr()
      assert err == ""


  def test_run_does_not_reformat_when_verbose_is_none(monkeypatch, capsys):
      tokens_stderr = (
          b'{"stage": "plcc-tokens", "event": "started", "message": "tokenizing"}\n'
      )
      procs = iter([
          _proc(stderr=tokens_stderr),
          _proc(stdout=_tree_record(), stderr=b""),
      ])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      p = TreePipeline(spec_path="s", ll1_path="l")  # verbose=None default
      result = p.run(b"1\n")
      assert result is not None
      _, err = capsys.readouterr()
      assert err == ""
  ```

- [ ] **Step 2: Run the new tests**

  ```bash
  bin/test/units.bash src/plcc/cmd/pipeline_test.py::test_run_suppresses_child_verbose_events_on_eof_probe src/plcc/cmd/pipeline_test.py::test_run_does_not_reformat_when_verbose_is_none
  ```

  Expected: both PASS (the implementation from Task 2 already handles both cases).

- [ ] **Step 3: Run all pipeline tests**

  ```bash
  bin/test/units.bash src/plcc/cmd/pipeline_test.py
  ```

  Expected: all green.

- [ ] **Step 4: Commit**

  ```bash
  git add src/plcc/cmd/pipeline_test.py
  git commit -m "test(cmd): pin eof-probe suppression and no-verbose default in TreePipeline"
  ```

---

## Task 4: Thread `verbose` through `ParseHandler`

**Files:**

- Modify: `src/plcc/cmd/parse_test.py`
- Modify: `src/plcc/cmd/parse.py`

`ParseHandler` needs to accept a `VerboseContext` and forward it to `TreePipeline`. `main()` already holds a `VerboseContext`; it just needs to pass it.

- [ ] **Step 1: Add a failing test to `parse_test.py`**

  Add this import at the top of the file alongside existing imports:

  ```python
  from plcc.verbose import VerboseContext
  ```

  Add this test:

  ```python
  def test_feed_reformats_child_verbose_events(monkeypatch, capsys):
      verbose = VerboseContext("test", None, level=1, fmt="text")
      handler = ParseHandler(
          spec_path="build/spec.json",
          ll1_path="build/ll1.json",
          child_flags=[],
          verbose=verbose,
      )
      tokens_stderr = (
          b'{"stage": "plcc-tokens", "event": "started", "message": "tokenizing"}\n'
      )
      procs = iter([
          _proc(stderr=tokens_stderr),
          _proc(stdout=_tree_record(), stderr=b""),
      ])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      handler.feed(b"1\n", "-")
      _, err = capsys.readouterr()
      assert "plcc-tokens: started: tokenizing" in err
  ```

- [ ] **Step 2: Run the test to confirm it fails**

  ```bash
  bin/test/units.bash src/plcc/cmd/parse_test.py::test_feed_reformats_child_verbose_events
  ```

  Expected: FAIL — `ParseHandler.__init__` does not accept `verbose`.

- [ ] **Step 3: Update `ParseHandler` and `main()` in `parse.py`**

  Change `ParseHandler.__init__`:

  ```python
  def __init__(self, spec_path, ll1_path, child_flags, verbose=None):
      self._pipeline = TreePipeline(spec_path, ll1_path, child_flags, verbose=verbose)
      self.had_error = False
  ```

  Change the handler construction in `main()`:

  ```python
  handler = ParseHandler(spec_path=spec_path, ll1_path=ll1_path,
                         child_flags=child_flags, verbose=verbose)
  ```

- [ ] **Step 4: Run the new test to confirm it passes**

  ```bash
  bin/test/units.bash src/plcc/cmd/parse_test.py::test_feed_reformats_child_verbose_events
  ```

  Expected: PASS.

- [ ] **Step 5: Run all parse tests**

  ```bash
  bin/test/units.bash src/plcc/cmd/parse_test.py
  ```

  Expected: all green.

- [ ] **Step 6: Commit**

  ```bash
  git add src/plcc/cmd/parse.py src/plcc/cmd/parse_test.py
  git commit -m "fix(cmd): thread VerboseContext through ParseHandler to TreePipeline"
  ```

---

## Task 5: Thread `verbose` through `RepHandler`

**Files:**

- Modify: `src/plcc/cmd/rep_test.py`
- Modify: `src/plcc/cmd/rep.py`

Same pattern as Task 4.

- [ ] **Step 1: Add a failing test to `rep_test.py`**

  Add this import at the top of the file alongside existing imports:

  ```python
  from plcc.verbose import VerboseContext
  ```

  Add this test after the existing `child_flags` propagation test:

  ```python
  def test_feed_reformats_child_verbose_events(monkeypatch, capsys):
      verbose = VerboseContext("test", None, level=1, fmt="text")
      h = RepHandler(
          spec_path="build/spec.json",
          ll1_path="build/ll1.json",
          interpreter=_make_interpreter(),
          verbose_format="text",
          verbose=verbose,
      )
      tokens_stderr = (
          b'{"stage": "plcc-tokens", "event": "started", "message": "tokenizing"}\n'
      )
      procs = iter([
          _proc(stderr=tokens_stderr),
          _proc(stdout=_tree_record(), stderr=b""),
      ])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      h.feed(b"42\n", "-")
      _, err = capsys.readouterr()
      assert "plcc-tokens: started: tokenizing" in err
  ```

- [ ] **Step 2: Run the test to confirm it fails**

  ```bash
  bin/test/units.bash src/plcc/cmd/rep_test.py::test_feed_reformats_child_verbose_events
  ```

  Expected: FAIL — `RepHandler.__init__` does not accept `verbose`.

- [ ] **Step 3: Update `RepHandler` and `main()` in `rep.py`**

  Change `RepHandler.__init__`:

  ```python
  def __init__(self, spec_path, ll1_path, interpreter, verbose_format,
               child_flags=None, verbose=None):
      self._pipeline = TreePipeline(spec_path, ll1_path, child_flags, verbose=verbose)
      self._interpreter = interpreter
      self._verbose_format = verbose_format
  ```

  Change the handler construction in `main()`:

  ```python
  handler = RepHandler(
      spec_path=spec_path,
      ll1_path=ll1_path,
      interpreter=interpreter,
      verbose_format=verbose_format,
      child_flags=child_flags,
      verbose=verbose,
  )
  ```

- [ ] **Step 4: Run the new test to confirm it passes**

  ```bash
  bin/test/units.bash src/plcc/cmd/rep_test.py::test_feed_reformats_child_verbose_events
  ```

  Expected: PASS.

- [ ] **Step 5: Run all rep tests**

  ```bash
  bin/test/units.bash src/plcc/cmd/rep_test.py
  ```

  Expected: all green.

- [ ] **Step 6: Commit**

  ```bash
  git add src/plcc/cmd/rep.py src/plcc/cmd/rep_test.py
  git commit -m "fix(cmd): thread VerboseContext through RepHandler to TreePipeline"
  ```

---

## Task 6: Full test run and manual smoke test

- [ ] **Step 1: Run all unit tests**

  ```bash
  bin/test/units.bash
  ```

  Expected: all green.

- [ ] **Step 2: Manual smoke test for `plcc-parse -v`**

  ```bash
  mkdir -p /tmp/plcc-smoke && cd /tmp/plcc-smoke
  cat > grammar.plcc << 'EOF'
  token NUM '\d+'
  %
  <program> ::= NUM
  EOF
  echo "1" | plcc-parse -v
  ```

  Expected: all output is reformatted text (`plcc-tokens: started: ...`), no raw `{...}` JSON lines.

- [ ] **Step 3: Manual smoke test for `plcc-rep -v`**

  ```bash
  cat > /tmp/plcc-smoke/grammar.plcc << 'EOF'
  token NUM '\d+'
  %
  <program> ::= <NUM>num
  % py Python _run
  Program
  %%%
  def _run(self):
      return int(self.num.lexeme)
  %%%
  EOF
  cd /tmp/plcc-smoke && echo "42" | plcc-rep -v
  ```

  Expected: all output is reformatted text, no raw JSON lines.

- [ ] **Step 4: Move issue 011 to done**

  ```bash
  git mv docs/issues/011-parse-verbose-child-events-uncaptured.md docs/issues/done/011-parse-verbose-child-events-uncaptured.md
  git commit -m "docs(issues): move issue 011 to done [skip ci]"
  ```
