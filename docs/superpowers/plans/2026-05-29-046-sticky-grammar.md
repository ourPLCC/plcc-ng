# Sticky Grammar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Store the active grammar in `build/.grammar` so any `plcc-*` command uses the last-specified grammar file automatically, with an explicit `--grammar-file` flag triggering a clean rebuild when the grammar changes.

**Architecture:** A new `plcc.build.grammar` module owns reading/writing `build/.grammar`. `plcc-make` applies three resolution rules (explicit > stored > fallback) at startup, wipes `build/` on grammar switch, and writes the resolved grammar after a successful build. The four caller commands (`plcc-scan`, `plcc-parse`, `plcc-rep`, `plcc-diagram`) stop defaulting to `grammar.plcc` locally and omit `--grammar-file` from their `plcc-make` invocations when the flag was not explicitly given.

**Tech Stack:** Python 3, docopt, pytest, bats

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/plcc/build/grammar.py` | `read_grammar` / `write_grammar` |
| Create | `src/plcc/build/grammar_test.py` | Unit tests for grammar module |
| Modify | `src/plcc/cmd/make.py` | Resolution logic, wipe-on-switch, write on success |
| Modify | `src/plcc/cmd/make_test.py` | Unit tests for new make.py behaviour |
| Modify | `src/plcc/cmd/scan.py` | Remove local default; conditional `--grammar-file` to plcc-make |
| Modify | `src/plcc/cmd/parse.py` | Same |
| Modify | `src/plcc/cmd/rep.py` | Same |
| Modify | `src/plcc/cmd/diagram.py` | Same |
| Modify | `tests/bats/commands/plcc-make.bats` | End-to-end sticky grammar tests |

---

## Task 1: `plcc/build/grammar.py` — new module

**Files:**
- Create: `src/plcc/build/grammar.py`
- Create: `src/plcc/build/grammar_test.py`

- [ ] **Step 1: Write the failing tests**

```python
# src/plcc/build/grammar_test.py
from pathlib import Path
import pytest
from plcc.build.grammar import read_grammar, write_grammar


def test_read_grammar_returns_none_when_absent(tmp_path):
    assert read_grammar(tmp_path) is None


def test_read_grammar_returns_stored_path(tmp_path):
    (tmp_path / ".grammar").write_text("a.plcc")
    assert read_grammar(tmp_path) == "a.plcc"


def test_write_grammar_creates_file(tmp_path):
    write_grammar(tmp_path, "a.plcc")
    assert (tmp_path / ".grammar").read_text() == "a.plcc"


def test_write_grammar_overwrites_existing(tmp_path):
    write_grammar(tmp_path, "a.plcc")
    write_grammar(tmp_path, "b.plcc")
    assert read_grammar(tmp_path) == "b.plcc"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion
bin/test/units.bash -k grammar_test 2>&1 | tail -10
```

Expected: `ModuleNotFoundError` or `ImportError` for `plcc.build.grammar`.

- [ ] **Step 3: Implement `grammar.py`**

```python
# src/plcc/build/grammar.py
from pathlib import Path

_GRAMMAR_FILE = ".grammar"


def read_grammar(build_dir):
    p = Path(build_dir) / _GRAMMAR_FILE
    try:
        return p.read_text().strip()
    except FileNotFoundError:
        return None


def write_grammar(build_dir, path):
    (Path(build_dir) / _GRAMMAR_FILE).write_text(path)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
bin/test/units.bash -k grammar_test 2>&1 | tail -5
```

Expected: `4 passed`.

- [ ] **Step 5: Commit**

```bash
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  add src/plcc/build/grammar.py src/plcc/build/grammar_test.py
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  commit -m "feat: add plcc.build.grammar module for sticky grammar tracking"
```

---

## Task 2: `plcc-make` — grammar resolution and error path

**Files:**
- Modify: `src/plcc/cmd/make.py`
- Modify: `src/plcc/cmd/make_test.py`

- [ ] **Step 1: Write the failing tests**

Add these tests to `src/plcc/cmd/make_test.py`:

```python
from plcc.build.grammar import write_grammar


