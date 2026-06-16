# Grammar-to-Spec Rename — Phases 3 & 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the grammar→spec rename by updating documentation (Phase 3, PR A) and internal Python identifiers including module names, function names, and the hidden build-dir file (Phase 4, PR B).

**Architecture:** Two independent PRs. PR A is pure text edits to markdown. PR B deletes `build/grammar.py` and `cmd/grammar.py`, creates `build/spec.py` and `cmd/spec.py` with renamed symbols, then updates all import sites.

**Tech Stack:** Python, pytest, bats (functional tests via `bin/test/functional.bash`), docopt

---

## Phase 3 — Documentation (PR A)

### Task 1: Update `docs/cli/index.md`

**Files:**
- Modify: `docs/cli/index.md`

- [ ] **Step 1: Apply edits**

Make these exact substitutions:

Line 13 — change:
```
| [`plcc-make`](orchestrators.md#plcc-make) | Build a PLCC project from a grammar file |
```
to:
```
| [`plcc-make`](orchestrators.md#plcc-make) | Build a PLCC project from a spec file |
```

Line 25 — change:
```
| [`plcc-spec`](primitives.md#plcc-spec) | Parse and validate a `.plcc` grammar file; emit spec JSON |
```
to:
```
| [`plcc-spec`](primitives.md#plcc-spec) | Parse and validate a `.plcc` spec file; emit spec JSON |
```

Line 30 — change:
```
| [`plcc-diagram`](primitives.md#plcc-diagram) | Generate a class diagram from a grammar file |
```
to:
```
| [`plcc-diagram`](primitives.md#plcc-diagram) | Generate a class diagram from a spec file |
```

Lines 42–46 — change the entire "Grammar memory" section:
```markdown
## Grammar memory

The Level 2 orchestrators remember the grammar path between invocations.
Pass `-g <path>` once; subsequent commands in the same directory use the same
grammar automatically.
```
to:
```markdown
## Spec memory

The Level 2 orchestrators remember the spec path between invocations.
Pass `-s <path>` once; subsequent commands in the same directory use the same
spec automatically.
```

- [ ] **Step 2: Verify no stale `grammar` references remain (excluding language-concept uses)**

```bash
grep -n "grammar" docs/cli/index.md
```

Expected output: no lines (the file contained no language-concept uses of "grammar").

---

### Task 2: Update `docs/cli/orchestrators.md`

**Files:**
- Modify: `docs/cli/orchestrators.md`

- [ ] **Step 1: Apply edits**

Line 10 — change:
```
Build a PLCC project from a grammar file.
```
to:
```
Build a PLCC project from a spec file.
```

Line 18 — change:
```
| `-g PATH`, `--grammar=PATH` | Grammar to build from. Remembered across invocations. Defaults to `grammar.plcc` on first use. |
```
to:
```
| `-s PATH`, `--spec=PATH` | Spec to build from. Remembered across invocations. Defaults to `spec.plcc` on first use. |
```

Line 20 — change:
```
| `--no-banner` | Suppress the version and grammar banner. |
```
to:
```
| `--no-banner` | Suppress the version and spec banner. |
```

Line 25 — change:
```
plcc-make -g subtract.plcc
```
to:
```
plcc-make -s subtract.plcc
```

Line 28 — change:
```
Run `plcc-make` again after editing your grammar to rebuild.
```
to:
```
Run `plcc-make` again after editing your spec to rebuild.
```

Line 43 — change:
```
| `-g PATH`, `--grammar=PATH` | Grammar to build from. Remembered across invocations. |
```
to:
```
| `-s PATH`, `--spec=PATH` | Spec to build from. Remembered across invocations. |
```

Line 45 — change:
```
| `--no-banner` | Suppress the version and grammar banner. |
```
to:
```
| `--no-banner` | Suppress the version and spec banner. |
```

