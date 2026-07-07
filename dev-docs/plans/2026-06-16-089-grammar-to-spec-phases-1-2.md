# Grammar-to-Spec Rename — Phases 1 & 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename all user-facing "grammar" references to "spec" — CLI flags (`--grammar`/`-g` → `--spec`/`-s`), default filename (`grammar.plcc` → `spec.plcc`), error messages, help text, and banner output. Hard rename; no backward-compat aliases.

**Architecture:** The preparatory refactor (PR #205) centralized everything into two modules — `build/grammar.py` (default filename) and `cmd/grammar.py` (CLI option text, args key, error text, child flag). Five source files change; each is committed with its tests. Tasks are ordered so cross-cutting test breakage is minimal.

**Tech Stack:** Python, docopt, pytest

**Working directory:** All commands run from inside the `.worktrees/089-grammar-to-spec-rename/` worktree. Use plain `git add` / `git commit` — no `-C` prefix needed.

---

## File Map

| Action | File | Purpose |
| ------ | ---- | ------- |
| Modify | `src/plcc/build/grammar.py` | Change `DEFAULT_GRAMMAR_FILE` value |
| Modify | `src/plcc/cmd/grammar.py` | Rename flag, args key, error text, child flag string |
| Modify | `src/plcc/cmd/grammar_test.py` | Update assertions for new flag and args key |
| Modify | `src/plcc/cmd/make.py` | Update args key, error messages, verbose emit, docstring |
| Modify | `src/plcc/cmd/make_test.py` | Update flag invocations, error text, filename, banner assertions |
| Modify | `src/plcc/cmd/output.py` | Change banner label from `grammar:` to `spec:` |
| Modify | `src/plcc/cmd/scan_test.py` | Update banner assertion |
| Modify | `src/plcc/cmd/parse_test.py` | Update banner assertion |
| Modify | `src/plcc/cmd/rep_test.py` | Update banner assertion and flag invocation |
| Modify | `src/plcc/cmd/diagram_test.py` | Update error text and banner assertions |
| Modify | `src/plcc/cmd/rep.py` | Update "no semantic sections" error message |

---

## Task 1: Change `DEFAULT_GRAMMAR_FILE` in `build/grammar.py`

**Files:**

- Modify: `src/plcc/build/grammar.py`

`build/grammar_test.py` already asserts `== DEFAULT_GRAMMAR_FILE` (uses the constant, not a string literal), so no test-file changes are needed here. After this commit, `make_test.py::test_no_grammar_flag_no_stored_falls_back_to_grammar_plcc` will be red — expected, fixed in Task 3.

- [ ] **Step 1: Change `DEFAULT_GRAMMAR_FILE`**

In `src/plcc/build/grammar.py`, change:

```python
DEFAULT_GRAMMAR_FILE = "grammar.plcc"
```

to:

```python
DEFAULT_GRAMMAR_FILE = "spec.plcc"
```

- [ ] **Step 2: Run build unit tests — confirm all pass**

```bash
bin/test/units.bash src/plcc/build/grammar_test.py -v
```

Expected: 8 passed

- [ ] **Step 3: Commit**

```bash
git -C .worktrees/089-grammar-to-spec-rename add src/plcc/build/grammar.py
git -C .worktrees/089-grammar-to-spec-rename commit -m "feat(089): rename default spec file grammar.plcc → spec.plcc"
```

---

## Task 2: Rename CLI flag in `cmd/grammar.py`

**Files:**

- Modify: `src/plcc/cmd/grammar_test.py`
- Modify: `src/plcc/cmd/grammar.py`

After this commit, `diagram_test.py::test_grammar_file_not_found_prints_error` and `rep_test.py` line 50 will be red — expected, fixed in Tasks 4–5.

- [ ] **Step 1: Rewrite `src/plcc/cmd/grammar_test.py` with failing tests**

Replace the entire file with:

```python
import pytest
from plcc.cmd.grammar import validate_grammar_flag, grammar_flag_for_child, GRAMMAR_OPTION
from plcc.build.grammar import DEFAULT_GRAMMAR_FILE


def test_grammar_option_contains_flag():
    assert '--spec' in GRAMMAR_OPTION


def test_grammar_option_contains_default_filename():
    assert DEFAULT_GRAMMAR_FILE in GRAMMAR_OPTION


def test_validate_grammar_flag_none_does_nothing():
    validate_grammar_flag('plcc-test', {'--spec': None})


def test_validate_grammar_flag_existing_file_does_nothing(tmp_path):
    f = tmp_path / 'foo.plcc'
    f.write_text('')
    validate_grammar_flag('plcc-test', {'--spec': str(f)})


def test_validate_grammar_flag_missing_file_exits_nonzero():
    with pytest.raises(SystemExit) as exc:
        validate_grammar_flag('plcc-test', {'--spec': 'nonexistent.plcc'})
    assert exc.value.code != 0


def test_validate_grammar_flag_missing_file_prints_cmd_name(capsys):
    with pytest.raises(SystemExit):
        validate_grammar_flag('plcc-test', {'--spec': 'nonexistent.plcc'})
    assert 'plcc-test' in capsys.readouterr().err


def test_validate_grammar_flag_missing_file_prints_path(capsys):
    with pytest.raises(SystemExit):
        validate_grammar_flag('plcc-test', {'--spec': 'nonexistent.plcc'})
    assert 'nonexistent.plcc' in capsys.readouterr().err


def test_grammar_flag_for_child_none_returns_empty():
    assert grammar_flag_for_child({'--spec': None}) == []


def test_grammar_flag_for_child_path_returns_flag():
    assert grammar_flag_for_child({'--spec': 'foo.plcc'}) == ['--spec=foo.plcc']
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
bin/test/units.bash src/plcc/cmd/grammar_test.py -v
```

Expected: failures on `--spec`, `--grammar`, `grammar_flag_for_child` assertions

- [ ] **Step 3: Rewrite `src/plcc/cmd/grammar.py`**

Replace the entire file with:

```python
import os
import sys

from plcc.build.grammar import DEFAULT_GRAMMAR_FILE

GRAMMAR_OPTION = f"""\
    -s <path> --spec=<path>
                            Spec to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to {DEFAULT_GRAMMAR_FILE} on first use.
"""


def validate_grammar_flag(cmd_name, args):
    path = args['--spec']
    if path is not None and not os.path.exists(path):
        print(f"{cmd_name}: spec file not found: {path}", file=sys.stderr)
        print(file=sys.stderr)
        print(f"Run '{cmd_name} --help' for more information.", file=sys.stderr)
        sys.exit(1)


def grammar_flag_for_child(args):
    path = args['--spec']
    return [f'--spec={path}'] if path is not None else []
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/grammar_test.py -v
```

Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git -C .worktrees/089-grammar-to-spec-rename add src/plcc/cmd/grammar.py src/plcc/cmd/grammar_test.py
git -C .worktrees/089-grammar-to-spec-rename commit -m "feat(089): rename CLI flag --grammar/-g → --spec/-s"
```

---

## Task 3: Update `cmd/make.py`, `cmd/make_test.py`, and `cmd/output.py`

**Files:**

- Modify: `src/plcc/cmd/make_test.py`
- Modify: `src/plcc/cmd/make.py`
- Modify: `src/plcc/cmd/output.py`

`make_test.py` has banner tests that check `output.py`'s output, so `output.py` is updated in the same task to keep the test suite green at commit time.

After this commit, banner assertions in `scan_test.py`, `parse_test.py`, `rep_test.py`, and `diagram_test.py` will be red — expected, fixed in Task 4.

- [ ] **Step 1: Update `src/plcc/cmd/make_test.py` with failing assertions**

Apply these changes (each is an independent edit):

**a.** `test_grammar_file_not_found_prints_error` — change error text:

```python
def test_grammar_file_not_found_prints_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main([])
    _, err = capsys.readouterr()
    assert "spec file not found" in err
```

**b.** `test_grammar_flag_not_found_exits_nonzero` — change flag:

```python
def test_grammar_flag_not_found_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main(['--spec=nonexistent.plcc'])
    assert exc.value.code != 0
```

**c.** `test_short_grammar_flag_not_found_exits_nonzero` — change flag:

```python
def test_short_grammar_flag_not_found_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main(['-s', 'nonexistent.plcc'])
    assert exc.value.code != 0
```

**d.** Rename test and update assertion — default filename:

```python
def test_no_spec_flag_no_stored_falls_back_to_spec_plcc(tmp_path, monkeypatch, capsys):
    # Fresh directory, no spec.plcc → error names spec.plcc
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main([])
    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert "spec.plcc" in err
```

**e.** `test_no_grammar_flag_stored_grammar_missing_errors_to_stderr` — update error text and flag hint:

```python
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
    assert "spec file not found" in err
    assert "missing.plcc" in err
    assert "--spec" in err
```

**f.** `test_no_grammar_flag_uses_stored_grammar_path` — update comment and fallback assertion:

```python
def test_no_grammar_flag_uses_stored_grammar_path(tmp_path, monkeypatch, capsys):
    # build/.grammar set to a.plcc (missing) — error names a.plcc, not spec.plcc
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    write_grammar(build, "a.plcc")
    with pytest.raises(SystemExit):
        run_main([])
    _, err = capsys.readouterr()
    assert "a.plcc" in err
    # Must NOT fall back to spec.plcc
    assert "spec.plcc" not in err
```

**g.** `test_explicit_grammar_differs_from_stored_wipes_build` — change flag:

```python
def test_explicit_grammar_differs_from_stored_wipes_build(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    (build / "marker.txt").write_text("from old grammar")
    write_grammar(build, "old.plcc")
    (tmp_path / "new.plcc").write_text("")  # valid but empty grammar
    run_main(["--spec=new.plcc"])
    # build/ was wiped when grammar changed, marker should not exist
    assert not (build / "marker.txt").exists()
```

**h.** `test_explicit_grammar_same_as_stored_does_not_wipe` — change flag:

```python
def test_explicit_grammar_same_as_stored_does_not_wipe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    (build / "marker.txt").write_text("from current grammar")
    write_grammar(build, "same.plcc")
    (tmp_path / "same.plcc").write_text("")  # valid but empty grammar
    run_main(["--spec=same.plcc"])
    # No wipe — marker is still present because grammar didn't change
    assert (build / "marker.txt").exists()
```

**i.** `test_grammar_written_before_build_stages_run` — change flag:

```python
def test_grammar_written_before_build_stages_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    (tmp_path / "bad.plcc").write_text("token BAD @@@\n")
    with pytest.raises(SystemExit):
        run_main(["--spec=bad.plcc"])
    assert read_grammar(build) == "bad.plcc"
```

**j.** `test_make_main_banner_prints_version_to_stderr` — use `spec.plcc`:

```python
def test_make_main_banner_prints_version_to_stderr(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spec.plcc").write_text("")
    monkeypatch.setattr("plcc.cmd.make.get_version", lambda: "1.2.3")
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **kw: SimpleNamespace(returncode=1, stderr=b""))
    with pytest.raises(SystemExit):
        run_main(["--banner"])
    _, err = capsys.readouterr()
    assert "plcc-ng 1.2.3" in err
```

**k.** `test_make_main_banner_prints_grammar_to_stderr` — rename test and update:

```python
def test_make_main_banner_prints_spec_to_stderr(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    spec = tmp_path / "spec.plcc"
    spec.write_text("")
    monkeypatch.setattr("plcc.cmd.make.get_version", lambda: "1.2.3")
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **kw: SimpleNamespace(returncode=1, stderr=b""))
    with pytest.raises(SystemExit):
        run_main(["--banner"])
    _, err = capsys.readouterr()
    assert "spec:" in err
    assert str(spec) in err
```

**l.** `test_make_main_banner_short_flag_works` — use `spec.plcc`:

```python
def test_make_main_banner_short_flag_works(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spec.plcc").write_text("")
    monkeypatch.setattr("plcc.cmd.make.get_version", lambda: "1.2.3")
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **kw: SimpleNamespace(returncode=1, stderr=b""))
    with pytest.raises(SystemExit):
        run_main(["-b"])
    _, err = capsys.readouterr()
    assert "plcc-ng 1.2.3" in err
```

**m.** `test_make_main_banner_is_plain_text_with_json_format` — use `spec.plcc`:

```python
def test_make_main_banner_is_plain_text_with_json_format(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spec.plcc").write_text("")
    monkeypatch.setattr("plcc.cmd.make.get_version", lambda: "1.2.3")
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **kw: SimpleNamespace(returncode=1, stderr=b""))
    with pytest.raises(SystemExit):
        run_main(["--banner", "--verbose-format=json"])
    _, err = capsys.readouterr()
    assert "plcc-ng 1.2.3" in err  # plain "plcc-ng X.Y.Z", not a JSON object
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
bin/test/units.bash src/plcc/cmd/make_test.py -v
```

Expected: failures on `--spec`, `"spec file not found"`, `"spec.plcc"`, `"spec:"`, `"--spec"` assertions

- [ ] **Step 3: Update `src/plcc/cmd/make.py`**

Change line 59:

```python
explicit_grammar = args['--spec']
```

Change lines 25, 76, 79, 85, 99 (the docstring and error messages):

```python
__doc__ = """plcc-make
    Build a PLCC project from a spec file.
```

```python
    if explicit_grammar is None and stored_grammar is not None and not os.path.exists(grammar):
        print(f"plcc-make: spec file not found: {grammar}", file=sys.stderr)
        print(
            "(the active spec was set by a previous run; "
            "use --spec to specify a different one)",
            file=sys.stderr,
        )
        sys.exit(1)

    if not os.path.exists(grammar):
        print(f"plcc-make: spec file not found: {grammar}", file=sys.stderr)
        sys.exit(1)
```

```python
    verbose.emit(Events.STARTED, message=f"spec: {grammar}")
```

- [ ] **Step 4: Update `src/plcc/cmd/output.py`**

Change line 10:

```python
    print(f"spec: {grammar_path}", file=sys.stderr, flush=True)
```

- [ ] **Step 5: Run make tests — confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/make_test.py -v
```

Expected: all passing (the ll1/report tests are unaffected — "grammar is not LL(1)" is a parsing concept and does not change)

- [ ] **Step 6: Commit**

```bash
git -C .worktrees/089-grammar-to-spec-rename add \
    src/plcc/cmd/make.py src/plcc/cmd/make_test.py src/plcc/cmd/output.py
git -C .worktrees/089-grammar-to-spec-rename commit -m "feat(089): update make error messages, banner, and default spec filename"
```

---

## Task 4: Fix banner assertions in scan, parse, rep, and diagram tests

**Files:**

- Modify: `src/plcc/cmd/scan_test.py`
- Modify: `src/plcc/cmd/parse_test.py`
- Modify: `src/plcc/cmd/rep_test.py`
- Modify: `src/plcc/cmd/diagram_test.py`

`output.py` was already updated in Task 3 to print `spec:` instead of `grammar:`. These four test files now have stale assertions; this task brings them in line. No source file changes — only test assertions.

- [ ] **Step 1: Update `src/plcc/cmd/scan_test.py`**

Change `test_main_banner_prints_grammar_to_stderr` (the function that asserts `"grammar:" in err`):

```python
def test_main_banner_prints_grammar_to_stderr(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    (build / ".grammar").write_text(str(tmp_path / "grammar.plcc"))
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0))
    monkeypatch.setattr(_scan_module, "SourceRunner",
                        lambda **kw: type("R", (), {"run": lambda self, s, h: True})())
    monkeypatch.setattr("plcc.cmd.scan.get_version", lambda: "1.2.3")
    run_main(["--banner"])
    _, err = capsys.readouterr()
    assert "spec:" in err
    assert str(tmp_path / "grammar.plcc") in err
```

- [ ] **Step 2: Update `src/plcc/cmd/parse_test.py`**

Change `test_parse_main_banner_prints_grammar_to_stderr` (asserts `"grammar:" in err`):

```python
def test_parse_main_banner_prints_grammar_to_stderr(monkeypatch, tmp_path, capsys):
    _setup_parse_main(monkeypatch, tmp_path)
    from .parse import main as parse_main
    parse_main(["--banner"])
    _, err = capsys.readouterr()
    assert "spec:" in err
    assert str(tmp_path / "grammar.plcc") in err
```

- [ ] **Step 3: Update `src/plcc/cmd/rep_test.py`**

Change `test_rep_main_banner_prints_grammar_to_stderr` (asserts `"grammar:" in err`):

```python
def test_rep_main_banner_prints_grammar_to_stderr(monkeypatch, tmp_path, capsys):
    _setup_rep_main(monkeypatch, tmp_path)
    _rep_module.main(["--tool=calc", "--banner"])
    _, err = capsys.readouterr()
    assert "spec:" in err
    assert str(tmp_path / "grammar.plcc") in err
```

- [ ] **Step 4: Update `src/plcc/cmd/diagram_test.py`**

Change `test_diagram_main_banner_prints_grammar_to_stderr` (asserts `"grammar:" in err`):

```python
def test_diagram_main_banner_prints_grammar_to_stderr(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'build'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    (build_dir / '.grammar').write_text(str(grammar))
    monkeypatch.chdir(tmp_path)
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr=b'')
        with patch('plcc.cmd.diagram.get_version', return_value='1.2.3'):
            with pytest.raises(SystemExit):
                run_main(['--banner'])
    _, err = capsys.readouterr()
    assert "spec:" in err
    assert str(grammar) in err
```

- [ ] **Step 5: Run these four test files — confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/scan_test.py src/plcc/cmd/parse_test.py src/plcc/cmd/rep_test.py src/plcc/cmd/diagram_test.py -v
```

Expected: all banner tests pass; `diagram_test.py::test_grammar_file_not_found_prints_error` and `rep_test.py` line 50 still fail — fixed in Task 5

- [ ] **Step 6: Commit**

```bash
git -C .worktrees/089-grammar-to-spec-rename add \
    src/plcc/cmd/scan_test.py src/plcc/cmd/parse_test.py \
    src/plcc/cmd/rep_test.py src/plcc/cmd/diagram_test.py
git -C .worktrees/089-grammar-to-spec-rename commit -m "feat(089): update banner test assertions grammar: → spec:"
```

---

## Task 5: Update `cmd/rep.py` and remaining stale assertions

**Files:**

- Modify: `src/plcc/cmd/rep_test.py`
- Modify: `src/plcc/cmd/diagram_test.py`
- Modify: `src/plcc/cmd/rep.py`

Two remaining failures:

1. `diagram_test.py::test_grammar_file_not_found_prints_error` — asserts `"grammar file not found"` but `validate_grammar_flag` now prints `"spec file not found"` (changed in Task 2)
2. `rep_test.py` line 50 — calls `main(["--grammar=grammar.plcc", ...])` but the flag is now `--spec`
3. `rep.py` line 155 — prints `"no semantic sections found in grammar."` — a user-visible message to update

- [ ] **Step 1: Fix `src/plcc/cmd/diagram_test.py::test_grammar_file_not_found_prints_error`**

```python
def test_grammar_file_not_found_prints_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main([])
    _, err = capsys.readouterr()
    assert "spec file not found" in err
```

- [ ] **Step 2: Fix `src/plcc/cmd/rep_test.py` line 50 — update `--grammar` flag call**

Find the test that calls `_rep_module.main(["--grammar=grammar.plcc", "--tool=calc"])` and change to:

```python
    _rep_module.main(["--spec=grammar.plcc", "--tool=calc"])
```

- [ ] **Step 3: Run diagram and rep tests — confirm those two specific failures are fixed**

```bash
bin/test/units.bash src/plcc/cmd/diagram_test.py src/plcc/cmd/rep_test.py -v
```

Expected: `test_grammar_file_not_found_prints_error` passes; the `--spec` call no longer raises a docopt error.

- [ ] **Step 4: Update the error message in `src/plcc/cmd/rep.py`**

Change line 155:

```python
        print("plcc-rep: no semantic sections found in spec.", file=sys.stderr)
```

- [ ] **Step 5: Run rep tests — confirm all pass**

```bash
bin/test/units.bash src/plcc/cmd/rep_test.py -v
```

Expected: all pass

- [ ] **Step 6: Commit**

```bash
git -C .worktrees/089-grammar-to-spec-rename add \
    src/plcc/cmd/rep.py src/plcc/cmd/rep_test.py src/plcc/cmd/diagram_test.py
git -C .worktrees/089-grammar-to-spec-rename commit -m "feat(089): update rep error message and remaining stale test assertions"
```

---

## Task 6: Full functional test suite

- [ ] **Step 1: Run all tiers**

```bash
bin/test/functional.bash
```

Expected: all tests pass — units, commands, integration, e2e

- [ ] **Step 2: If any bats tests fail, check the `--help` output for the affected command**

Flag and help-text changes may break bats tests that match on `--grammar`, `-g`, or `grammar.plcc`. Update the bats assertion to match the new output. The CLI behavior is identical — only option names and default filename changed.