def test_no_grammar_flag_no_stored_falls_back_to_grammar_plcc(tmp_path, monkeypatch, capsys):
    # Fresh directory, no grammar.plcc → error names grammar.plcc
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main([])
    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert "grammar.plcc" in err


def test_no_grammar_flag_stored_grammar_missing_errors_to_stderr(tmp_path, monkeypatch, capsys):
    # build/.grammar points to a file that does not exist
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    write_grammar(build, "missing.plcc")
    with pytest.raises(SystemExit) as exc:
        run_main([])
    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert "grammar file not found" in err
    assert "missing.plcc" in err
    assert "--grammar-file" in err


def test_no_grammar_flag_uses_stored_grammar_path(tmp_path, monkeypatch, capsys):
    # build/.grammar set to a.plcc (missing) — error names a.plcc, not grammar.plcc
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    write_grammar(build, "a.plcc")
    with pytest.raises(SystemExit):
        run_main([])
    _, err = capsys.readouterr()
    assert "a.plcc" in err
    # Must NOT fall back to grammar.plcc
    assert "grammar.plcc" not in err
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash -k "test_no_grammar_flag" 2>&1 | tail -10
```

Expected: failures or errors because resolution logic doesn't exist yet.

- [ ] **Step 3: Update `make.py` — imports and docstring**

At the top of `src/plcc/cmd/make.py`, add `shutil` to the existing imports and add the grammar import:

```python
import shutil
```

```python
from plcc.build.grammar import read_grammar, write_grammar
```

In the `__doc__` string, change the `--grammar-file` line from:

```
    --grammar-file=<path>   Path to the PLCC grammar file [default: grammar.plcc].
```

to:

```
    --grammar-file=<path>   Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to grammar.plcc on first use.
```

- [ ] **Step 4: Replace the grammar resolution block in `make.py`**

In `main()`, find the current lines (approximately lines 52–54):

```python
    grammar = args['--grammar-file']
    through = args['--through']
    build_dir = Path('build')
```

Replace with:

```python
    explicit_grammar = args['--grammar-file']
    through = args['--through']
    build_dir = Path('build')

    stored_grammar = read_grammar(build_dir) if build_dir.exists() else None

    if explicit_grammar is not None:
        grammar = explicit_grammar
    elif stored_grammar is not None:
        grammar = stored_grammar
    else:
        grammar = 'grammar.plcc'

    if explicit_grammar is None and stored_grammar is not None and not os.path.exists(grammar):
        print(f"plcc-make: grammar file not found: {grammar}", file=sys.stderr)
        print(
            "(the active grammar was set by a previous run; "
            "use --grammar-file to specify a different one)",
            file=sys.stderr,
        )
        sys.exit(1)
```

Also update the verbose STARTED emit (find `verbose.emit(Events.STARTED, ...)`):

```python
    verbose.emit(Events.STARTED, message=f"grammar: {grammar}")
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
bin/test/units.bash -k "test_no_grammar_flag" 2>&1 | tail -5
```

Expected: `3 passed`.

- [ ] **Step 6: Run full unit suite to check for regressions**

```bash
bin/test/units.bash 2>&1 | tail -5
```

Expected: all previously passing tests still pass.

- [ ] **Step 7: Commit**

```bash
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  commit -m "feat(make): add grammar resolution rules and stored-grammar error path"
```

---

## Task 3: `plcc-make` — wipe on grammar switch

**Files:**
- Modify: `src/plcc/cmd/make.py`
- Modify: `src/plcc/cmd/make_test.py`

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/cmd/make_test.py`:

