# plcc-scan TTY Hint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Print `Enter input. Press ^D (EOF) when done.` to stderr each time `plcc-scan` begins reading from a TTY stdin source.

**Architecture:** Restructure the single `subprocess.Popen` call in `scan.py` into a per-source loop. Before each `-` source, check `sys.stdin.isatty()` and emit the hint to stderr if true. Unit-test the hint logic with pytest monkeypatching; the existing bats negative tests require a small string update to match the new message.

**Tech Stack:** Python 3, pytest, bats

---

## Files

- Modify: `src/plcc/cmd/scan.py` — restructure subprocess loop; add TTY hint
- Create: `src/plcc/cmd/scan_test.py` — pytest unit tests for hint behavior
- Modify: `tests/bats/commands/plcc-scan.bats` — update two lines to match new hint message

---

### Task 1: Update bats negative tests to match the new hint message

The existing bats tests assert the hint is absent by checking for `"press ^D"` (lowercase p). The new message uses `"Press ^D"` (uppercase P), so these checks would silently become no-ops. Update both to match the new message substring.

**Files:**
- Modify: `tests/bats/commands/plcc-scan.bats`

- [ ] **Step 1: Open the bats file and locate the two lines**

  In `tests/bats/commands/plcc-scan.bats`:

  Line 185 (inside `@test "plcc-scan -v hint is absent from stderr"`):
  ```bash
      [[ "$stderr" != *"press ^D"* ]]
  ```

  Line 207 (inside `@test "plcc-scan TTY hint absent when stdin is not a TTY"`):
  ```bash
      [[ "$output" != *"press ^D"* ]]
  ```

- [ ] **Step 2: Update both lines**

  Change line 185 to:
  ```bash
      [[ "$stderr" != *"Press ^D"* ]]
  ```

  Change line 207: add `--separate-stderr` to the `run` call and check `$stderr` (not `$output`), since the hint goes to stderr:
  ```bash
  @test "plcc-scan TTY hint absent when stdin is not a TTY" {
      run --separate-stderr bash -c "echo '42' | plcc-scan"
      [ "$status" -eq 0 ]
      [[ "$stderr" != *"Press ^D"* ]]
  }
  ```