Lines 50–51 — change:
```
plcc-scan -g subtract.plcc samples
echo "42" | plcc-scan
```
to:
```
plcc-scan -s subtract.plcc samples
echo "42" | plcc-scan
```

Line 67 — change:
```
| `-g PATH`, `--grammar=PATH` | Grammar to build from. Remembered across invocations. |
```
to:
```
| `-s PATH`, `--spec=PATH` | Spec to build from. Remembered across invocations. |
```

Line 68 — change:
```
| `--no-banner` | Suppress the version and grammar banner. |
```
to:
```
| `--no-banner` | Suppress the version and spec banner. |
```

Lines 73–74 — change:
```
plcc-parse -g subtract.plcc samples
echo "42" | plcc-parse
```
to:
```
plcc-parse -s subtract.plcc samples
echo "42" | plcc-parse
```

Line 81 — change:
```
REPL — read, eval, print loop for a PLCC grammar.
```
to:
```
REPL — read, eval, print loop for a PLCC spec.
```

Line 90 — change:
```
| `-g PATH`, `--grammar=PATH` | Grammar to build from. Remembered across invocations. |
```
to:
```
| `-s PATH`, `--spec=PATH` | Spec to build from. Remembered across invocations. |
```

Line 92 — change:
```
| `--no-banner` | Suppress the version and grammar banner. |
```
to:
```
| `--no-banner` | Suppress the version and spec banner. |
```

Lines 98–101 — change:
```
# Run the 'subtract' semantic section against samples, then enter interactive mode
plcc-rep -g subtract.plcc --tool=subtract samples

# Evaluate a file only (no interactive mode)
plcc-rep -g subtract.plcc samples < /dev/null
```
to:
```
# Run the 'subtract' semantic section against samples, then enter interactive mode
plcc-rep -s subtract.plcc --tool=subtract samples

# Evaluate a file only (no interactive mode)
plcc-rep -s subtract.plcc samples < /dev/null
```

- [ ] **Step 2: Verify no stale file/flag references remain**

```bash
grep -n "\-\-grammar\|-g PATH\|grammar file\|grammar banner\|grammar to rebuild\|grammar\.plcc" docs/cli/orchestrators.md
```

Expected output: no lines.

---

### Task 3: Update `docs/cli/primitives.md`

**Files:**
- Modify: `docs/cli/primitives.md`

- [ ] **Step 1: Apply edits**

Line 10 — change:
```
Parse, validate, and print a PLCC grammar file as JSON.
```
to:
```
Parse, validate, and print a PLCC spec file as JSON.
```

Line 18 — change:
```
| `FILE` | `.plcc` grammar file. Use `-` to read from stdin. |
```
to:
```
| `FILE` | `.plcc` spec file. Use `-` to read from stdin. |
```

Line 24 — change:
```
plcc-spec grammar.plcc
```
to:
```
plcc-spec spec.plcc
```

Line 47 — change:
```
plcc-spec grammar.plcc | plcc-tokens - samples
```
to:
```
plcc-spec spec.plcc | plcc-tokens - samples
```

Line 85 — change:
```
plcc-spec grammar.plcc | plcc-model
```
to:
```
plcc-spec spec.plcc | plcc-model
```

Line 106 — change:
```
plcc-spec grammar.plcc | plcc-model | plcc-lang-emit --target=Python --output=out/
```
to:
```
plcc-spec spec.plcc | plcc-model | plcc-lang-emit --target=Python --output=out/
```

Line 113 — change:
```
Generate and display a class diagram from a PLCC grammar file.
```
to:
```
Generate and display a class diagram from a PLCC spec file.
```

Line 120 — change:
```
| `-g PATH`, `--grammar=PATH` | Grammar file. Remembers across invocations. Defaults to `grammar.plcc`. |
```
to:
```
| `-s PATH`, `--spec=PATH` | Spec file. Remembers across invocations. Defaults to `spec.plcc`. |
```

