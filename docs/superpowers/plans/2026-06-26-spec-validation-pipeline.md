# Spec Validation Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the existing `validate_semantic_spec` and `validate_syntactic_spec` (and a new thin `validate_lexical_spec`) into `plcc-make` at the correct pipeline levels via three new commands (`plcc-validate-lexical`, `plcc-validate-syntactic`, `plcc-validate-semantic`), fixing the root cause of issue 118 — spec parser silently accepting invalid block delimiters like `%%{`.

**Architecture:** The three existing validator functions are dead code in production. Each gets a thin CLI wrapper that reads spec JSON from stdin, reconstructs the needed domain objects, calls the validator, and emits errors using the same `verbose.emit_error` pattern as `plcc-spec`. `plcc-make` calls them at the right `--through` levels: validate-lexical for all, validate-syntactic + ll1 for parse/model/all, validate-semantic for model/all. Semantic and syntactic error classes are promoted from `ValidationError` to `SpecError` to gain the `column`, `kind`, and `hint` attributes the CLI pattern requires.

**Tech Stack:** Python 3.14, pytest, bats 1.5+, existing plcc domain objects, `VerboseContext`, `parse_args`/docopt.

## Global Constraints

- Unit tests live alongside source (`_test.py` suffix, same directory); run with `bin/test/units.bash`
- Bats command tests: `tests/bats/commands/`; e2e: `tests/bats/e2e/`; run with `bin/test/commands.bash` / `bin/test/e2e.bash`
- All new validate CLIs read spec JSON from stdin only (no file argument), matching `plcc-ll1` convention
- Error reporting pattern: `verbose.emit_error({"file": e.line.file, "line": e.line.number, "column": e.column}, e.kind, source_line=e.line.string[, hint=e.hint])`
- Entry points go in `pyproject.toml` under `[project.scripts]`; run `pdm install` after adding
- Commit after every task with `[skip ci]` in the subject (no code is shipped until the pipeline wiring is complete)

---

### Task 1: Upgrade semantic validation error classes to SpecError

The three semantic error classes currently extend `ValidationError`, which has no `column`, `kind`, or `hint`. The validate CLI (Task 3) needs all three. Promote them to `SpecError` and improve their messages. The `InvalidClassNameError.hint` property returns a `%%{`/`%%}` suggestion when the bad name starts with `%%` — this is the user-facing fix for issue 118.

**Files:**
- Modify: `src/plcc/spec/semantics/InvalidClassNameError.py`
- Modify: `src/plcc/spec/semantics/UndefinedBlockError.py`
- Modify: `src/plcc/spec/semantics/UndefinedTargetLocatorError.py`
- Verify: `src/plcc/spec/semantics/validation_test.py` (existing tests still pass — `isinstance` checks are unaffected because `SpecError` extends `ValidationError`)

**Interfaces:**
- Consumes: `src/plcc/spec/SpecError.py` — `SpecError(line, column, message)`; produces `e.column`, `e.kind` (returns message), `e.hint`
- Produces: Error instances with `.line.file`, `.line.number`, `.line.string`, `.column`, `.kind`, `.hint` — consumed by the CLI in Task 3

- [ ] **Step 1: Replace `InvalidClassNameError.py`**

```python
# src/plcc/spec/semantics/InvalidClassNameError.py
from ..SpecError import SpecError


class InvalidClassNameError(SpecError):
    def __init__(self, line):
        super().__init__(
            line=line,
            column=1,
            message=(
                f"invalid class name '{line.string.strip()}' — "
                "must start with an uppercase letter followed by letters, digits, or underscores"
            ),
        )

    @property
    def hint(self):
        if self.line.string.strip().startswith('%%'):
            return "did you mean '%%%' instead of '%%{' or '%%}'?"
        return None
```

- [ ] **Step 2: Replace `UndefinedBlockError.py`**

```python
# src/plcc/spec/semantics/UndefinedBlockError.py
from ..SpecError import SpecError


class UndefinedBlockError(SpecError):
    def __init__(self, line):
        super().__init__(
            line=line,
            column=1,
            message=(
                f"class name '{line.string.strip()}' must be "
                "immediately followed by '%%%' on the next line"
            ),
        )
```

- [ ] **Step 3: Replace `UndefinedTargetLocatorError.py`**

```python
# src/plcc/spec/semantics/UndefinedTargetLocatorError.py
from ..SpecError import SpecError


class UndefinedTargetLocatorError(SpecError):
    def __init__(self, line):
        super().__init__(
            line=line,
            column=1,
            message="'%%%' block has no preceding class name",
        )
```

- [ ] **Step 4: Run existing validation tests — verify they still pass**

```
bin/test/units.bash src/plcc/spec/semantics/validation_test.py
```

Expected: all tests pass (isinstance checks are unaffected; SpecError extends ValidationError).

- [ ] **Step 5: Commit**

```bash
git add src/plcc/spec/semantics/InvalidClassNameError.py \
        src/plcc/spec/semantics/UndefinedBlockError.py \
        src/plcc/spec/semantics/UndefinedTargetLocatorError.py
git commit -m "refactor: upgrade semantic error classes to SpecError with improved messages [skip ci]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 2: SemanticSpec deserializer

`plcc-validate-semantic` receives spec JSON from stdin. It must reconstruct the `SemanticSpec` Python object graph so it can call the existing `validate_semantic_spec`. The spec JSON structure is produced by `plcc-spec` via `dataclasses.asdict()` and mirrors the domain objects exactly — `Line.string/number/file` are all present.

**Files:**
- Create: `src/plcc/spec/semantics/deserialize.py`
- Create: `src/plcc/spec/semantics/deserialize_test.py`

**Interfaces:**
- Consumes: spec JSON dict (from `json.load(sys.stdin)`)
- Produces: `deserialize_semantic_spec(spec: dict) -> SemanticSpec | None` — returns `None` when there is no `"semantics"` key; consumed by the CLI in Task 3

- [ ] **Step 1: Write failing tests**

```python
# src/plcc/spec/semantics/deserialize_test.py
import pytest
from .deserialize import deserialize_semantic_spec


