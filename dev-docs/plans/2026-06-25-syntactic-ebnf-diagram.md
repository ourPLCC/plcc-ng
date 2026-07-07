# Syntactic EBNF Diagram Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `plcc-diagram-syntactic` and `plcc-diagram-syntactic-plantuml-emit`, update `plcc-diagram-class` output paths, and wire up packaging/bats tests.

**Architecture:** A new `syntactic_diagram/` package mirrors `class_diagram/`: an orchestrator runs `plcc-spec` to get spec JSON (instead of `plcc-make --through=model`), pipes it to `plcc-diagram-emit --type=syntactic`, then reuses the existing `plcc-diagram-plantuml-build` and `plcc-diagram-plantuml-run`. All diagram build artifacts are flat in `build/diagram/` named by type (`class.puml`, `syntactic.puml`).

**Tech Stack:** Python 3, docopt, pytest, bats (for CLI tests), pdm (package manager).

## Global Constraints

- Run `bin/test/units.bash` after every code change before committing.
- Run `pdm install` after any change to `pyproject.toml` entry points.
- All test commands run from the repo root (`/workspaces/plcc-ng`).
- Commit messages follow the pattern: `feat:`, `fix:`, `test:`, `docs:` prefix.
- Add `[skip ci]` to commits that only touch docs/specs/plans.
- The spec JSON shape for syntactic rules: each rule has `lhs.name` (string), `lhs.altName` (string or null), `rhsSymbolList` (list of symbols), and optionally `separator` (terminal object or null — present only on repeating rules). Symbol shape: `name` (string), `isTerminal` (bool).
- Detect repeating rules by the presence of `"separator"` key in the rule dict (even if its value is null).

---

### Task 1: Update `plcc-diagram-class` output paths

Change `build/diagram/diagram.{ext}` → `build/diagram/class.{ext}` so all diagram artifacts follow the `build/diagram/{type}.{ext}` convention.

**Files:**
- Modify: `src/plcc/diagram/class_diagram/diagram.py:72-76`
- Modify: `src/plcc/diagram/class_diagram/diagram_test.py`
- Modify: `tests/bats/e2e/happy-path.bats:45-57`
- Modify: `bin/test/packaging.bash:58`

**Interfaces:**
- Produces: `build/diagram/class.puml`, `build/diagram/class.png` (was `build/diagram/diagram.puml`, `build/diagram/diagram.png`)

- [ ] **Step 1: Add a test verifying the class diagram writes to `build/diagram/class.puml`**

In `src/plcc/diagram/class_diagram/diagram_test.py`, add after the existing `test_calls_emit_with_type_class` test:

```python
def test_build_uses_class_puml_path(tmp_path, monkeypatch):
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

    build_call = calls[2]  # plcc-diagram-build is the 3rd call
    assert '--input=build/diagram/class.puml' in build_call
    assert '--output=build/diagram/class.png' in build_call
```

- [ ] **Step 2: Run the new test to confirm it fails**

```bash
bin/test/units.bash src/plcc/diagram/class_diagram/diagram_test.py::test_build_uses_class_puml_path
```

Expected: FAIL — `AssertionError` because `--input` currently contains `diagram.puml`.

- [ ] **Step 3: Update the output paths in `diagram.py`**

In `src/plcc/diagram/class_diagram/diagram.py`, change lines 74–76:

```python
    source_ext = _SOURCE_EXT.get(fmt, fmt)
    build_diagram_dir = os.path.join('build', 'diagram')
    os.makedirs(build_diagram_dir, exist_ok=True)
    diagram_source = os.path.join(build_diagram_dir, f'class.{source_ext}')
    diagram_image = os.path.join(build_diagram_dir, 'class.png')
```

- [ ] **Step 4: Run the unit tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/diagram/class_diagram/
```

Expected: all pass.

- [ ] **Step 5: Update the e2e happy-path bats test**

In `tests/bats/e2e/happy-path.bats`, update lines 45–57:

```bash
@test "plcc-spec | plcc-model | plcc-diagram-class-plantuml-emit produces diagram.puml" {
    mkdir -p "${DIAGRAM_DIR}"
    plcc-spec "${FIXTURES}/arith.plcc" | plcc-model | plcc-diagram-class-plantuml-emit --output="${DIAGRAM_DIR}"
    [ -f "${DIAGRAM_DIR}/diagram.puml" ]
}

