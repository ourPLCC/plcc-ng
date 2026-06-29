# Help Output vs Diagnostics Grouping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the flat `Options:` section in each user-facing plcc command's `--help` output into three named sections (`Options:`, `Output:`, `Diagnostics:`) so users can immediately distinguish feature flags from diagnostic flags.

**Architecture:** Add a new `DIAGNOSTICS_OPTIONS` constant to `verbose.py` that includes the `Diagnostics:` section header; the existing `VERBOSE_OPTIONS` constant is left untouched for the ~30 lower-level CLI files that use it. Each of the five user-facing commands in `src/plcc/cmd/` switches to `DIAGNOSTICS_OPTIONS` and gains an `Output:` section for `--banner` (and `--trace` for scan). General/control flags (`-h/--help`, `--spec`, `--through`) stay in `Options:`. No flag renames; no behavior changes.

**Tech Stack:** Python, docopt

## Global Constraints

- Help-text-only change — no flag renames, no behavior changes
- `VERBOSE_OPTIONS` in `src/plcc/verbose.py` must not be removed or modified (30+ files depend on it)
- TDD: write the failing test first, then implement, then verify green
- Run `bin/test/units.bash` after each task to catch regressions
- Commit after each task

---

### Task 1: Add DIAGNOSTICS_OPTIONS constant to verbose.py

**Files:**
- Modify: `src/plcc/verbose.py` (after line 17, add new constant)
- Test: `src/plcc/verbose_test.py` (add one test function)

**Interfaces:**
- Produces: `DIAGNOSTICS_OPTIONS` — a `str` constant importable from `plcc.verbose`, beginning with `"\nDiagnostics:\n"` and containing `-v` and `--verbose-format`

- [ ] **Step 1: Write the failing test**

In `src/plcc/verbose_test.py`, add after the existing `test_verbose_options_is_a_string` test:

```python
def test_diagnostics_options_is_a_string():
    from plcc.verbose import DIAGNOSTICS_OPTIONS
    assert isinstance(DIAGNOSTICS_OPTIONS, str)
    assert "Diagnostics:" in DIAGNOSTICS_OPTIONS
    assert "-v" in DIAGNOSTICS_OPTIONS
    assert "--verbose-format" in DIAGNOSTICS_OPTIONS
```

- [ ] **Step 2: Run test to verify it fails**

```
bin/test/units.bash src/plcc/verbose_test.py::test_diagnostics_options_is_a_string -v
```

Expected: FAIL — `ImportError: cannot import name 'DIAGNOSTICS_OPTIONS'`

- [ ] **Step 3: Add DIAGNOSTICS_OPTIONS to verbose.py**

In `src/plcc/verbose.py`, after the existing `VERBOSE_OPTIONS` block (after line 17), add:

```python
DIAGNOSTICS_OPTIONS = """
Diagnostics:
    -v                      Increase verbosity (may repeat: -v, -vv, -vvv for levels 1-3).
    --verbose-format=FMT    Output format: text or json [default: text].
"""
```

Do not remove or modify `VERBOSE_OPTIONS`.

- [ ] **Step 4: Run test to verify it passes**

```
bin/test/units.bash src/plcc/verbose_test.py::test_diagnostics_options_is_a_string -v
```

Expected: PASS

- [ ] **Step 5: Run full unit suite to check for regressions**

```
bin/test/units.bash
```

Expected: all previously passing tests still pass

- [ ] **Step 6: Commit**

```bash
git add src/plcc/verbose.py src/plcc/verbose_test.py
git commit -m "feat: add DIAGNOSTICS_OPTIONS constant with Diagnostics: section header"
```

---

### Task 2: Update plcc-scan help sections

**Files:**
- Modify: `src/plcc/cmd/scan.py` (lines 10, 128–133)
- Test: `src/plcc/cmd/scan_test.py`

**Interfaces:**
- Consumes: `DIAGNOSTICS_OPTIONS` from `plcc.verbose` (produced by Task 1)

- [ ] **Step 1: Write the failing test**

In `src/plcc/cmd/scan_test.py`, add at the top of the file (after existing imports):

```python
def test_scan_help_has_output_section():
    import plcc.cmd.scan as m
    assert "Output:" in m.__doc__
    assert "--trace" in m.__doc__
    assert "--banner" in m.__doc__


def test_scan_help_has_diagnostics_section():
    import plcc.cmd.scan as m
    assert "Diagnostics:" in m.__doc__
```

- [ ] **Step 2: Run tests to verify they fail**

```
bin/test/units.bash src/plcc/cmd/scan_test.py::test_scan_help_has_output_section src/plcc/cmd/scan_test.py::test_scan_help_has_diagnostics_section -v
```

