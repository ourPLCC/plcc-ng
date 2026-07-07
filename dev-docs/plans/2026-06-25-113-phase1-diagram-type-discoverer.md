# Issue 113 Phase 1: `plcc-diagram` Type-Discoverer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `plcc-diagram` with a type-discoverer that scans PATH for `plcc-diagram-{type}` executables and runs each in sequence.

**Architecture:** `src/plcc/cmd/diagram.py` is replaced entirely. Its old class-orchestrator content is discarded here (recreated as `plcc-diagram-class` in Phase 2). The type-discoverer scans PATH using the same pattern as `plcc-diagram-list`, filters on a single-word type name, excludes reserved words, and runs each found command. In Phase 1 no type orchestrators exist yet so `plcc-diagram` exits cleanly with no output.

**Tech Stack:** Python 3, docopt, pytest, bats

## Global Constraints

- Type name regex: `^plcc-diagram-([a-z][a-z0-9]*)$` (single lowercase word, no hyphens)
- Reserved names excluded: `emit`, `build`, `run`, `list`
- Command name in docstring/VerboseContext: `plcc-diagram`
- Unit tests: `bin/test/units.bash src/plcc/cmd/diagram_test.py`
- Bats tests: `bats tests/bats/commands/plcc-diagram.bats`
- Full suite: `bin/test/units.bash`
- Commit only after all tests pass

---

### Task 1: `_extract_type_name` with TDD

**Files:**
- Modify: `src/plcc/cmd/diagram.py` — stub with just `_extract_type_name`
- Modify: `src/plcc/cmd/diagram_test.py` — replace entirely with type-discoverer tests

**Interfaces:**
- Produces: `_extract_type_name(command_name: str) -> str | None` — returns type name if `command_name` matches `plcc-diagram-{type}` (single-word, not reserved), else `None`

- [ ] **Step 1: Replace `diagram_test.py` with failing tests for `_extract_type_name`**

```python
# src/plcc/cmd/diagram_test.py
from .diagram import _extract_type_name


class TestExtractTypeName:
    def test_class_type(self):
        assert _extract_type_name('plcc-diagram-class') == 'class'

    def test_ebnf_type(self):
        assert _extract_type_name('plcc-diagram-ebnf') == 'ebnf'

    def test_reserved_emit(self):
        assert _extract_type_name('plcc-diagram-emit') is None

    def test_reserved_build(self):
        assert _extract_type_name('plcc-diagram-build') is None

    def test_reserved_run(self):
        assert _extract_type_name('plcc-diagram-run') is None

    def test_reserved_list(self):
        assert _extract_type_name('plcc-diagram-list') is None

    def test_plugin_name_excluded(self):
        # extra hyphens mean it is a plugin, not a type orchestrator
        assert _extract_type_name('plcc-diagram-class-plantuml-emit') is None

    def test_unrelated_command(self):
        assert _extract_type_name('plcc-make') is None

    def test_wrong_prefix(self):
        assert _extract_type_name('plcc-plantuml-diagram-emit') is None

    def test_empty_string(self):
        assert _extract_type_name('') is None
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
bin/test/units.bash src/plcc/cmd/diagram_test.py
```

Expected: FAIL with `ImportError: cannot import name '_extract_type_name'`

- [ ] **Step 3: Replace `diagram.py` with a stub containing only `_extract_type_name`**

```python
# src/plcc/cmd/diagram.py
import re

_TYPE_PATTERN = re.compile(r'^plcc-diagram-([a-z][a-z0-9]*)$')
_RESERVED = frozenset({'emit', 'build', 'run', 'list'})


def _extract_type_name(command_name):
    m = _TYPE_PATTERN.match(command_name)
    if not m:
        return None
    name = m.group(1)
    if name in _RESERVED:
        return None
    return name
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
bin/test/units.bash src/plcc/cmd/diagram_test.py
```

Expected: 10 tests PASS

---

### Task 2: `find_types` with TDD

**Files:**
- Modify: `src/plcc/cmd/diagram.py` — add `find_types`, `_path_dirs`, `_is_executable`
- Modify: `src/plcc/cmd/diagram_test.py` — append `TestFindTypes`

