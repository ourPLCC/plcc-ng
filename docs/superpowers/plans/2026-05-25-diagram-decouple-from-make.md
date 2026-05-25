# Decouple Diagram Operations from plcc-make — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all diagram operations from `plcc-make`; make `plcc-diagram` own the full emit → build → print-path workflow; replace viewer-launcher logic with a simple `print(path)`.

**Architecture:** Three independent changes applied in order: (1) simplify the two `run` commands to print the file path; (2) strip diagram stages from `make.py` and rename `--through=diagram` to `--through=model`; (3) update `diagram.py` to call `plcc-make --through=model` then explicitly orchestrate emit, build, and run.

**Tech Stack:** Python 3, pytest, `unittest.mock`, `subprocess`, `docopt`

**Working directory:** `.worktrees/fix/xdg-open-missing` — all paths are relative to the repo root; run commands from this worktree. Use `/workspaces/plcc-ng/.venv/bin/pytest` (the venv is shared).

---

### Task 1: Replace viewer-launcher logic with `print(path)` — plantuml

The `plantuml/run.py` on this branch already has an error-handling fix that is now superseded. Replace the entire `_open_file` function and all platform-detection logic with a single `print(path)`.

**Files:**
- Modify: `src/plcc/diagram/plantuml/run.py`
- Modify: `src/plcc/diagram/plantuml/run_test.py`

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/diagram/plantuml/run_test.py`:

```python
def test_prints_path_to_stdout(tmp_path, capsys):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    run_main([f'--input={img}'])
    out, _ = capsys.readouterr()
    assert str(img) in out
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
/workspaces/plcc-ng/.venv/bin/pytest src/plcc/diagram/plantuml/run_test.py::test_prints_path_to_stdout -v
```

Expected: FAIL — `run_main` currently calls `xdg-open` (or raises), never prints.

- [ ] **Step 3: Replace `run.py` with the new implementation**

Replace the entire contents of `src/plcc/diagram/plantuml/run.py` with:

```python
import enum
import sys

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-plantuml-diagram-run
    Print the path to the rendered diagram image.

Usage:
    plcc-plantuml-diagram-run --input=FILE [-v ...] [options]

Options:
    --input=FILE    Path to image file.
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
    verbose.emit(Events.STARTED, message=f"diagram ready: {input_file}")
    print(input_file)
    verbose.emit(Events.FINISHED)
```

- [ ] **Step 4: Replace `run_test.py` with the updated test file**

Replace the entire contents of `src/plcc/diagram/plantuml/run_test.py` with:

```python
import pytest

from .run import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_prints_path_to_stdout(tmp_path, capsys):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    run_main([f'--input={img}'])
    out, _ = capsys.readouterr()
    assert str(img) in out
```

- [ ] **Step 5: Run all plantuml run tests to verify they pass**

```bash
/workspaces/plcc-ng/.venv/bin/pytest src/plcc/diagram/plantuml/run_test.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/diagram/plantuml/run.py src/plcc/diagram/plantuml/run_test.py
git commit -m "fix(diagram): plantuml run prints path instead of opening viewer"
```

---

### Task 2: Replace viewer-launcher logic with `print(path)` — mermaid

Identical change to Task 1, applied to the mermaid module.

**Files:**
- Modify: `src/plcc/diagram/mermaid/run.py`
- Modify: `src/plcc/diagram/mermaid/run_test.py`

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/diagram/mermaid/run_test.py`:

```python
def test_prints_path_to_stdout(tmp_path, capsys):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    run_main([f'--input={img}'])
    out, _ = capsys.readouterr()
    assert str(img) in out
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
/workspaces/plcc-ng/.venv/bin/pytest src/plcc/diagram/mermaid/run_test.py::test_prints_path_to_stdout -v
```

Expected: FAIL.

- [ ] **Step 3: Replace `run.py` with the new implementation**

Replace the entire contents of `src/plcc/diagram/mermaid/run.py` with:

```python
import enum
import sys

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-mermaid-diagram-run
    Print the path to the rendered diagram image.

Usage:
    plcc-mermaid-diagram-run --input=FILE [-v ...] [options]

Options:
    --input=FILE    Path to image file.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-mermaid-diagram-run", Events, args)
    input_file = args['--input']
    verbose.emit(Events.STARTED, message=f"diagram ready: {input_file}")
    print(input_file)
    verbose.emit(Events.FINISHED)
```

- [ ] **Step 4: Replace `run_test.py` with the updated test file**

Replace the entire contents of `src/plcc/diagram/mermaid/run_test.py` with:

```python
import pytest

from .run import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_prints_path_to_stdout(tmp_path, capsys):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    run_main([f'--input={img}'])
    out, _ = capsys.readouterr()
    assert str(img) in out
```

- [ ] **Step 5: Run all mermaid run tests to verify they pass**

```bash
/workspaces/plcc-ng/.venv/bin/pytest src/plcc/diagram/mermaid/run_test.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/diagram/mermaid/run.py src/plcc/diagram/mermaid/run_test.py
git commit -m "fix(diagram): mermaid run prints path instead of opening viewer"
```

---

### Task 3: Remove diagram operations from `plcc-make`; rename `--through=diagram` to `--through=model`

`make.py` currently runs `plcc-diagram-emit` and `plcc-diagram-build` as part of `--through=diagram` and `--through=all`. Remove both. Rename `diagram` level to `model` (the model is what that level actually produces). Remove `--diagram-format` option.

**Files:**
- Modify: `src/plcc/cmd/make.py`
- Modify: `src/plcc/cmd/make_test.py`

- [ ] **Step 1: Write three failing tests**

Add to `src/plcc/cmd/make_test.py`:

```python
def test_through_model_is_valid(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main(['--through=model'])
    _, err = capsys.readouterr()
    assert "invalid --through" not in err


def test_through_diagram_is_rejected(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main(['--through=diagram'])
    _, err = capsys.readouterr()
    assert "invalid --through" in err


def test_invalid_through_error_message_includes_model(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main(['--through=typo'])
    _, err = capsys.readouterr()
    assert "model" in err
```

- [ ] **Step 2: Run the new tests to verify they fail**

```bash
/workspaces/plcc-ng/.venv/bin/pytest src/plcc/cmd/make_test.py::test_through_model_is_valid src/plcc/cmd/make_test.py::test_through_diagram_is_rejected src/plcc/cmd/make_test.py::test_invalid_through_error_message_includes_model -v
```

Expected: all 3 FAIL — `--through=diagram` is currently valid, `--through=model` is not, and the error message says "diagram" not "model".

- [ ] **Step 3: Update the docstring in `make.py`**

In `src/plcc/cmd/make.py`, replace the `__doc__` string:

```python
__doc__ = """plcc-make
    Build a PLCC project from a grammar file.

Usage:
    plcc-make [-v ...] [options]

Options:
    --grammar-file=<path>   Path to the PLCC grammar file [default: grammar.plcc].
    --through=<level>       Build up to this level: scan, parse, model, or all [default: all].
    -h --help               Show this message.
""" + VERBOSE_OPTIONS
```

- [ ] **Step 4: Update `main()` in `make.py` — remove `diagram_fmt`, update validation, update `_REQUIRED`**

In `main()`, remove this line:
```python
    diagram_fmt = args['--diagram-format'] or 'plantuml'
```

Replace the `through` validation block:
```python
    if through not in ('scan', 'parse', 'model', 'all'):
        print(
            f"plcc-make: invalid --through value '{through}'; "
            "must be scan, parse, model, or all",
            file=sys.stderr,
        )
        sys.exit(1)
```

Replace the `_REQUIRED` dict:
```python
    _REQUIRED = {
        'scan':  {'scan'},
        'parse': {'scan', 'parse'},
        'model': {'scan', 'model'},
        'all':   {'scan', 'parse', 'model'} | tool_stages,
    }
```

