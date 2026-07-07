# Grammar CLI Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize the `--grammar`/`-g` CLI option text, validation logic, default filename, and path resolution into shared modules without changing any user-visible behavior.

**Architecture:** Two new additions — `DEFAULT_GRAMMAR_FILE` and `resolve_grammar_path()` go into `build/grammar.py` (build-level concerns); a new `cmd/grammar.py` module holds the CLI option string and arg-handling helpers (cmd-level concerns). Five command files are then updated to use these.

**Tech Stack:** Python, docopt (for CLI option string format), pytest

---

## File Map

| Action | File | Purpose |
|--------|------|---------|
| Modify | `src/plcc/build/grammar.py` | Add `DEFAULT_GRAMMAR_FILE` constant and `resolve_grammar_path()` |
| Modify | `src/plcc/build/grammar_test.py` | Tests for the two new additions |
| Create | `src/plcc/cmd/grammar.py` | `GRAMMAR_OPTION`, `validate_grammar_flag()`, `grammar_flag_for_child()` |
| Create | `src/plcc/cmd/grammar_test.py` | Tests for the new cmd helpers |
| Modify | `src/plcc/cmd/make.py` | Use `resolve_grammar_path()` and `GRAMMAR_OPTION` |
| Modify | `src/plcc/cmd/scan.py` | Use `GRAMMAR_OPTION`, `validate_grammar_flag()`, `grammar_flag_for_child()` |
| Modify | `src/plcc/cmd/parse.py` | Same as scan.py |
| Modify | `src/plcc/cmd/rep.py` | Same as scan.py |
| Modify | `src/plcc/cmd/diagram.py` | Same as scan.py |

---

## Task 1: Add `DEFAULT_GRAMMAR_FILE` and `resolve_grammar_path` to `build/grammar.py`

**Files:**
- Modify: `src/plcc/build/grammar_test.py`
- Modify: `src/plcc/build/grammar.py`

- [ ] **Step 1: Add failing tests to `src/plcc/build/grammar_test.py`**

Append these tests after the existing ones (keep the existing import line, add the new import):

```python
from plcc.build.grammar import resolve_grammar_path, DEFAULT_GRAMMAR_FILE


def test_resolve_grammar_path_explicit_wins():
    assert resolve_grammar_path('explicit.plcc', 'stored.plcc') == 'explicit.plcc'


def test_resolve_grammar_path_uses_stored_when_no_explicit():
    assert resolve_grammar_path(None, 'stored.plcc') == 'stored.plcc'


def test_resolve_grammar_path_falls_back_to_default():
    assert resolve_grammar_path(None, None) == DEFAULT_GRAMMAR_FILE
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/build/grammar_test.py -v
```

Expected: 3 failures with `ImportError: cannot import name 'resolve_grammar_path'`

- [ ] **Step 3: Add `DEFAULT_GRAMMAR_FILE` and `resolve_grammar_path` to `src/plcc/build/grammar.py`**

The full file after changes:

```python
from pathlib import Path

_GRAMMAR_FILE = ".grammar"
DEFAULT_GRAMMAR_FILE = "grammar.plcc"


def read_grammar(build_dir):
    p = Path(build_dir) / _GRAMMAR_FILE
    try:
        return p.read_text().strip() or None
    except FileNotFoundError:
        return None


def write_grammar(build_dir, path):
    (Path(build_dir) / _GRAMMAR_FILE).write_text(path)


def resolve_grammar_path(explicit, stored):
    if explicit is not None:
        return explicit
    elif stored is not None:
        return stored
    else:
        return DEFAULT_GRAMMAR_FILE
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/build/grammar_test.py -v
```

Expected: 8 passed (5 existing + 3 new)

- [ ] **Step 5: Commit**

```bash
git add src/plcc/build/grammar.py src/plcc/build/grammar_test.py
git commit -m "refactor(build): add DEFAULT_GRAMMAR_FILE and resolve_grammar_path"
```

---

## Task 2: Create `cmd/grammar.py` with CLI helpers

**Files:**
- Create: `src/plcc/cmd/grammar_test.py`
- Create: `src/plcc/cmd/grammar.py`

- [ ] **Step 1: Create `src/plcc/cmd/grammar_test.py` with failing tests**

