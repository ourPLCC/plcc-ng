# Level-2 Startup Info Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Print version and grammar path at startup for `plcc-scan`, `plcc-parse`, and `plcc-rep`; `plcc-rep` also prints `Running <tool> with <language>.`

**Architecture:** Add `print_startup_banner()` to `output.py`, then call it in each command's `main()` right after `plcc-make` returns successfully. Grammar path is read from `build/.grammar` (sticky-grammar sentinel) and resolved to absolute. Version comes from `plcc.version.get_version()`.

**Tech Stack:** Python, pytest, `plcc.version.get_version`, `plcc.build.grammar.read_grammar`, `os.path.abspath`

---

## File Map

| File | Change |
|---|---|
| `src/plcc/cmd/output.py` | Add `print_startup_banner()` |
| `src/plcc/cmd/output_test.py` | Tests for `print_startup_banner()` |
| `src/plcc/cmd/scan.py` | Call banner after make |
| `src/plcc/cmd/scan_test.py` | Tests for banner in `scan.main()` |
| `src/plcc/cmd/parse.py` | Call banner after make |
| `src/plcc/cmd/parse_test.py` | Tests for banner in `parse.main()` |
| `src/plcc/cmd/rep.py` | Call banner after make + `_resolve_tool` |
| `src/plcc/cmd/rep_test.py` | Tests for banner in `rep.main()` |

All work is in the worktree at `.worktrees/049-level-2-startup-info/`. Run all commands from inside that directory.

---

## Task 1: `print_startup_banner()` in `output.py`

**Files:**
- Modify: `src/plcc/cmd/output.py`
- Modify: `src/plcc/cmd/output_test.py`

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/cmd/output_test.py`:

```python
from .output import print_startup_banner


def test_print_startup_banner_contains_version(capsys):
    print_startup_banner("/abs/path/grammar.plcc", "1.2.3")
    out, _ = capsys.readouterr()
    assert "plcc-ng 1.2.3" in out


def test_print_startup_banner_contains_grammar_path(capsys):
    print_startup_banner("/abs/path/grammar.plcc", "1.2.3")
    out, _ = capsys.readouterr()
    assert "/abs/path/grammar.plcc" in out


def test_print_startup_banner_goes_to_stdout(capsys):
    print_startup_banner("/abs/path/grammar.plcc", "1.2.3")
    _, err = capsys.readouterr()
    assert err == ""


def test_print_startup_banner_no_tool_prints_one_line(capsys):
    print_startup_banner("/abs/path/grammar.plcc", "1.2.3")
    out, _ = capsys.readouterr()
    assert out.count("\n") == 1


def test_print_startup_banner_with_tool_prints_running_line(capsys):
    print_startup_banner("/abs/path/grammar.plcc", "1.2.3", tool="calc", language="python")
    out, _ = capsys.readouterr()
    assert "Running calc with python." in out


def test_print_startup_banner_tool_line_goes_to_stdout(capsys):
    print_startup_banner("/abs/path/grammar.plcc", "1.2.3", tool="calc", language="python")
    _, err = capsys.readouterr()
    assert err == ""


def test_print_startup_banner_with_tool_prints_two_lines(capsys):
    print_startup_banner("/abs/path/grammar.plcc", "1.2.3", tool="calc", language="python")
    out, _ = capsys.readouterr()
    assert out.count("\n") == 2
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/cmd/output_test.py -v
```

Expected: `ImportError` or `FAILED` — `print_startup_banner` does not exist yet.

- [ ] **Step 3: Implement `print_startup_banner` in `output.py`**

The current content of `src/plcc/cmd/output.py` is:

```python
def print_user_error(message):
    print(message, flush=True)
```

Replace it with:

```python
def print_user_error(message):
    print(message, flush=True)


def print_startup_banner(grammar_path, version, tool=None, language=None):
    print(f"plcc-ng {version}  grammar: {grammar_path}", flush=True)
    if tool is not None and language is not None:
        print(f"Running {tool} with {language}.", flush=True)
```

- [ ] **Step 4: Run the tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/output_test.py -v
```