**Interfaces:**
- Consumes: `_extract_type_name` from Task 1
- Produces: `find_types() -> list[str]` — type names found in PATH, deduplicated, in discovery order

- [ ] **Step 1: Update the import and append `TestFindTypes` to `diagram_test.py`**

Replace the import at the top of `src/plcc/cmd/diagram_test.py`:
```python
from .diagram import _extract_type_name, find_types
```

Append at the bottom of `src/plcc/cmd/diagram_test.py`:

```python
class TestFindTypes:
    def test_finds_installed_type(self, tmp_path, monkeypatch):
        cmd = tmp_path / 'plcc-diagram-class'
        cmd.write_text('#!/bin/sh\n')
        cmd.chmod(0o755)
        monkeypatch.setenv('PATH', str(tmp_path))
        assert find_types() == ['class']

    def test_excludes_reserved_names(self, tmp_path, monkeypatch):
        for name in ('plcc-diagram-emit', 'plcc-diagram-build',
                     'plcc-diagram-run', 'plcc-diagram-list'):
            f = tmp_path / name
            f.write_text('#!/bin/sh\n')
            f.chmod(0o755)
        monkeypatch.setenv('PATH', str(tmp_path))
        assert find_types() == []

    def test_excludes_non_executable(self, tmp_path, monkeypatch):
        cmd = tmp_path / 'plcc-diagram-class'
        cmd.write_text('#!/bin/sh\n')
        cmd.chmod(0o644)
        monkeypatch.setenv('PATH', str(tmp_path))
        assert find_types() == []

    def test_excludes_plugin_names_with_extra_segments(self, tmp_path, monkeypatch):
        cmd = tmp_path / 'plcc-diagram-class-plantuml-emit'
        cmd.write_text('#!/bin/sh\n')
        cmd.chmod(0o755)
        monkeypatch.setenv('PATH', str(tmp_path))
        assert find_types() == []

    def test_deduplicates_across_path_dirs(self, tmp_path, monkeypatch):
        dir1 = tmp_path / 'dir1'
        dir2 = tmp_path / 'dir2'
        dir1.mkdir()
        dir2.mkdir()
        for d in (dir1, dir2):
            f = d / 'plcc-diagram-class'
            f.write_text('#!/bin/sh\n')
            f.chmod(0o755)
        monkeypatch.setenv('PATH', f'{dir1}:{dir2}')
        assert find_types() == ['class']

    def test_returns_empty_when_no_types(self, tmp_path, monkeypatch):
        monkeypatch.setenv('PATH', str(tmp_path))
        assert find_types() == []

    def test_finds_multiple_types(self, tmp_path, monkeypatch):
        for name in ('plcc-diagram-class', 'plcc-diagram-ebnf'):
            f = tmp_path / name
            f.write_text('#!/bin/sh\n')
            f.chmod(0o755)
        monkeypatch.setenv('PATH', str(tmp_path))
        assert sorted(find_types()) == ['class', 'ebnf']
```

- [ ] **Step 2: Run tests — expect ImportError on `find_types`**

```bash
bin/test/units.bash src/plcc/cmd/diagram_test.py
```

Expected: FAIL with `ImportError: cannot import name 'find_types'`

- [ ] **Step 3: Add `find_types` and helpers to `diagram.py`**

Append to `src/plcc/cmd/diagram.py`:

```python
import os


def find_types():
    types = []
    seen = set()
    for directory in _path_dirs():
        try:
            for entry in os.scandir(directory):
                name = _extract_type_name(entry.name)
                if name and name not in seen and _is_executable(entry):
                    types.append(name)
                    seen.add(name)
        except (PermissionError, FileNotFoundError):
            continue
    return types


def _path_dirs():
    return os.environ.get('PATH', '').split(os.pathsep)


def _is_executable(entry):
    return entry.is_file() and os.access(entry.path, os.X_OK)
```

- [ ] **Step 4: Run tests — expect all PASS**

```bash
bin/test/units.bash src/plcc/cmd/diagram_test.py
```

Expected: 17 tests PASS

---

### Task 3: `main`, bats tests, docs, and commit