```python
import pytest
from plcc.cmd.grammar import validate_grammar_flag, grammar_flag_for_child, GRAMMAR_OPTION
from plcc.build.grammar import DEFAULT_GRAMMAR_FILE


def test_grammar_option_contains_flag():
    assert '--grammar' in GRAMMAR_OPTION


def test_grammar_option_contains_default_filename():
    assert DEFAULT_GRAMMAR_FILE in GRAMMAR_OPTION


def test_validate_grammar_flag_none_does_nothing():
    validate_grammar_flag('plcc-test', {'--grammar': None})


def test_validate_grammar_flag_existing_file_does_nothing(tmp_path):
    f = tmp_path / 'foo.plcc'
    f.write_text('')
    validate_grammar_flag('plcc-test', {'--grammar': str(f)})


def test_validate_grammar_flag_missing_file_exits_nonzero():
    with pytest.raises(SystemExit) as exc:
        validate_grammar_flag('plcc-test', {'--grammar': 'nonexistent.plcc'})
    assert exc.value.code != 0


def test_validate_grammar_flag_missing_file_prints_cmd_name(capsys):
    with pytest.raises(SystemExit):
        validate_grammar_flag('plcc-test', {'--grammar': 'nonexistent.plcc'})
    assert 'plcc-test' in capsys.readouterr().err


def test_validate_grammar_flag_missing_file_prints_path(capsys):
    with pytest.raises(SystemExit):
        validate_grammar_flag('plcc-test', {'--grammar': 'nonexistent.plcc'})
    assert 'nonexistent.plcc' in capsys.readouterr().err


def test_grammar_flag_for_child_none_returns_empty():
    assert grammar_flag_for_child({'--grammar': None}) == []


def test_grammar_flag_for_child_path_returns_flag():
    assert grammar_flag_for_child({'--grammar': 'foo.plcc'}) == ['--grammar=foo.plcc']
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/cmd/grammar_test.py -v
```

Expected: 9 failures with `ModuleNotFoundError: No module named 'plcc.cmd.grammar'`

- [ ] **Step 3: Create `src/plcc/cmd/grammar.py`**

```python
import os
import sys

from plcc.build.grammar import DEFAULT_GRAMMAR_FILE

GRAMMAR_OPTION = f"""\
    -g <path> --grammar=<path>
                            Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to {DEFAULT_GRAMMAR_FILE} on first use.
"""


def validate_grammar_flag(cmd_name, args):
    path = args['--grammar']
    if path is not None and not os.path.exists(path):
        print(f"{cmd_name}: grammar file not found: {path}", file=sys.stderr)
        print(file=sys.stderr)
        print(f"Run '{cmd_name} --help' for more information.", file=sys.stderr)
        sys.exit(1)


def grammar_flag_for_child(args):
    path = args['--grammar']
    return [f'--grammar={path}'] if path is not None else []
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/cmd/grammar_test.py -v
```

Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/grammar.py src/plcc/cmd/grammar_test.py
git commit -m "refactor(cmd): add shared grammar CLI helpers"
```

---

## Task 3: Update `make.py`

**Files:**
- Modify: `src/plcc/cmd/make.py`

`make.py` uses `resolve_grammar_path()` (from Task 1) and `GRAMMAR_OPTION` (from Task 2). It does NOT use `validate_grammar_flag` or `grammar_flag_for_child` — its validation has two distinct error messages and it does not forward `--grammar` to a single child in the same pattern.

- [ ] **Step 1: Update imports in `src/plcc/cmd/make.py`**

Change:
```python
from plcc.build.grammar import read_grammar, write_grammar
```
To:
```python
from plcc.build.grammar import read_grammar, write_grammar, resolve_grammar_path
from plcc.cmd.grammar import GRAMMAR_OPTION
```

- [ ] **Step 2: Replace the inline grammar option text in the `__doc__` string**

Change the Options section from:
```python
__doc__ = """plcc-make
    Build a PLCC project from a grammar file.

Usage:
    plcc-make [-v ...] [options]

Options:
    -g <path> --grammar=<path>
                            Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to grammar.plcc on first use.
    --through=<level>       Build up to this level: scan, parse, model, or all [default: all].
    -b --banner             Show the version and grammar banner on stderr.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS
```

To:
```python
__doc__ = """plcc-make
    Build a PLCC project from a grammar file.

Usage:
    plcc-make [-v ...] [options]

Options:
""" + GRAMMAR_OPTION + """\
    --through=<level>       Build up to this level: scan, parse, model, or all [default: all].
    -b --banner             Show the version and grammar banner on stderr.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS
```

- [ ] **Step 3: Replace the 3-way `if/elif/else` with `resolve_grammar_path()`**

In `main()`, change:
```python
    if explicit_grammar is not None:
        grammar = explicit_grammar
    elif stored_grammar is not None:
        grammar = stored_grammar
    else:
        grammar = 'grammar.plcc'
```

To:
```python
    grammar = resolve_grammar_path(explicit_grammar, stored_grammar)
```

- [ ] **Step 4: Run unit tests**

```bash
bin/test/units.bash src/plcc/cmd/make_test.py -v
```

Expected: all existing tests pass

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/make.py
git commit -m "refactor(make): use resolve_grammar_path and GRAMMAR_OPTION"
```

---

## Task 4: Update `scan.py`

**Files:**
- Modify: `src/plcc/cmd/scan.py`