Line 123 — change:
```
| `--no-banner` | Suppress the version and grammar banner. |
```
to:
```
| `--no-banner` | Suppress the version and spec banner. |
```

Line 128 — change:
```
plcc-diagram -g mylang.plcc
```
to:
```
plcc-diagram -s mylang.plcc
```

- [ ] **Step 2: Verify no stale file/flag references remain**

```bash
grep -n "grammar file\|grammar\.plcc\|\-\-grammar\|-g PATH\|grammar banner" docs/cli/primitives.md
```

Expected output: no lines.

---

### Task 4: Update `CONTRIBUTING.md` and commit PR A

**Files:**
- Modify: `CONTRIBUTING.md`

- [ ] **Step 1: Apply edit**

Line 57 — change:
```
| **End-to-end** | `tests/bats/e2e/` | The full pipeline from grammar file to final output, via `plcc-make` or equivalent orchestrator. Exercises the whole system against a fixture. |
```
to:
```
| **End-to-end** | `tests/bats/e2e/` | The full pipeline from spec file to final output, via `plcc-make` or equivalent orchestrator. Exercises the whole system against a fixture. |
```

- [ ] **Step 2: Verify**

```bash
grep -n "grammar file" CONTRIBUTING.md
```

Expected output: no lines.

- [ ] **Step 3: Commit**

```bash
git add docs/cli/index.md docs/cli/orchestrators.md docs/cli/primitives.md CONTRIBUTING.md
git commit -m "docs(089): update docs grammar-file references to spec-file [skip ci]"
```

---

## Phase 4 — Internal Identifiers (PR B)

### Task 5: TDD for `build/spec.py`

**Files:**
- Create: `src/plcc/build/spec_test.py`
- Create: `src/plcc/build/spec.py`
- Delete: `src/plcc/build/grammar_test.py`
- Delete: `src/plcc/build/grammar.py`

- [ ] **Step 1: Write failing test file**

Create `src/plcc/build/spec_test.py`:

```python
# src/plcc/build/spec_test.py
from plcc.build.spec import read_spec, write_spec, resolve_spec_path, DEFAULT_SPEC_FILE


def test_read_spec_returns_none_when_absent(tmp_path):
    assert read_spec(tmp_path) is None


def test_read_spec_returns_stored_path(tmp_path):
    (tmp_path / ".spec").write_text("a.plcc")
    assert read_spec(tmp_path) == "a.plcc"


def test_write_spec_creates_file(tmp_path):
    write_spec(tmp_path, "a.plcc")
    assert (tmp_path / ".spec").read_text() == "a.plcc"


def test_write_spec_overwrites_existing(tmp_path):
    write_spec(tmp_path, "a.plcc")
    write_spec(tmp_path, "b.plcc")
    assert read_spec(tmp_path) == "b.plcc"


def test_read_spec_returns_none_when_empty(tmp_path):
    (tmp_path / ".spec").write_text("   ")
    assert read_spec(tmp_path) is None


def test_resolve_spec_path_explicit_wins():
    assert resolve_spec_path('explicit.plcc', 'stored.plcc') == 'explicit.plcc'


def test_resolve_spec_path_uses_stored_when_no_explicit():
    assert resolve_spec_path(None, 'stored.plcc') == 'stored.plcc'


def test_resolve_spec_path_falls_back_to_default():
    assert resolve_spec_path(None, None) == DEFAULT_SPEC_FILE
```

- [ ] **Step 2: Run to confirm import failure**

```bash
bin/test/units.bash -k spec_test
```

Expected: `ModuleNotFoundError: No module named 'plcc.build.spec'`

- [ ] **Step 3: Create `src/plcc/build/spec.py`**