def _line(string='X\n', number=1, file='g.plcc'):
    return {'string': string, 'number': number, 'file': file}

def _frag(class_name, modifier=None, block=True):
    return {
        'targetLocator': {
            'line': _line(class_name + '\n'),
            'className': class_name,
            'modifier': modifier,
        },
        'block': {'lines': [_line('%%%\n'), _line('%%%\n')]} if block else None,
    }

def _spec(fragments, language='Java'):
    return {'semantics': {'language': language, 'codeFragmentList': fragments}}


def test_returns_none_when_no_semantics_key():
    assert deserialize_semantic_spec({}) is None

def test_language_preserved():
    result = deserialize_semantic_spec(_spec([], 'Python'))
    assert result.language == 'Python'

def test_empty_fragment_list():
    result = deserialize_semantic_spec(_spec([]))
    assert result.codeFragmentList == []

def test_class_name_preserved():
    result = deserialize_semantic_spec(_spec([_frag('MyClass')]))
    assert result.codeFragmentList[0].targetLocator.className == 'MyClass'

def test_modifier_preserved():
    result = deserialize_semantic_spec(_spec([_frag('MyClass', modifier='init')]))
    assert result.codeFragmentList[0].targetLocator.modifier == 'init'

def test_null_modifier_preserved():
    result = deserialize_semantic_spec(_spec([_frag('MyClass', modifier=None)]))
    assert result.codeFragmentList[0].targetLocator.modifier is None

def test_line_fields_preserved():
    frag = {
        'targetLocator': {
            'line': {'string': 'MyClass\n', 'number': 7, 'file': 'grammar.plcc'},
            'className': 'MyClass',
            'modifier': None,
        },
        'block': {'lines': []},
    }
    result = deserialize_semantic_spec({'semantics': {'language': 'Java', 'codeFragmentList': [frag]}})
    line = result.codeFragmentList[0].targetLocator.line
    assert line.string == 'MyClass\n'
    assert line.number == 7
    assert line.file == 'grammar.plcc'

def test_null_block_preserved():
    result = deserialize_semantic_spec(_spec([_frag('MyClass', block=False)]))
    assert result.codeFragmentList[0].block is None

def test_null_locator_preserved():
    frag = {'targetLocator': None, 'block': {'lines': []}}
    result = deserialize_semantic_spec({'semantics': {'language': 'Java', 'codeFragmentList': [frag]}})
    assert result.codeFragmentList[0].targetLocator is None

def test_multiple_fragments():
    result = deserialize_semantic_spec(_spec([_frag('A'), _frag('B')]))
    assert len(result.codeFragmentList) == 2
    assert result.codeFragmentList[1].targetLocator.className == 'B'
```

- [ ] **Step 2: Run tests to confirm they fail**

```
bin/test/units.bash src/plcc/spec/semantics/deserialize_test.py
```

Expected: `ModuleNotFoundError` or `ImportError` — `deserialize.py` does not exist yet.

- [ ] **Step 3: Write the deserializer**

```python
# src/plcc/spec/semantics/deserialize.py
from ...lines import Line
from ..rough import Block
from .CodeFragment import CodeFragment
from .SemanticSpec import SemanticSpec
from .TargetLocator import TargetLocator


def deserialize_semantic_spec(spec):
    sem = spec.get('semantics')
    if sem is None:
        return None
    fragments = [_fragment(f) for f in sem.get('codeFragmentList', [])]
    return SemanticSpec(language=sem['language'], codeFragmentList=fragments)


def _fragment(f):
    return CodeFragment(
        targetLocator=_locator(f.get('targetLocator')),
        block=_block(f.get('block')),
    )


def _locator(loc):
    if loc is None:
        return None
    return TargetLocator(
        line=_line(loc['line']),
        className=loc['className'],
        modifier=loc.get('modifier'),
    )


def _block(blk):
    if blk is None:
        return None
    return Block(lines=[_line(l) for l in blk.get('lines', [])])


def _line(d):
    return Line(string=d['string'], number=d['number'], file=d.get('file'))
```

- [ ] **Step 4: Run tests to confirm they pass**

```
bin/test/units.bash src/plcc/spec/semantics/deserialize_test.py
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/spec/semantics/deserialize.py \
        src/plcc/spec/semantics/deserialize_test.py
git commit -m "feat: add SemanticSpec deserializer from spec JSON [skip ci]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 3: `plcc-validate-semantic` command

The CLI reads spec JSON from stdin, calls `deserialize_semantic_spec`, calls `validate_semantic_spec`, and emits structured errors. No semantics section → exits 0 silently (the command is a no-op when the spec has no semantic section).

**Files:**
- Create: `src/plcc/spec/semantics/plcc_validate_semantic_cli.py`
- Modify: `pyproject.toml` (add entry point)
- Create: `tests/bats/commands/plcc-validate-semantic.bats`

**Interfaces:**
- Consumes: `deserialize_semantic_spec` (Task 2), `validate_semantic_spec` (existing)
- Produces: `plcc-validate-semantic` binary (stdin → exit 0/1 + stderr errors)

- [ ] **Step 1: Write the CLI**

