# PlantUML pip-install default diagram backend — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `plcc-plantuml-diagram-build` and `plcc-plantuml-diagram-run` plugins, make `plantuml` the default format, and wire `pip install plcc[diagram]` to the `plantuml` PyPI package so users get working diagrams with zero extra binaries.

**Architecture:** Two new plugin files in `src/plcc/diagram/plantuml/` follow the same structure as the existing mermaid plugins. The `plantuml` PyPI package is imported lazily inside `main()` so the module loads without it installed. Default format changes from `mermaid` to `plantuml` in five docstrings/fallbacks across the dispatcher and command layers.

**Tech Stack:** Python, `plantuml` PyPI package (calls plantuml.com web API), `docopt`, `pytest`, `bats`

**Working directory:** All commands run from `.worktrees/plantuml-pip-default/` unless stated otherwise.

---

## File Map

| Action | Path |
|--------|------|
| Create | `src/plcc/diagram/plantuml/build.py` |
| Create | `src/plcc/diagram/plantuml/build_test.py` |
| Create | `src/plcc/diagram/plantuml/run.py` |
| Create | `src/plcc/diagram/plantuml/run_test.py` |
| Create | `tests/bats/commands/plcc-plantuml-diagram-build.bats` |
| Create | `tests/bats/commands/plcc-plantuml-diagram-run.bats` |
| Modify | `pyproject.toml` — add two entry points + `plantuml` optional dep |
| Modify | `src/plcc/diagram/emit.py` — default mermaid → plantuml |
| Modify | `src/plcc/diagram/build.py` — default mermaid → plantuml |
| Modify | `src/plcc/diagram/run.py` — default mermaid → plantuml |
| Modify | `src/plcc/cmd/diagram.py` — default mermaid → plantuml |
| Modify | `src/plcc/cmd/make.py` — default mermaid → plantuml (docstring + fallback) |
| Modify | `src/plcc/diagram/emit_test.py` — update default assertion |
| Modify | `src/plcc/cmd/diagram_test.py` — update default assertion |

---

## Task 1: `plcc-plantuml-diagram-build` — unit tests

**Files:**
- Create: `src/plcc/diagram/plantuml/build_test.py`

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/diagram/plantuml/build_test.py`:

```python
import pytest
from unittest.mock import patch, MagicMock

from .build import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_missing_plantuml_lib_prints_helpful_error(tmp_path, capsys):
    src = tmp_path / "diagram.puml"
    src.write_text("@startuml\n@enduml\n")
    out = tmp_path / "diagram.png"

    with patch.dict('sys.modules', {'plantuml': None}):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={src}', f'--output={out}'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'pip install plcc[diagram]' in err


def test_calls_plantuml_server_and_writes_png(tmp_path):
    src = tmp_path / "diagram.puml"
    src.write_text("@startuml\nclass Foo {}\n@enduml\n")
    out = tmp_path / "diagram.png"
    fake_png = b'\x89PNG fake'

    mock_lib = MagicMock()
    mock_server = MagicMock()
    mock_server.processes.return_value = fake_png
    mock_lib.PlantUML.return_value = mock_server

    with patch.dict('sys.modules', {'plantuml': mock_lib}):
        run_main([f'--input={src}', f'--output={out}'])

    assert out.read_bytes() == fake_png
    mock_server.processes.assert_called_once()


def test_plantuml_error_prints_message_and_exits(tmp_path, capsys):
    src = tmp_path / "diagram.puml"
    src.write_text("@startuml\n@enduml\n")
    out = tmp_path / "diagram.png"

    mock_lib = MagicMock()
    mock_server = MagicMock()
    mock_server.processes.side_effect = Exception("connection refused")
    mock_lib.PlantUML.return_value = mock_server

    with patch.dict('sys.modules', {'plantuml': mock_lib}):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={src}', f'--output={out}'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'connection refused' in err