Expected: FAIL — `AssertionError` (neither `Output:` nor `Diagnostics:` appears in `__doc__`)

- [ ] **Step 3: Update scan.py**

Change the import on line 10 from:

```python
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
```

to:

```python
from plcc.verbose import VerboseContext, DIAGNOSTICS_OPTIONS
```

Replace the `__doc__` block (lines 128–133) with:

```python
__doc__ = """plcc-scan
    Tokenize source input and print tokens in human-readable format.

Usage:
    plcc-scan [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to tokenize. Reads stdin if none given.

Options:
    -h --help                   Show this message.
""" + SPEC_OPTION + """\

Output:
    -t --trace                  Show detailed scanning output.
    -b --banner                 Show the version and spec banner on stderr.
""" + DIAGNOSTICS_OPTIONS
```

- [ ] **Step 4: Run tests to verify they pass**

```
bin/test/units.bash src/plcc/cmd/scan_test.py -v
```

Expected: all scan tests pass

- [ ] **Step 5: Run full unit suite to check for regressions**

```
bin/test/units.bash
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/scan.py src/plcc/cmd/scan_test.py
git commit -m "feat(scan): split help into Options/Output/Diagnostics sections"
```

---

### Task 3: Update plcc-parse help sections

**Files:**
- Modify: `src/plcc/cmd/parse.py` (lines 12, 26–30)
- Test: `src/plcc/cmd/parse_test.py`

**Interfaces:**
- Consumes: `DIAGNOSTICS_OPTIONS` from `plcc.verbose` (Task 1)

- [ ] **Step 1: Write the failing test**

In `src/plcc/cmd/parse_test.py`, add:

```python
def test_parse_help_has_output_section():
    import plcc.cmd.parse as m
    assert "Output:" in m.__doc__
    assert "--banner" in m.__doc__


def test_parse_help_has_diagnostics_section():
    import plcc.cmd.parse as m
    assert "Diagnostics:" in m.__doc__
```

- [ ] **Step 2: Run tests to verify they fail**

```
bin/test/units.bash src/plcc/cmd/parse_test.py::test_parse_help_has_output_section src/plcc/cmd/parse_test.py::test_parse_help_has_diagnostics_section -v
```

Expected: FAIL — `AssertionError`

- [ ] **Step 3: Update parse.py**

Change the import on line 12 from:

```python
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
```

to:

```python
from plcc.verbose import VerboseContext, DIAGNOSTICS_OPTIONS
```

Replace the `__doc__` block (lines 26–30) with:

```python
__doc__ = """plcc-parse
    Parse source input and print parse tree in human-readable format.

Usage:
    plcc-parse [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to parse. Reads stdin if none given.

Options:
    -h --help                   Show this message.
""" + SPEC_OPTION + """\

Output:
    -b --banner                 Show the version and spec banner on stderr.
""" + DIAGNOSTICS_OPTIONS
```

- [ ] **Step 4: Run tests to verify they pass**

```
bin/test/units.bash src/plcc/cmd/parse_test.py -v
```

Expected: all parse tests pass

- [ ] **Step 5: Run full unit suite**

```
bin/test/units.bash
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/parse.py src/plcc/cmd/parse_test.py
git commit -m "feat(parse): split help into Options/Output/Diagnostics sections"
```

---

### Task 4: Update plcc-rep help sections

**Files:**
- Modify: `src/plcc/cmd/rep.py` (lines 10, 27–31)
- Test: `src/plcc/cmd/rep_test.py`

**Interfaces:**
- Consumes: `DIAGNOSTICS_OPTIONS` from `plcc.verbose` (Task 1)

- [ ] **Step 1: Write the failing test**

In `src/plcc/cmd/rep_test.py`, add:

```python
def test_rep_help_has_output_section():
    import plcc.cmd.rep as m
    assert "Output:" in m.__doc__
    assert "--banner" in m.__doc__


def test_rep_help_has_diagnostics_section():
    import plcc.cmd.rep as m
    assert "Diagnostics:" in m.__doc__
```

- [ ] **Step 2: Run tests to verify they fail**

```
bin/test/units.bash src/plcc/cmd/rep_test.py::test_rep_help_has_output_section src/plcc/cmd/rep_test.py::test_rep_help_has_diagnostics_section -v
```

Expected: FAIL — `AssertionError`

- [ ] **Step 3: Update rep.py**

Change the import on line 10 from:

```python
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
```

to:

```python
from plcc.verbose import VerboseContext, DIAGNOSTICS_OPTIONS
```

Replace the `__doc__` block (lines 27–31) with:

```python
__doc__ = """plcc-rep
    REPL — read, eval, print loop for a PLCC spec.

Usage:
    plcc-rep [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to evaluate before entering interactive mode.

Options:
    -h --help               Show this message.
""" + SPEC_OPTION + """\

Output:
    -b --banner             Show the version and spec banner on stderr.
""" + DIAGNOSTICS_OPTIONS
```

- [ ] **Step 4: Run tests to verify they pass**

```
bin/test/units.bash src/plcc/cmd/rep_test.py -v
```

Expected: all rep tests pass

- [ ] **Step 5: Run full unit suite**

```
bin/test/units.bash
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/rep.py src/plcc/cmd/rep_test.py
git commit -m "feat(rep): split help into Options/Output/Diagnostics sections"
```

---

### Task 5: Update plcc-make help sections

**Files:**
- Modify: `src/plcc/cmd/make.py` (lines 14, 30–35)
- Test: `src/plcc/cmd/make_test.py`

**Interfaces:**
- Consumes: `DIAGNOSTICS_OPTIONS` from `plcc.verbose` (Task 1)

- [ ] **Step 1: Write the failing test**

In `src/plcc/cmd/make_test.py`, add:

```python
def test_make_help_has_output_section():
    import plcc.cmd.make as m
    assert "Output:" in m.__doc__
    assert "--banner" in m.__doc__


def test_make_help_has_diagnostics_section():
    import plcc.cmd.make as m
    assert "Diagnostics:" in m.__doc__
```

- [ ] **Step 2: Run tests to verify they fail**

```
bin/test/units.bash src/plcc/cmd/make_test.py::test_make_help_has_output_section src/plcc/cmd/make_test.py::test_make_help_has_diagnostics_section -v
```

Expected: FAIL — `AssertionError`

- [ ] **Step 3: Update make.py**

Change the import on line 14 from:

```python
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
```

to:

```python
from plcc.verbose import VerboseContext, DIAGNOSTICS_OPTIONS
```

Replace the `__doc__` block (lines 30–35) with:

```python
__doc__ = """plcc-make
    Build a PLCC project from a spec file.

Usage:
    plcc-make [-v ...] [options]

Options:
    -h --help               Show this message.
""" + SPEC_OPTION + """\
    --through=<level>       Build up to this level: scan, parse, model, or all [default: all].

Output:
    -b --banner             Show the version and spec banner on stderr.
""" + DIAGNOSTICS_OPTIONS
```

- [ ] **Step 4: Run tests to verify they pass**

```
bin/test/units.bash src/plcc/cmd/make_test.py -v
```

Expected: all make tests pass

- [ ] **Step 5: Run full unit suite**

```
bin/test/units.bash
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
git commit -m "feat(make): split help into Options/Output/Diagnostics sections"
```

---

### Task 6: Update plcc-diagram help sections

**Files:**
- Modify: `src/plcc/cmd/diagram.py` (lines 10, 19–23)
- Test: `src/plcc/cmd/diagram_test.py`

**Interfaces:**
- Consumes: `DIAGNOSTICS_OPTIONS` from `plcc.verbose` (Task 1)

- [ ] **Step 1: Write the failing test**

In `src/plcc/cmd/diagram_test.py`, add:

```python
def test_diagram_help_has_output_section():
    import plcc.cmd.diagram as m
    assert "Output:" in m.__doc__
    assert "--banner" in m.__doc__


def test_diagram_help_has_diagnostics_section():
    import plcc.cmd.diagram as m
    assert "Diagnostics:" in m.__doc__
```

- [ ] **Step 2: Run tests to verify they fail**

```
bin/test/units.bash src/plcc/cmd/diagram_test.py::test_diagram_help_has_output_section src/plcc/cmd/diagram_test.py::test_diagram_help_has_diagnostics_section -v
```

Expected: FAIL — `AssertionError`

- [ ] **Step 3: Update diagram.py**

Change the import on line 10 from:

```python
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
```

to:

```python
from plcc.verbose import VerboseContext, DIAGNOSTICS_OPTIONS
```

Replace the `__doc__` block (lines 19–23) with:

```python
__doc__ = """plcc-diagram
    Generate all installed diagram types from a PLCC spec file.

Usage:
    plcc-diagram [-v ...] [options]

Options:
    -h --help               Show this message.
""" + SPEC_OPTION + """\

Output:
    -b --banner             Show the version and spec banner on stderr.
""" + DIAGNOSTICS_OPTIONS
```

- [ ] **Step 4: Run tests to verify they pass**

```
bin/test/units.bash src/plcc/cmd/diagram_test.py -v
```

Expected: all diagram tests pass

- [ ] **Step 5: Run full unit suite**

```
bin/test/units.bash
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/diagram.py src/plcc/cmd/diagram_test.py
git commit -m "feat(diagram): split help into Options/Output/Diagnostics sections"
```