```python
# src/plcc/build/spec.py
from pathlib import Path

_SPEC_FILE = ".spec"
DEFAULT_SPEC_FILE = "spec.plcc"


def read_spec(build_dir):
    p = Path(build_dir) / _SPEC_FILE
    try:
        return p.read_text().strip() or None
    except FileNotFoundError:
        return None


def write_spec(build_dir, path):
    (Path(build_dir) / _SPEC_FILE).write_text(path)


def resolve_spec_path(explicit, stored):
    if explicit is not None:
        return explicit
    elif stored is not None:
        return stored
    else:
        return DEFAULT_SPEC_FILE
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
bin/test/units.bash -k spec_test
```

Expected: 8 passed

- [ ] **Step 5: Delete the old grammar module files**

```bash
git rm src/plcc/build/grammar.py src/plcc/build/grammar_test.py
```

- [ ] **Step 6: Commit**

```bash
git add src/plcc/build/spec.py src/plcc/build/spec_test.py
git commit -m "refactor(089): rename build/grammar → build/spec, .grammar → .spec"
```

---

### Task 6: TDD for `cmd/spec.py`

**Files:**
- Create: `src/plcc/cmd/spec_test.py`
- Create: `src/plcc/cmd/spec.py`
- Delete: `src/plcc/cmd/grammar_test.py`
- Delete: `src/plcc/cmd/grammar.py`

- [ ] **Step 1: Write failing test file**

Create `src/plcc/cmd/spec_test.py`:

```python
# src/plcc/cmd/spec_test.py
import pytest
from plcc.cmd.spec import validate_spec_flag, spec_flag_for_child, SPEC_OPTION
from plcc.build.spec import DEFAULT_SPEC_FILE


def test_spec_option_contains_flag():
    assert '--spec' in SPEC_OPTION


def test_spec_option_contains_default_filename():
    assert DEFAULT_SPEC_FILE in SPEC_OPTION


def test_validate_spec_flag_none_does_nothing():
    validate_spec_flag('plcc-test', {'--spec': None})


def test_validate_spec_flag_existing_file_does_nothing(tmp_path):
    f = tmp_path / 'foo.plcc'
    f.write_text('')
    validate_spec_flag('plcc-test', {'--spec': str(f)})


def test_validate_spec_flag_missing_file_exits_nonzero():
    with pytest.raises(SystemExit) as exc:
        validate_spec_flag('plcc-test', {'--spec': 'nonexistent.plcc'})
    assert exc.value.code != 0


def test_validate_spec_flag_missing_file_prints_cmd_name(capsys):
    with pytest.raises(SystemExit):
        validate_spec_flag('plcc-test', {'--spec': 'nonexistent.plcc'})
    assert 'plcc-test' in capsys.readouterr().err


def test_validate_spec_flag_missing_file_prints_path(capsys):
    with pytest.raises(SystemExit):
        validate_spec_flag('plcc-test', {'--spec': 'nonexistent.plcc'})
    assert 'nonexistent.plcc' in capsys.readouterr().err


def test_spec_flag_for_child_none_returns_empty():
    assert spec_flag_for_child({'--spec': None}) == []


def test_spec_flag_for_child_path_returns_flag():
    assert spec_flag_for_child({'--spec': 'foo.plcc'}) == ['--spec=foo.plcc']
```

- [ ] **Step 2: Run to confirm import failure**

```bash
bin/test/units.bash -k spec_test
```

Expected: `ModuleNotFoundError: No module named 'plcc.cmd.spec'`

- [ ] **Step 3: Create `src/plcc/cmd/spec.py`**

```python
# src/plcc/cmd/spec.py
import os
import sys

from plcc.build.spec import DEFAULT_SPEC_FILE

SPEC_OPTION = f"""\
    -s <path> --spec=<path>
                            Spec to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to {DEFAULT_SPEC_FILE} on first use.
"""


def validate_spec_flag(cmd_name, args):
    path = args['--spec']
    if path is not None and not os.path.exists(path):
        print(f"{cmd_name}: spec file not found: {path}", file=sys.stderr)
        print(file=sys.stderr)
        print(f"Run '{cmd_name} --help' for more information.", file=sys.stderr)
        sys.exit(1)


def spec_flag_for_child(args):
    path = args['--spec']
    return [f'--spec={path}'] if path is not None else []
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
bin/test/units.bash -k spec_test
```