- [ ] **Step 3: Run the bats command tests to confirm they still pass**

  ```bash
  bin/test/commands.bash tests/bats/commands/plcc-scan.bats
  ```

  Expected: all existing tests pass (the hint is still absent in non-TTY mode because the feature isn't implemented yet).

- [ ] **Step 4: Commit**

  ```bash
  git add tests/bats/commands/plcc-scan.bats
  git commit -m "test(scan): update bats hint checks to match new message casing"
  ```

---

### Task 2: Write failing unit tests for the TTY hint

**Files:**
- Create: `src/plcc/cmd/scan_test.py`

- [ ] **Step 1: Create the test file**

  Create `src/plcc/cmd/scan_test.py` with this content:

  ```python
  import subprocess
  import sys
  from types import SimpleNamespace

  import pytest

  from .scan import main as run_main

  HINT = "Enter input. Press ^D (EOF) when done."


  def _make_proc():
      return SimpleNamespace(
          stdout=iter([]),
          returncode=0,
          wait=lambda: None,
      )


  @pytest.fixture(autouse=True)
  def grammar(tmp_path, monkeypatch):
      monkeypatch.chdir(tmp_path)
      (tmp_path / "grammar.plcc").write_text("")


  @pytest.fixture(autouse=True)
  def stub_subprocesses(monkeypatch):
      monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0))
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: _make_proc())


  def test_hint_printed_for_implicit_stdin_when_tty(monkeypatch, capsys):
      monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: True))
      run_main([])
      _, err = capsys.readouterr()
      assert err.count(HINT) == 1


  def test_hint_printed_for_explicit_dash_source_when_tty(monkeypatch, capsys):
      monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: True))
      run_main(["-"])
      _, err = capsys.readouterr()
      assert err.count(HINT) == 1


  def test_hint_printed_twice_for_two_dash_sources_when_tty(monkeypatch, capsys):
      monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: True))
      run_main(["-", "-"])
      _, err = capsys.readouterr()
      assert err.count(HINT) == 2


  def test_hint_absent_when_not_tty(monkeypatch, capsys):
      monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: False))
      run_main([])
      _, err = capsys.readouterr()
      assert HINT not in err


  def test_hint_absent_for_file_source_even_when_tty(monkeypatch, capsys):
      monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: True))
      run_main(["somefile.txt"])
      _, err = capsys.readouterr()
      assert HINT not in err
  ```

- [ ] **Step 2: Run the new tests to confirm they fail**

  ```bash
  bin/test/units.bash src/plcc/cmd/scan_test.py -v
  ```

  Expected: all five tests FAIL (the hint logic does not exist yet). You should see failures like `AssertionError: assert 0 == 1` for the "hint printed" tests.

- [ ] **Step 3: Commit the failing tests**

  ```bash
  git add src/plcc/cmd/scan_test.py
  git commit -m "test(scan): add failing unit tests for TTY hint"
  ```

---

### Task 3: Implement the TTY hint in `scan.py`

**Files:**
- Modify: `src/plcc/cmd/scan.py`

- [ ] **Step 1: Replace the single Popen block with a per-source loop**

  In `src/plcc/cmd/scan.py`, locate this block (starts around line 129):

  ```python
      token_sources = sources if sources else ["-"]
      tokens_flags = child_flags + (["--trace"] if any_enrichment else [])

      proc = subprocess.Popen(
          ["plcc-tokens", spec_path] + token_sources + tokens_flags,
          stdout=subprocess.PIPE,
          stderr=None,
      )

      for raw in proc.stdout:
          line = raw.decode("utf-8").strip()
          if not line:
              continue
          record = json.loads(line)
          _render_record(record, trace, trace, trace)

      proc.wait()

      if proc.returncode != 0:
          print(f"plcc-scan: plcc-tokens failed (exit {proc.returncode})", file=sys.stderr)
          sys.exit(proc.returncode)
  ```

  Replace it with:

  ```python
      token_sources = sources if sources else ["-"]
      tokens_flags = child_flags + (["--trace"] if any_enrichment else [])

      for source in token_sources:
          if source == "-" and sys.stdin.isatty():
              print("Enter input. Press ^D (EOF) when done.", file=sys.stderr)

          proc = subprocess.Popen(
              ["plcc-tokens", spec_path, source] + tokens_flags,
              stdout=subprocess.PIPE,
              stderr=None,
          )

          for raw in proc.stdout:
              line = raw.decode("utf-8").strip()
              if not line:
                  continue
              record = json.loads(line)
              _render_record(record, trace, trace, trace)

          proc.wait()

          if proc.returncode != 0:
              print(f"plcc-scan: plcc-tokens failed (exit {proc.returncode})", file=sys.stderr)
              sys.exit(proc.returncode)
  ```

- [ ] **Step 2: Run the unit tests to confirm they now pass**

  ```bash
  bin/test/units.bash src/plcc/cmd/scan_test.py -v
  ```

  Expected: all five tests PASS.

- [ ] **Step 3: Run the full unit suite to check for regressions**

  ```bash
  bin/test/units.bash
  ```

  Expected: all tests pass.

- [ ] **Step 4: Run the bats command tests**

  ```bash
  bin/test/commands.bash tests/bats/commands/plcc-scan.bats
  ```

  Expected: all tests pass.

- [ ] **Step 5: Commit**

  ```bash
  git add src/plcc/cmd/scan.py
  git commit -m "feat(scan): print TTY hint each time interactive stdin read begins"
  ```

---

### Task 4: Final verification

- [ ] **Step 1: Run the full functional test suite**

  ```bash
  bin/test/functional.bash
  ```

  Expected: all tiers pass (units, commands, integration, e2e).