**Files:**
- Modify: `src/plcc/cmd/diagram.py` — add full CLI wiring (`main`, `__doc__`, `Events`)
- Modify: `tests/bats/commands/plcc-diagram.bats` — replace with type-discoverer tests
- Modify: `docs/cli/commands/plcc-diagram.md` — update for type-discoverer

**Interfaces:**
- Consumes: `find_types` from Task 2

- [ ] **Step 1: Replace `diagram.py` entirely with the complete type-discoverer**

```python
# src/plcc/cmd/diagram.py
import enum
import os
import re
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.cmd.spec import SPEC_OPTION, spec_flag_for_child

__doc__ = """plcc-diagram
    Generate all installed diagram types from a PLCC spec file.

Usage:
    plcc-diagram [-v ...] [options]

Options:
""" + SPEC_OPTION + """\
    -b --banner             Show the version and spec banner on stderr.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS

_TYPE_PATTERN = re.compile(r'^plcc-diagram-([a-z][a-z0-9]*)$')
_RESERVED = frozenset({'emit', 'build', 'run', 'list'})


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
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose = VerboseContext.from_args("plcc-diagram", Events, args)
    verbose.emit(Events.STARTED, message="generating diagrams")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    for diagram_type in sorted(find_types()):
        cmd = f'plcc-diagram-{diagram_type}'
        result = subprocess.run(
            [cmd]
            + spec_flag_for_child(args)
            + (['--banner'] if args['--banner'] else [])
            + child_flags,
            stderr=subprocess.PIPE,
        )
        if result.stderr:
            events = verbose.parse_child_events(result.stderr.decode('utf-8', errors='replace'))
            verbose.reformat_child_events(events)
        if result.returncode != 0:
            sys.exit(result.returncode)

    verbose.emit(Events.FINISHED, message="done")


def find_types():
    types = []
    seen = set()
    for directory in _path_dirs():
        try:
            for entry in os.scandir(directory):
                name = _extract_type_name(entry.name)
                if name and name not in seen and _is_executable(entry):
                    types.append(name)
                    seen.add(name)
        except (PermissionError, FileNotFoundError):
            continue
    return types


def _extract_type_name(command_name):
    m = _TYPE_PATTERN.match(command_name)
    if not m:
        return None
    name = m.group(1)
    if name in _RESERVED:
        return None
    return name


def _path_dirs():
    return os.environ.get('PATH', '').split(os.pathsep)


def _is_executable(entry):
    return entry.is_file() and os.access(entry.path, os.X_OK)
```

- [ ] **Step 2: Run unit tests — expect all PASS**

```bash
bin/test/units.bash src/plcc/cmd/diagram_test.py
```

Expected: 17 tests PASS

- [ ] **Step 3: Replace `tests/bats/commands/plcc-diagram.bats`**

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
```

- [ ] **Step 4: Run bats — expect all PASS**

```bash
bats tests/bats/commands/plcc-diagram.bats
```

Expected: 3 tests PASS

- [ ] **Step 5: Replace `docs/cli/commands/plcc-diagram.md`**

```markdown
# plcc-diagram

Generate all installed diagram types from a PLCC spec file. Discovers and
runs each installed `plcc-diagram-{type}` command in alphabetical order.

## Usage

```text
plcc-diagram [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-s PATH`, `--spec=PATH` | Spec file. Remembered across invocations. Defaults to `spec.plcc`. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-diagram -s subtract.plcc
```

## Diagram types

`plcc-diagram` discovers installed diagram types by scanning PATH for
`plcc-diagram-{type}` executables. Use [`plcc-diagram-list`](plcc-diagram-list.md)
to see installed formats per type.
See [Diagram extensions](../../docs/cli/guide/diagram-extensions.md) for details.
```

- [ ] **Step 6: Run the full unit test suite**

```bash
bin/test/units.bash
```

Expected: PASS (no regressions)

- [ ] **Step 7: Commit**

```bash
git add src/plcc/cmd/diagram.py src/plcc/cmd/diagram_test.py \
    tests/bats/commands/plcc-diagram.bats \
    docs/cli/commands/plcc-diagram.md
git commit -m "feat: replace plcc-diagram with type-discoverer (issue 113 phase 1) [skip ci]"
```