Expected: all 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/output.py src/plcc/cmd/output_test.py
git commit -m "feat(cmd): add print_startup_banner to output.py"
```

---

## Task 2: Banner in `plcc-scan`

**Files:**
- Modify: `src/plcc/cmd/scan.py`
- Modify: `src/plcc/cmd/scan_test.py`

`scan_test.py` has two `autouse=True` fixtures: `grammar` (chdirs to `tmp_path`, creates `grammar.plcc`) and `stub_make` (stubs `subprocess.run` to succeed). New tests rely on both and additionally write `build/.grammar`.

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/cmd/scan_test.py` (after existing imports, add `import plcc.cmd.scan as _scan_module` and the tests below):

```python
import plcc.cmd.scan as _scan_module
```

Then add these tests:

```python
def test_main_banner_contains_version(monkeypatch, tmp_path, capsys):
    build = tmp_path / "build"
    build.mkdir()
    (build / ".grammar").write_text(str(tmp_path / "grammar.plcc"))
    monkeypatch.setattr(_scan_module, "SourceRunner",
                        lambda **kw: type("R", (), {"run": lambda self, s, h: True})())
    monkeypatch.setattr("plcc.cmd.scan.get_version", lambda: "1.2.3")
    run_main([])
    out, _ = capsys.readouterr()
    assert "plcc-ng 1.2.3" in out


def test_main_banner_contains_grammar_path(monkeypatch, tmp_path, capsys):
    build = tmp_path / "build"
    build.mkdir()
    (build / ".grammar").write_text(str(tmp_path / "grammar.plcc"))
    monkeypatch.setattr(_scan_module, "SourceRunner",
                        lambda **kw: type("R", (), {"run": lambda self, s, h: True})())
    monkeypatch.setattr("plcc.cmd.scan.get_version", lambda: "1.2.3")
    run_main([])
    out, _ = capsys.readouterr()
    assert str(tmp_path / "grammar.plcc") in out


def test_main_banner_goes_to_stdout(monkeypatch, tmp_path, capsys):
    build = tmp_path / "build"
    build.mkdir()
    (build / ".grammar").write_text(str(tmp_path / "grammar.plcc"))
    monkeypatch.setattr(_scan_module, "SourceRunner",
                        lambda **kw: type("R", (), {"run": lambda self, s, h: True})())
    monkeypatch.setattr("plcc.cmd.scan.get_version", lambda: "1.2.3")
    run_main([])
    _, err = capsys.readouterr()
    assert "plcc-ng" not in err
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/cmd/scan_test.py::test_main_banner_contains_version src/plcc/cmd/scan_test.py::test_main_banner_contains_grammar_path src/plcc/cmd/scan_test.py::test_main_banner_goes_to_stdout -v
```

Expected: `FAILED` — no banner output yet.

- [ ] **Step 3: Add the banner call to `scan.py`**

In `src/plcc/cmd/scan.py`, add these imports at the top with the other imports:

```python
from plcc.version import get_version
from plcc.build.grammar import read_grammar
from .output import print_startup_banner
```

The current import from `.output` is:
```python
from .output import print_user_error
```

Replace it with:
```python
from .output import print_startup_banner, print_user_error
```

Then in `main()`, after the make returncode check (currently at line ~157):

```python
    make_result = subprocess.run(
        ['plcc-make', '--through=scan']
        + ([f'--grammar={grammar_file}'] if grammar_file is not None else [])
        + child_flags,
        stderr=None,
    )
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    print_startup_banner(os.path.abspath(read_grammar('build')), get_version())  # ADD THIS LINE
```

`os` is already imported in `scan.py`. Also add these two imports at the top alongside the existing imports:

```python
from plcc.version import get_version
from plcc.build.grammar import read_grammar
```