- [ ] **Step 5: Update the model-build condition and remove the diagram emit/build block**

Replace:
```python
    if through in ('diagram', 'all'):
        verbose.emit(Events.PHASE, message="model")
        model_json = str(build_dir / 'model.json')
        _run_or_die(['plcc-model', spec_json] + child_flags, stdout_file=model_json, verbose=verbose)
```
with:
```python
    if through in ('model', 'all'):
        verbose.emit(Events.PHASE, message="model")
        model_json = str(build_dir / 'model.json')
        _run_or_die(['plcc-model', spec_json] + child_flags, stdout_file=model_json, verbose=verbose)
```

Then delete the entire diagram emit/build block that follows (currently lines ~165–191):
```python
    if through in ('diagram', 'all'):
        verbose.emit(Events.PHASE, message="diagram emit")
        (build_dir / 'diagram').mkdir(exist_ok=True)
        required = (through == 'diagram')
        _SOURCE_EXT = {'mermaid': 'mmd', 'plantuml': 'puml'}
        source_ext = _SOURCE_EXT.get(diagram_fmt, diagram_fmt)
        diagram_source = str(build_dir / 'diagram' / f'diagram.{source_ext}')
        diagram_ok = _run_or_die(
            ['plcc-diagram-emit', f'--format={diagram_fmt}'] + child_flags,
            stdin_file=model_json,
            stdout_file=diagram_source,
            verbose=verbose,
            required=required,
        )
        if diagram_ok:
            verbose.emit(Events.PHASE, message="diagram build")
            diagram_ok = _run_or_die(
                ['plcc-diagram-build', f'--format={diagram_fmt}',
                 f'--input={diagram_source}',
                 f'--output={build_dir / "diagram" / "diagram.png"}'] + child_flags,
                verbose=verbose,
                required=required,
            )
        if diagram_ok:
            required_stages = required_stages | {'diagram'}
        else:
            print("plcc-make: diagram generation skipped", file=sys.stderr)
```

- [ ] **Step 6: Run the three new tests to verify they pass**

```bash
/workspaces/plcc-ng/.venv/bin/pytest src/plcc/cmd/make_test.py::test_through_model_is_valid src/plcc/cmd/make_test.py::test_through_diagram_is_rejected src/plcc/cmd/make_test.py::test_invalid_through_error_message_includes_model -v
```

Expected: all 3 PASS.

- [ ] **Step 7: Delete the three now-wrong tests from `make_test.py`**

Remove these three tests entirely from `src/plcc/cmd/make_test.py`:
- `test_invalid_through_diagram_is_now_valid`
- `test_diagram_format_flag_accepted`
- `test_invalid_through_error_message_includes_diagram`

- [ ] **Step 8: Run the full make test suite**

```bash
/workspaces/plcc-ng/.venv/bin/pytest src/plcc/cmd/make_test.py -v
```

Expected: all remaining tests pass.

- [ ] **Step 9: Commit**

```bash
git add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
git commit -m "fix(make): remove diagram operations; rename --through=diagram to --through=model"
```

---

### Task 4: Update `plcc-diagram` to orchestrate emit → build → run

`diagram.py` currently calls `plcc-make --through=diagram` (which ran emit and build) then `plcc-diagram-run`. Now it must call `plcc-make --through=model` and explicitly run emit, build, and run in sequence.

**Files:**
- Modify: `src/plcc/cmd/diagram.py`
- Modify: `src/plcc/cmd/diagram_test.py`

- [ ] **Step 1: Write two failing tests**

Add to `src/plcc/cmd/diagram_test.py`:

```python
def test_calls_plcc_make_with_through_model(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        m = MagicMock()
        m.returncode = 1
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main([])

    assert calls[0][0] == 'plcc-make'
    assert '--through=model' in calls[0]
    assert not any('--through=diagram' in arg for arg in calls[0])


def test_calls_emit_build_run_after_make(tmp_path, monkeypatch):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'build'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main([])

    cmds = [c[0] for c in calls]
    assert cmds == ['plcc-make', 'plcc-diagram-emit', 'plcc-diagram-build', 'plcc-diagram-run']
```