```python
# src/plcc/spec/semantics/plcc_validate_semantic_cli.py
import enum
import json
import sys

from plcc.cli import parse_args
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

from .deserialize import deserialize_semantic_spec
from .validation import validate_semantic_spec

__doc__ = """plcc-validate-semantic
    Validate the semantic section of a spec JSON.

Usage:
    plcc-validate-semantic [-v ...] [options]

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-validate-semantic", Events, args)
    verbose.emit(Events.STARTED)
    try:
        spec = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        verbose.emit_error({}, f"malformed spec JSON: {e}")
        sys.exit(1)
    sem = deserialize_semantic_spec(spec)
    if sem is None:
        verbose.emit(Events.FINISHED, message="no semantics section")
        return
    errors = validate_semantic_spec(sem)
    if errors:
        for e in errors:
            pos = {"file": e.line.file, "line": e.line.number, "column": e.column}
            kwargs = {"source_line": e.line.string}
            if e.hint:
                kwargs["hint"] = e.hint
            verbose.emit_error(pos, e.kind, **kwargs)
        sys.exit(1)
    verbose.emit(Events.FINISHED, message="ok")
```

- [ ] **Step 2: Add the entry point to `pyproject.toml`**

Add after the `plcc-spec` line (line 53):

```toml
plcc-validate-semantic  = "plcc.spec.semantics.plcc_validate_semantic_cli:main"
```

- [ ] **Step 3: Install the new entry point**

```
pdm install
```

Expected: no errors; `plcc-validate-semantic --help` prints Usage.

- [ ] **Step 4: Write bats command tests**

```bash
# tests/bats/commands/plcc-validate-semantic.bats
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
}

@test "plcc-validate-semantic is on PATH" {
    command -v plcc-validate-semantic
}

@test "plcc-validate-semantic --help exits 0 and prints Usage" {
    run plcc-validate-semantic --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage"* ]]
}

@test "plcc-validate-semantic exits 0 for valid spec with semantic section" {
    run bash -c "plcc-spec '${FIXTURES}/trivial-python.plcc' | plcc-validate-semantic"
    [ "$status" -eq 0 ]
}

@test "plcc-validate-semantic exits 0 for valid spec without semantic section" {
    run bash -c "plcc-spec '${FIXTURES}/trivial.plcc' | plcc-validate-semantic"
    [ "$status" -eq 0 ]
}

@test "plcc-validate-semantic exits 1 for spec with invalid class name" {
    SPEC_JSON=$(mktemp)
    trap "rm -f '${SPEC_JSON}'" EXIT
    cat > "${SPEC_JSON}" <<'EOF'
{
  "semantics": {
    "language": "Java",
    "codeFragmentList": [{
      "targetLocator": {
        "line": {"string": "%%{\n", "number": 5, "file": "bad.plcc"},
        "className": "%%{",
        "modifier": null
      },
      "block": null
    }]
  }
}
EOF
    run --separate-stderr bash -c "plcc-validate-semantic < '${SPEC_JSON}'"
    [ "$status" -eq 1 ]
    [ -n "$stderr" ]
}

@test "plcc-validate-semantic error references offending line" {
    SPEC_JSON=$(mktemp)
    trap "rm -f '${SPEC_JSON}'" EXIT
    cat > "${SPEC_JSON}" <<'EOF'
{
  "semantics": {
    "language": "Java",
    "codeFragmentList": [{
      "targetLocator": {
        "line": {"string": "%%{\n", "number": 5, "file": "bad.plcc"},
        "className": "%%{",
        "modifier": null
      },
      "block": null
    }]
  }
}
EOF
    run --separate-stderr bash -c "plcc-validate-semantic < '${SPEC_JSON}'"
    [[ "$stderr" == *"bad.plcc"* ]]
    [[ "$stderr" == *":5:"* ]]
}

@test "plcc-validate-semantic hint mentions %%% for %% prefix" {
    SPEC_JSON=$(mktemp)
    trap "rm -f '${SPEC_JSON}'" EXIT
    cat > "${SPEC_JSON}" <<'EOF'
{
  "semantics": {
    "language": "Java",
    "codeFragmentList": [{
      "targetLocator": {
        "line": {"string": "%%{\n", "number": 3, "file": "bad.plcc"},
        "className": "%%{",
        "modifier": null
      },
      "block": null
    }]
  }
}
EOF
    run --separate-stderr bash -c "plcc-validate-semantic < '${SPEC_JSON}'"
    [[ "$stderr" == *"%%%"* ]]
}
```

- [ ] **Step 5: Run bats command tests**

```
bin/test/commands.bash
```

Expected: the new `plcc-validate-semantic.bats` tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/spec/semantics/plcc_validate_semantic_cli.py \
        pyproject.toml \
        tests/bats/commands/plcc-validate-semantic.bats
git commit -m "feat: add plcc-validate-semantic command [skip ci]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 4: Wire `plcc-validate-semantic` into `plcc-make` + e2e acceptance test

Add `plcc-validate-semantic` to the `model` and `all` pipeline levels in `plcc-make`. Create a fixture with `%%{`/`%%}` delimiters and an e2e test that confirms `plcc-make --through=model` exits non-zero with a useful error, not a `FileNotFoundError`. This task fully fixes issue 118.

**Files:**
- Modify: `src/plcc/cmd/make.py`
- Create: `tests/fixtures/bad-delimiters.plcc`
- Create: `tests/bats/e2e/bad_block_delimiters.bats`

**Interfaces:**
- Consumes: `plcc-validate-semantic` binary (Task 3)
- Produces: `plcc-make --through=model` fails fast on bad delimiters with a clear error

- [ ] **Step 1: Create the bad-delimiters fixture**

```
# tests/fixtures/bad-delimiters.plcc
token NUM '\d+'
skip WS '\s+'
%
<Program> ::= NUM
%
Java
%%{
public void _run() {}
%%}
```

- [ ] **Step 2: Write the e2e test**

