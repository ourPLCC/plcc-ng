# Docopts Error Message Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace docopt's cryptic `Warning: found unmatched (duplicate?) arguments [Option(...)]` message with precise, user-facing errors: `error: unrecognized option '-x'` or `error: duplicate option '--trace'`.

**Architecture:** Create a thin `parse_args(doc, argv)` wrapper in a new `src/plcc/cli.py` module that catches `DocoptExit`, inspects the message for the internal `Option(...)` repr, classifies it as "unrecognized" or "duplicate" by checking against the docstring's known options, prints a clean error to stderr, then exits 1. All 39 CLI entry-point files swap `from docopt import docopt` → `from plcc.cli import parse_args` and `docopt(...)` → `parse_args(...)`.

**Tech Stack:** Python, pytest, docopt (existing dependency)

## Global Constraints

- All tests run via `bin/test/units.bash` (wraps `pdm test`/pytest). Run this command — not `pytest` directly.
- Follow the TDD inner loop: failing test → minimal implementation → passing test → commit.
- Commit messages must not add `[skip ci]` (these are code changes, not docs-only).
- Do not create new shell scripts; use `bin/` scripts that already exist.
- Import style: `from plcc.cli import parse_args` using the package path (not relative) for consistency with other top-level imports in these files.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/plcc/cli.py` | `parse_args` wrapper + `_reformat_if_cryptic` helper |
| Create | `src/plcc/cli_test.py` | 5 unit tests for `parse_args` |
| Modify (×32) | files listed in Task 2 with `from docopt import docopt` | swap import + call |
| Modify (×7) | files listed in Task 2 with `from docopt import docopt, DocoptExit` | swap import, keep DocoptExit |

---

## Task 1: Create `src/plcc/cli.py` (TDD)

**Files:**
- Create: `src/plcc/cli.py`
- Create: `src/plcc/cli_test.py`

**Interfaces:**
- Produces: `parse_args(doc: str, argv: list[str]) -> dict` — drop-in replacement for `docopt(doc, argv)`

---

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/cli_test.py`:

```python
import pytest

from plcc.cli import parse_args

_DOC = """Usage: test [-t]
Options:
  -t --trace  Trace.
"""

_DOC_POSITIONAL = """Usage: test FILE
"""


def test_valid_args_returns_dict():
    args = parse_args(_DOC, ['-t'])
    assert args['--trace'] is True


def test_unrecognized_short_option_exits_1(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(_DOC, ['-x'])
    assert exc.value.code == 1
    _, err = capsys.readouterr()
    assert "error: unrecognized option '-x'" in err
    assert "Usage:" in err


def test_unrecognized_long_option_exits_1(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(_DOC, ['--unknown'])
    assert exc.value.code == 1
    _, err = capsys.readouterr()
    assert "error: unrecognized option '--unknown'" in err
    assert "Usage:" in err


def test_duplicate_option_exits_1(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(_DOC, ['-t', '-t'])
    assert exc.value.code == 1
    _, err = capsys.readouterr()
    assert "error: duplicate option '--trace'" in err
    assert "Usage:" in err


def test_missing_positional_passes_through_unchanged(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(_DOC_POSITIONAL, [])
    _, err = capsys.readouterr()
    # Our rewriter did NOT touch this — no "error: unrecognized/duplicate" prefix
    assert "error: unrecognized" not in err
    assert "error: duplicate" not in err
    # docopt's original message is carried in the exception code
    assert "Usage:" in str(exc.value.code)
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/cli_test.py -v
```

Expected: `ModuleNotFoundError: No module named 'plcc.cli'` (or similar import error). All 5 tests fail.

- [ ] **Step 3: Implement `src/plcc/cli.py`**

Create `src/plcc/cli.py`:

```python
import re
import sys

from docopt import DocoptExit, docopt, parse_options


def parse_args(doc, argv):
    try:
        return docopt(doc, argv)
    except DocoptExit as e:
        _reformat_if_cryptic(str(e), doc)
        raise SystemExit(str(e))


def _reformat_if_cryptic(msg, doc):
    m = re.search(r"Option\(([^)]+)\)", msg)
    if not m:
        return
    parts = [p.strip().strip("'") for p in m.group(1).split(",")]
    short, long_ = parts[0], parts[1]
    opt = long_ if long_ != "None" else short
    opts = parse_options(doc)
    known = {o.short for o in opts if o.short} | {o.longer for o in opts if o.longer}
    kind = "duplicate" if (short in known or long_ in known) else "unrecognized"
    usage = re.search(r"(Usage:.*)", msg, re.DOTALL)
    usage_str = usage.group(1) if usage else ""
    print(f"error: {kind} option '{opt}'\n{usage_str}", file=sys.stderr)
    raise SystemExit(1)
```

- [ ] **Step 4: Run the tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/cli_test.py -v
```

Expected output (5 tests, all green):
```
PASSED src/plcc/cli_test.py::test_valid_args_returns_dict
PASSED src/plcc/cli_test.py::test_unrecognized_short_option_exits_1
PASSED src/plcc/cli_test.py::test_unrecognized_long_option_exits_1
PASSED src/plcc/cli_test.py::test_duplicate_option_exits_1
PASSED src/plcc/cli_test.py::test_missing_positional_passes_through_unchanged
```

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cli.py src/plcc/cli_test.py
git commit -m "feat: add parse_args wrapper to give clear error messages for bad options (issue 116)"
```

---

## Task 2: Migrate all 39 call sites

**Files — 32 files with `from docopt import docopt` only:**
- Modify: `src/plcc/diagram/build.py`
- Modify: `src/plcc/diagram/class_diagram/mermaid/emit.py`
- Modify: `src/plcc/diagram/class_diagram/plantuml/emit.py`
- Modify: `src/plcc/diagram/emit.py`
- Modify: `src/plcc/diagram/list.py`
- Modify: `src/plcc/diagram/mermaid/build.py`
- Modify: `src/plcc/diagram/mermaid/run.py`
- Modify: `src/plcc/diagram/plantuml/build.py`
- Modify: `src/plcc/diagram/plantuml/run.py`
- Modify: `src/plcc/diagram/run.py`
- Modify: `src/plcc/diagram/syntactic_diagram/plantuml/emit.py`
- Modify: `src/plcc/lang/build.py`
- Modify: `src/plcc/lang/emit.py`
- Modify: `src/plcc/lang/ext/haskell/build.py`
- Modify: `src/plcc/lang/ext/haskell/emit.py`
- Modify: `src/plcc/lang/ext/haskell/run.py`
- Modify: `src/plcc/lang/ext/java/build.py`
- Modify: `src/plcc/lang/ext/java/emit.py`
- Modify: `src/plcc/lang/ext/java/run.py`
- Modify: `src/plcc/lang/ext/javascript/emit.py`
- Modify: `src/plcc/lang/ext/javascript/run.py`
- Modify: `src/plcc/lang/ext/python/emit.py`
- Modify: `src/plcc/lang/ext/python/run.py`
- Modify: `src/plcc/lang/list.py`
- Modify: `src/plcc/lang/run.py`
- Modify: `src/plcc/ll1/ll1_cli.py`
- Modify: `src/plcc/model/model_cli.py`
- Modify: `src/plcc/parser/list_cli.py`
- Modify: `src/plcc/parser/table_cli.py`
- Modify: `src/plcc/spec/plcc_spec_cli.py`
- Modify: `src/plcc/tokens/tokens_cli.py`
- Modify: `src/plcc/tree/tree_cli.py`

**Files — 7 files with `from docopt import docopt, DocoptExit`:**
- Modify: `src/plcc/cmd/diagram.py`
- Modify: `src/plcc/cmd/make.py`
- Modify: `src/plcc/cmd/parse.py`
- Modify: `src/plcc/cmd/rep.py`
- Modify: `src/plcc/cmd/scan.py`
- Modify: `src/plcc/diagram/class_diagram/diagram.py`
- Modify: `src/plcc/diagram/syntactic_diagram/diagram.py`