Expected: 10 passed

- [ ] **Step 5: Delete the old grammar module files**

```bash
git rm src/plcc/cmd/grammar.py src/plcc/cmd/grammar_test.py
```

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/spec.py src/plcc/cmd/spec_test.py
git commit -m "refactor(089): rename cmd/grammar → cmd/spec and its symbols"
```

---

### Task 7: Update imports and locals in `make.py`

**Files:**
- Modify: `src/plcc/cmd/make.py`

At this point `plcc.build.grammar` and `plcc.cmd.grammar` no longer exist, so `make.py` is broken. Fix it:

- [ ] **Step 1: Replace the two import lines (lines 18–19)**

Change:
```python
from plcc.build.grammar import read_grammar, write_grammar, resolve_grammar_path
from plcc.cmd.grammar import GRAMMAR_OPTION
```
to:
```python
from plcc.build.spec import read_spec, write_spec, resolve_spec_path
from plcc.cmd.spec import SPEC_OPTION
```

- [ ] **Step 2: Update the docstring reference (line 31)**

Change:
```python
""" + GRAMMAR_OPTION + """\
```
to:
```python
""" + SPEC_OPTION + """\
```

- [ ] **Step 3: Rename locals in `main()` (lines 59–103)**

Change:
```python
    explicit_grammar = args['--spec']
    through = args['--through']
    build_dir = Path('build')

    stored_grammar = read_grammar(build_dir) if build_dir.is_dir() else None

    grammar = resolve_grammar_path(explicit_grammar, stored_grammar)
```
to:
```python
    explicit_spec = args['--spec']
    through = args['--through']
    build_dir = Path('build')

    stored_spec = read_spec(build_dir) if build_dir.is_dir() else None

    spec = resolve_spec_path(explicit_spec, stored_spec)
```

Change:
```python
    if explicit_grammar is None and stored_grammar is not None and not os.path.exists(grammar):
        print(f"plcc-make: spec file not found: {grammar}", file=sys.stderr)
```
to:
```python
    if explicit_spec is None and stored_spec is not None and not os.path.exists(spec):
        print(f"plcc-make: spec file not found: {spec}", file=sys.stderr)
```

Change:
```python
    if not os.path.exists(grammar):
        print(f"plcc-make: spec file not found: {grammar}", file=sys.stderr)
```
to:
```python
    if not os.path.exists(spec):
        print(f"plcc-make: spec file not found: {spec}", file=sys.stderr)
```

Change:
```python
    if banner:
        print_banner(get_version(), os.path.abspath(grammar))

    if (
        explicit_grammar is not None
        and stored_grammar is not None
        and explicit_grammar != stored_grammar
    ):
```
to:
```python
    if banner:
        print_banner(get_version(), os.path.abspath(spec))

    if (
        explicit_spec is not None
        and stored_spec is not None
        and explicit_spec != stored_spec
    ):