```bash
# tests/bats/e2e/bad_block_delimiters.bats
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-make --through=model exits nonzero for spec with bad block delimiters" {
    run --separate-stderr plcc-make --spec="${FIXTURES}/bad-delimiters.plcc" --through=model
    [ "$status" -ne 0 ]
}

@test "plcc-make error mentions the offending line content" {
    run --separate-stderr plcc-make --spec="${FIXTURES}/bad-delimiters.plcc" --through=model
    [[ "$stderr" == *"%%{"* ]]
}

@test "plcc-make error does not mention FileNotFoundError" {
    run --separate-stderr plcc-make --spec="${FIXTURES}/bad-delimiters.plcc" --through=model
    [[ "$stderr" != *"FileNotFoundError"* ]]
}

@test "plcc-make --through=scan succeeds for spec with bad block delimiters" {
    run plcc-make --spec="${FIXTURES}/bad-delimiters.plcc" --through=scan
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 3: Run the e2e test before the fix to confirm it fails**

```
bin/test/e2e.bash
```

Expected: the `bad_block_delimiters.bats` tests fail (validate-semantic is not yet wired in, so `plcc-make --through=model` currently succeeds with bad output).

- [ ] **Step 4: Add `plcc-validate-semantic` to `plcc-make`**

In `src/plcc/cmd/make.py`, find the block:

```python
    if through in ('model', 'all'):
        verbose.emit(Events.PHASE, message="model")
        model_json = str(build_dir / 'model.json')
        _run_or_die(['plcc-model', spec_json] + child_flags, stdout_file=model_json, verbose=verbose)
```

Replace with:

```python
    if through in ('model', 'all'):
        verbose.emit(Events.PHASE, message="validate-semantic")
        _run_or_die(['plcc-validate-semantic'] + child_flags, stdin_file=spec_json, verbose=verbose)
        verbose.emit(Events.PHASE, message="model")
        model_json = str(build_dir / 'model.json')
        _run_or_die(['plcc-model', spec_json] + child_flags, stdout_file=model_json, verbose=verbose)
```

- [ ] **Step 5: Run the e2e test after the fix to confirm it passes**

```
PLCC_NO_TEST_CACHE=1 bin/test/e2e.bash
```

Expected: all `bad_block_delimiters.bats` tests pass. The `--through=scan` test also passes (validate-semantic is not called at scan level).

- [ ] **Step 6: Run the full unit + command suite to check for regressions**

```
PLCC_NO_TEST_CACHE=1 bin/test/functional.bash
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/plcc/cmd/make.py \
        tests/fixtures/bad-delimiters.plcc \
        tests/bats/e2e/bad_block_delimiters.bats
git commit -m "fix(118): wire plcc-validate-semantic into plcc-make; add e2e test for bad block delimiters

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 5: `validate_lexical_spec` + `plcc-validate-lexical` command

Create a thin `validate_lexical_spec` function (returns an empty list — lexical validation is already inline in the lexical parser). Create the `plcc-validate-lexical` CLI, register the entry point, add bats command tests, and wire into `plcc-make` for all levels. This establishes the pattern and provides a hook for future lexical validations.

**Files:**
- Create: `src/plcc/spec/lexical/validate_lexical_spec.py`
- Create: `src/plcc/spec/lexical/validate_lexical_spec_test.py`
- Create: `src/plcc/spec/lexical/plcc_validate_lexical_cli.py`
- Modify: `pyproject.toml`
- Create: `tests/bats/commands/plcc-validate-lexical.bats`
- Modify: `src/plcc/cmd/make.py`

**Interfaces:**
- Produces: `validate_lexical_spec(spec: dict) -> list` — returns `[]`; `plcc-validate-lexical` binary (stdin → exit 0)

- [ ] **Step 1: Write the failing unit test**

```python
# src/plcc/spec/lexical/validate_lexical_spec_test.py
from .validate_lexical_spec import validate_lexical_spec


def test_returns_empty_list_for_any_spec():
    assert validate_lexical_spec({'lexical': {'ruleList': []}}) == []

def test_returns_empty_list_for_empty_dict():
    assert validate_lexical_spec({}) == []
```

- [ ] **Step 2: Run test to confirm it fails**

```
bin/test/units.bash src/plcc/spec/lexical/validate_lexical_spec_test.py
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write the validator**

```python
# src/plcc/spec/lexical/validate_lexical_spec.py
def validate_lexical_spec(spec):
    """Validate the lexical section of a spec JSON dict. Currently a no-op hook."""
    return []
```

- [ ] **Step 4: Run test to confirm it passes**

```
bin/test/units.bash src/plcc/spec/lexical/validate_lexical_spec_test.py
```

Expected: passes.

- [ ] **Step 5: Write the CLI**

```python
# src/plcc/spec/lexical/plcc_validate_lexical_cli.py
import enum
import json
import sys

from plcc.cli import parse_args
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

from .validate_lexical_spec import validate_lexical_spec