**Interfaces:**
- Consumes: `parse_args` from `src/plcc/cli.py` (Task 1)

---

- [ ] **Step 1: Apply the mechanical substitution to the 32 docopt-only files**

Run this Python script from the repo root:

```bash
python3 - <<'EOF'
import subprocess, pathlib

files_docopt_only = [
    "src/plcc/diagram/build.py",
    "src/plcc/diagram/class_diagram/mermaid/emit.py",
    "src/plcc/diagram/class_diagram/plantuml/emit.py",
    "src/plcc/diagram/emit.py",
    "src/plcc/diagram/list.py",
    "src/plcc/diagram/mermaid/build.py",
    "src/plcc/diagram/mermaid/run.py",
    "src/plcc/diagram/plantuml/build.py",
    "src/plcc/diagram/plantuml/run.py",
    "src/plcc/diagram/run.py",
    "src/plcc/diagram/syntactic_diagram/plantuml/emit.py",
    "src/plcc/lang/build.py",
    "src/plcc/lang/emit.py",
    "src/plcc/lang/ext/haskell/build.py",
    "src/plcc/lang/ext/haskell/emit.py",
    "src/plcc/lang/ext/haskell/run.py",
    "src/plcc/lang/ext/java/build.py",
    "src/plcc/lang/ext/java/emit.py",
    "src/plcc/lang/ext/java/run.py",
    "src/plcc/lang/ext/javascript/emit.py",
    "src/plcc/lang/ext/javascript/run.py",
    "src/plcc/lang/ext/python/emit.py",
    "src/plcc/lang/ext/python/run.py",
    "src/plcc/lang/list.py",
    "src/plcc/lang/run.py",
    "src/plcc/ll1/ll1_cli.py",
    "src/plcc/model/model_cli.py",
    "src/plcc/parser/list_cli.py",
    "src/plcc/parser/table_cli.py",
    "src/plcc/spec/plcc_spec_cli.py",
    "src/plcc/tokens/tokens_cli.py",
    "src/plcc/tree/tree_cli.py",
]

for path in files_docopt_only:
    p = pathlib.Path(path)
    text = p.read_text()
    text = text.replace(
        "from docopt import docopt\n",
        "from plcc.cli import parse_args\n",
    )
    text = text.replace("docopt(__doc__, argv)", "parse_args(__doc__, argv)")
    p.write_text(text)
    print(f"updated {path}")
EOF
```

- [ ] **Step 2: Apply the substitution to the 7 files that also import DocoptExit**

```bash
python3 - <<'EOF'
import pathlib

files_with_docoptexit = [
    "src/plcc/cmd/diagram.py",
    "src/plcc/cmd/make.py",
    "src/plcc/cmd/parse.py",
    "src/plcc/cmd/rep.py",
    "src/plcc/cmd/scan.py",
    "src/plcc/diagram/class_diagram/diagram.py",
    "src/plcc/diagram/syntactic_diagram/diagram.py",
]

for path in files_with_docoptexit:
    p = pathlib.Path(path)
    text = p.read_text()
    text = text.replace(
        "from docopt import docopt, DocoptExit\n",
        "from docopt import DocoptExit\nfrom plcc.cli import parse_args\n",
    )
    text = text.replace("docopt(__doc__, argv)", "parse_args(__doc__, argv)")
    p.write_text(text)
    print(f"updated {path}")
EOF
```

- [ ] **Step 3: Verify no `docopt(__doc__, argv)` call sites remain**

```bash
grep -r "docopt(__doc__, argv)" src/ --include="*.py"
```

Expected: no output (zero matches).

- [ ] **Step 4: Run the full unit test suite**

```bash
bin/test/units.bash
```

Expected: all tests pass, zero failures. If a test fails, check that the substitution in that file's corresponding `_cli.py` is correct — the most likely cause is a variant call form (e.g. `docopt(__doc__, args)` or `docopt(doc, argv)`). Fix any such variants by hand using the same pattern.

- [ ] **Step 5: Commit**

```bash
git add src/
git commit -m "refactor: migrate all CLI entry points from docopt() to parse_args() (issue 116)"
```