```

Change:
```python
    verbose.emit(Events.STARTED, message=f"spec: {grammar}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    build_dir.mkdir(exist_ok=True)
    write_grammar(build_dir, grammar)
```
to:
```python
    verbose.emit(Events.STARTED, message=f"spec: {spec}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    build_dir.mkdir(exist_ok=True)
    write_spec(build_dir, spec)
```

- [ ] **Step 4: Verify no stale grammar identifiers remain in make.py**

```bash
grep -n "\bgrammar\b\|GRAMMAR_OPTION\|read_grammar\|write_grammar\|resolve_grammar" src/plcc/cmd/make.py
```

Expected output: no lines. (The only allowed "grammar" in this file is in the string `"grammar is not LL(1)"` on line 209, which refers to grammatical structure, not the file — verify it is still present and untouched.)

- [ ] **Step 5: Run unit tests for make**

```bash
bin/test/units.bash src/plcc/cmd/make_test.py
```

Expected: all pass (the make tests import from `plcc.build.spec` via make.py — if imports are wrong, you'll see ImportError).

---

### Task 8: Update imports in `scan.py`, `parse.py`, `rep.py`, `diagram.py`

**Files:**
- Modify: `src/plcc/cmd/scan.py`
- Modify: `src/plcc/cmd/parse.py`
- Modify: `src/plcc/cmd/rep.py`
- Modify: `src/plcc/cmd/diagram.py`

Apply the same import pattern to all four files.

- [ ] **Step 1: Update `scan.py`**

Change lines 11–12:
```python
from plcc.build.grammar import read_grammar
from plcc.cmd.grammar import GRAMMAR_OPTION, validate_grammar_flag, grammar_flag_for_child
```
to:
```python
from plcc.build.spec import read_spec
from plcc.cmd.spec import SPEC_OPTION, validate_spec_flag, spec_flag_for_child
```

Update the docstring reference (search for `GRAMMAR_OPTION`):
```python
""" + GRAMMAR_OPTION + """\
```
→
```python
""" + SPEC_OPTION + """\
```

Update the three call sites in `main()`:
```python
    validate_grammar_flag('plcc-scan', args)
```
→
```python
    validate_spec_flag('plcc-scan', args)
```

```python
        + grammar_flag_for_child(args)
```
→
```python
        + spec_flag_for_child(args)
```

```python
        print_banner(get_version(), os.path.abspath(read_grammar("build")))
```
→
```python
        print_banner(get_version(), os.path.abspath(read_spec("build")))
```

- [ ] **Step 2: Update `parse.py`**

Change lines 9–10:
```python
from plcc.build.grammar import read_grammar
from plcc.cmd.grammar import GRAMMAR_OPTION, validate_grammar_flag, grammar_flag_for_child
```
to:
```python
from plcc.build.spec import read_spec
from plcc.cmd.spec import SPEC_OPTION, validate_spec_flag, spec_flag_for_child
```

Update docstring `GRAMMAR_OPTION` → `SPEC_OPTION`.

Update call sites:
- `validate_grammar_flag('plcc-parse', args)` → `validate_spec_flag('plcc-parse', args)`
- `+ grammar_flag_for_child(args)` → `+ spec_flag_for_child(args)`
- `read_grammar("build")` → `read_spec("build")`

- [ ] **Step 3: Update `rep.py`**

Change lines 11–12:
```python
from plcc.build.grammar import read_grammar
from plcc.cmd.grammar import GRAMMAR_OPTION, validate_grammar_flag, grammar_flag_for_child
```
to:
```python
from plcc.build.spec import read_spec
from plcc.cmd.spec import SPEC_OPTION, validate_spec_flag, spec_flag_for_child
```

Update docstring `GRAMMAR_OPTION` → `SPEC_OPTION`.

Update call sites:
- `validate_grammar_flag('plcc-rep', args)` → `validate_spec_flag('plcc-rep', args)`
- `+ grammar_flag_for_child(args)` → `+ spec_flag_for_child(args)`
- `read_grammar('build')` → `read_spec('build')`

- [ ] **Step 4: Update `diagram.py`**

Change lines 10–11:
```python
from plcc.build.grammar import read_grammar
from plcc.cmd.grammar import GRAMMAR_OPTION, validate_grammar_flag, grammar_flag_for_child
```
to:
```python
from plcc.build.spec import read_spec
from plcc.cmd.spec import SPEC_OPTION, validate_spec_flag, spec_flag_for_child
```

Update docstring `GRAMMAR_OPTION` → `SPEC_OPTION`.

Update call sites:
- `validate_grammar_flag('plcc-diagram', args)` → `validate_spec_flag('plcc-diagram', args)`
- `+ grammar_flag_for_child(args)` → `+ spec_flag_for_child(args)`
- `read_grammar('build')` → `read_spec('build')`

- [ ] **Step 5: Verify no stale grammar imports remain across all command files**

```bash
grep -rn "from plcc.build.grammar\|from plcc.cmd.grammar\|GRAMMAR_OPTION\|read_grammar\|write_grammar\|resolve_grammar\|validate_grammar_flag\|grammar_flag_for_child" src/plcc/cmd/
```

Expected output: no lines.

- [ ] **Step 6: Run unit tests**

```bash
bin/test/units.bash src/plcc/cmd/scan_test.py src/plcc/cmd/parse_test.py src/plcc/cmd/rep_test.py src/plcc/cmd/diagram_test.py
```

Expected: all pass.

---

### Task 9: Update consumer test files

**Files:**
- Modify: `src/plcc/cmd/make_test.py`
- Modify: `src/plcc/cmd/scan_test.py`
- Modify: `src/plcc/cmd/parse_test.py`
- Modify: `src/plcc/cmd/rep_test.py`
- Modify: `src/plcc/cmd/diagram_test.py`

These files import `read_grammar`/`write_grammar` directly for test setup. Update those imports.

- [ ] **Step 1: Update `make_test.py`**

Change:
```python
from plcc.build.grammar import read_grammar, write_grammar
```
to:
```python
from plcc.build.spec import read_spec, write_spec
```

Then replace all uses of `read_grammar(` → `read_spec(` and `write_grammar(` → `write_spec(` throughout the file.

- [ ] **Step 2: Update `rep_test.py`**

Find any direct imports from `plcc.build.grammar`:
```bash
grep -n "from plcc.build.grammar\|from plcc.cmd.grammar" src/plcc/cmd/rep_test.py
```

If any exist, update them to `plcc.build.spec` / `plcc.cmd.spec` and rename the called functions accordingly (`read_grammar` → `read_spec`, `write_grammar` → `write_spec`).

- [ ] **Step 3: Check remaining test files for direct grammar imports**

```bash
grep -rn "from plcc.build.grammar\|from plcc.cmd.grammar" src/plcc/cmd/scan_test.py src/plcc/cmd/parse_test.py src/plcc/cmd/diagram_test.py
```

If any lines appear, apply the same pattern: update the import and rename all call sites within that file.

- [ ] **Step 4: Run all unit tests**

```bash
bin/test/units.bash
```

Expected: all pass, no import errors.

---

### Task 10: Full test suite and commit PR B

- [ ] **Step 1: Run functional tests**

```bash
bin/test/functional.bash
```

Expected: all pass. If any bats test references `.grammar` (the hidden build-dir file) or old function names, fix those bats files now and re-run.

- [ ] **Step 2: Verify no orphaned grammar identifiers remain in src/**

```bash
grep -rn "from plcc.build.grammar\|from plcc.cmd.grammar\|read_grammar\|write_grammar\|resolve_grammar\|GRAMMAR_OPTION\|validate_grammar_flag\|grammar_flag_for_child\|DEFAULT_GRAMMAR_FILE\|_GRAMMAR_FILE" src/plcc/ --include="*.py"
```

Expected output: no lines.

- [ ] **Step 3: Commit**

```bash
git add src/plcc/cmd/make.py src/plcc/cmd/scan.py src/plcc/cmd/parse.py src/plcc/cmd/rep.py src/plcc/cmd/diagram.py
git add src/plcc/cmd/make_test.py src/plcc/cmd/scan_test.py src/plcc/cmd/parse_test.py src/plcc/cmd/rep_test.py src/plcc/cmd/diagram_test.py
git commit -m "refactor(089): update all import sites to use build/spec and cmd/spec"
```