__doc__ = """plcc-validate-lexical
    Validate the lexical section of a spec JSON.

Usage:
    plcc-validate-lexical [-v ...] [options]

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-validate-lexical", Events, args)
    verbose.emit(Events.STARTED)
    try:
        spec = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        verbose.emit_error({}, f"malformed spec JSON: {e}")
        sys.exit(1)
    errors = validate_lexical_spec(spec)
    if errors:
        for e in errors:
            pos = {"file": e.line.file, "line": e.line.number, "column": e.column}
            kwargs = {"source_line": e.line.string}
            if e.hint:
                kwargs["hint"] = e.hint
            verbose.emit_error(pos, e.kind, **kwargs)
        sys.exit(1)
    verbose.emit(Events.FINISHED, message="ok")
```

- [ ] **Step 6: Add entry point to `pyproject.toml`**

Add after the `plcc-validate-semantic` line:

```toml
plcc-validate-lexical   = "plcc.spec.lexical.plcc_validate_lexical_cli:main"
```

- [ ] **Step 7: Install and verify**

```
pdm install
plcc-validate-lexical --help
```

Expected: prints Usage.

- [ ] **Step 8: Write bats command tests**

```bash
# tests/bats/commands/plcc-validate-lexical.bats
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
}

@test "plcc-validate-lexical is on PATH" {
    command -v plcc-validate-lexical
}

@test "plcc-validate-lexical --help exits 0 and prints Usage" {
    run plcc-validate-lexical --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage"* ]]
}

@test "plcc-validate-lexical exits 0 for valid spec" {
    run bash -c "plcc-spec '${FIXTURES}/trivial.plcc' | plcc-validate-lexical"
    [ "$status" -eq 0 ]
}

@test "plcc-validate-lexical exits 0 for spec with semantic section" {
    run bash -c "plcc-spec '${FIXTURES}/trivial-python.plcc' | plcc-validate-lexical"
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 9: Run command tests**

```
bin/test/commands.bash
```

Expected: new lexical tests pass.

- [ ] **Step 10: Wire `plcc-validate-lexical` into `plcc-make`**

In `src/plcc/cmd/make.py`, find the line:

```python
    os.replace(tmp_spec, build_dir / 'spec.json')
    spec_json = str(build_dir / 'spec.json')
    model_json = None
    delete_sentinel(build_dir)  # absent until final success write below
```

Add after `delete_sentinel`:

```python
    verbose.emit(Events.PHASE, message="validate-lexical")
    _run_or_die(['plcc-validate-lexical'] + child_flags, stdin_file=spec_json, verbose=verbose)
```

- [ ] **Step 11: Run full functional suite to check for regressions**

```
PLCC_NO_TEST_CACHE=1 bin/test/functional.bash
```

Expected: all tests pass.

- [ ] **Step 12: Commit**

```bash
git add src/plcc/spec/lexical/validate_lexical_spec.py \
        src/plcc/spec/lexical/validate_lexical_spec_test.py \
        src/plcc/spec/lexical/plcc_validate_lexical_cli.py \
        pyproject.toml \
        tests/bats/commands/plcc-validate-lexical.bats \
        src/plcc/cmd/make.py
git commit -m "feat: add plcc-validate-lexical command and wire into plcc-make [skip ci]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 6: Upgrade syntactic validation error classes to SpecError

Ten error classes in `src/plcc/spec/syntax/` extend `ValidationError` (lacking `column`, `kind`, `hint`). Promote all to `SpecError`. Each takes a `rule` (a `SyntacticRule` with a `.line` field). Use `column=1` throughout — the validators don't track column within the line.

**Files (all modify):**
- `src/plcc/spec/syntax/DuplicateAttribute.py`
- `src/plcc/spec/syntax/DuplicateLhsError.py`
- `src/plcc/spec/syntax/InvalidAttribute.py`
- `src/plcc/spec/syntax/InvalidLhsAltNameError.py`
- `src/plcc/spec/syntax/InvalidLhsNameError.py`
- `src/plcc/spec/syntax/InvalidNonterminal.py`
- `src/plcc/spec/syntax/InvalidSeparator.py`
- `src/plcc/spec/syntax/InvalidTerminal.py`
- `src/plcc/spec/syntax/UndefinedNonterminal.py`
- `src/plcc/spec/syntax/UndefinedTerminalError.py`

**Interfaces:**
- Consumes: `src/plcc/spec/SpecError.py`
- Produces: error instances with `.line`, `.column`, `.kind`, `.hint` — consumed by the CLI in Task 7

- [ ] **Step 1: Replace all ten error classes**

Apply the same pattern to each: replace `from ..ValidationError import ValidationError` with `from ..SpecError import SpecError`, change the base class, add `column=1` to `super().__init__()`. Show each file in full:

```python
# src/plcc/spec/syntax/DuplicateLhsError.py
from ..SpecError import SpecError

class DuplicateLhsError(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message=f"duplicate LHS name '{rule.lhs.name}'")
```

```python
# src/plcc/spec/syntax/InvalidLhsNameError.py
from ..SpecError import SpecError

class InvalidLhsNameError(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message=f"invalid LHS name '{rule.lhs.name}' — must start with a lowercase letter followed by letters, digits, or underscores")
```

```python
# src/plcc/spec/syntax/InvalidLhsAltNameError.py
from ..SpecError import SpecError

class InvalidLhsAltNameError(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message=f"invalid LHS alternate name '{rule.lhs.altName}' — must start with an uppercase letter followed by letters, digits, or underscores")
```

```python
# src/plcc/spec/syntax/DuplicateAttribute.py
from ..SpecError import SpecError

class DuplicateAttribute(SpecError):
    def __init__(self, rule, symbolName):
        super().__init__(line=rule.line, column=1,
            message=f"duplicate RHS symbol name '{symbolName}' — all capturing RHS symbols must have unique names")
```

```python
# src/plcc/spec/syntax/InvalidAttribute.py
from ..SpecError import SpecError

class InvalidAttribute(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message="invalid RHS alternate name — must start with a lowercase letter followed by letters, digits, or underscores")
```

```python
# src/plcc/spec/syntax/InvalidNonterminal.py
from ..SpecError import SpecError

class InvalidNonterminal(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message="invalid RHS non-terminal name — must start with a lowercase letter followed by letters, digits, or underscores")
```

```python
# src/plcc/spec/syntax/InvalidSeparator.py
from ..SpecError import SpecError

class InvalidSeparator(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message="repeating rule separator must be a terminal (all-uppercase)")
```

```python
# src/plcc/spec/syntax/InvalidTerminal.py
from ..SpecError import SpecError

class InvalidTerminal(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message="invalid RHS terminal name — must be all uppercase letters, digits, and underscores, and cannot start with a digit")
```

```python
# src/plcc/spec/syntax/UndefinedNonterminal.py
from ..SpecError import SpecError

class UndefinedNonterminal(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message="rule contains an RHS non-terminal not defined in any LHS rule")
```

```python
# src/plcc/spec/syntax/UndefinedTerminalError.py
from ..SpecError import SpecError

class UndefinedTerminalError(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message="RHS terminal is not defined in the lexical section")
```

- [ ] **Step 2: Run unit tests — verify existing syntactic validation tests still pass**

```
bin/test/units.bash src/plcc/spec/syntax/
```

Expected: all tests pass. (`isinstance` checks are unaffected; `SpecError` extends `ValidationError`.)

- [ ] **Step 3: Commit**

```bash
git add src/plcc/spec/syntax/DuplicateAttribute.py \
        src/plcc/spec/syntax/DuplicateLhsError.py \
        src/plcc/spec/syntax/InvalidAttribute.py \
        src/plcc/spec/syntax/InvalidLhsAltNameError.py \
        src/plcc/spec/syntax/InvalidLhsNameError.py \
        src/plcc/spec/syntax/InvalidNonterminal.py \
        src/plcc/spec/syntax/InvalidSeparator.py \
        src/plcc/spec/syntax/InvalidTerminal.py \
        src/plcc/spec/syntax/UndefinedNonterminal.py \
        src/plcc/spec/syntax/UndefinedTerminalError.py
git commit -m "refactor: upgrade syntactic validation error classes to SpecError [skip ci]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 7: `plcc-validate-syntactic` command + wiring + `_REQUIRED` fix

The most complex task. The deserializer must reconstruct `SyntacticSpec` (list of `SyntacticRule` subclass instances) and `LexicalSpec` from JSON. The dispatch is on `isTerminal`+`isCapturing` flags for RHS symbols, and on presence of a `"separator"` key for `RepeatingSyntacticRule`. Wire into `plcc-make` for parse/model/all levels, expand `ll1` to run for model too, and fix `_REQUIRED` so model subsumes parse.

**Files:**
- Create: `src/plcc/spec/syntax/deserialize.py`
- Create: `src/plcc/spec/syntax/deserialize_test.py`
- Create: `src/plcc/spec/syntax/plcc_validate_syntactic_cli.py`
- Modify: `pyproject.toml`
- Create: `tests/bats/commands/plcc-validate-syntactic.bats`
- Modify: `src/plcc/cmd/make.py`

**Interfaces:**
- Consumes: `validate_syntactic_spec(SyntacticSpec, LexicalSpec)` (existing); error classes from Task 6
- Produces: `deserialize_syntactic_spec(spec: dict) -> tuple[SyntacticSpec, LexicalSpec]`; `plcc-validate-syntactic` binary

- [ ] **Step 1: Write failing deserializer tests**

```python
# src/plcc/spec/syntax/deserialize_test.py
import pytest
from .deserialize import deserialize_syntactic_spec
from .StandardSyntacticRule import StandardSyntacticRule
from .RepeatingSyntacticRule import RepeatingSyntacticRule
from .Terminal import Terminal
from .CapturingTerminal import CapturingTerminal
from .RhsNonTerminal import RhsNonTerminal


def _line(s='<A> ::= B\n', n=1, f='g.plcc'):
    return {'string': s, 'number': n, 'file': f}

def _lhs(name, alt=None):
    return {'name': name, 'altName': alt, 'isTerminal': False, 'isCapturing': False}

def _terminal(name, capturing=False, alt=None):
    d = {'name': name, 'isTerminal': True, 'isCapturing': capturing}
    if alt:
        d['altName'] = alt
    return d

def _nonterminal(name, alt=None):
    return {'name': name, 'isTerminal': False, 'isCapturing': True, 'altName': alt}

def _rule(lhs_name, rhs=None, separator=None):
    r = {'line': _line(), 'lhs': _lhs(lhs_name), 'rhsSymbolList': rhs or []}
    if separator is not None:
        r['separator'] = separator
    return r

def _lex_rule(name, pattern='x', skip=False):
    return {'line': _line(), 'name': name, 'pattern': pattern, 'isSkip': skip}


def test_empty_syntax_gives_empty_spec():
    syn, lex = deserialize_syntactic_spec({'syntax': {'rules': []}, 'lexical': {'ruleList': []}})
    assert len(syn) == 0

def test_standard_rule_is_standard_syntactic_rule():
    spec = {'syntax': {'rules': [_rule('Program')]}, 'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    assert isinstance(syn[0], StandardSyntacticRule)

def test_rule_with_separator_is_repeating_syntactic_rule():
    spec = {'syntax': {'rules': [_rule('Items', separator=_terminal('COMMA'))]},
            'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    assert isinstance(syn[0], RepeatingSyntacticRule)

def test_separator_is_terminal_instance():
    spec = {'syntax': {'rules': [_rule('Items', separator=_terminal('COMMA'))]},
            'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    assert isinstance(syn[0].separator, Terminal)
    assert syn[0].separator.name == 'COMMA'

def test_lhs_name_preserved():
    spec = {'syntax': {'rules': [_rule('Program')]}, 'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    assert syn[0].lhs.name == 'Program'

def test_lhs_alt_name_preserved():
    r = _rule('Expr')
    r['lhs']['altName'] = 'AddExpr'
    spec = {'syntax': {'rules': [r]}, 'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    assert syn[0].lhs.altName == 'AddExpr'

def test_terminal_rhs_symbol():
    spec = {'syntax': {'rules': [_rule('A', rhs=[_terminal('NUM')])]},
            'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    sym = syn[0].rhsSymbolList[0]
    assert isinstance(sym, Terminal)
    assert sym.name == 'NUM'

def test_capturing_terminal_rhs_symbol():
    spec = {'syntax': {'rules': [_rule('A', rhs=[_terminal('NUM', capturing=True, alt='n')])]},
            'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    sym = syn[0].rhsSymbolList[0]
    assert isinstance(sym, CapturingTerminal)
    assert sym.altName == 'n'

def test_nonterminal_rhs_symbol():
    spec = {'syntax': {'rules': [_rule('A', rhs=[_nonterminal('B', alt='b')])]},
            'lexical': {'ruleList': []}}
    syn, _ = deserialize_syntactic_spec(spec)
    sym = syn[0].rhsSymbolList[0]
    assert isinstance(sym, RhsNonTerminal)
    assert sym.name == 'B'
    assert sym.altName == 'b'

def test_lexical_rule_name_preserved():
    spec = {'syntax': {'rules': []}, 'lexical': {'ruleList': [_lex_rule('NUM')]}}
    _, lex = deserialize_syntactic_spec(spec)
    assert lex.ruleList[0].name == 'NUM'

def test_lexical_skip_rule():
    from ..lexical.TokenRule import TokenRule
    from ..lexical.SkipRule import SkipRule
    spec = {'syntax': {'rules': []}, 'lexical': {'ruleList': [_lex_rule('WS', skip=True)]}}
    _, lex = deserialize_syntactic_spec(spec)
    assert isinstance(lex.ruleList[0], SkipRule)

def test_lexical_token_rule():
    from ..lexical.TokenRule import TokenRule
    spec = {'syntax': {'rules': []}, 'lexical': {'ruleList': [_lex_rule('NUM', skip=False)]}}
    _, lex = deserialize_syntactic_spec(spec)
    assert isinstance(lex.ruleList[0], TokenRule)
```

- [ ] **Step 2: Run tests to confirm they fail**

```
bin/test/units.bash src/plcc/spec/syntax/deserialize_test.py
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write the deserializer**

```python
# src/plcc/spec/syntax/deserialize.py
from ...lines import Line
from ..lexical.LexicalSpec import LexicalSpec
from ..lexical.TokenRule import TokenRule
from ..lexical.SkipRule import SkipRule
from .CapturingTerminal import CapturingTerminal
from .LhsNonTerminal import LhsNonTerminal
from .RepeatingSyntacticRule import RepeatingSyntacticRule
from .RhsNonTerminal import RhsNonTerminal
from .StandardSyntacticRule import StandardSyntacticRule
from .SyntacticSpec import SyntacticSpec
from .Terminal import Terminal


def deserialize_syntactic_spec(spec):
    rules = [_rule(r) for r in spec.get('syntax', {}).get('rules', [])]
    syn = SyntacticSpec(rules=rules)
    lex_rules = [_lex_rule(r) for r in spec.get('lexical', {}).get('ruleList', [])]
    lex = LexicalSpec(ruleList=lex_rules)
    return syn, lex


def _rule(r):
    line = _line(r['line'])
    lhs = LhsNonTerminal(name=r['lhs']['name'], altName=r['lhs'].get('altName'))
    rhs = [_symbol(s) for s in r.get('rhsSymbolList', [])]
    if 'separator' in r:
        sep = _symbol(r['separator']) if r['separator'] is not None else None
        return RepeatingSyntacticRule(line=line, lhs=lhs, rhsSymbolList=rhs, separator=sep)
    return StandardSyntacticRule(line=line, lhs=lhs, rhsSymbolList=rhs)


def _symbol(s):
    name = s.get('name')
    alt = s.get('altName')
    is_terminal = s.get('isTerminal', False)
    is_capturing = s.get('isCapturing', False)
    if is_terminal and is_capturing:
        return CapturingTerminal(name=name, altName=alt)
    if is_terminal:
        return Terminal(name=name)
    return RhsNonTerminal(name=name, altName=alt)


def _lex_rule(r):
    line = _line(r['line']) if r.get('line') else None
    RuleClass = SkipRule if r.get('isSkip') else TokenRule
    return RuleClass(line=line, name=r['name'], pattern=r['pattern'])


def _line(d):
    return Line(string=d['string'], number=d['number'], file=d.get('file'))
```

- [ ] **Step 4: Run tests to confirm they pass**

```
bin/test/units.bash src/plcc/spec/syntax/deserialize_test.py
```

Expected: all tests pass.

- [ ] **Step 5: Write the CLI**

```python
# src/plcc/spec/syntax/plcc_validate_syntactic_cli.py
import enum
import json
import sys

from plcc.cli import parse_args
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

from .deserialize import deserialize_syntactic_spec
from .validations.validate_syntactic_spec import validate_syntactic_spec

__doc__ = """plcc-validate-syntactic
    Validate the syntactic section of a spec JSON.

