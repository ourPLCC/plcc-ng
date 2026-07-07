# Issue 113 Phase 2: Rename + Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename all diagram commands to the `plcc-diagram-*` namespace, move Python modules into the `class_diagram/` layout, and update all dispatchers, tests, and docs.

**Architecture:** New `src/plcc/diagram/class_diagram/` package holds the class-diagram type orchestrator and its emit plugins. Format-specific build/run plugins stay in `src/plcc/diagram/plantuml/` and `src/plcc/diagram/mermaid/` (emit removed). The three dispatchers (`plcc-diagram-emit`, `plcc-diagram-build`, `plcc-diagram-run`) keep their names but update their dispatch targets. `plcc-diagram-emit` gains a required `--type` flag. `plcc-diagram-list` updates its scan pattern and output format.

**Tech Stack:** Python 3, docopt, pytest, bats

## Global Constraints

- `class` is a Python keyword; the subdirectory is `class_diagram` everywhere
- `plcc-diagram-emit` `--type` is required; `plcc-diagram-class` passes `--type=class`
- `plcc-diagram-list` output: one `type/format` pair per line (e.g., `class/plantuml`)
- Unit tests: `bin/test/units.bash`
- Bats tests: `bats tests/bats/commands/<name>.bats`
- `pip install -e .` must be re-run after any `pyproject.toml` change
- Commit only after all tests pass

## File Map

**New files:**
- `src/plcc/diagram/class_diagram/__init__.py`
- `src/plcc/diagram/class_diagram/diagram.py` — `plcc-diagram-class` orchestrator
- `src/plcc/diagram/class_diagram/diagram_test.py`
- `src/plcc/diagram/class_diagram/plantuml/__init__.py`
- `src/plcc/diagram/class_diagram/plantuml/emit.py` — `plcc-diagram-class-plantuml-emit`
- `src/plcc/diagram/class_diagram/plantuml/emit_test.py`
- `src/plcc/diagram/class_diagram/mermaid/__init__.py`
- `src/plcc/diagram/class_diagram/mermaid/emit.py` — `plcc-diagram-class-mermaid-emit`
- `src/plcc/diagram/class_diagram/mermaid/emit_test.py`
- `tests/bats/commands/plcc-diagram-class.bats`
- `docs/cli/commands/plcc-diagram-class.md`
- `docs/cli/commands/plcc-diagram-class-plantuml-emit.md`
- `docs/cli/commands/plcc-diagram-class-mermaid-emit.md`

**Modified files:**
- `src/plcc/diagram/emit.py` — gains `--type` flag, new dispatch pattern
- `src/plcc/diagram/emit_test.py` — updated dispatch assertions
- `src/plcc/diagram/build.py` — new dispatch pattern
- `src/plcc/diagram/build_test.py` — updated dispatch assertions
- `src/plcc/diagram/run.py` — new dispatch pattern
- `src/plcc/diagram/run_test.py` — updated dispatch assertions
- `src/plcc/diagram/list.py` — new scan pattern, new output format
- `src/plcc/diagram/list_test.py` — updated assertions
- `pyproject.toml` — new entries, renamed entries, removed old entries
- `tests/bats/commands/plcc-diagram-build.bats` — updated command names
- `tests/bats/commands/plcc-diagram-list.bats` — updated assertions
- `tests/bats/commands/plcc-diagram-run.bats` — updated command names
- `tests/bats/commands/plcc-diagram.bats` — add spec-not-found test
- `docs/cli/commands/plcc-diagram.md` — add spec-not-found behavior note
- `docs/cli/commands/plcc-diagram-build.md` — update dispatch target
- `docs/cli/commands/plcc-diagram-run.md` — update dispatch target
- `docs/cli/commands/plcc-diagram-emit.md` — add `--type` option
- `docs/cli/commands/plcc-diagram-list.md` — update output format description
- `docs/cli/guide/diagram-extensions.md` — update all command names
- `docs/cli/guide/under-the-hood.md` — update all command names
- `docs/cli/guide/author-commands.md` — update all command names

**Deleted files:**
- `src/plcc/diagram/plantuml/emit.py`
- `src/plcc/diagram/plantuml/emit_test.py`
- `src/plcc/diagram/mermaid/emit.py`
- `src/plcc/diagram/mermaid/emit_test.py`
- `tests/bats/commands/plcc-plantuml-diagram-emit.bats`
- `tests/bats/commands/plcc-plantuml-diagram-build.bats`
- `tests/bats/commands/plcc-plantuml-diagram-run.bats`
- `docs/cli/commands/plcc-plantuml-diagram-emit.md`
- `docs/cli/commands/plcc-plantuml-diagram-build.md`
- `docs/cli/commands/plcc-plantuml-diagram-run.md`
- `docs/cli/commands/plcc-mermaid-diagram-emit.md`
- `docs/cli/commands/plcc-mermaid-diagram-build.md`
- `docs/cli/commands/plcc-mermaid-diagram-run.md`

---

### Task 1: `class_diagram` package scaffold + `plcc-diagram-class` orchestrator

**Files:**
- Create: `src/plcc/diagram/class_diagram/__init__.py`
- Create: `src/plcc/diagram/class_diagram/plantuml/__init__.py`
- Create: `src/plcc/diagram/class_diagram/mermaid/__init__.py`
- Create: `src/plcc/diagram/class_diagram/diagram.py`
- Create: `src/plcc/diagram/class_diagram/diagram_test.py`
- Modify: `pyproject.toml` — add `plcc-diagram-class` entry point