- [ ] **Step 2: Run the new tests to verify they fail**

```bash
/workspaces/plcc-ng/.venv/bin/pytest src/plcc/cmd/diagram_test.py::test_calls_plcc_make_with_through_model src/plcc/cmd/diagram_test.py::test_calls_emit_build_run_after_make -v
```

Expected: both FAIL — current code calls `--through=diagram` and only dispatches to `plcc-diagram-run`, not emit/build separately.

- [ ] **Step 3: Replace `diagram.py` `main()` with the new implementation**

Replace the body of `main()` in `src/plcc/cmd/diagram.py` (from `verbose.emit(Events.STARTED` onward) with:

```python
    verbose.emit(Events.STARTED, message=f"generating diagram for {grammar_file}")
    child_flags = verbose.child_flags()

    make_result = subprocess.run(
        ['plcc-make', '--through=model', f'--grammar-file={grammar_file}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        sys.stderr.buffer.write(make_result.stderr)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    _SOURCE_EXT = {'mermaid': 'mmd', 'plantuml': 'puml'}
    source_ext = _SOURCE_EXT.get(fmt, fmt)
    build_diagram_dir = os.path.join('build', 'diagram')
    os.makedirs(build_diagram_dir, exist_ok=True)
    diagram_source = os.path.join(build_diagram_dir, f'diagram.{source_ext}')
    diagram_image = os.path.join(build_diagram_dir, 'diagram.png')
    model_json = os.path.join('build', 'model.json')

    with open(model_json) as stdin_f, open(diagram_source, 'w') as stdout_f:
        emit_result = subprocess.run(
            ['plcc-diagram-emit', f'--format={fmt}'] + child_flags,
            stdin=stdin_f, stdout=stdout_f, stderr=subprocess.PIPE,
        )
    if emit_result.stderr:
        sys.stderr.buffer.write(emit_result.stderr)
    if emit_result.returncode != 0:
        sys.exit(emit_result.returncode)

    build_result = subprocess.run(
        ['plcc-diagram-build', f'--format={fmt}',
         f'--input={diagram_source}',
         f'--output={diagram_image}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if build_result.stderr:
        sys.stderr.buffer.write(build_result.stderr)
    if build_result.returncode != 0:
        sys.exit(build_result.returncode)

    run_result = subprocess.run(
        ['plcc-diagram-run', f'--format={fmt}', f'--input={diagram_image}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if run_result.stderr:
        sys.stderr.buffer.write(run_result.stderr)
    if run_result.returncode != 0:
        sys.exit(run_result.returncode)

    verbose.emit(Events.FINISHED, message="done")
```

- [ ] **Step 4: Run the two new tests to verify they pass**

```bash
/workspaces/plcc-ng/.venv/bin/pytest src/plcc/cmd/diagram_test.py::test_calls_plcc_make_with_through_model src/plcc/cmd/diagram_test.py::test_calls_emit_build_run_after_make -v
```

Expected: both PASS.

- [ ] **Step 5: Delete and update the now-wrong tests in `diagram_test.py`**

Delete `test_calls_plcc_make_with_through_diagram` and `test_default_format_is_plantuml` entirely.

- [ ] **Step 6: Run the full diagram test suite**

```bash
/workspaces/plcc-ng/.venv/bin/pytest src/plcc/cmd/diagram_test.py -v
```

Expected: all remaining tests pass.

- [ ] **Step 7: Run the full test suite to check for regressions**

```bash
/workspaces/plcc-ng/.venv/bin/pytest src/ -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add src/plcc/cmd/diagram.py src/plcc/cmd/diagram_test.py
git commit -m "fix(diagram): orchestrate emit, build, run directly; drop --through=diagram from make"
```