```

- [ ] **Step 2: Run tests to confirm they fail (import error)**

```bash
pdm test src/plcc/diagram/plantuml/build_test.py -v
```

Expected: errors like `ModuleNotFoundError: No module named 'plcc.diagram.plantuml.build'`

---

## Task 2: `plcc-plantuml-diagram-build` — implementation

**Files:**
- Create: `src/plcc/diagram/plantuml/build.py`

- [ ] **Step 1: Implement `plcc-plantuml-diagram-build`**

Create `src/plcc/diagram/plantuml/build.py`:

```python
import enum
import sys

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-plantuml-diagram-build
    Render a PlantUML diagram source file to a PNG image via plantuml.com.

Usage:
    plcc-plantuml-diagram-build --input=FILE --output=FILE [-v ...] [options]

Options:
    --input=FILE    Path to .puml source file.
    --output=FILE   Path to write .png image.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-plantuml-diagram-build", Events, args)
    input_file = args['--input']
    output_file = args['--output']
    verbose.emit(Events.STARTED, message=f"rendering {input_file}")
    try:
        import plantuml as plantuml_lib
    except ImportError:
        print(
            "plcc-plantuml-diagram-build: plantuml not installed — "
            "run: pip install plcc[diagram]",
            file=sys.stderr,
        )
        sys.exit(1)
    server = plantuml_lib.PlantUML(url='http://www.plantuml.com/plantuml/png/')
    with open(input_file) as f:
        source = f.read()
    try:
        png_bytes = server.processes(source)
    except Exception as e:
        print(f"plcc-plantuml-diagram-build: {e}", file=sys.stderr)
        sys.exit(1)
    with open(output_file, 'wb') as f:
        f.write(png_bytes)
    verbose.emit(Events.FINISHED, message=f"wrote {output_file}")
```

- [ ] **Step 2: Run tests and confirm they pass**

```bash
pdm test src/plcc/diagram/plantuml/build_test.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 3: Commit**

```bash
git add src/plcc/diagram/plantuml/build.py src/plcc/diagram/plantuml/build_test.py
git commit -m "feat(diagram): add plcc-plantuml-diagram-build plugin using plantuml PyPI"
```

---

## Task 3: `plcc-plantuml-diagram-run` — unit tests

**Files:**
- Create: `src/plcc/diagram/plantuml/run_test.py`

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/diagram/plantuml/run_test.py`:

```python
import pytest
from unittest.mock import patch