Usage:
    plcc-validate-syntactic [-v ...] [options]

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-validate-syntactic", Events, args)
    verbose.emit(Events.STARTED)
    try:
        spec = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        verbose.emit_error({}, f"malformed spec JSON: {e}")
        sys.exit(1)
    if not spec.get('syntax', {}).get('rules'):
        verbose.emit(Events.FINISHED, message="no syntactic rules")
        return
    syn, lex = deserialize_syntactic_spec(spec)
    errors = validate_syntactic_spec(syn, lex)
    if errors:
        for e in errors:
            pos = {"file": e.line.file, "line": e.line.number, "column": e.column}
            kwargs = {"source_line": e.line.string}
            if e.hint:
                kwargs["hint"] = e.hint
            verbose.emit_error(pos, e.kind, **kwargs)
        sys.exit(1)
    verbose.emit(Events.FINISHED, message="ok")
```

- [ ] **Step 6: Add entry point to `pyproject.toml`**

Add after the `plcc-validate-lexical` line:

```toml
plcc-validate-syntactic = "plcc.spec.syntax.plcc_validate_syntactic_cli:main"
```

- [ ] **Step 7: Install and verify**

```
pdm install
plcc-validate-syntactic --help
```

Expected: prints Usage.

- [ ] **Step 8: Write bats command tests**

```bash
# tests/bats/commands/plcc-validate-syntactic.bats
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
}