- [ ] **Step 1: Update imports**

Change:
```python
from plcc.build.grammar import read_grammar
```
To:
```python
from plcc.build.grammar import read_grammar
from plcc.cmd.grammar import GRAMMAR_OPTION, validate_grammar_flag, grammar_flag_for_child
```

- [ ] **Step 2: Replace inline grammar option text in `__doc__`**

Change:
```python
__doc__ = """plcc-scan
    Tokenize source input and print tokens in human-readable format.

Usage:
    plcc-scan [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to tokenize. Reads stdin if none given.

Options:
    -h --help                   Show this message.
    -g <path> --grammar=<path>  Grammar to build from. Once set, remembered for subsequent
                                commands until changed. Defaults to grammar.plcc on first use.
    -t --trace                  Show detailed scanning output.
    -b --banner                 Show the version and grammar banner on stderr.
""" + VERBOSE_OPTIONS
```

To:
```python
__doc__ = """plcc-scan
    Tokenize source input and print tokens in human-readable format.

Usage:
    plcc-scan [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to tokenize. Reads stdin if none given.

Options:
    -h --help                   Show this message.
""" + GRAMMAR_OPTION + """\
    -t --trace                  Show detailed scanning output.
    -b --banner                 Show the version and grammar banner on stderr.
""" + VERBOSE_OPTIONS
```

- [ ] **Step 3: Replace validation block and flag expression in `main()`**

In `main()`, remove the `grammar_file` local variable and its inline validation, and replace the subprocess flag expression.

Change this block:
```python
    grammar_file = args["--grammar"]
    sources = args["SOURCE"]
    trace = args["--trace"]

    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-scan: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-scan --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message="scanning")
    child_flags = verbose.child_flags()

    make_result = subprocess.run(
        ["plcc-make", "--through=scan"]
        + ([f"--grammar={grammar_file}"] if grammar_file is not None else [])
        + child_flags,
```

To:
```python
    sources = args["SOURCE"]
    trace = args["--trace"]

    validate_grammar_flag('plcc-scan', args)

    verbose.emit(Events.STARTED, message="scanning")
    child_flags = verbose.child_flags()

    make_result = subprocess.run(
        ["plcc-make", "--through=scan"]
        + grammar_flag_for_child(args)
        + child_flags,
```

- [ ] **Step 4: Run unit and command tests**

```bash
bin/test/units.bash src/plcc/cmd/scan_test.py -v
```

Expected: all existing scan tests pass

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/scan.py
git commit -m "refactor(scan): use shared grammar CLI helpers"
```

---

## Task 5: Update `parse.py`

**Files:**
- Modify: `src/plcc/cmd/parse.py`

- [ ] **Step 1: Update imports**

Change:
```python
from plcc.build.grammar import read_grammar
```
To:
```python
from plcc.build.grammar import read_grammar
from plcc.cmd.grammar import GRAMMAR_OPTION, validate_grammar_flag, grammar_flag_for_child
```

- [ ] **Step 2: Replace inline grammar option text in `__doc__`**

Change:
```python
__doc__ = """plcc-parse
    Parse source input and print parse tree in human-readable format.

Usage:
    plcc-parse [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to parse. Reads stdin if none given.

Options:
    -h --help                   Show this message.
    -g <path> --grammar=<path>  Grammar to build from. Once set, remembered for subsequent
                                commands until changed. Defaults to grammar.plcc on first use.
    -b --banner                 Show the version and grammar banner on stderr.
""" + VERBOSE_OPTIONS
```

To:
```python
__doc__ = """plcc-parse
    Parse source input and print parse tree in human-readable format.

Usage:
    plcc-parse [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to parse. Reads stdin if none given.

Options:
    -h --help                   Show this message.
""" + GRAMMAR_OPTION + """\
    -b --banner                 Show the version and grammar banner on stderr.
""" + VERBOSE_OPTIONS
```

- [ ] **Step 3: Replace validation block and flag expression in `main()`**

Change:
```python
    grammar_file = args["--grammar"]
    sources = args["SOURCE"]

    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-parse: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-parse --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message="parsing")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ["plcc-make", "--through=parse"]
        + ([f"--grammar={grammar_file}"] if grammar_file is not None else [])
        + child_flags,
```

To:
```python
    sources = args["SOURCE"]

    validate_grammar_flag('plcc-parse', args)

    verbose.emit(Events.STARTED, message="parsing")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ["plcc-make", "--through=parse"]
        + grammar_flag_for_child(args)
        + child_flags,
```

- [ ] **Step 4: Run unit tests**

```bash
bin/test/units.bash src/plcc/cmd/parse_test.py -v
```

Expected: all existing parse tests pass

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/parse.py
git commit -m "refactor(parse): use shared grammar CLI helpers"
```

---

## Task 6: Update `rep.py`