from .run import main as run_main, _open_file


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_open_file_calls_open_on_macos(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    calls = []

    with patch('platform.system', return_value='Darwin'):
        with patch('subprocess.run', side_effect=lambda cmd, **kw: calls.append(cmd)):
            _open_file(str(img))

    assert calls[0] == ['open', str(img)]


def test_open_file_calls_xdg_open_on_linux(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    calls = []

    with patch('platform.system', return_value='Linux'):
        with patch('subprocess.run', side_effect=lambda cmd, **kw: calls.append(cmd)):
            _open_file(str(img))

    assert calls[0] == ['xdg-open', str(img)]


def test_open_file_calls_startfile_on_windows(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")

    with patch('platform.system', return_value='Windows'):
        with patch('plcc.diagram.plantuml.run.os.startfile', create=True) as mock_startfile:
            _open_file(str(img))

    mock_startfile.assert_called_once_with(str(img))


def test_main_calls_open_file(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")

    with patch('plcc.diagram.plantuml.run._open_file') as mock_open:
        run_main([f'--input={img}'])

    mock_open.assert_called_once_with(str(img))
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pdm test src/plcc/diagram/plantuml/run_test.py -v
```

Expected: errors like `ModuleNotFoundError: No module named 'plcc.diagram.plantuml.run'`

---

## Task 4: `plcc-plantuml-diagram-run` — implementation

**Files:**
- Create: `src/plcc/diagram/plantuml/run.py`

- [ ] **Step 1: Implement `plcc-plantuml-diagram-run`**

Create `src/plcc/diagram/plantuml/run.py`:

```python
import enum
import os
import platform
import subprocess
import sys

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-plantuml-diagram-run
    Open a diagram image in the system viewer.

Usage:
    plcc-plantuml-diagram-run --input=FILE [-v ...] [options]

Options:
    --input=FILE    Path to image file to open.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-plantuml-diagram-run", Events, args)
    input_file = args['--input']
    verbose.emit(Events.STARTED, message=f"opening {input_file}")
    _open_file(input_file)
    verbose.emit(Events.FINISHED)


def _open_file(path):
    system = platform.system()
    if system == 'Darwin':
        subprocess.run(['open', path], check=True)
    elif system == 'Windows':
        os.startfile(path)
    else:
        subprocess.run(['xdg-open', path], check=True)
```

- [ ] **Step 2: Run tests and confirm they pass**

```bash
pdm test src/plcc/diagram/plantuml/run_test.py -v
```

Expected: 5 tests PASSED

- [ ] **Step 3: Commit**

```bash
git add src/plcc/diagram/plantuml/run.py src/plcc/diagram/plantuml/run_test.py
git commit -m "feat(diagram): add plcc-plantuml-diagram-run plugin"
```

---

## Task 5: Wire up `pyproject.toml` and bats command tests

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/bats/commands/plcc-plantuml-diagram-build.bats`
- Create: `tests/bats/commands/plcc-plantuml-diagram-run.bats`

- [ ] **Step 1: Add entry points and optional dependency to `pyproject.toml`**

In the `[project.scripts]` section, add after `plcc-plantuml-diagram-emit`:

```toml
plcc-plantuml-diagram-build = "plcc.diagram.plantuml.build:main"
plcc-plantuml-diagram-run   = "plcc.diagram.plantuml.run:main"
```

Add or update the `[project.optional-dependencies]` section:

```toml
[project.optional-dependencies]
diagram = ["plantuml"]
```

- [ ] **Step 2: Reinstall so entry points are registered**

```bash
pdm install
```

Expected: completes without error; `.venv/bin/plcc-plantuml-diagram-build` and `.venv/bin/plcc-plantuml-diagram-run` now exist.

- [ ] **Step 3: Write bats test for `plcc-plantuml-diagram-build`**

Create `tests/bats/commands/plcc-plantuml-diagram-build.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-plantuml-diagram-build is on PATH" {
    command -v plcc-plantuml-diagram-build
}

@test "plcc-plantuml-diagram-build --help exits 0" {
    run plcc-plantuml-diagram-build --help
    [ "$status" -eq 0 ]
}

@test "plcc-plantuml-diagram-build requires --input and --output" {
    run plcc-plantuml-diagram-build
    [ "$status" -ne 0 ]
}
```

- [ ] **Step 4: Write bats test for `plcc-plantuml-diagram-run`**

Create `tests/bats/commands/plcc-plantuml-diagram-run.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-plantuml-diagram-run is on PATH" {
    command -v plcc-plantuml-diagram-run
}

@test "plcc-plantuml-diagram-run --help exits 0" {
    run plcc-plantuml-diagram-run --help
    [ "$status" -eq 0 ]
}

@test "plcc-plantuml-diagram-run requires --input" {
    run plcc-plantuml-diagram-run
    [ "$status" -ne 0 ]
}
```

- [ ] **Step 5: Run bats command tests for the two new commands**

```bash
bin/test/commands.bash
```

Expected: new tests pass alongside existing command tests.

- [ ] **Step 6: Run packaging test to verify entry points are registered**

```bash
bin/build/package.bash && bin/test/packaging.bash
```

Expected: `OK: plcc-plantuml-diagram-build` and `OK: plcc-plantuml-diagram-run` appear in output.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml pdm.lock \
    tests/bats/commands/plcc-plantuml-diagram-build.bats \
    tests/bats/commands/plcc-plantuml-diagram-run.bats
git commit -m "build(diagram): register plantuml build/run entry points and plantuml optional dep"
```

---

## Task 6: Change default format from `mermaid` to `plantuml`

**Files:**
- Modify: `src/plcc/diagram/emit.py`
- Modify: `src/plcc/diagram/build.py`
- Modify: `src/plcc/diagram/run.py`
- Modify: `src/plcc/cmd/diagram.py`
- Modify: `src/plcc/cmd/make.py`
- Modify: `src/plcc/diagram/emit_test.py`
- Modify: `src/plcc/cmd/diagram_test.py`

- [ ] **Step 1: Confirm the tests that will break before touching code**

```bash
pdm test src/plcc/diagram/emit_test.py src/plcc/cmd/diagram_test.py -v
```

Expected: `test_dispatches_to_mermaid_diagram_emit_by_default` and `test_default_format_is_mermaid` PASS (they test the current `mermaid` default).

- [ ] **Step 2: Update the five docstrings/fallbacks**

In each file below, change `[default: mermaid]` to `[default: plantuml]` in the docstring.

**`src/plcc/diagram/emit.py`** line 17:
```
    --format=FMT    Diagram format [default: plantuml].
```

**`src/plcc/diagram/build.py`** line 17:
```
    --format=FMT    Diagram format [default: plantuml].
```

**`src/plcc/diagram/run.py`** line 17:
```
    --format=FMT    Diagram format [default: plantuml].
```

**`src/plcc/cmd/diagram.py`** line 18:
```
    --format=FMT            Diagram format [default: plantuml].
```

**`src/plcc/cmd/make.py`** — two changes:

Line 27 (docstring):
```
    --diagram-format=FMT    Diagram format when using --through=diagram or --through=all [default: plantuml].
```

Line 54 (hardcoded fallback):
```python
    diagram_fmt = args['--diagram-format'] or 'plantuml'
```

- [ ] **Step 3: Update `emit_test.py`**

In `src/plcc/diagram/emit_test.py`, replace `test_dispatches_to_mermaid_diagram_emit_by_default`:

```python
def test_dispatches_to_plantuml_diagram_emit_by_default(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    calls = []

    def fake_run(cmd, stdin, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-plantuml-diagram-emit'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([])

    assert calls[0][0] == 'plcc-plantuml-diagram-emit'
```

- [ ] **Step 4: Update `diagram_test.py`**

In `src/plcc/cmd/diagram_test.py`, replace `test_default_format_is_mermaid`:

```python
def test_default_format_is_plantuml(tmp_path, monkeypatch):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    make_calls = []

    def fake_run(cmd, **kwargs):
        make_calls.append(cmd)
        m = MagicMock()
        m.returncode = 1  # fail so we stop after first call
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main([])

    assert any('--diagram-format=plantuml' in str(c) for c in make_calls[0])
```

- [ ] **Step 5: Run updated tests and confirm they pass**

```bash
pdm test src/plcc/diagram/emit_test.py src/plcc/cmd/diagram_test.py -v
```

Expected: `test_dispatches_to_plantuml_diagram_emit_by_default` and `test_default_format_is_plantuml` PASS.

- [ ] **Step 6: Run full unit test suite to confirm no regressions**

```bash
bin/test/units.bash
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add \
    src/plcc/diagram/emit.py \
    src/plcc/diagram/build.py \
    src/plcc/diagram/run.py \
    src/plcc/cmd/diagram.py \
    src/plcc/cmd/make.py \
    src/plcc/diagram/emit_test.py \
    src/plcc/cmd/diagram_test.py
git commit -m "feat(diagram): change default diagram format from mermaid to plantuml"
```

---

## Task 7: Full verification

- [ ] **Step 1: Run all functional tests**

```bash
bin/test/functional.bash
```

Expected: all tiers (units, commands, integration, e2e) PASS.

- [ ] **Step 2: Run packaging test**

```bash
bin/build/package.bash && bin/test/packaging.bash
```

Expected: all entry points verified; `OK: plcc-plantuml-diagram-build` and `OK: plcc-plantuml-diagram-run` in output.