@test "plcc-validate-syntactic is on PATH" {
    command -v plcc-validate-syntactic
}

@test "plcc-validate-syntactic --help exits 0 and prints Usage" {
    run plcc-validate-syntactic --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage"* ]]
}

@test "plcc-validate-syntactic exits 0 for valid spec" {
    run bash -c "plcc-spec '${FIXTURES}/trivial.plcc' | plcc-validate-syntactic"
    [ "$status" -eq 0 ]
}

@test "plcc-validate-syntactic exits 0 for valid arith spec" {
    run bash -c "plcc-spec '${FIXTURES}/arith.plcc' | plcc-validate-syntactic"
    [ "$status" -eq 0 ]
}

@test "plcc-validate-syntactic exits 1 for spec with undefined terminal" {
    SPEC_JSON=$(mktemp)
    trap "rm -f '${SPEC_JSON}'" EXIT
    cat > "${SPEC_JSON}" <<'EOF'
{
  "lexical": {"ruleList": []},
  "syntax": {"rules": [{
    "line": {"string": "<Program> ::= UNDEFINED\n", "number": 3, "file": "bad.plcc"},
    "lhs": {"name": "Program", "altName": null, "isTerminal": false, "isCapturing": false},
    "rhsSymbolList": [{"name": "UNDEFINED", "isTerminal": true, "isCapturing": false}]
  }]}
}
EOF
    run --separate-stderr bash -c "plcc-validate-syntactic < '${SPEC_JSON}'"
    [ "$status" -eq 1 ]
    [ -n "$stderr" ]
}