@test "diagram.puml contains expected classes" {
    mkdir -p "${DIAGRAM_DIR}"
    plcc-spec "${FIXTURES}/arith.plcc" | plcc-model | plcc-diagram-class-plantuml-emit --output="${DIAGRAM_DIR}"
    grep 'ExprRest' "${DIAGRAM_DIR}/diagram.puml"
    grep 'ExprRest <|-- AddRest' "${DIAGRAM_DIR}/diagram.puml"
}
```

These e2e tests test `plcc-diagram-class-plantuml-emit --output=DIR` which still writes `diagram.puml` inside the output dir — that's the emitter's own convention, unchanged. No edit needed here.

Verify by running the e2e test to confirm it still passes: the `--output` tests use the emitter directly, not the orchestrator. Only the orchestrator changed paths.

- [ ] **Step 6: Update the packaging test**

In `bin/test/packaging.bash`, line 58, change:

```bash
    test -f "${DIAGRAM_DIR}/diagram.puml" || { echo "FAIL: diagram.puml missing"; exit 1; }
```

to:

```bash
    test -f "${DIAGRAM_DIR}/diagram.puml" || { echo "FAIL: diagram.puml missing"; exit 1; }
```

Actually, check the context: line 57–58 uses `plcc-diagram-class-plantuml-emit --output="${DIAGRAM_DIR}"` which writes `diagram.puml` in the dir — that's the emitter's `--output` convention, not the orchestrator paths. No change needed.

- [ ] **Step 7: Run full unit tests**

```bash
bin/test/units.bash
```

Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add src/plcc/diagram/class_diagram/diagram.py src/plcc/diagram/class_diagram/diagram_test.py
git commit -m "fix: update plcc-diagram-class output paths to build/diagram/class.* (issue 109)"
```

---

### Task 2: Implement `plcc-diagram-syntactic-plantuml-emit`

The emitter reads spec JSON from stdin, groups syntactic rules by LHS name, and writes a `@startebnf ... @endebnf` block to stdout.

**Files:**
- Create: `src/plcc/diagram/syntactic_diagram/__init__.py`
- Create: `src/plcc/diagram/syntactic_diagram/plantuml/__init__.py`
- Create: `src/plcc/diagram/syntactic_diagram/plantuml/emit.py`
- Create: `src/plcc/diagram/syntactic_diagram/plantuml/emit_test.py`

**Interfaces:**
- Consumes: spec JSON on stdin (`{"syntax": {"rules": [...]}}`)
- Produces: PlantUML EBNF source on stdout (`@startebnf\n...\n@endebnf\n`)
- Exports: `build_ebnf(spec: dict) -> str` — used by tests and by `main()`

- [ ] **Step 1: Create the package skeleton**

```bash
mkdir -p src/plcc/diagram/syntactic_diagram/plantuml
touch src/plcc/diagram/syntactic_diagram/__init__.py
touch src/plcc/diagram/syntactic_diagram/plantuml/__init__.py
```

- [ ] **Step 2: Write the failing tests**

Create `src/plcc/diagram/syntactic_diagram/plantuml/emit_test.py`:

```python
import io
import json
import pytest

from .emit import build_ebnf


_RULE = lambda name, alt, rhs: {
    'line': {'string': '', 'number': 1, 'file': ''},
    'lhs': {'name': name, 'isTerminal': False, 'altName': alt, 'isCapturing': False},
    'rhsSymbolList': rhs,
}
_NT = lambda name: {'name': name, 'isTerminal': False, 'altName': None, 'isCapturing': False}
_T  = lambda name: {'name': name, 'isTerminal': True, 'isCapturing': False}
_REPEAT = lambda name, rhs, sep=None: {
    **_RULE(name, None, rhs),
    'separator': {'name': sep, 'isTerminal': True, 'isCapturing': False} if sep else None,
}


def _spec(rules):
    return {'syntax': {'rules': rules}}


def test_startebnf_and_endebnf():
    result = build_ebnf(_spec([_RULE('A', None, [_NT('B')])]))
    assert result.startswith('@startebnf\n')
    assert result.rstrip().endswith('@endebnf')


def test_standard_rule_single_nonterminal():
    result = build_ebnf(_spec([_RULE('Program', None, [_NT('Stmt')])]))
    assert 'Program ::= Stmt ;' in result


def test_nonterminal_rendered_unquoted():
    result = build_ebnf(_spec([_RULE('A', None, [_NT('B')])]))
    assert 'B' in result
    assert "'B'" not in result


def test_terminal_rendered_quoted():
    result = build_ebnf(_spec([_RULE('A', None, [_T('PLUS')])]))
    assert "'PLUS'" in result


def test_standard_rule_multiple_symbols():
    result = build_ebnf(_spec([_RULE('Expr', None, [_NT('Term'), _T('PLUS'), _NT('Expr')])]))
    assert "Expr ::= Term 'PLUS' Expr ;" in result


def test_multiple_alternatives_same_lhs():
    rules = [
        _RULE('Expr', None, [_NT('Term')]),
        _RULE('Expr', 'Add', [_NT('Expr'), _T('PLUS'), _NT('Term')]),
    ]
    result = build_ebnf(_spec(rules))
    assert "Expr ::= Term | Expr 'PLUS' Term ;" in result


def test_alternatives_appear_once_not_twice():
    rules = [
        _RULE('Expr', None, [_NT('Term')]),
        _RULE('Expr', 'Add', [_NT('Expr'), _T('PLUS'), _NT('Term')]),
    ]
    result = build_ebnf(_spec(rules))
    assert result.count('Expr ::=') == 1


def test_repeating_rule_no_separator():
    result = build_ebnf(_spec([_REPEAT('Items', [_NT('Item')])]))
    assert 'Items ::= { Item } ;' in result


def test_repeating_rule_with_separator():
    result = build_ebnf(_spec([_REPEAT('Args', [_NT('Arg')], sep='COMMA')]))
    assert "Args ::= { Arg 'COMMA' } ;" in result


def test_empty_production():
    result = build_ebnf(_spec([_RULE('Opt', None, [])]))
    assert 'Opt ::=  ;' in result


def test_lhs_order_preserved():
    rules = [
        _RULE('B', None, [_NT('C')]),
        _RULE('A', None, [_NT('B')]),
    ]
    result = build_ebnf(_spec(rules))
    assert result.index('B ::=') < result.index('A ::=')


def test_arith_grammar_smoke():
    rules = [
        _RULE('Program', None, [_NT('Expr')]),
        _RULE('Expr', None, [_NT('Term'), _NT('ExprRest')]),
        _RULE('ExprRest', 'AddRest', [_T('PLUS'), _NT('Term'), _NT('ExprRest')]),
        _RULE('ExprRest', 'NilRest', []),
        _RULE('Term', None, [_T('NUM')]),
    ]
    result = build_ebnf(_spec(rules))
    assert '@startebnf' in result
    assert 'Program ::= Expr ;' in result
    assert "ExprRest ::= 'PLUS' Term ExprRest |  ;" in result
    assert "Term ::= 'NUM' ;" in result
```

- [ ] **Step 3: Run the tests to confirm they all fail**

```bash
bin/test/units.bash src/plcc/diagram/syntactic_diagram/plantuml/emit_test.py
```

Expected: ImportError or similar — `emit.py` doesn't exist yet.

- [ ] **Step 4: Implement the emitter**

Create `src/plcc/diagram/syntactic_diagram/plantuml/emit.py`:

```python
import enum
import json
import sys

from docopt import docopt

from ....verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-syntactic-plantuml-emit
    Emit a PlantUML EBNF diagram from spec JSON.

Usage:
    plcc-diagram-syntactic-plantuml-emit [-v ...] [options]

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
    VerboseContext.from_args("plcc-diagram-syntactic-plantuml-emit", Events, args)
    spec = json.load(sys.stdin)
    sys.stdout.write(build_ebnf(spec))


def build_ebnf(spec):
    rules = spec.get('syntax', {}).get('rules', [])
    groups = {}
    order = []
    for rule in rules:
        name = rule['lhs']['name']
        if name not in groups:
            groups[name] = []
            order.append(name)
        groups[name].append(rule)
    lines = ['@startebnf']
    for name in order:
        rhs = _render_alternatives(groups[name])
        lines.append(f'{name} ::= {rhs} ;')
    lines.append('@endebnf')
    return '\n'.join(lines) + '\n'


def _render_alternatives(rules):
    return ' | '.join(_render_rule(r) for r in rules)


def _render_rule(rule):
    if 'separator' in rule:
        return _render_repeating(rule)
    return _render_standard(rule)


def _render_standard(rule):
    return ' '.join(_render_symbol(s) for s in rule['rhsSymbolList'])


def _render_repeating(rule):
    body = ' '.join(_render_symbol(s) for s in rule['rhsSymbolList'])
    sep = rule['separator']
    if sep:
        return f'{{ {body} \'{sep["name"]}\' }}'
    return f'{{ {body} }}'


def _render_symbol(sym):
    if sym['isTerminal']:
        return f'\'{sym["name"]}\''
    return sym['name']
```

- [ ] **Step 5: Run the tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/diagram/syntactic_diagram/plantuml/emit_test.py
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/diagram/syntactic_diagram/
git commit -m "feat: add plcc-diagram-syntactic-plantuml-emit (issue 109)"
```

---

### Task 3: Implement `plcc-diagram-syntactic` orchestrator and entry points

**Files:**
- Create: `src/plcc/diagram/syntactic_diagram/diagram.py`
- Create: `src/plcc/diagram/syntactic_diagram/diagram_test.py`
- Modify: `pyproject.toml` (add 2 entry points)

**Interfaces:**
- Consumes: `plcc-spec <path>` stdout (spec JSON), `plcc-diagram-emit --type=syntactic`, `plcc-diagram-build`, `plcc-diagram-run`
- Produces: `build/diagram/syntactic.puml`, `build/diagram/syntactic.png`

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/diagram/syntactic_diagram/diagram_test.py`:

```python
import pytest
from unittest.mock import patch, MagicMock

from .diagram import main as run_main


def _fake_run(returncode=0, stdout=b'{}'):
    def fake(cmd, **kwargs):
        m = MagicMock()
        m.returncode = returncode
        m.stderr = b''
        m.stdout = stdout
        return m
    return fake


def test_spec_file_not_found_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main([])
    assert exc.value.code != 0


def test_spec_file_not_found_prints_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main([])
    _, err = capsys.readouterr()
    assert "spec file not found" in err


def test_calls_plcc_spec(tmp_path, monkeypatch):
    spec = tmp_path / "spec.plcc"
    spec.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        m = MagicMock()
        m.returncode = 1
        m.stderr = b''
        m.stdout = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main([])

    assert calls[0][0] == 'plcc-spec'
    assert str(spec) in calls[0]


def test_calls_emit_build_run_in_order(tmp_path, monkeypatch):
    spec = tmp_path / "spec.plcc"
    spec.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        m.stdout = b'{}'
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main([])

    cmds = [c[0] for c in calls]
    assert cmds == ['plcc-spec', 'plcc-diagram-emit', 'plcc-diagram-build', 'plcc-diagram-run']


def test_emit_called_with_type_syntactic(tmp_path, monkeypatch):
    spec = tmp_path / "spec.plcc"
    spec.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        m.stdout = b'{}'
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main([])

    emit_call = calls[1]
    assert '--type=syntactic' in emit_call
    assert '--format=plantuml' in emit_call


def test_build_uses_syntactic_paths(tmp_path, monkeypatch):
    spec = tmp_path / "spec.plcc"
    spec.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        m.stdout = b'{}'
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main([])

    build_call = calls[2]
    assert '--input=build/diagram/syntactic.puml' in build_call
    assert '--output=build/diagram/syntactic.png' in build_call
```

- [ ] **Step 2: Run to confirm they fail**