- [ ] **Step 4: Run the tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/scan_test.py::test_main_banner_contains_version src/plcc/cmd/scan_test.py::test_main_banner_contains_grammar_path src/plcc/cmd/scan_test.py::test_main_banner_goes_to_stdout -v
```

Expected: all 3 pass.

- [ ] **Step 5: Run the full scan test suite to check for regressions**

```bash
bin/test/units.bash src/plcc/cmd/scan_test.py -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/scan.py src/plcc/cmd/scan_test.py
git commit -m "feat(scan): print startup banner after make"
```

---

## Task 3: Banner in `plcc-parse`

**Files:**
- Modify: `src/plcc/cmd/parse.py`
- Modify: `src/plcc/cmd/parse_test.py`

`parse_test.py` has no autouse grammar/stub_make fixtures — those must be set up manually per test. All parse main() tests need: `tmp_path` with `grammar.plcc`, `build/` with `.grammar`, `spec.json`, and `ll1.json`; `subprocess.run` stubbed; and `SourceRunner` stubbed. `subprocess.Popen` does not need stubbing — `SourceRunner` is fully stubbed so `ParseHandler.feed()` is never called.

- [ ] **Step 1: Write the failing tests**

`parse_test.py` currently imports `json`, `subprocess`, `sys`, `pytest`, `VerboseContext`, `ParseHandler`, and helpers from `_test_helpers`. It does not import `SimpleNamespace`. Add these two imports alongside the existing ones at the top:

```python
from types import SimpleNamespace
import plcc.cmd.parse as _parse_module
```

Then add these tests at the bottom of the file:

```python
def _setup_parse_main(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "grammar.plcc").write_text("")
    build = tmp_path / "build"
    build.mkdir()
    (build / ".grammar").write_text(str(tmp_path / "grammar.plcc"))
    (build / "spec.json").write_text("{}")
    (build / "ll1.json").write_text("{}")
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **kw: SimpleNamespace(returncode=0, stderr=b""))
    monkeypatch.setattr(_parse_module, "SourceRunner",
                        lambda **kw: type("R", (), {"run": lambda self, s, h: True})())
    monkeypatch.setattr("plcc.cmd.parse.get_version", lambda: "1.2.3")


def test_parse_main_banner_contains_version(monkeypatch, tmp_path, capsys):
    _setup_parse_main(monkeypatch, tmp_path)
    from .parse import main as parse_main
    parse_main([])
    out, _ = capsys.readouterr()
    assert "plcc-ng 1.2.3" in out


def test_parse_main_banner_contains_grammar_path(monkeypatch, tmp_path, capsys):
    _setup_parse_main(monkeypatch, tmp_path)
    from .parse import main as parse_main
    parse_main([])
    out, _ = capsys.readouterr()
    assert str(tmp_path / "grammar.plcc") in out