```python
def test_explicit_grammar_differs_from_stored_wipes_build(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    (build / "marker.txt").write_text("from old grammar")
    write_grammar(build, "old.plcc")
    (tmp_path / "new.plcc").write_text("")  # exists but will fail plcc-spec
    with pytest.raises(SystemExit):
        run_main(["--grammar-file=new.plcc"])
    # build/ was wiped before the (failing) rebuild attempt
    assert not (build / "marker.txt").exists()


def test_explicit_grammar_same_as_stored_does_not_wipe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    (build / "marker.txt").write_text("from current grammar")
    write_grammar(build, "same.plcc")
    (tmp_path / "same.plcc").write_text("")  # exists but will fail plcc-spec
    with pytest.raises(SystemExit):
        run_main(["--grammar-file=same.plcc"])
    # No wipe — marker is still present
    assert (build / "marker.txt").exists()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash -k "test_explicit_grammar" 2>&1 | tail -10
```

Expected: both tests fail (wipe logic not yet implemented).

- [ ] **Step 3: Add wipe-on-switch logic to `make.py`**

Immediately after the resolution block added in Task 2 (before the `if not os.path.exists(grammar)` check), add:

```python
    if (
        explicit_grammar is not None
        and stored_grammar is not None
        and explicit_grammar != stored_grammar
    ):
        shutil.rmtree(build_dir)
        build_dir.mkdir()
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
bin/test/units.bash -k "test_explicit_grammar" 2>&1 | tail -5
```

Expected: `2 passed`.

- [ ] **Step 5: Run full unit suite**

```bash
bin/test/units.bash 2>&1 | tail -5
```

Expected: all passing.

- [ ] **Step 6: Commit**

```bash
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  commit -m "feat(make): wipe build/ when grammar file changes"
```

---

## Task 4: `plcc-make` — write grammar after successful build

**Files:**
- Modify: `src/plcc/cmd/make.py`
- Modify: `tests/bats/commands/plcc-make.bats`

- [ ] **Step 1: Add bats tests for the full sticky grammar behaviour**

Append to `tests/bats/commands/plcc-make.bats`:

```bash
# ── Sticky grammar ─────────────────────────────────────────────────────────────

@test "plcc-make writes build/.grammar after successful build" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    plcc-make --through=scan
    [ -f "build/.grammar" ]
    [[ "$(cat build/.grammar)" == "grammar.plcc" ]]
}

@test "plcc-make with --grammar-file writes that path to build/.grammar" {
    run plcc-make --through=scan "--grammar-file=${FIXTURES}/trivial.plcc"
    [ "$status" -eq 0 ]
    [[ "$(cat build/.grammar)" == "${FIXTURES}/trivial.plcc" ]]
}

@test "plcc-make without --grammar-file uses stored grammar" {
    # Build from an absolute path grammar, then invoke plcc-make with no args
    # → should use stored path, not look for grammar.plcc in CWD
    run plcc-make --through=scan "--grammar-file=${FIXTURES}/trivial.plcc"
    [ "$status" -eq 0 ]
    [[ "$(cat build/.grammar)" == "${FIXTURES}/trivial.plcc" ]]
    # Now run with no --grammar-file from a dir with no grammar.plcc
    run --separate-stderr plcc-make --through=scan
    [ "$status" -eq 0 ]
    [[ "$(cat build/.grammar)" == "${FIXTURES}/trivial.plcc" ]]
}

@test "plcc-make with --grammar-file differing from stored wipes build" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    plcc-make --through=scan
    sentinel_before=$(cat build/.spec-hash 2>/dev/null || echo "absent")
    cp "${FIXTURES}/trivial-python.plcc" other.plcc
    plcc-make --through=scan --grammar-file=other.plcc
    # build/ was wiped and rebuilt from other.plcc
    [[ "$(cat build/.grammar)" == "other.plcc" ]]
}

@test "plcc-make stored grammar missing gives error to stderr with hint" {
    mkdir -p build
    echo "ghost.plcc" > build/.grammar
    run --separate-stderr plcc-make
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"grammar file not found"* ]]
    [[ "$stderr" == *"ghost.plcc"* ]]
    [[ "$stderr" == *"--grammar-file"* ]]
}

@test "plcc-make no build/.grammar no --grammar-file falls back to grammar.plcc" {
    run --separate-stderr plcc-make
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"grammar.plcc"* ]]
}
```

- [ ] **Step 2: Run bats tests to confirm they fail**