```bash
bin/test/units.bash src/plcc/diagram/syntactic_diagram/diagram_test.py
```

Expected: ImportError — `diagram.py` doesn't exist yet.

- [ ] **Step 3: Implement the orchestrator**

Create `src/plcc/diagram/syntactic_diagram/diagram.py`:

```python
import enum
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.version import get_version
from plcc.build.spec import read_spec, resolve_spec_path
from plcc.cmd.spec import SPEC_OPTION, validate_spec_flag
from plcc.cmd.output import print_banner

__doc__ = """plcc-diagram-syntactic
    Generate and display a syntactic grammar diagram from a PLCC spec file.

Usage:
    plcc-diagram-syntactic [-v ...] [options]

Options:
""" + SPEC_OPTION + """\
    --format=FMT            Diagram format [default: plantuml].
    -b --banner             Show the version and spec banner on stderr.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


_SOURCE_EXT = {'plantuml': 'puml', 'mermaid': 'mmd'}


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
        print("Run 'plcc-diagram-syntactic --help' for more information.", file=sys.stderr)
        sys.exit(1)

    banner = args["--banner"]
    fmt = args['--format']

    validate_spec_flag('plcc-diagram-syntactic', args)

    spec_path = resolve_spec_path(args['--spec'], read_spec('build'))
    if not os.path.exists(spec_path):
        print(f"plcc-diagram-syntactic: spec file not found: {spec_path}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram-syntactic --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose = VerboseContext.from_args("plcc-diagram-syntactic", Events, args)
    verbose.emit(Events.STARTED, message="generating syntactic diagram")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    spec_result = subprocess.run(
        ['plcc-spec', spec_path] + child_flags,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if spec_result.stderr:
        events = verbose.parse_child_events(spec_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if spec_result.returncode != 0:
        sys.exit(spec_result.returncode)

    if banner:
        print_banner(get_version(), os.path.abspath(spec_path))

    source_ext = _SOURCE_EXT.get(fmt, fmt)
    build_diagram_dir = os.path.join('build', 'diagram')
    os.makedirs(build_diagram_dir, exist_ok=True)
    diagram_source = os.path.join(build_diagram_dir, f'syntactic.{source_ext}')
    diagram_image = os.path.join(build_diagram_dir, 'syntactic.png')

    with open(diagram_source, 'w') as stdout_f:
        emit_result = subprocess.run(
            ['plcc-diagram-emit', '--type=syntactic', f'--format={fmt}'] + child_flags,
            input=spec_result.stdout, stdout=stdout_f, stderr=subprocess.PIPE,
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

- [ ] **Step 4: Run the tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/diagram/syntactic_diagram/diagram_test.py
```

Expected: all pass.

- [ ] **Step 5: Add entry points to `pyproject.toml`**

In `pyproject.toml`, in the `[project.scripts]` section, add after the `plcc-diagram-class` block:

```toml
plcc-diagram-syntactic               = "plcc.diagram.syntactic_diagram.diagram:main"
plcc-diagram-syntactic-plantuml-emit = "plcc.diagram.syntactic_diagram.plantuml.emit:main"
```

- [ ] **Step 6: Install and smoke-test**

```bash
pdm install
plcc-diagram-syntactic --help
plcc-diagram-syntactic-plantuml-emit --help
```

Expected: both print usage and exit 0.

- [ ] **Step 7: Run full unit tests**

```bash
bin/test/units.bash
```

Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add src/plcc/diagram/syntactic_diagram/diagram.py \
        src/plcc/diagram/syntactic_diagram/diagram_test.py \
        pyproject.toml
git commit -m "feat: add plcc-diagram-syntactic orchestrator and entry points (issue 109)"
```

---

### Task 4: Bats command tests and packaging

**Files:**
- Create: `tests/bats/commands/plcc-diagram-syntactic.bats`
- Create: `tests/bats/commands/plcc-diagram-syntactic-plantuml-emit.bats`
- Modify: `tests/bats/commands/plcc-diagram-list.bats`
- Modify: `bin/test/packaging.bash`

**Interfaces:**
- Consumes: `tests/fixtures/arith.plcc` (existing fixture)

- [ ] **Step 1: Create bats test for the orchestrator**

Create `tests/bats/commands/plcc-diagram-syntactic.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-syntactic is on PATH" { command -v plcc-diagram-syntactic; }