def test_parse_main_banner_goes_to_stdout(monkeypatch, tmp_path, capsys):
    _setup_parse_main(monkeypatch, tmp_path)
    from .parse import main as parse_main
    parse_main([])
    _, err = capsys.readouterr()
    assert "plcc-ng" not in err
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/cmd/parse_test.py::test_parse_main_banner_contains_version src/plcc/cmd/parse_test.py::test_parse_main_banner_contains_grammar_path src/plcc/cmd/parse_test.py::test_parse_main_banner_goes_to_stdout -v
```

Expected: `FAILED` — no banner output yet.

- [ ] **Step 3: Add the banner call to `parse.py`**

In `src/plcc/cmd/parse.py`, add these imports at the top alongside the existing imports:

```python
from plcc.version import get_version
from plcc.build.grammar import read_grammar
from .output import print_startup_banner
```

Then in `main()`, after the make returncode check:

```python
    make_result = subprocess.run(
        ['plcc-make', '--through=parse']
        + ([f'--grammar={grammar_file}'] if grammar_file is not None else [])
        + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        events = verbose.parse_child_events(make_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    print_startup_banner(os.path.abspath(read_grammar('build')), get_version())  # ADD THIS LINE
```

`os` is already imported in `parse.py`.

- [ ] **Step 4: Run the tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/parse_test.py::test_parse_main_banner_contains_version src/plcc/cmd/parse_test.py::test_parse_main_banner_contains_grammar_path src/plcc/cmd/parse_test.py::test_parse_main_banner_goes_to_stdout -v
```

Expected: all 3 pass.

- [ ] **Step 5: Run the full parse test suite to check for regressions**

```bash
bin/test/units.bash src/plcc/cmd/parse_test.py -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/parse.py src/plcc/cmd/parse_test.py
git commit -m "feat(parse): print startup banner after make"
```

---

## Task 4: Banner in `plcc-rep`

**Files:**
- Modify: `src/plcc/cmd/rep.py`
- Modify: `src/plcc/cmd/rep_test.py`

The banner for `plcc-rep` has two lines: the standard version+grammar line, then `Running <tool> with <language>.` It is printed after `_resolve_tool()` returns, since that is when both `tool_name` and `language` are known.

- [ ] **Step 1: Write the failing tests**

At the top of `src/plcc/cmd/rep_test.py`, confirm `import plcc.cmd.rep as _rep_module` is already present (it is).

Add these tests at the bottom:

```python
def _setup_rep_main(monkeypatch, tmp_path):
    """Set up filesystem and stubs for rep main() tests."""
    import json as _j
    monkeypatch.chdir(tmp_path)
    (tmp_path / "grammar.plcc").write_text("")
    build = tmp_path / "build"
    build.mkdir()
    (build / ".grammar").write_text(str(tmp_path / "grammar.plcc"))
    spec = {"semantics": [{"tool": "calc", "language": "python"}]}
    (build / "spec.json").write_text(_j.dumps(spec))
    (build / "ll1.json").write_text("{}")
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: _MagicMock(returncode=0, stderr=b""),
    )
    monkeypatch.setattr(
        "subprocess.Popen",
        lambda *a, **kw: _MagicMock(stdin=_MagicMock(), wait=_MagicMock()),
    )
    monkeypatch.setattr(_rep_module, "SourceRunner",
                        lambda **kw: type("R", (), {"run": lambda self, s, h: True})())
    monkeypatch.setattr("plcc.cmd.rep.get_version", lambda: "1.2.3")


def test_rep_main_banner_contains_version(monkeypatch, tmp_path, capsys):
    _setup_rep_main(monkeypatch, tmp_path)
    _rep_module.main(["--tool=calc"])
    out, _ = capsys.readouterr()
    assert "plcc-ng 1.2.3" in out


def test_rep_main_banner_contains_grammar_path(monkeypatch, tmp_path, capsys):
    _setup_rep_main(monkeypatch, tmp_path)
    _rep_module.main(["--tool=calc"])
    out, _ = capsys.readouterr()
    assert str(tmp_path / "grammar.plcc") in out


def test_rep_main_banner_contains_running_line(monkeypatch, tmp_path, capsys):
    _setup_rep_main(monkeypatch, tmp_path)
    _rep_module.main(["--tool=calc"])
    out, _ = capsys.readouterr()
    assert "Running calc with python." in out


def test_rep_main_banner_goes_to_stdout(monkeypatch, tmp_path, capsys):
    _setup_rep_main(monkeypatch, tmp_path)
    _rep_module.main(["--tool=calc"])
    _, err = capsys.readouterr()
    assert "plcc-ng" not in err
    assert "Running" not in err
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/cmd/rep_test.py::test_rep_main_banner_contains_version src/plcc/cmd/rep_test.py::test_rep_main_banner_contains_grammar_path src/plcc/cmd/rep_test.py::test_rep_main_banner_contains_running_line src/plcc/cmd/rep_test.py::test_rep_main_banner_goes_to_stdout -v
```

Expected: `FAILED` — no banner output yet.

- [ ] **Step 3: Add the banner call to `rep.py`**

In `src/plcc/cmd/rep.py`, add these imports at the top alongside the existing imports:

```python
from plcc.version import get_version
from plcc.build.grammar import read_grammar
```

The existing `.output` import is:
```python
from .output import print_user_error
```

Replace it with:
```python
from .output import print_startup_banner, print_user_error
```

Then in `main()`, right after `_resolve_tool()` returns and before `tool_dir` is used:

```python
    tool_name, language = _resolve_tool(spec, tool_name)
    print_startup_banner(                          # ADD THESE 3 LINES
        os.path.abspath(read_grammar('build')),
        get_version(),
        tool=tool_name,
        language=language,
    )
    tool_dir = os.path.join('build', tool_name)
```

`os` is already imported in `rep.py`.

- [ ] **Step 4: Run the tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/rep_test.py::test_rep_main_banner_contains_version src/plcc/cmd/rep_test.py::test_rep_main_banner_contains_grammar_path src/plcc/cmd/rep_test.py::test_rep_main_banner_contains_running_line src/plcc/cmd/rep_test.py::test_rep_main_banner_goes_to_stdout -v
```

Expected: all 4 pass.

- [ ] **Step 5: Run the full rep test suite to check for regressions**

```bash
bin/test/units.bash src/plcc/cmd/rep_test.py -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/rep.py src/plcc/cmd/rep_test.py
git commit -m "feat(rep): print startup banner after make"
```

---

## Final Check

- [ ] **Run all unit tests**

```bash
bin/test/units.bash -v
```

Expected: all pass.