```bash
bin/test/commands.bash tests/bats/commands/plcc-make.bats 2>&1 | tail -20
```

Expected: the new sticky grammar tests fail (write not implemented yet).

- [ ] **Step 3: Add `write_grammar` call in `make.py` after `write_sentinel`**

Find the line `write_sentinel(build_dir, new_hash, required_stages)` near the end of `main()` and add immediately after it:

```python
    write_grammar(build_dir, grammar)
```

- [ ] **Step 4: Run bats tests to confirm they pass**

```bash
bin/test/commands.bash tests/bats/commands/plcc-make.bats 2>&1 | tail -20
```

Expected: all plcc-make.bats tests pass.

- [ ] **Step 5: Run full unit suite**

```bash
bin/test/units.bash 2>&1 | tail -5
```

Expected: all passing.

- [ ] **Step 6: Commit**

```bash
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  add src/plcc/cmd/make.py tests/bats/commands/plcc-make.bats
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  commit -m "feat(make): write build/.grammar after successful build; add bats tests"
```

---

## Task 5: Update `plcc-scan`

**Files:**
- Modify: `src/plcc/cmd/scan.py`

- [ ] **Step 1: Update the docstring**

In `src/plcc/cmd/scan.py`, find:

```
    --grammar-file=<path>       Path to the PLCC grammar file [default: grammar.plcc].
```

Replace with:

```
    --grammar-file=<path>       Grammar to build from. Once set, remembered for subsequent
                                commands until changed. Defaults to grammar.plcc on first use.
```

- [ ] **Step 2: Update `main()` — skip local check and update verbose emit**

Find:

```python
    grammar_file = args["--grammar-file"]
    ...
    if not os.path.exists(grammar_file):
        print(f"plcc-scan: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-scan --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message=f"scanning with {grammar_file}")
```

Replace with:

```python
    grammar_file = args["--grammar-file"]

    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-scan: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-scan --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message="scanning")
```

- [ ] **Step 3: Update the `plcc-make` subprocess call**

Find:

```python
        ['plcc-make', '--through=scan', f'--grammar-file={grammar_file}'] + child_flags,
```

Replace with:

```python
        ['plcc-make', '--through=scan']
        + ([f'--grammar-file={grammar_file}'] if grammar_file is not None else [])
        + child_flags,
```

- [ ] **Step 4: Run tests**

```bash
bin/test/units.bash -k scan 2>&1 | tail -5
bin/test/commands.bash tests/bats/commands/plcc-scan.bats 2>&1 | tail -10
```

Expected: all passing.

- [ ] **Step 5: Commit**

```bash
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  add src/plcc/cmd/scan.py
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  commit -m "feat(scan): delegate grammar resolution to plcc-make"
```

---

## Task 6: Update `plcc-parse`

**Files:**
- Modify: `src/plcc/cmd/parse.py`

- [ ] **Step 1: Update the docstring**

In `src/plcc/cmd/parse.py`, find:

```
    --grammar-file=<path>       Path to the PLCC grammar file [default: grammar.plcc].
```

Replace with:

```
    --grammar-file=<path>       Grammar to build from. Once set, remembered for subsequent
                                commands until changed. Defaults to grammar.plcc on first use.
```

- [ ] **Step 2: Update `main()` — skip local check and update verbose emit**

Find:

```python
    grammar_file = args["--grammar-file"]
    ...
    if not os.path.exists(grammar_file):
        print(f"plcc-parse: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-parse --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message=f"parsing with {grammar_file}")
```

Replace with:

```python
    grammar_file = args["--grammar-file"]

    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-parse: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-parse --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message="parsing")
```

- [ ] **Step 3: Update the `plcc-make` subprocess call**

Find:

```python
        ['plcc-make', '--through=parse', f'--grammar-file={grammar_file}'] + child_flags,
```

Replace with:

```python
        ['plcc-make', '--through=parse']
        + ([f'--grammar-file={grammar_file}'] if grammar_file is not None else [])
        + child_flags,
```