**Interfaces:**
- Produces: `plcc-diagram-class` command — same behavior as old `plcc-diagram` but calls `plcc-diagram-emit --type=class`

- [ ] **Step 1: Create package directories with empty `__init__.py` files**

```bash
touch src/plcc/diagram/class_diagram/__init__.py
mkdir -p src/plcc/diagram/class_diagram/plantuml
touch src/plcc/diagram/class_diagram/plantuml/__init__.py
mkdir -p src/plcc/diagram/class_diagram/mermaid
touch src/plcc/diagram/class_diagram/mermaid/__init__.py
```

- [ ] **Step 2: Write failing tests for `plcc-diagram-class`**

```python
# src/plcc/diagram/class_diagram/diagram_test.py
import json
import pytest
from unittest.mock import patch, MagicMock

from .diagram import main as run_main


def test_grammar_file_not_found_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main([])
    assert exc.value.code != 0


def test_grammar_file_not_found_prints_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main([])
    _, err = capsys.readouterr()
    assert "spec file not found" in err


def test_calls_plcc_make_with_through_model(tmp_path, monkeypatch):
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


def test_calls_emit_with_type_class(tmp_path, monkeypatch):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'build'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    (build_dir / '.spec').write_text(str(grammar))
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
    emit_call = calls[1]
    assert '--type=class' in emit_call
    assert '--format=plantuml' in emit_call


def test_banner_prints_version_to_stderr(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'build'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    (build_dir / '.spec').write_text(str(grammar))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "plcc.diagram.class_diagram.diagram.get_version", lambda: "1.2.3"
    )

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main(["--banner"])

    _, err = capsys.readouterr()
    assert "plcc-ng 1.2.3" in err
```

- [ ] **Step 3: Run tests — expect ImportError**

```bash
bin/test/units.bash src/plcc/diagram/class_diagram/diagram_test.py
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 4: Create `src/plcc/diagram/class_diagram/diagram.py`**

```python
import enum
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.version import get_version
from plcc.build.spec import read_spec
from plcc.cmd.spec import SPEC_OPTION, validate_spec_flag, spec_flag_for_child
from plcc.cmd.output import print_banner

