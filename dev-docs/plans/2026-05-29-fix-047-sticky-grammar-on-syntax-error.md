# Fix 047 — Sticky Grammar on Syntax Error Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write `build/.grammar` before any build stages run so the sticky grammar is recorded even when the build fails with a syntax error.

**Architecture:** Move the single `write_grammar(build_dir, grammar)` call to immediately after `build_dir.mkdir(exist_ok=True)` in `plcc-make`'s `main()`, then remove the two now-redundant calls on the fast path and slow-path success. No other modules change.

**Tech Stack:** Python 3, pytest (unit tests), bats (CLI tests). Run unit tests with `bin/test/units.bash`, CLI tests with `bin/test/commands.bash`.

---

### Task 1: Add the failing unit test

**Files:**
- Modify: `src/plcc/cmd/make_test.py`

Context: `make_test.py` imports `run_main` from `.make` and `write_grammar` / `read_grammar` from `plcc.build.grammar`. Tests use `tmp_path` (pytest fixture) and `monkeypatch.chdir(tmp_path)` to isolate the working directory. `run_main` is a real call that spawns `plcc-spec` as a subprocess — so a malformed grammar (`token BAD @@@`) causes `plcc-spec` to return non-zero, which triggers `sys.exit` inside `run_main`.

- [ ] **Step 1: Add the import for `read_grammar`**

Open `src/plcc/cmd/make_test.py`. The top of the file currently has:

```python
from plcc.build.grammar import write_grammar
```

Change it to:

```python
from plcc.build.grammar import read_grammar, write_grammar
```

- [ ] **Step 2: Add the failing test at the end of the sticky-grammar block**

Append this test after the last existing test in the file (currently `test_explicit_grammar_same_as_stored_does_not_wipe`):

```python
def test_grammar_written_before_build_stages_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    (tmp_path / "bad.plcc").write_text("token BAD @@@\n")
    with pytest.raises(SystemExit):
        run_main(["--grammar-file=bad.plcc"])
    assert read_grammar(build) == "bad.plcc"
```

- [ ] **Step 3: Run the test and confirm it fails**

```bash
bin/test/units.bash src/plcc/cmd/make_test.py::test_grammar_written_before_build_stages_run -v
```

Expected: `FAILED` — `AssertionError` because `read_grammar(build)` returns `None` (file was never written).

---

### Task 2: Move `write_grammar` to before the build stages

**Files:**
- Modify: `src/plcc/cmd/make.py:100-195`

Context: In `main()`, the relevant lines are:

```python
build_dir.mkdir(exist_ok=True)                          # line ~100

# ... fast path (is_current check) ...
write_grammar(build_dir, grammar)                       # line ~145  ← REMOVE
# ...

write_sentinel(build_dir, new_hash, required_stages)
write_grammar(build_dir, grammar)                       # line ~195  ← REMOVE
```

- [ ] **Step 1: Insert `write_grammar` after `build_dir.mkdir(exist_ok=True)`**

Find this line in `main()`:

```python
    build_dir.mkdir(exist_ok=True)
```

Change it to:

```python
    build_dir.mkdir(exist_ok=True)
    write_grammar(build_dir, grammar)
```

- [ ] **Step 2: Remove the fast-path `write_grammar` call**

The fast path block looks like:

```python
    if is_current(sentinel, new_hash, required_stages):
        os.unlink(tmp_spec)
        write_grammar(build_dir, grammar)
        verbose.emit(Events.FINISHED, message="build is current")
        return
```

Remove the `write_grammar` call so it becomes:

```python
    if is_current(sentinel, new_hash, required_stages):
        os.unlink(tmp_spec)
        verbose.emit(Events.FINISHED, message="build is current")
        return
```

- [ ] **Step 3: Remove the slow-path `write_grammar` call**

The end of `main()` currently looks like:

```python
    write_sentinel(build_dir, new_hash, required_stages)
    write_grammar(build_dir, grammar)
    verbose.emit(Events.FINISHED, message="done")
```

Change it to:

```python
    write_sentinel(build_dir, new_hash, required_stages)
    verbose.emit(Events.FINISHED, message="done")
```

- [ ] **Step 4: Run the new unit test and confirm it passes**

```bash
bin/test/units.bash src/plcc/cmd/make_test.py::test_grammar_written_before_build_stages_run -v
```

Expected: `PASSED`

- [ ] **Step 5: Run the full unit suite to catch regressions**

```bash
bin/test/units.bash
```

Expected: all tests pass, no failures.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
git commit -m "fix(make): write build/.grammar before build stages so sticky grammar survives syntax errors"
```

---

### Task 3: Add the failing CLI test

**Files:**
- Modify: `tests/bats/commands/plcc-make.bats`

Context: The sticky grammar section starts at the comment `# ── Sticky grammar ──`. Bats tests use `run --separate-stderr <cmd>` or just `run <cmd>`. `$status` is the exit code. `$(cat build/.grammar)` reads the file directly. The fixture `${FIXTURES}/trivial.plcc` is a valid grammar. The `printf 'token BAD @@@\n'` pattern is already used in existing tests for a grammar that causes `plcc-spec` to fail.

- [ ] **Step 1: Add the failing bats test**

In `tests/bats/commands/plcc-make.bats`, locate the sticky grammar block (after the `# ── Sticky grammar ──` comment). Add this test after the last sticky-grammar test in that block:

```bash
@test "plcc-make writes build/.grammar even when plcc-spec fails" {
    printf 'token BAD @@@\n' > bad.plcc
    run plcc-make --grammar-file=bad.plcc
    [ "$status" -ne 0 ]
    [ -f "build/.grammar" ]
    [[ "$(cat build/.grammar)" == "bad.plcc" ]]
}
```

- [ ] **Step 2: Run the CLI test and confirm it passes**

```bash
bin/test/commands.bash -- --filter "plcc-make writes build/.grammar even when plcc-spec fails"
```

Expected: test passes.

- [ ] **Step 3: Run the full commands tier to catch regressions**

```bash
bin/test/commands.bash
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/bats/commands/plcc-make.bats
git commit -m "test(make): CLI test - build/.grammar written even on plcc-spec failure"
```