- [ ] **Step 4: Run tests**

```bash
bin/test/units.bash -k parse 2>&1 | tail -5
bin/test/commands.bash tests/bats/commands/plcc-parse.bats 2>&1 | tail -10
```

Expected: all passing.

- [ ] **Step 5: Commit**

```bash
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  add src/plcc/cmd/parse.py
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  commit -m "feat(parse): delegate grammar resolution to plcc-make"
```

---

## Task 7: Update `plcc-rep`

**Files:**
- Modify: `src/plcc/cmd/rep.py`

- [ ] **Step 1: Update the docstring**

In `src/plcc/cmd/rep.py`, find:

```
    --grammar-file=<path>   Path to the PLCC grammar file [default: grammar.plcc].
```

Replace with:

```
    --grammar-file=<path>   Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to grammar.plcc on first use.
```

- [ ] **Step 2: Update `main()` — skip local check and update verbose emit**

Find:

```python
    if not os.path.exists(grammar_file):
        print(f"plcc-rep: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-rep --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message=f'starting rep with {grammar_file}')
```

Replace with:

```python
    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-rep: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-rep --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message='starting')
```

- [ ] **Step 3: Update the `plcc-make` subprocess call**

Find:

```python
        ['plcc-make', f'--grammar-file={grammar_file}'] + child_flags,
```

Replace with:

```python
        ['plcc-make']
        + ([f'--grammar-file={grammar_file}'] if grammar_file is not None else [])
        + child_flags,
```

- [ ] **Step 4: Run tests**

```bash
bin/test/units.bash -k rep 2>&1 | tail -5
bin/test/commands.bash tests/bats/commands/plcc-rep.bats 2>&1 | tail -10
```

Expected: all passing.

- [ ] **Step 5: Commit**

```bash
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  add src/plcc/cmd/rep.py
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  commit -m "feat(rep): delegate grammar resolution to plcc-make"
```

---

## Task 8: Update `plcc-diagram`

**Files:**
- Modify: `src/plcc/cmd/diagram.py`

- [ ] **Step 1: Update the docstring**

In `src/plcc/cmd/diagram.py`, find:

```
    --grammar-file=<path>   Path to the PLCC grammar file [default: grammar.plcc].
```

Replace with:

```
    --grammar-file=<path>   Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to grammar.plcc on first use.
```

- [ ] **Step 2: Update `main()` — skip local check and update verbose emit**

Find:

```python
    if not os.path.exists(grammar_file):
        print(f"plcc-diagram: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message=f"generating diagram for {grammar_file}")
```

Replace with:

```python
    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-diagram: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message="generating diagram")
```

- [ ] **Step 3: Update the `plcc-make` subprocess call**

Find:

```python
        ['plcc-make', '--through=model', f'--grammar-file={grammar_file}'] + child_flags,
```

Replace with:

```python
        ['plcc-make', '--through=model']
        + ([f'--grammar-file={grammar_file}'] if grammar_file is not None else [])
        + child_flags,
```

- [ ] **Step 4: Run tests**

```bash
bin/test/units.bash -k diagram 2>&1 | tail -5
bin/test/commands.bash tests/bats/commands/plcc-diagram.bats 2>&1 | tail -10
```

Expected: all passing.

- [ ] **Step 5: Commit**

```bash
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  add src/plcc/cmd/diagram.py
git -C /workspaces/plcc-ng/.worktrees/038-rep-stale-build-confusion \
  commit -m "feat(diagram): delegate grammar resolution to plcc-make"
```

---

## Self-Review Checklist (for plan author — do not delegate)

- [ ] All spec requirements covered by a task
- [ ] No TBDs or placeholders
- [ ] Type/name consistency across tasks (`read_grammar`, `write_grammar`, `explicit_grammar`, `stored_grammar`, `grammar`)
- [ ] Error messages go to stderr in all paths
- [ ] `write_grammar` is called only on the success path (after `write_sentinel`)
- [ ] Wipe uses `shutil.rmtree` + `build_dir.mkdir()` (not just sentinel delete)