@test "plcc-diagram-syntactic --help exits 0" {
    run plcc-diagram-syntactic --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-syntactic fails when spec file not found" {
    run bash -c "cd /tmp && plcc-diagram-syntactic --spec=nonexistent.plcc"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "spec file not found" ]]
}
```

- [ ] **Step 2: Create bats test for the emitter**

Create `tests/bats/commands/plcc-diagram-syntactic-plantuml-emit.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
}

@test "plcc-diagram-syntactic-plantuml-emit is on PATH" {
    command -v plcc-diagram-syntactic-plantuml-emit
}

@test "plcc-diagram-syntactic-plantuml-emit --help exits 0" {
    run plcc-diagram-syntactic-plantuml-emit --help
    [ "$status" -eq 0 ]
}

@test "emitter produces @startebnf output" {
    run bash -c "plcc-spec '${FIXTURES}/arith.plcc' | plcc-diagram-syntactic-plantuml-emit"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "@startebnf" ]]
    [[ "$output" =~ "@endebnf" ]]
}

@test "emitter output contains grammar rule names" {
    run bash -c "plcc-spec '${FIXTURES}/arith.plcc' | plcc-diagram-syntactic-plantuml-emit"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Program" ]]
    [[ "$output" =~ "Expr" ]]
    [[ "$output" =~ "Term" ]]
}

@test "emitter output contains quoted terminal" {
    run bash -c "plcc-spec '${FIXTURES}/arith.plcc' | plcc-diagram-syntactic-plantuml-emit"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "'PLUS'" ]]
}
```

- [ ] **Step 3: Update `plcc-diagram-list` bats test**

In `tests/bats/commands/plcc-diagram-list.bats`, add after the `class/mermaid` test:

```bash
@test "plcc-diagram-list finds syntactic/plantuml" {
    run plcc-diagram-list
    [ "$status" -eq 0 ]
    [[ "$output" =~ "syntactic/plantuml" ]]
}
```

- [ ] **Step 4: Run the bats command tests**

```bash
bin/test/commands.bash
```

Expected: all pass including the new tests.

- [ ] **Step 5: Update the packaging test**

In `bin/test/packaging.bash`, on the `for cmd in ...` line (around line 24), add `plcc-diagram-syntactic plcc-diagram-syntactic-plantuml-emit \` after the existing `plcc-diagram-class` line:

```bash
    for cmd in plcc-spec plcc-tokens plcc-trees plcc-model \
               plcc-lang-emit plcc-lang-build plcc-lang-list \
               plcc-diagram plcc-diagram-emit plcc-diagram-build plcc-diagram-run plcc-diagram-list \
               plcc-diagram-class plcc-diagram-class-plantuml-emit plcc-diagram-class-mermaid-emit \
               plcc-diagram-syntactic plcc-diagram-syntactic-plantuml-emit \
               plcc-diagram-plantuml-build plcc-diagram-plantuml-run \
               plcc-diagram-mermaid-build plcc-diagram-mermaid-run \
               plcc-make plcc-scan plcc-parse plcc-rep; do
```

Also add after the `class/plantuml` diagram-list check (around line 42):

```bash
    echo "${DIAGRAM_LIST}" | grep -q "syntactic/plantuml" || { echo "FAIL: plcc-diagram-list missing 'syntactic/plantuml'"; exit 1; }
    echo "OK: plcc-diagram-list reports syntactic/plantuml"
```

- [ ] **Step 6: Run all functional tests**

```bash
bin/test/functional.bash
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add tests/bats/commands/plcc-diagram-syntactic.bats \
        tests/bats/commands/plcc-diagram-syntactic-plantuml-emit.bats \
        tests/bats/commands/plcc-diagram-list.bats \
        bin/test/packaging.bash
git commit -m "test: add bats tests for plcc-diagram-syntactic and update packaging (issue 109)"
```