**Files:**
- Modify: `src/plcc/cmd/rep.py`

- [ ] **Step 1: Update imports**

Change:
```python
from plcc.build.grammar import read_grammar
```
To:
```python
from plcc.build.grammar import read_grammar
from plcc.cmd.grammar import GRAMMAR_OPTION, validate_grammar_flag, grammar_flag_for_child
```

- [ ] **Step 2: Replace inline grammar option text in `__doc__`**

Change:
```python
__doc__ = """plcc-rep
    REPL — read, eval, print loop for a PLCC grammar.

Usage:
    plcc-rep [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to evaluate before entering interactive mode.

Options:
    -g <path> --grammar=<path>
                            Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to grammar.plcc on first use.
    --tool=NAME             Semantic section to run (inferred if only one exists).
    -b --banner             Show the version and grammar banner on stderr.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS
```

To:
```python
__doc__ = """plcc-rep
    REPL — read, eval, print loop for a PLCC grammar.

Usage:
    plcc-rep [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to evaluate before entering interactive mode.

Options:
""" + GRAMMAR_OPTION + """\
    --tool=NAME             Semantic section to run (inferred if only one exists).
    -b --banner             Show the version and grammar banner on stderr.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS
```

- [ ] **Step 3: Replace validation block and flag expression in `main()`**

Change:
```python
    grammar_file = args['--grammar']
    sources = args['SOURCE']
    tool_name = args['--tool']
    verbose_format = args['--verbose-format'] or 'text'

    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-rep: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-rep --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message='starting')
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ['plcc-make']
        + ([f'--grammar={grammar_file}'] if grammar_file is not None else [])
        + child_flags,
```

To:
```python
    sources = args['SOURCE']
    tool_name = args['--tool']
    verbose_format = args['--verbose-format'] or 'text'

    validate_grammar_flag('plcc-rep', args)

    verbose.emit(Events.STARTED, message='starting')
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ['plcc-make']
        + grammar_flag_for_child(args)
        + child_flags,
```

- [ ] **Step 4: Run unit tests**

```bash
bin/test/units.bash src/plcc/cmd/rep_test.py -v
```

Expected: all existing rep tests pass

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/rep.py
git commit -m "refactor(rep): use shared grammar CLI helpers"
```

---

## Task 7: Update `diagram.py`

**Files:**
- Modify: `src/plcc/cmd/diagram.py`

- [ ] **Step 1: Update imports**

Change:
```python
from plcc.build.grammar import read_grammar
```
To:
```python
from plcc.build.grammar import read_grammar
from plcc.cmd.grammar import GRAMMAR_OPTION, validate_grammar_flag, grammar_flag_for_child
```

- [ ] **Step 2: Replace inline grammar option text in `__doc__`**

Change:
```python
__doc__ = """plcc-diagram
    Generate and display a class diagram from a PLCC grammar file.

Usage:
    plcc-diagram [-v ...] [options]

Options:
    -g <path> --grammar=<path>
                            Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to grammar.plcc on first use.
    --format=FMT            Diagram format [default: plantuml].
    -b --banner             Show the version and grammar banner on stderr.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS
```

To:
```python
__doc__ = """plcc-diagram
    Generate and display a class diagram from a PLCC grammar file.

Usage:
    plcc-diagram [-v ...] [options]

Options:
""" + GRAMMAR_OPTION + """\
    --format=FMT            Diagram format [default: plantuml].
    -b --banner             Show the version and grammar banner on stderr.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS
```

- [ ] **Step 3: Replace validation block and flag expression in `main()`**

Change:
```python
    grammar_file = args['--grammar']
    fmt = args['--format']

    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-diagram: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message="generating diagram")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ['plcc-make', '--through=model']
        + ([f'--grammar={grammar_file}'] if grammar_file is not None else [])
        + child_flags,
```

To:
```python
    fmt = args['--format']

    validate_grammar_flag('plcc-diagram', args)

    verbose.emit(Events.STARTED, message="generating diagram")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ['plcc-make', '--through=model']
        + grammar_flag_for_child(args)
        + child_flags,
```

- [ ] **Step 4: Run unit tests**

```bash
bin/test/units.bash src/plcc/cmd/diagram_test.py -v
```

Expected: all existing diagram tests pass

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/diagram.py
git commit -m "refactor(diagram): use shared grammar CLI helpers"
```

---

## Task 8: Final verification

- [ ] **Step 1: Run the full functional test suite**

```bash
bin/test/functional.bash
```

Expected: all tests pass (units + commands + integration + e2e)

- [ ] **Step 2: If any bats tests fail, check the `--help` output for the affected command**

The docstring format change (two-line grammar option instead of one-line) may affect tests that match against `--help` output. If so, update the failing bats test assertions to match the new format. The option behavior is identical — only the whitespace layout of the description changed.