__doc__ = """plcc-diagram-class
    Generate and display a class diagram from a PLCC spec file.

Usage:
    plcc-diagram-class [-v ...] [options]

Options:
""" + SPEC_OPTION + """\
    --format=FMT            Diagram format [default: plantuml].
    -b --banner             Show the version and spec banner on stderr.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


_SOURCE_EXT = {'mermaid': 'mmd', 'plantuml': 'puml'}


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram-class --help' for more information.", file=sys.stderr)
        sys.exit(1)

    banner = args["--banner"]
    verbose = VerboseContext.from_args("plcc-diagram-class", Events, args)
    fmt = args['--format']

    validate_spec_flag('plcc-diagram-class', args)

    verbose.emit(Events.STARTED, message="generating diagram")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ['plcc-make', '--through=model']
        + spec_flag_for_child(args)
        + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        events = verbose.parse_child_events(make_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    if banner:
        print_banner(get_version(), os.path.abspath(read_spec('build')))

    source_ext = _SOURCE_EXT.get(fmt, fmt)
    build_diagram_dir = os.path.join('build', 'diagram')
    os.makedirs(build_diagram_dir, exist_ok=True)
    diagram_source = os.path.join(build_diagram_dir, f'diagram.{source_ext}')
    diagram_image = os.path.join(build_diagram_dir, 'diagram.png')
    model_json = os.path.join('build', 'model.json')

    with open(model_json) as stdin_f, open(diagram_source, 'w') as stdout_f:
        emit_result = subprocess.run(
            ['plcc-diagram-emit', '--type=class', f'--format={fmt}'] + child_flags,
            stdin=stdin_f, stdout=stdout_f, stderr=subprocess.PIPE,
        )
    if emit_result.stderr:
        events = verbose.parse_child_events(emit_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if emit_result.returncode != 0:
        sys.exit(emit_result.returncode)

    build_result = subprocess.run(
        ['plcc-diagram-build', f'--format={fmt}',
         f'--input={diagram_source}',
         f'--output={diagram_image}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if build_result.stderr:
        events = verbose.parse_child_events(build_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if build_result.returncode != 0:
        sys.exit(build_result.returncode)

    run_result = subprocess.run(
        ['plcc-diagram-run', f'--format={fmt}', f'--input={diagram_image}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if run_result.stderr:
        events = verbose.parse_child_events(run_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if run_result.returncode != 0:
        sys.exit(run_result.returncode)

    verbose.emit(Events.FINISHED, message="done")
```

- [ ] **Step 5: Add `plcc-diagram-class` entry point to `pyproject.toml`**

In `[project.scripts]`, add:
```toml
plcc-diagram-class = "plcc.diagram.class_diagram.diagram:main"
```

- [ ] **Step 6: Re-install and run tests — expect PASS**

```bash
pip install -e . -q
bin/test/units.bash src/plcc/diagram/class_diagram/diagram_test.py
```

Expected: 5 tests PASS

---

### Task 2: `plcc-diagram-class-plantuml-emit`

**Files:**
- Create: `src/plcc/diagram/class_diagram/plantuml/emit.py`
- Create: `src/plcc/diagram/class_diagram/plantuml/emit_test.py`
- Modify: `pyproject.toml` — add entry point

**Interfaces:**
- Produces: `plcc-diagram-class-plantuml-emit` — reads model JSON from stdin, emits PlantUML to stdout (same logic as old `plcc-plantuml-diagram-emit`)

- [ ] **Step 1: Write failing test**

```python
# src/plcc/diagram/class_diagram/plantuml/emit_test.py
import io
import json
import pytest

from .emit import main as run_main, build_diagram


_MODEL = {
    "start": "program",
    "classes": [
        {"name": "Expr", "abstract": True, "extends": None, "fields": []},
        {"name": "Add", "abstract": False, "extends": "Expr",
         "fields": [{"name": "left", "type": "Expr"}]},
    ],
    "semantic_sections": []
}


def test_emits_startuml_and_enduml(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_MODEL)))
    import sys
    from io import StringIO
    captured = StringIO()
    monkeypatch.setattr('sys.stdout', captured)
    run_main([])
    out = captured.getvalue()
    assert out.startswith('@startuml')
    assert out.rstrip().endswith('@enduml')


def test_build_diagram_contains_class_name():
    result = build_diagram(_MODEL)
    assert 'Expr' in result
    assert 'Add' in result


def test_build_diagram_abstract_class():
    result = build_diagram(_MODEL)
    assert 'abstract class Expr' in result


def test_build_diagram_inheritance_arrow():
    result = build_diagram(_MODEL)
    assert 'Expr <|-- Add' in result


def test_build_diagram_field():
    result = build_diagram(_MODEL)
    assert 'left: Expr' in result
```

- [ ] **Step 2: Run test — expect ModuleNotFoundError**

```bash
bin/test/units.bash src/plcc/diagram/class_diagram/plantuml/emit_test.py
```

Expected: FAIL

- [ ] **Step 3: Create `src/plcc/diagram/class_diagram/plantuml/emit.py`**

```python
import enum
import json
import os
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-class-plantuml-emit
    Emit a PlantUML class diagram from model JSON.

Usage:
    plcc-diagram-class-plantuml-emit [--output=DIR] [-v ...] [options]

Options:
    --output=DIR    Directory to write diagram.puml into (writes to stdout if omitted).
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-class-plantuml-emit", Events, args)
    output_dir = args['--output']
    model = json.load(sys.stdin)
    content = build_diagram(model)
    if output_dir is None:
        sys.stdout.write(content)
    else:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, 'diagram.puml')
        with open(path, 'w') as f:
            f.write(content)


def build_diagram(model):
    lines = ['@startuml']
    classes = model.get('classes', [])
    for i, cls in enumerate(classes):
        if i > 0:
            lines.append('')
        lines.extend(_render_class(cls))
        if cls.get('extends'):
            lines.append(f'{cls["extends"]} <|-- {cls["name"]}')
    lines.append('@enduml')
    return '\n'.join(lines) + '\n'


def _render_class(cls):
    if cls.get('abstract'):
        return [f'abstract class {cls["name"]}']
    result = [f'class {cls["name"]} {{']
    for field in cls.get('fields', []):
        result.append(f'  {field["name"]}: {field["type"]}')
    result.append('}')
    return result
```

- [ ] **Step 4: Add entry point to `pyproject.toml`**

```toml
plcc-diagram-class-plantuml-emit = "plcc.diagram.class_diagram.plantuml.emit:main"
```

- [ ] **Step 5: Re-install and run tests — expect PASS**

```bash
pip install -e . -q
bin/test/units.bash src/plcc/diagram/class_diagram/plantuml/emit_test.py
```

Expected: 5 tests PASS

---

### Task 3: `plcc-diagram-class-mermaid-emit`

**Files:**
- Create: `src/plcc/diagram/class_diagram/mermaid/emit.py`
- Create: `src/plcc/diagram/class_diagram/mermaid/emit_test.py`
- Modify: `pyproject.toml` — add entry point

**Interfaces:**
- Produces: `plcc-diagram-class-mermaid-emit` — reads model JSON from stdin, emits Mermaid to stdout

- [ ] **Step 1: Write failing test**

```python
# src/plcc/diagram/class_diagram/mermaid/emit_test.py
import io
import json
import pytest

from .emit import main as run_main, build_diagram


_MODEL = {
    "start": "program",
    "classes": [
        {"name": "Expr", "abstract": True, "extends": None, "fields": []},
        {"name": "Add", "abstract": False, "extends": "Expr",
         "fields": [{"name": "left", "type": "Expr"}]},
    ],
    "semantic_sections": []
}


def test_emits_classDiagram_header(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_MODEL)))
    from io import StringIO
    captured = StringIO()
    monkeypatch.setattr('sys.stdout', captured)
    run_main([])
    assert captured.getvalue().startswith('classDiagram')


def test_build_diagram_contains_class_name():
    result = build_diagram(_MODEL)
    assert 'Expr' in result
    assert 'Add' in result


def test_build_diagram_abstract_marker():
    result = build_diagram(_MODEL)
    assert '<<abstract>>' in result


def test_build_diagram_inheritance_arrow():
    result = build_diagram(_MODEL)
    assert 'Add --|> Expr' in result


def test_build_diagram_field():
    result = build_diagram(_MODEL)
    assert 'left: Expr' in result
```

- [ ] **Step 2: Run test — expect ModuleNotFoundError**

```bash
bin/test/units.bash src/plcc/diagram/class_diagram/mermaid/emit_test.py
```

Expected: FAIL

- [ ] **Step 3: Create `src/plcc/diagram/class_diagram/mermaid/emit.py`**

```python
import enum
import json
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-class-mermaid-emit
    Emit a Mermaid class diagram from model JSON.

Usage:
    plcc-diagram-class-mermaid-emit [-v ...] [options]

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-class-mermaid-emit", Events, args)
    verbose.emit(Events.STARTED)
    model = json.load(sys.stdin)
    sys.stdout.write(build_diagram(model))
    verbose.emit(Events.FINISHED)


def build_diagram(model):
    lines = ['classDiagram']
    classes = model.get('classes', [])
    for cls in classes:
        lines.extend(_render_class(cls))
    for cls in classes:
        if cls.get('extends'):
            lines.append(f'    {cls["name"]} --|> {cls["extends"]}')
    return '\n'.join(lines) + '\n'


def _render_class(cls):
    name = cls['name']
    result = [f'    class {name} {{']
    if cls.get('abstract'):
        result.append('        <<abstract>>')
    for field in cls.get('fields', []):
        result.append(f'        {field["name"]}: {field["type"]}')
    result.append('    }')
    return result
```

- [ ] **Step 4: Add entry point to `pyproject.toml`**

```toml
plcc-diagram-class-mermaid-emit = "plcc.diagram.class_diagram.mermaid.emit:main"
```

- [ ] **Step 5: Re-install and run tests — expect PASS**

```bash
pip install -e . -q
bin/test/units.bash src/plcc/diagram/class_diagram/mermaid/emit_test.py
```

Expected: 5 tests PASS

---

### Task 4: Update `plcc-diagram-emit` dispatcher — add `--type`, new dispatch pattern

**Files:**
- Modify: `src/plcc/diagram/emit.py`
- Modify: `src/plcc/diagram/emit_test.py`

**Interfaces:**
- Consumes: `plcc-diagram-class-plantuml-emit` from Task 2
- Produces: `plcc-diagram-emit --type=class --format=plantuml` dispatches to `plcc-diagram-class-plantuml-emit`

- [ ] **Step 1: Replace `emit_test.py` with updated assertions**

```python
# src/plcc/diagram/emit_test.py
import io
import json
import pytest
from unittest.mock import patch, MagicMock

from .emit import main as run_main

_TRIVIAL_MODEL = json.dumps({
    "start": "program",
    "classes": [{"name": "Program", "abstract": False, "extends": None,
                 "fields": [{"name": "num", "type": "Token"}]}],
    "semantic_sections": []
})


def test_dispatches_to_class_plantuml_emit_by_default(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    calls = []

    def fake_run(cmd, stdin, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-diagram-class-plantuml-emit'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main(['--type=class'])

    assert calls[0][0] == 'plcc-diagram-class-plantuml-emit'


def test_explicit_type_and_format(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    calls = []

    def fake_run(cmd, stdin, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-diagram-class-plantuml-emit'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main(['--type=class', '--format=plantuml'])

    assert calls[0][0] == 'plcc-diagram-class-plantuml-emit'


def test_missing_type_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    import docopt as _docopt
    with pytest.raises((SystemExit, _docopt.DocoptExit)):
        run_main([])


def test_missing_plugin_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))

    with patch('shutil.which', return_value=None):
        with pytest.raises(SystemExit) as exc:
            run_main(['--type=class', '--format=nonexistent'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'nonexistent' in err
```

- [ ] **Step 2: Run tests — expect failures (old dispatch target)**

```bash
bin/test/units.bash src/plcc/diagram/emit_test.py
```

Expected: FAIL

- [ ] **Step 3: Replace `src/plcc/diagram/emit.py`**

```python
import enum
import shutil
import subprocess
import sys

from docopt import docopt

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-emit
    Dispatch model JSON to the appropriate plcc-diagram-{type}-{fmt}-emit command.

Usage:
    plcc-diagram-emit --type=TYPE [-v ...] [options]

Options:
    --type=TYPE     Diagram type (e.g., class).
    --format=FMT    Diagram format [default: plantuml].
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-emit", Events, args)
    diagram_type = args['--type']
    fmt = args['--format']
    cmd = f'plcc-diagram-{diagram_type}-{fmt}-emit'
    if not shutil.which(cmd):
        print(
            f"No diagram plugin found for type='{diagram_type}' format='{fmt}'."
            f" Is {cmd} installed?\n"
            f"Run plcc-diagram-list to see what is available.",
            file=sys.stderr,
        )
        sys.exit(1)
    result = subprocess.run(
        [cmd] + verbose.child_flags(),
        stdin=sys.stdin,
    )
    if result.returncode != 0:
        sys.exit(result.returncode)
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
bin/test/units.bash src/plcc/diagram/emit_test.py
```

Expected: 4 tests PASS

---

### Task 5: Update `plcc-diagram-build` dispatcher — new dispatch pattern

**Files:**
- Modify: `src/plcc/diagram/build.py`
- Modify: `src/plcc/diagram/build_test.py`

**Interfaces:**
- Produces: `plcc-diagram-build --format=plantuml` dispatches to `plcc-diagram-plantuml-build`

- [ ] **Step 1: Update `build_test.py` with new dispatch assertions**

```python
# src/plcc/diagram/build_test.py
import pytest
from unittest.mock import patch, MagicMock

from .build import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_dispatches_to_diagram_plantuml_build(tmp_path):
    src = tmp_path / "diagram.puml"
    src.write_text("@startuml\n@enduml\n")
    out = tmp_path / "diagram.png"
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-diagram-plantuml-build'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--input={src}', f'--output={out}'])

    assert calls[0][0] == 'plcc-diagram-plantuml-build'
    assert f'--input={src}' in calls[0]
    assert f'--output={out}' in calls[0]


def test_custom_format_dispatches_correctly(tmp_path):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n")
    out = tmp_path / "diagram.png"
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-diagram-mermaid-build'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--input={src}', f'--output={out}', '--format=mermaid'])

    assert calls[0][0] == 'plcc-diagram-mermaid-build'


def test_missing_plugin_exits_nonzero(tmp_path, capsys):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n")
    out = tmp_path / "diagram.png"

    with patch('shutil.which', return_value=None):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={src}', f'--output={out}', '--format=nonexistent'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'nonexistent' in err
```

- [ ] **Step 2: Run tests — expect failures**

```bash
bin/test/units.bash src/plcc/diagram/build_test.py
```

Expected: FAIL (old dispatch target `plcc-plantuml-diagram-build`)

- [ ] **Step 3: Update `src/plcc/diagram/build.py`** — change the dispatch pattern and docstring

Change:
```python
cmd = f'plcc-{fmt}-diagram-build'
```
to:
```python
cmd = f'plcc-diagram-{fmt}-build'
```

Also update the docstring command name reference and error message from `plcc-<fmt>-diagram-build` to `plcc-diagram-<fmt>-build`.

- [ ] **Step 4: Run tests — expect PASS**

```bash
bin/test/units.bash src/plcc/diagram/build_test.py
```

Expected: 4 tests PASS

---

### Task 6: Update `plcc-diagram-run` dispatcher — new dispatch pattern

**Files:**
- Modify: `src/plcc/diagram/run.py`
- Modify: `src/plcc/diagram/run_test.py`

**Interfaces:**
- Produces: `plcc-diagram-run --format=plantuml` dispatches to `plcc-diagram-plantuml-run`

- [ ] **Step 1: Update `run_test.py` with new dispatch assertions**

```python
# src/plcc/diagram/run_test.py
import pytest
from unittest.mock import patch, MagicMock

from .run import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_dispatches_to_diagram_plantuml_run(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b'\x89PNG')
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-diagram-plantuml-run'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--input={img}'])

    assert calls[0][0] == 'plcc-diagram-plantuml-run'
    assert f'--input={img}' in calls[0]


def test_custom_format_dispatches_correctly(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b'\x89PNG')
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-diagram-mermaid-run'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--input={img}', '--format=mermaid'])

    assert calls[0][0] == 'plcc-diagram-mermaid-run'


def test_missing_plugin_exits_nonzero(tmp_path, capsys):
    img = tmp_path / "diagram.png"
    img.write_bytes(b'\x89PNG')

    with patch('shutil.which', return_value=None):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={img}', '--format=nonexistent'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'nonexistent' in err
```

- [ ] **Step 2: Run tests — expect failures**

```bash
bin/test/units.bash src/plcc/diagram/run_test.py
```

Expected: FAIL (old dispatch target `plcc-plantuml-diagram-run`)

- [ ] **Step 3: Update `src/plcc/diagram/run.py`** — change the dispatch pattern

Change:
```python
cmd = f'plcc-{fmt}-diagram-run'
```
to:
```python
cmd = f'plcc-diagram-{fmt}-run'
```

Also update the docstring command name reference and error message.

- [ ] **Step 4: Run tests — expect PASS**

```bash
bin/test/units.bash src/plcc/diagram/run_test.py
```

Expected: 4 tests PASS

---

### Task 7: Update `plcc-diagram-list` — new scan pattern and output format

**Files:**
- Modify: `src/plcc/diagram/list.py`
- Modify: `src/plcc/diagram/list_test.py`

**Interfaces:**
- Produces: `plcc-diagram-list` scans for `plcc-diagram-{type}-{fmt}-emit`, prints `type/format` per line

- [ ] **Step 1: Replace `list_test.py`**

```python
# src/plcc/diagram/list_test.py
from .list import extract_type_format, find_plugins, main


def test_extract_type_format_plantuml():
    assert extract_type_format('plcc-diagram-class-plantuml-emit') == ('class', 'plantuml')


def test_extract_type_format_mermaid():
    assert extract_type_format('plcc-diagram-class-mermaid-emit') == ('class', 'mermaid')


def test_extract_ignores_dispatcher():
    assert extract_type_format('plcc-diagram-emit') is None


def test_extract_ignores_old_pattern():
    assert extract_type_format('plcc-plantuml-diagram-emit') is None


def test_extract_ignores_non_matching():
    assert extract_type_format('plcc-diagram-list') is None
    assert extract_type_format('python') is None


def test_main_prints_type_slash_format(capsys, monkeypatch):
    monkeypatch.setattr(
        'plcc.diagram.list.find_plugins',
        lambda: [('class', 'mermaid'), ('class', 'plantuml')]
    )
    main([])
    out, _ = capsys.readouterr()
    assert out.splitlines() == ['class/mermaid', 'class/plantuml']
```

- [ ] **Step 2: Run tests — expect failures**

```bash
bin/test/units.bash src/plcc/diagram/list_test.py
```

Expected: FAIL (`extract_type_format` not found)

- [ ] **Step 3: Replace `src/plcc/diagram/list.py`**

```python
import enum
import os
import re
import sys

from docopt import docopt

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-list
    List installed diagram plugins.

Usage:
    plcc-diagram-list [-v ...] [options]

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS

_PLUGIN_PATTERN = re.compile(r'^plcc-diagram-([a-z][a-z0-9]*)-([a-z][a-z0-9]*)-emit$')


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-list", Events, args)
    for diagram_type, fmt in sorted(find_plugins()):
        print(f'{diagram_type}/{fmt}')


def find_plugins():
    plugins = []
    seen = set()
    for directory in _path_dirs():
        try:
            for entry in os.scandir(directory):
                result = extract_type_format(entry.name)
                if result and result not in seen and _is_executable(entry):
                    plugins.append(result)
                    seen.add(result)
        except (PermissionError, FileNotFoundError):
            continue
    return plugins


def extract_type_format(command_name):
    m = _PLUGIN_PATTERN.match(command_name)
    if not m:
        return None
    return (m.group(1), m.group(2))


def _path_dirs():
    return os.environ.get('PATH', '').split(os.pathsep)


def _is_executable(entry):
    return entry.is_file() and os.access(entry.path, os.X_OK)
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
bin/test/units.bash src/plcc/diagram/list_test.py
```

Expected: 7 tests PASS

---

### Task 8: Update `pyproject.toml` entry points + delete old emit files

**Files:**
- Modify: `pyproject.toml`
- Delete: `src/plcc/diagram/plantuml/emit.py`, `src/plcc/diagram/plantuml/emit_test.py`
- Delete: `src/plcc/diagram/mermaid/emit.py`, `src/plcc/diagram/mermaid/emit_test.py`

- [ ] **Step 1: Update `pyproject.toml` `[project.scripts]` section**

Remove these entries:
```toml
plcc-mermaid-diagram-build = "plcc.diagram.mermaid.build:main"
plcc-mermaid-diagram-emit = "plcc.diagram.mermaid.emit:main"
plcc-mermaid-diagram-run = "plcc.diagram.mermaid.run:main"
plcc-plantuml-diagram-emit = "plcc.diagram.plantuml.emit:main"
plcc-plantuml-diagram-build = "plcc.diagram.plantuml.build:main"
plcc-plantuml-diagram-run   = "plcc.diagram.plantuml.run:main"
```

Add/update these entries (the `plcc-diagram-class*` entries were added in Tasks 1-3; add the renamed build/run entries now):
```toml
plcc-diagram-plantuml-build = "plcc.diagram.plantuml.build:main"
plcc-diagram-plantuml-run   = "plcc.diagram.plantuml.run:main"
plcc-diagram-mermaid-build  = "plcc.diagram.mermaid.build:main"
plcc-diagram-mermaid-run    = "plcc.diagram.mermaid.run:main"
```

- [ ] **Step 2: Delete old emit files**

```bash
rm src/plcc/diagram/plantuml/emit.py
rm src/plcc/diagram/plantuml/emit_test.py
rm src/plcc/diagram/mermaid/emit.py
rm src/plcc/diagram/mermaid/emit_test.py
```

- [ ] **Step 3: Re-install**

```bash
pip install -e . -q
```

- [ ] **Step 4: Run full unit test suite — expect PASS**

```bash
bin/test/units.bash
```

Expected: PASS (no references to deleted emit files remain)

---

### Task 9: Rename and update bats tests

**Files:**
- Delete: `tests/bats/commands/plcc-plantuml-diagram-emit.bats`
- Delete: `tests/bats/commands/plcc-plantuml-diagram-build.bats`
- Delete: `tests/bats/commands/plcc-plantuml-diagram-run.bats`
- Create: `tests/bats/commands/plcc-diagram-class.bats`
- Create: `tests/bats/commands/plcc-diagram-class-plantuml-emit.bats`
- Create: `tests/bats/commands/plcc-diagram-plantuml-build.bats`
- Create: `tests/bats/commands/plcc-diagram-plantuml-run.bats`
- Modify: `tests/bats/commands/plcc-diagram.bats`
- Modify: `tests/bats/commands/plcc-diagram-build.bats`
- Modify: `tests/bats/commands/plcc-diagram-run.bats`
- Modify: `tests/bats/commands/plcc-diagram-list.bats`

- [ ] **Step 1: Delete old bats files**

```bash
rm tests/bats/commands/plcc-plantuml-diagram-emit.bats
rm tests/bats/commands/plcc-plantuml-diagram-build.bats
rm tests/bats/commands/plcc-plantuml-diagram-run.bats
```

- [ ] **Step 2: Create `tests/bats/commands/plcc-diagram-class.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-class is on PATH" { command -v plcc-diagram-class; }

@test "plcc-diagram-class --help exits 0" {
    run plcc-diagram-class --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-class fails when spec file not found" {
    run bash -c "cd /tmp && plcc-diagram-class --spec=nonexistent.plcc"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "spec file not found" ]]
}
```

- [ ] **Step 3: Create `tests/bats/commands/plcc-diagram-class-plantuml-emit.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    MODEL_JSON="$(mktemp)"
    OUTPUT_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/arith.plcc" | plcc-model > "${MODEL_JSON}"
}

teardown() {
    rm -f "${MODEL_JSON}"
    rm -rf "${OUTPUT_DIR}"
}

@test "plcc-diagram-class-plantuml-emit is on PATH" {
    command -v plcc-diagram-class-plantuml-emit
}

@test "plcc-diagram-class-plantuml-emit creates diagram.puml" {
    run bash -c "cat '${MODEL_JSON}' | plcc-diagram-class-plantuml-emit --output='${OUTPUT_DIR}'"
    [ "$status" -eq 0 ]
    [ -f "${OUTPUT_DIR}/diagram.puml" ]
}

@test "diagram.puml contains ExprRest" {
    bash -c "cat '${MODEL_JSON}' | plcc-diagram-class-plantuml-emit --output='${OUTPUT_DIR}'"
    grep 'ExprRest' "${OUTPUT_DIR}/diagram.puml"
}

@test "diagram.puml contains inheritance arrow" {
    bash -c "cat '${MODEL_JSON}' | plcc-diagram-class-plantuml-emit --output='${OUTPUT_DIR}'"
    grep 'ExprRest <|-- AddRest' "${OUTPUT_DIR}/diagram.puml"
}
```

- [ ] **Step 4: Create `tests/bats/commands/plcc-diagram-plantuml-build.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-plantuml-build is on PATH" {
    command -v plcc-diagram-plantuml-build
}

@test "plcc-diagram-plantuml-build --help exits 0" {
    run plcc-diagram-plantuml-build --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-plantuml-build requires --input and --output" {
    run plcc-diagram-plantuml-build
    [ "$status" -ne 0 ]
}
```

- [ ] **Step 5: Create `tests/bats/commands/plcc-diagram-plantuml-run.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-plantuml-run is on PATH" {
    command -v plcc-diagram-plantuml-run
}

@test "plcc-diagram-plantuml-run --help exits 0" {
    run plcc-diagram-plantuml-run --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-plantuml-run requires --input" {
    run plcc-diagram-plantuml-run
    [ "$status" -ne 0 ]
}
```

- [ ] **Step 6: Update `tests/bats/commands/plcc-diagram.bats`** — add spec-not-found test now that types exist

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram is on PATH" { command -v plcc-diagram; }

@test "plcc-diagram --help exits 0" {
    run plcc-diagram --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram --help mentions plcc-diagram-list" {
    run plcc-diagram --help
    [[ "$output" =~ "plcc-diagram" ]]
}

@test "plcc-diagram fails when spec file not found" {
    run bash -c "cd /tmp && plcc-diagram --spec=nonexistent.plcc"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "spec file not found" ]]
}
```

- [ ] **Step 7: Update `tests/bats/commands/plcc-diagram-build.bats`** — replace `plcc-plantuml-diagram-build` with `plcc-diagram-plantuml-build` in any assertions inside the file

Open the file and replace every occurrence of `plcc-plantuml-diagram-build` with `plcc-diagram-plantuml-build`.

- [ ] **Step 8: Update `tests/bats/commands/plcc-diagram-run.bats`** — replace `plcc-plantuml-diagram-run` with `plcc-diagram-plantuml-run`

Open the file and replace every occurrence of `plcc-plantuml-diagram-run` with `plcc-diagram-plantuml-run`.

- [ ] **Step 9: Create `tests/bats/commands/plcc-diagram-class-mermaid-emit.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    MODEL_JSON="$(mktemp)"
    OUTPUT_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/arith.plcc" | plcc-model > "${MODEL_JSON}"
}

teardown() {
    rm -f "${MODEL_JSON}"
    rm -rf "${OUTPUT_DIR}"
}

@test "plcc-diagram-class-mermaid-emit is on PATH" {
    command -v plcc-diagram-class-mermaid-emit
}

@test "plcc-diagram-class-mermaid-emit emits classDiagram" {
    run bash -c "cat '${MODEL_JSON}' | plcc-diagram-class-mermaid-emit"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "classDiagram" ]]
}
```

- [ ] **Step 10: Create `tests/bats/commands/plcc-diagram-mermaid-build.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-mermaid-build is on PATH" {
    command -v plcc-diagram-mermaid-build
}

@test "plcc-diagram-mermaid-build --help exits 0" {
    run plcc-diagram-mermaid-build --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-mermaid-build requires --input and --output" {
    run plcc-diagram-mermaid-build
    [ "$status" -ne 0 ]
}
```

- [ ] **Step 11: Create `tests/bats/commands/plcc-diagram-mermaid-run.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-mermaid-run is on PATH" {
    command -v plcc-diagram-mermaid-run
}

@test "plcc-diagram-mermaid-run --help exits 0" {
    run plcc-diagram-mermaid-run --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-mermaid-run requires --input" {
    run plcc-diagram-mermaid-run
    [ "$status" -ne 0 ]
}
```

- [ ] **Step 12: Update `tests/bats/commands/plcc-diagram-list.bats`** — update expected output format

Open the file. If any test asserts the output contains `plantuml` or `mermaid` as bare words, update them to assert `class/plantuml` or `class/mermaid`.

- [ ] **Step 14: Run all relevant bats tests**

```bash
bats tests/bats/commands/plcc-diagram-class.bats
bats tests/bats/commands/plcc-diagram-class-plantuml-emit.bats
bats tests/bats/commands/plcc-diagram-plantuml-build.bats
bats tests/bats/commands/plcc-diagram-plantuml-run.bats
bats tests/bats/commands/plcc-diagram.bats
```

Expected: all PASS

---

### Task 10: Update documentation

**Files:** All listed doc files in the File Map above.

- [ ] **Step 1: Create `docs/cli/commands/plcc-diagram-class.md`**

```markdown
# plcc-diagram-class

Generate and display a class diagram from a PLCC spec file. Shows the classes
and inheritance relationships derived from the syntactic grammar.

Requires the `plcc-diagram` package.

## Usage

```text
plcc-diagram-class [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-s PATH`, `--spec=PATH` | Spec file. Remembered across invocations. Defaults to `spec.plcc`. |
| `--format=FMT` | Diagram format plugin to use. Default: `plantuml`. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-diagram-class -s subtract.plcc
plcc-diagram-class --format=mermaid
```

## Diagram formats

`plcc-diagram-class` dispatches to diagram extension plugins via `--format`.
Use [`plcc-diagram-list`](plcc-diagram-list.md) to see installed formats.
See [Diagram extensions](../../docs/cli/guide/diagram-extensions.md) for details.
```

- [ ] **Step 2: Create `docs/cli/commands/plcc-diagram-class-plantuml-emit.md`**

```markdown
# plcc-diagram-class-plantuml-emit

Emit a PlantUML class diagram from model JSON. Reads model JSON from stdin
and writes PlantUML source to stdout (or to a file if `--output` is given).

Called by [`plcc-diagram-emit --type=class --format=plantuml`](plcc-diagram-emit.md).

## Usage

```text
plcc-diagram-class-plantuml-emit [--output=DIR] [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Write `diagram.puml` into this directory. Writes to stdout if omitted. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-diagram-class-plantuml-emit > diagram.puml
```
```

- [ ] **Step 3: Create `docs/cli/commands/plcc-diagram-class-mermaid-emit.md`**

```markdown
# plcc-diagram-class-mermaid-emit

Emit a Mermaid class diagram from model JSON. Reads model JSON from stdin
and writes Mermaid source to stdout.

Called by [`plcc-diagram-emit --type=class --format=mermaid`](plcc-diagram-emit.md).

## Usage

```text
plcc-diagram-class-mermaid-emit [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-diagram-class-mermaid-emit > diagram.mmd
```
```

- [ ] **Step 4: Update `docs/cli/commands/plcc-diagram-emit.md`** — add `--type` option

Add `--type=TYPE` to the options table:
```markdown
| `--type=TYPE` | Diagram type (e.g., `class`). Required. |
```

Update the dispatch description from `plcc-{fmt}-diagram-emit` to `plcc-diagram-{type}-{fmt}-emit`.

- [ ] **Step 5: Update `docs/cli/commands/plcc-diagram-build.md`** — update dispatch target

Change any reference to `plcc-{fmt}-diagram-build` → `plcc-diagram-{fmt}-build`.

- [ ] **Step 6: Update `docs/cli/commands/plcc-diagram-run.md`** — update dispatch target

Change any reference to `plcc-{fmt}-diagram-run` → `plcc-diagram-{fmt}-run`.

- [ ] **Step 7: Update `docs/cli/commands/plcc-diagram-list.md`** — update output description

Update output format description: each line is now `type/format` (e.g., `class/plantuml`), not just a format name.

- [ ] **Step 8: Delete old doc pages**

```bash
rm docs/cli/commands/plcc-plantuml-diagram-emit.md
rm docs/cli/commands/plcc-plantuml-diagram-build.md
rm docs/cli/commands/plcc-plantuml-diagram-run.md
rm docs/cli/commands/plcc-mermaid-diagram-emit.md
rm docs/cli/commands/plcc-mermaid-diagram-build.md
rm docs/cli/commands/plcc-mermaid-diagram-run.md
```

- [ ] **Step 9: Search and replace old command names in guide pages**

For each file in `docs/cli/guide/` (diagram-extensions.md, under-the-hood.md, author-commands.md):
- `plcc-plantuml-diagram-emit` → `plcc-diagram-class-plantuml-emit`
- `plcc-mermaid-diagram-emit` → `plcc-diagram-class-mermaid-emit`
- `plcc-plantuml-diagram-build` → `plcc-diagram-plantuml-build`
- `plcc-plantuml-diagram-run` → `plcc-diagram-plantuml-run`
- `plcc-mermaid-diagram-build` → `plcc-diagram-mermaid-build`
- `plcc-mermaid-diagram-run` → `plcc-diagram-mermaid-run`
- `plcc-{fmt}-diagram-emit` → `plcc-diagram-{type}-{fmt}-emit`
- `plcc-{fmt}-diagram-build` → `plcc-diagram-{fmt}-build`
- `plcc-{fmt}-diagram-run` → `plcc-diagram-{fmt}-run`

---

### Task 11: Final verification and commit

- [ ] **Step 1: Run full unit test suite**

```bash
bin/test/units.bash
```

Expected: PASS

- [ ] **Step 2: Run all diagram bats tests**

```bash
bats tests/bats/commands/plcc-diagram.bats \
     tests/bats/commands/plcc-diagram-class.bats \
     tests/bats/commands/plcc-diagram-class-plantuml-emit.bats \
     tests/bats/commands/plcc-diagram-plantuml-build.bats \
     tests/bats/commands/plcc-diagram-plantuml-run.bats \
     tests/bats/commands/plcc-diagram-build.bats \
     tests/bats/commands/plcc-diagram-run.bats \
     tests/bats/commands/plcc-diagram-list.bats
```

Expected: all PASS

- [ ] **Step 3: Verify no old command names remain in source**

```bash
grep -r 'plcc-plantuml-diagram\|plcc-mermaid-diagram' src/ tests/ docs/ pyproject.toml
```

Expected: no output

- [ ] **Step 4: Commit**

```bash
git add -p  # stage all changes
git commit -m "feat: rename diagram commands to plcc-diagram-* namespace (issue 113 phase 2)"
```