@test "plcc-validate-syntactic error references offending line" {
    SPEC_JSON=$(mktemp)
    trap "rm -f '${SPEC_JSON}'" EXIT
    cat > "${SPEC_JSON}" <<'EOF'
{
  "lexical": {"ruleList": []},
  "syntax": {"rules": [{
    "line": {"string": "<Program> ::= UNDEFINED\n", "number": 3, "file": "bad.plcc"},
    "lhs": {"name": "Program", "altName": null, "isTerminal": false, "isCapturing": false},
    "rhsSymbolList": [{"name": "UNDEFINED", "isTerminal": true, "isCapturing": false}]
  }]}
}
EOF
    run --separate-stderr bash -c "plcc-validate-syntactic < '${SPEC_JSON}'"
    [[ "$stderr" == *"bad.plcc"* ]]
    [[ "$stderr" == *":3:"* ]]
}
```

- [ ] **Step 9: Run command tests**

```
bin/test/commands.bash
```

Expected: new syntactic tests pass.

- [ ] **Step 10: Wire `plcc-validate-syntactic` into `plcc-make` and fix `_REQUIRED`**

In `src/plcc/cmd/make.py`, make these three changes:

**Change 1** — update `_REQUIRED` (model subsumes parse):

```python
    _REQUIRED = {
        'scan':  {'scan'},
        'parse': {'scan', 'parse'},
        'model': {'scan', 'parse', 'model'},
        'all':   {'scan', 'parse', 'model'} | lang_stage,
    }
```

**Change 2** — expand `ll1` condition from `('parse', 'all')` to `('parse', 'model', 'all')` and add `plcc-validate-syntactic` before it:

Find:
```python
    if through in ('parse', 'all'):
        verbose.emit(Events.PHASE, message="ll1")
        ll1_json = str(build_dir / 'll1.json')
        _run_or_die(['plcc-ll1'] + child_flags, stdin_file=spec_json, stdout_file=ll1_json, verbose=verbose)
        with open(ll1_json) as f:
            ll1 = json.load(f)
        if not ll1.get("is_ll1", True):
            _report_ll1_failure(ll1)
            sys.exit(1)
```

Replace with:
```python
    if through in ('parse', 'model', 'all'):
        verbose.emit(Events.PHASE, message="validate-syntactic")
        _run_or_die(['plcc-validate-syntactic'] + child_flags, stdin_file=spec_json, verbose=verbose)
        verbose.emit(Events.PHASE, message="ll1")
        ll1_json = str(build_dir / 'll1.json')
        _run_or_die(['plcc-ll1'] + child_flags, stdin_file=spec_json, stdout_file=ll1_json, verbose=verbose)
        with open(ll1_json) as f:
            ll1 = json.load(f)
        if not ll1.get("is_ll1", True):
            _report_ll1_failure(ll1)
            sys.exit(1)
```

- [ ] **Step 11: Run the full functional suite**

```
PLCC_NO_TEST_CACHE=1 bin/test/functional.bash
```

Expected: all tests pass.

- [ ] **Step 12: Commit**

```bash
git add src/plcc/spec/syntax/deserialize.py \
        src/plcc/spec/syntax/deserialize_test.py \
        src/plcc/spec/syntax/plcc_validate_syntactic_cli.py \
        pyproject.toml \
        tests/bats/commands/plcc-validate-syntactic.bats \
        src/plcc/cmd/make.py
git commit -m "feat: add plcc-validate-syntactic command; wire all validators into plcc-make; fix _REQUIRED hierarchy

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```
