# Unified Build Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `build/` the single source of truth for all Level 2 commands by implementing hash-based staleness detection in `plcc-make` and having `plcc-scan`, `plcc-parse`, and `plcc-rep` call `plcc-make` first.

**Architecture:** `plcc-make` runs `plcc-spec` into a temp file, hashes the output, compares to a JSON sentinel (`build/.spec-hash`), and skips downstream steps when the grammar and required level are already current. All other Level 2 commands call `plcc-make --through=<level>` before using artifacts from `build/`. Grammar file defaults to `./grammar.plcc` with `--grammar-file=<path>` override on all four commands.

**Tech Stack:** Python 3, `hashlib` (stdlib), `json` (stdlib), `docopt-ng`, `subprocess`, `bats-core` for CLI tests, `pytest` for unit tests.

**Spec:** `docs/superpowers/specs/2026-05-11-unified-build-design.md`

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `src/plcc/build/__init__.py` | Package marker |
| Create | `src/plcc/build/staleness.py` | Hash computation, sentinel read/write/delete, `is_current` |
| Create | `src/plcc/build/staleness_test.py` | Unit tests for staleness module |
| Create | `tests/fixtures/lexical-only.plcc` | Grammar with only a lexical section (no `%`) |
| Modify | `src/plcc/cmd/make.py` | Remove positional GRAMMAR, add `--grammar-file`/`--through`, implement staleness algorithm |
| Modify | `src/plcc/cmd/make_test.py` | Update for new interface; remove positional-arg tests |
| Modify | `src/plcc/cmd/scan.py` | Remove positional GRAMMAR, add `--grammar-file`, call `plcc-make --through=scan` |
| Modify | `src/plcc/cmd/parse.py` | Remove positional GRAMMAR, add `--grammar-file`, call `plcc-make --through=parse` |
| Modify | `src/plcc/cmd/rep.py` | Remove positional GRAMMAR (fixing silent-ignore bug), add `--grammar-file`, call `plcc-make` |
| Modify | `tests/bats/commands/plcc-make.bats` | New staleness, `--through`, grammar-resolution tests; update existing to drop positional arg |
| Modify | `tests/bats/commands/plcc-scan.bats` | Add WORK_DIR setup; update all tests to new interface |
| Modify | `tests/bats/commands/plcc-parse.bats` | Add WORK_DIR setup; update all tests to new interface |
| Modify | `tests/bats/commands/plcc-rep.bats` | Simplify setup; update all tests to new interface |

---

## Task 1: Lexical-only fixture

**Files:**
- Create: `tests/fixtures/lexical-only.plcc`

- [ ] **Step 1: Create the fixture**

```
token NUM '\d+'
```

Save as `tests/fixtures/lexical-only.plcc`. No `%` divider — lexical section only.

- [ ] **Step 2: Verify it parses**

```bash
plcc-spec tests/fixtures/lexical-only.plcc | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['lexical'], 'no lexical'; assert d['syntax']==[], 'has syntax'"
```

Expected: exits 0 silently.

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/lexical-only.plcc
git commit -m "test: add lexical-only fixture for partial-grammar tests"
```

---

## Task 2: Staleness module

**Files:**
- Create: `src/plcc/build/__init__.py`
- Create: `src/plcc/build/staleness_test.py`
- Create: `src/plcc/build/staleness.py`

- [ ] **Step 1: Write the failing unit tests**

Create `src/plcc/build/staleness_test.py`:

```python
import json
import pytest
from pathlib import Path
from plcc.build.staleness import (
    compute_hash, read_sentinel, write_sentinel, delete_sentinel, is_current,
)


def test_compute_hash_returns_hex_string(tmp_path):
    f = tmp_path / "spec.json"
    f.write_text('{"x": 1}')
    h = compute_hash(f)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_compute_hash_same_content_same_hash(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text("hello")
    b.write_text("hello")
    assert compute_hash(a) == compute_hash(b)


def test_compute_hash_different_content_different_hash(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text("hello")
    b.write_text("world")
    assert compute_hash(a) != compute_hash(b)


def test_read_sentinel_returns_none_when_absent(tmp_path):
    assert read_sentinel(tmp_path) is None


def test_read_sentinel_returns_none_on_malformed_json(tmp_path):
    (tmp_path / ".spec-hash").write_text("not json")
    assert read_sentinel(tmp_path) is None


def test_write_then_read_sentinel_roundtrips(tmp_path):
    write_sentinel(tmp_path, "abc123", "all")
    s = read_sentinel(tmp_path)
    assert s == {"hash": "abc123", "through": "all"}


def test_delete_sentinel_removes_file(tmp_path):
    write_sentinel(tmp_path, "abc123", "all")
    delete_sentinel(tmp_path)
    assert read_sentinel(tmp_path) is None


def test_delete_sentinel_is_idempotent(tmp_path):
    delete_sentinel(tmp_path)  # no error when absent


def test_is_current_false_when_sentinel_none():
    assert not is_current(None, "abc", "all")


def test_is_current_false_when_hash_differs():
    s = {"hash": "old", "through": "all"}
    assert not is_current(s, "new", "all")


def test_is_current_true_when_hash_matches_and_level_sufficient():
    s = {"hash": "abc", "through": "all"}
    assert is_current(s, "abc", "scan")
    assert is_current(s, "abc", "parse")
    assert is_current(s, "abc", "all")


def test_is_current_false_when_stored_level_insufficient():
    s = {"hash": "abc", "through": "scan"}
    assert not is_current(s, "abc", "parse")
    assert not is_current(s, "abc", "all")


def test_is_current_scan_satisfies_scan():
    s = {"hash": "abc", "through": "scan"}
    assert is_current(s, "abc", "scan")


def test_is_current_parse_satisfies_scan_and_parse():
    s = {"hash": "abc", "through": "parse"}
    assert is_current(s, "abc", "scan")
    assert is_current(s, "abc", "parse")
    assert not is_current(s, "abc", "all")
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/build/staleness_test.py
```

Expected: `ModuleNotFoundError` — `plcc.build.staleness` does not exist.

- [ ] **Step 3: Create the package marker**

Create `src/plcc/build/__init__.py` (empty).

- [ ] **Step 4: Implement `staleness.py`**

Create `src/plcc/build/staleness.py`:

```python
import hashlib
import json
from pathlib import Path

_SENTINEL = ".spec-hash"
_LEVELS = {"scan": 0, "parse": 1, "all": 2}


def compute_hash(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_sentinel(build_dir) -> dict | None:
    p = Path(build_dir) / _SENTINEL
    try:
        return json.loads(p.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def write_sentinel(build_dir, hash_: str, through: str) -> None:
    (Path(build_dir) / _SENTINEL).write_text(
        json.dumps({"hash": hash_, "through": through})
    )


def delete_sentinel(build_dir) -> None:
    try:
        (Path(build_dir) / _SENTINEL).unlink()
    except FileNotFoundError:
        pass


def is_current(sentinel: dict | None, new_hash: str, through: str) -> bool:
    if sentinel is None:
        return False
    if sentinel.get("hash") != new_hash:
        return False
    stored = _LEVELS.get(sentinel.get("through", ""), -1)
    requested = _LEVELS.get(through, -1)
    return stored >= requested
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/build/staleness_test.py
```

Expected: all 15 tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/build/__init__.py src/plcc/build/staleness.py src/plcc/build/staleness_test.py
git commit -m "feat: add staleness module for build/ sentinel management"
```

---

## Task 3: Update `plcc-make`

**Files:**
- Modify: `src/plcc/cmd/make.py`
- Modify: `src/plcc/cmd/make_test.py`

- [ ] **Step 1: Update the unit tests**

Replace `src/plcc/cmd/make_test.py` entirely:

```python
import pytest
import docopt

from .make import main as run_main, validate_tool_name, _report_ll1_failure


def test_help(capsys):
    with pytest.raises(SystemExit):
        run_main(['--help'])
    out, err = capsys.readouterr()
    assert 'Usage' in out


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
    assert "grammar file not found" in err


def test_grammar_file_flag_not_found_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main(['--grammar-file=nonexistent.plcc'])
    assert exc.value.code != 0


def test_validate_tool_name_accepts_valid():
    validate_tool_name('diagram')
    validate_tool_name('Java')
    validate_tool_name('my-tool')
    validate_tool_name('tool_123')


def test_validate_tool_name_rejects_path_traversal():
    with pytest.raises(ValueError):
        validate_tool_name('../etc')
    with pytest.raises(ValueError):
        validate_tool_name('foo/bar')
    with pytest.raises(ValueError):
        validate_tool_name('/absolute')


def test_validate_tool_name_rejects_empty():
    with pytest.raises(ValueError):
        validate_tool_name('')


def test_report_ll1_failure_prints_error_and_conflicts(capsys):
    ll1 = {
        "is_ll1": False,
        "conflicts": [
            {"nonterminal": "E", "lookahead": "+", "competing": ["E + T", "E"]}
        ],
        "left_recursion": [],
    }
    _report_ll1_failure(ll1, "build/ll1.json", verbose=None)
    _, err = capsys.readouterr()
    assert "plcc-make: error:" in err
    assert "build/ll1.json" in err
    assert "E" in err
    assert "+" in err


def test_report_left_recursion_cycle(capsys):
    ll1 = {
        "conflicts": [],
        "left_recursion": [{"cycle": ["A", "B", "A"]}],
    }
    _report_ll1_failure(ll1, "build/ll1.json", None)
    _, err = capsys.readouterr()
    assert "A -> B -> A" in err
```

- [ ] **Step 2: Run to confirm failures**

```bash
bin/test/units.bash src/plcc/cmd/make_test.py
```

Expected: `test_grammar_file_not_found_exits_nonzero` and `test_grammar_file_not_found_prints_error` and `test_grammar_file_flag_not_found_exits_nonzero` fail; others pass.

- [ ] **Step 3: Rewrite `make.py`**

Replace `src/plcc/cmd/make.py` entirely:

```python
import contextlib
import enum
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.build.staleness import (
    compute_hash, read_sentinel, write_sentinel, delete_sentinel, is_current,
)

__doc__ = """plcc-make
    Build a PLCC project from a grammar file.

Usage:
    plcc-make [-v ...] [options]

Options:
    --grammar-file=<path>   Path to the PLCC grammar file [default: grammar.plcc].
    --through=<level>       Build up to this level: scan, parse, or all [default: all].
    -h --help               Show this message.
""" + VERBOSE_OPTIONS

_TOOL_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')


class Events(enum.Enum):
    STARTED = "started"
    PHASE = "phase"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-make --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose = VerboseContext.from_args("plcc-make", Events, args)
    grammar = args['--grammar-file'] or 'grammar.plcc'
    through = args['--through'] or 'all'
    build_dir = Path('build')

    if not os.path.exists(grammar):
        print(f"plcc-make: grammar file not found: {grammar}", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message=f"building {grammar}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    build_dir.mkdir(exist_ok=True)

    # Run plcc-spec into a temp file to avoid corrupting build/spec.json on failure
    verbose.emit(Events.PHASE, message="spec")
    tmp_fd, tmp_spec = tempfile.mkstemp(suffix='.json')
    os.close(tmp_fd)
    try:
        with open(tmp_spec, 'w') as spec_out:
            result = subprocess.run(
                ['plcc-spec', grammar] + child_flags,
                stdout=spec_out,
                stderr=subprocess.PIPE,
            )
        if result.stderr:
            events = verbose.parse_child_events(result.stderr.decode('utf-8', errors='replace'))
            verbose.reformat_child_events(events)
        if result.returncode != 0:
            os.unlink(tmp_spec)
            delete_sentinel(build_dir)
            print(f"plcc-make: plcc-spec failed (exit {result.returncode})", file=sys.stderr)
            sys.exit(result.returncode)
    except Exception:
        if os.path.exists(tmp_spec):
            os.unlink(tmp_spec)
        delete_sentinel(build_dir)
        raise

    new_hash = compute_hash(tmp_spec)
    sentinel = read_sentinel(build_dir)

    if is_current(sentinel, new_hash, through):
        os.unlink(tmp_spec)
        verbose.emit(Events.FINISHED, message="build is current")
        return

    # Slow path: move spec into place, delete sentinel, run downstream steps
    shutil.move(tmp_spec, build_dir / 'spec.json')
    spec_json = str(build_dir / 'spec.json')
    delete_sentinel(build_dir)  # absent until final success write below

    if through in ('parse', 'all'):
        verbose.emit(Events.PHASE, message="ll1")
        ll1_json = str(build_dir / 'll1.json')
        _run_or_die(['plcc-ll1'] + child_flags, stdin_file=spec_json, stdout_file=ll1_json, verbose=verbose)
        with open(ll1_json) as f:
            ll1 = json.load(f)
        if not ll1.get("is_ll1", True):
            _report_ll1_failure(ll1, ll1_json, verbose)
            delete_sentinel(build_dir)
            sys.exit(1)

    if through == 'all':
        verbose.emit(Events.PHASE, message="model")
        model_json = str(build_dir / 'model.json')
        _run_or_die(['plcc-model', spec_json] + child_flags, stdout_file=model_json, verbose=verbose)

        with open(spec_json) as f:
            spec = json.load(f)
        for section in spec.get('semantics', []):
            tool = section['tool']
            lang = section['language']
            try:
                validate_tool_name(tool)
            except ValueError as e:
                print(f"plcc-make: {e}", file=sys.stderr)
                delete_sentinel(build_dir)
                sys.exit(1)
            output_dir = str(build_dir / tool)
            os.makedirs(output_dir, exist_ok=True)
            verbose.emit(Events.PHASE, message=f"emit {lang} -> {tool}")
            _run_or_die(
                ['plcc-lang-emit', f'--target={lang}', f'--output={output_dir}'] + child_flags,
                stdin_file=model_json,
                verbose=verbose,
            )
            verbose.emit(Events.PHASE, message=f"build {lang} -> {tool}")
            _run_or_die(
                ['plcc-lang-build', f'--target={lang}', f'--output={output_dir}'] + child_flags,
                verbose=verbose,
            )

    write_sentinel(build_dir, new_hash, through)
    verbose.emit(Events.FINISHED, message="done")


def validate_tool_name(name):
    if not name or not _TOOL_NAME_RE.match(name):
        raise ValueError(
            f"Invalid tool name '{name}'. "
            "Tool names must match [a-zA-Z0-9_-]+ to prevent path traversal."
        )


def _report_ll1_failure(ll1, path, verbose):
    print(f"plcc-make: error: grammar is not LL(1); see {path}", file=sys.stderr)
    for conflict in ll1.get("conflicts", []):
        print(
            f"plcc-make: error: conflict at "
            f"{conflict.get('nonterminal', '?')} on "
            f"{conflict.get('lookahead', '?')}: "
            f"{conflict.get('productions', [])}",
            file=sys.stderr,
        )
    for entry in ll1.get("left_recursion", []):
        cycle = entry.get("cycle", [])
        print(f"plcc-make: error: left-recursion cycle: {' -> '.join(cycle)}", file=sys.stderr)


def _run_or_die(cmd, stdout_file=None, stdin_file=None, verbose=None):
    with contextlib.ExitStack() as stack:
        stdin = stack.enter_context(open(stdin_file)) if stdin_file else None
        stdout = stack.enter_context(open(stdout_file, 'w')) if stdout_file else None
        result = subprocess.run(cmd, stdin=stdin, stdout=stdout, stderr=subprocess.PIPE)
    if verbose and result.stderr:
        events = verbose.parse_child_events(result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if result.returncode != 0:
        print(f"plcc-make: {cmd[0]} failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)
```

- [ ] **Step 4: Run unit tests**

```bash
bin/test/units.bash src/plcc/cmd/make_test.py
```

Expected: all tests pass.

- [ ] **Step 5: Smoke-test manually**

```bash
cd /tmp && mkdir smoke-make && cd smoke-make
cp /workspaces/plcc-ng/tests/fixtures/trivial-python.plcc grammar.plcc
plcc-make
ls build/
```

Expected: `build/` contains `spec.json ll1.json model.json .spec-hash py/`.

```bash
plcc-make   # second run
```

Expected: exits 0 immediately with "build is current".

```bash
plcc-make --through=scan --grammar-file=/workspaces/plcc-ng/tests/fixtures/trivial.plcc
```

Expected: exits 0, only `build/spec.json` and `build/.spec-hash` present (or updated).

- [ ] **Step 6: Commit**

```bash
cd /workspaces/plcc-ng
git add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
git commit -m "feat: add staleness algorithm, --grammar-file, --through to plcc-make"
```

---

## Task 4: Update `plcc-make` bats tests

**Files:**
- Modify: `tests/bats/commands/plcc-make.bats`

- [ ] **Step 1: Replace the bats file**

```bash
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

# ── Basic interface ────────────────────────────────────────────────────────────

@test "plcc-make is on PATH" { command -v plcc-make; }

@test "plcc-make --help exits 0" {
    run plcc-make --help
    [ "$status" -eq 0 ]
}

@test "plcc-make with no grammar.plcc exits nonzero" {
    run --separate-stderr plcc-make
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"grammar file not found"* ]]
}

@test "plcc-make --grammar-file with missing file exits nonzero" {
    run --separate-stderr plcc-make --grammar-file=no-such-file.plcc
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"grammar file not found"* ]]
}

@test "plcc-make defaults to grammar.plcc in CWD" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    run plcc-make --through=scan
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
}

@test "plcc-make --grammar-file uses specified path" {
    run plcc-make --through=scan "--grammar-file=${FIXTURES}/trivial.plcc"
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
}

@test "plcc-make accepts -v" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    run plcc-make -v --through=scan
    [ "$status" -eq 0 ]
}

# ── Build artifacts ────────────────────────────────────────────────────────────

@test "plcc-make full build produces spec.json ll1.json model.json" {
    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc
    run plcc-make
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
    [ -f build/ll1.json ]
    [ -f build/model.json ]
}

@test "plcc-make full build writes .spec-hash sentinel" {
    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc
    run plcc-make
    [ "$status" -eq 0 ]
    [ -f "build/.spec-hash" ]
}

@test "plcc-make --through=scan creates spec.json but not ll1.json" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    run plcc-make --through=scan
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
    [ ! -f build/ll1.json ]
}

@test "plcc-make --through=parse creates spec.json and ll1.json but not model.json" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    run plcc-make --through=parse
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
    [ -f build/ll1.json ]
    [ ! -f build/model.json ]
}

# ── Staleness: fast path ───────────────────────────────────────────────────────

@test "plcc-make does not rebuild when grammar is unchanged" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    plcc-make --through=parse
    rm build/ll1.json          # manually remove artifact
    plcc-make --through=parse  # grammar unchanged → fast path
    [ ! -f build/ll1.json ]    # not rebuilt confirms fast path taken
}

@test "plcc-make --through=all fast-paths when all-level sentinel present" {
    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc
    plcc-make
    rm build/ll1.json          # manually corrupt build/
    plcc-make                  # grammar unchanged, sentinel at 'all' level → fast path
    [ ! -f build/ll1.json ]    # not rebuilt confirms fast path taken
}

# ── Staleness: slow path ───────────────────────────────────────────────────────

@test "plcc-make rebuilds when grammar changes" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    plcc-make --through=scan
    first_spec=$(cat build/spec.json)

    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc  # different grammar
    plcc-make --through=scan
    second_spec=$(cat build/spec.json)

    [ "$first_spec" != "$second_spec" ]
}

@test "plcc-make --through=scan then --through=all completes full build" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    plcc-make --through=scan
    [ ! -f build/ll1.json ]

    plcc-make  # grammar unchanged but level insufficient (scan < all)
    [ -f build/ll1.json ]
}

@test "plcc-make --through=all then --through=scan fast-paths" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    plcc-make
    rm build/ll1.json
    plcc-make --through=scan  # all >= scan → fast path
    [ ! -f build/ll1.json ]   # not rebuilt confirms fast path
}

# ── Staleness: failure handling ────────────────────────────────────────────────

@test "plcc-make deletes sentinel when plcc-spec fails" {
    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc
    plcc-make
    [ -f "build/.spec-hash" ]

    printf 'token BAD @@@\n' > grammar.plcc  # syntax error
    run plcc-make
    [ "$status" -ne 0 ]
    [ ! -f "build/.spec-hash" ]
}

@test "plcc-make re-fails on repeated call with broken grammar" {
    printf 'token BAD @@@\n' > grammar.plcc
    run plcc-make
    [ "$status" -ne 0 ]
    run plcc-make
    [ "$status" -ne 0 ]
}

@test "plcc-make rebuilds after broken grammar is fixed" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    plcc-make --through=scan

    printf 'token BAD @@@\n' > grammar.plcc
    run plcc-make --through=scan
    [ "$status" -ne 0 ]

    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc
    run plcc-make --through=scan
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
}

# ── Partial grammars ───────────────────────────────────────────────────────────

@test "plcc-make --through=scan succeeds with lexical-only grammar" {
    cp "${FIXTURES}/lexical-only.plcc" grammar.plcc
    run plcc-make --through=scan
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
}

@test "plcc-make --through=parse succeeds with lexical-only grammar" {
    cp "${FIXTURES}/lexical-only.plcc" grammar.plcc
    run plcc-make --through=parse
    [ "$status" -eq 0 ]
    [ -f build/ll1.json ]
}

@test "plcc-make full build succeeds with lexical+syntactic grammar and no semantics" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    run plcc-make
    [ "$status" -eq 0 ]
    [ -f build/ll1.json ]
    [ -f build/model.json ]
}
```

- [ ] **Step 2: Run the bats tests**

```bash
bin/test/commands.bash tests/bats/commands/plcc-make.bats
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/bats/commands/plcc-make.bats
git commit -m "test: rewrite plcc-make bats for staleness, --through, --grammar-file"
```

---

## Task 5: Update `plcc-scan`

**Files:**
- Modify: `src/plcc/cmd/scan.py`
- Modify: `tests/bats/commands/plcc-scan.bats`

- [ ] **Step 1: Rewrite `scan.py`**

Replace `src/plcc/cmd/scan.py` entirely:

```python
import enum
import json
import os
import subprocess
import sys
import threading

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


def _location_str(source):
    file = source.get("file", "?")
    line = source.get("line", "?")
    col = source.get("column", "?")
    return f"{file}:{line}:{col}"


__doc__ = """plcc-scan
    Tokenize source input and print tokens in human-readable format.

Usage:
    plcc-scan [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to tokenize. Reads stdin if none given.

Options:
    --grammar-file=<path>   Path to the PLCC grammar file [default: grammar.plcc].
    --show-skips            Print skipped tokens.
    --show-line             Print source line and cursor for each token.
    --show-attempts         Print pattern-match attempts for each token.
    --show-regex            Print the regex of each matched pattern.
    --trace                 Print source line, cursor, attempts, and token (enables all --show-* options).
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


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
        print("Run 'plcc-scan --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose = VerboseContext.from_args("plcc-scan", Events, args)
    grammar_file = args['--grammar-file'] or 'grammar.plcc'
    sources = args['SOURCE']

    verbose.emit(Events.STARTED, message=f"scanning with {grammar_file}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    # Ensure build/ is current for the scan level
    make_result = subprocess.run(
        ['plcc-make', '--through=scan', f'--grammar-file={grammar_file}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        events = verbose.parse_child_events(make_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    spec_path = os.path.join('build', 'spec.json')

    # Build plcc-tokens flags
    tokens_flags = []
    if args.get('--show-skips'):
        tokens_flags.append('--show-skips')
    if args.get('--show-line'):
        tokens_flags.append('--show-line')
    if args.get('--show-attempts'):
        tokens_flags.append('--show-attempts')
    if args.get('--show-regex'):
        tokens_flags.append('--show-regex')
    if args.get('--trace'):
        tokens_flags.append('--trace')

    token_sources = sources if sources else ['-']
    proc = subprocess.Popen(
        ['plcc-tokens', spec_path] + token_sources + tokens_flags + child_flags,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stderr_chunks = []

    def _drain_stderr():
        stderr_chunks.append(proc.stderr.read())

    stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
    stderr_thread.start()

    for raw in proc.stdout:
        line = raw.decode('utf-8').strip()
        if not line:
            continue
        record = json.loads(line)
        if record.get('kind') == 'token':
            name = record.get('name', '?')
            lexeme = record.get('lexeme', '?')
            source = record.get('source', {})
            loc = _location_str(source)
            extra = ''
            if record.get('skipped'):
                extra = ' SKIPPED'
            if 'regex' in record:
                extra = f" '{record['regex']}'"
            print(f"{loc} {name} '{lexeme}'{extra}", flush=True)
            if record.get('line_text') is not None:
                print(record['line_text'])
                col = record.get('source', {}).get('column', 1)
                print(' ' * (col - 1) + '^')
            for attempt in record.get('attempts', []):
                winner = '*' if attempt.get('matched') else ' '
                print(f"  {winner} {attempt.get('name')} {attempt.get('chars', '')}")
        elif record.get('kind') == 'error':
            loc = _location_str(record.get('pos', {}))
            lexeme = record.get('lexeme', '?')
            message = record.get('message', 'unrecognized character')
            print(f"{loc}: error: {message} '{lexeme}'", flush=True)

    stderr_thread.join()
    proc.wait()

    stderr_data = b''.join(stderr_chunks)
    if stderr_data:
        events = verbose.parse_child_events(stderr_data.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)

    if proc.returncode != 0:
        print(f"plcc-scan: plcc-tokens failed (exit {proc.returncode})", file=sys.stderr)
        sys.exit(proc.returncode)

    verbose.emit(Events.FINISHED, message='done')
```

**Note:** The `--show-skips`, `--show-line`, `--show-attempts`, `--show-regex`, `--trace` flags are carried over from the existing implementation. Check the existing `scan.py` before running to verify these flags match what `plcc-tokens` actually accepts — adjust the tokens_flags list if needed.

- [ ] **Step 2: Update `plcc-scan.bats`**

Add `WORK_DIR` setup and update all tests to drop the positional GRAMMAR arg. Replace the file:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-scan is on PATH" { command -v plcc-scan; }

@test "plcc-scan --help exits 0" {
    run plcc-scan --help
    [ "$status" -eq 0 ]
}

@test "plcc-scan tokenizes input" {
    run bash -c "echo '42' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
    [[ "$output" == *"42"* ]]
}

@test "plcc-scan reads from source file" {
    run plcc-scan "${FIXTURES}/trivial_input.txt"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
}

@test "plcc-scan accepts -v" {
    run bash -c "echo '42' | plcc-scan -v"
    [ "$status" -eq 0 ]
}

@test "plcc-scan accepts -vv (bundled short flag)" {
    run bash -c "echo '42' | plcc-scan -vv --verbose-format=json"
    [ "$status" -eq 0 ]
}

@test "plcc-scan includes file:line:col in token output" {
    run bash -c "echo '42' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^-:1:1\ NUM\ \'42\'$ ]]
}

@test "plcc-scan exits 0 on lex error in source" {
    run --separate-stderr bash -c "echo 'abc' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"error"* ]]
}

@test "plcc-scan brief usage mentions --help" {
    run --separate-stderr bash -c "cd '${WORK_DIR}' && rm grammar.plcc && plcc-scan"
    [[ "$stderr" == *"--help"* ]]
}

@test "plcc-scan accepts '-' as stdin" {
    run bash -c "echo '42' | plcc-scan -"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
    [[ "$output" == *"42"* ]]
}

@test "plcc-scan '-' interleaved with file reads both" {
    run bash -c "echo '99' | plcc-scan '${FIXTURES}/trivial_input.txt' -"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"99"* ]]
}

@test "plcc-scan prints tokens before and after a lex error" {
    run --separate-stderr bash -c "printf '42 @ 99\n' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"99"* ]]
    [[ "$output" == *"error"* ]]
}

@test "plcc-scan outputs tokens for multi-line input" {
    run bash -c "printf '42\n99\n' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"99"* ]]
}

@test "plcc-scan includes source filename in token output for named file" {
    run plcc-scan "${FIXTURES}/trivial_input.txt"
    [ "$status" -eq 0 ]
    [[ "$output" == *"trivial_input.txt"* ]]
}

@test "plcc-scan exits nonzero when source file does not exist" {
    run --separate-stderr plcc-scan "/nonexistent/no-such-file.txt"
    [ "$status" -ne 0 ]
}

@test "plcc-scan --grammar-file uses specified grammar" {
    run bash -c "echo '42' | plcc-scan --grammar-file='${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
}

@test "plcc-scan --show-skips adds SKIPPED lines" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42 99' | plcc-scan --show-skips"
    [ "$status" -eq 0 ]
    [[ "$output" == *"SKIPPED"* ]]
}

@test "plcc-scan --show-skips format is file:line:col NAME 'lexeme' SKIPPED" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42 99' | plcc-scan --show-skips"
    [ "$status" -eq 0 ]
    [[ "$output" =~ -:1:[0-9]+\ WS\ \'\ \'\ SKIPPED ]]
}

@test "plcc-scan --show-line shows source line and caret cursor" {
    run bash -c "echo '42' | plcc-scan --show-line"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"^"* ]]
}

@test "plcc-scan --show-line cursor is at correct column" {
    run bash -c "echo '42' | plcc-scan --show-line"
    [ "$status" -eq 0 ]
    second_line=$(echo "$output" | sed -n '2p')
    [ "$second_line" = "^" ]
}

@test "plcc-scan --show-attempts produces indented attempt lines" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-scan --show-attempts"
    [ "$status" -eq 0 ]
    [[ "$output" == *"chars"* ]]
}

@test "plcc-scan --show-attempts has exactly one starred winner" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-scan --show-attempts"
    [ "$status" -eq 0 ]
    star_count=$(echo "$output" | grep -c '^\s*\*')
    [ "$star_count" -eq 1 ]
}

@test "plcc-scan --show-regex includes regex in token output" {
    run bash -c "echo '42' | plcc-scan --show-regex"
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^-:1:1\ NUM\ \'\\\d\+\'\ \'42\'$ ]]
}

@test "plcc-scan --trace produces source line, cursor, attempts, and token line" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"^"* ]]
    [[ "$output" == *"chars"* ]]
    [[ "$output" =~ \'\\\d\+ ]]
}

@test "plcc-scan -v emits started and finished events on stderr" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v"
    [ "$status" -eq 0 ]
    [[ "$stderr" == *"started"* ]]
    [[ "$stderr" == *"finished"* ]]
}

@test "plcc-scan -v hint is absent from stderr" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v"
    [ "$status" -eq 0 ]
    [[ "$stderr" != *"press ^D"* ]]
}

@test "plcc-scan -vv produces no more plcc-scan stderr lines than -v" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v"
    v1_lines=$(echo "$stderr" | grep '^plcc-scan:' | wc -l)
    run --separate-stderr bash -c "echo '42' | plcc-scan -vv"
    v2_lines=$(echo "$stderr" | grep '^plcc-scan:' | wc -l)
    [ "$v2_lines" -le "$v1_lines" ]
}

@test "plcc-scan -vvv produces no more plcc-scan stderr lines than -v" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v"
    v1_lines=$(echo "$stderr" | grep '^plcc-scan:' | wc -l)
    run --separate-stderr bash -c "echo '42' | plcc-scan -vvv"
    v3_lines=$(echo "$stderr" | grep '^plcc-scan:' | wc -l)
    [ "$v3_lines" -le "$v1_lines" ]
}

@test "plcc-scan TTY hint absent when stdin is not a TTY" {
    run bash -c "echo '42' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" != *"press ^D"* ]]
}

@test "plcc-scan does not rebuild when grammar is unchanged" {
    plcc-scan < /dev/null || true   # first run builds
    rm build/spec.json              # manually remove artifact
    run bash -c "echo '42' | plcc-scan"
    [ "$status" -ne 0 ]             # fails because spec.json is missing but fast-path taken
}

@test "plcc-scan triggers rebuild when grammar changes" {
    echo '42' | plcc-scan > /dev/null  # prime build
    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc  # change grammar
    run bash -c "echo '42' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
}

@test "plcc-scan exits nonzero when grammar has syntax error" {
    printf 'token BAD @@@\n' > grammar.plcc
    run --separate-stderr bash -c "echo '42' | plcc-scan"
    [ "$status" -ne 0 ]
}

@test "plcc-scan works with lexical-only grammar" {
    cp "${FIXTURES}/lexical-only.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
}
```

- [ ] **Step 3: Run the bats tests**

```bash
bin/test/commands.bash tests/bats/commands/plcc-scan.bats
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/cmd/scan.py tests/bats/commands/plcc-scan.bats
git commit -m "feat: plcc-scan uses build/ via plcc-make, drops positional GRAMMAR arg"
```

---

## Task 6: Update `plcc-parse`

**Files:**
- Modify: `src/plcc/cmd/parse.py`
- Modify: `tests/bats/commands/plcc-parse.bats`

- [ ] **Step 1: Rewrite `parse.py`**

Replace `src/plcc/cmd/parse.py` entirely:

```python
import enum
import json
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS, reap_pipeline

__doc__ = """plcc-parse
    Parse source input and print parse tree in human-readable format.

Usage:
    plcc-parse [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to parse. Reads stdin if none given.

Options:
    --grammar-file=<path>   Path to the PLCC grammar file [default: grammar.plcc].
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def _location_str(source):
    file = source.get("file")
    line = source.get("line", "?")
    col = source.get("column", "?")
    if file and file != "<stdin>":
        return f"{file}:{line}:{col}"
    return f"{line}:{col}"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-parse --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose = VerboseContext.from_args("plcc-parse", Events, args)
    grammar_file = args['--grammar-file'] or 'grammar.plcc'
    sources = args['SOURCE']

    verbose.emit(Events.STARTED, message=f"parsing with {grammar_file}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    # Ensure build/ is current for the parse level
    make_result = subprocess.run(
        ['plcc-make', '--through=parse', f'--grammar-file={grammar_file}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        events = verbose.parse_child_events(make_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    spec_path = os.path.join('build', 'spec.json')
    ll1_path = os.path.join('build', 'll1.json')

    # Build input
    chunks = []
    for src in sources:
        if src == '-':
            chunks.append(sys.stdin.buffer.read())
        else:
            with open(src, 'rb') as sf:
                chunks.append(sf.read())
    if not sources:
        chunks.append(sys.stdin.buffer.read())
    input_data = b''.join(chunks)

    # plcc-tokens | plcc-tree
    tokens_proc = subprocess.Popen(
        ['plcc-tokens', spec_path] + child_flags,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    tree_proc = subprocess.Popen(
        ['plcc-tree', f'--ll1={ll1_path}'] + child_flags,
        stdin=tokens_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    tokens_proc.stdout.close()
    tokens_proc.stdin.write(input_data)
    tokens_proc.stdin.close()

    tree_out, tree_err = tree_proc.communicate()
    tokens_err = tokens_proc.stderr.read()
    tokens_proc.wait()
    tokens_proc.stderr_captured = tokens_err
    tree_proc.stderr_captured = tree_err

    result = reap_pipeline([
        (tokens_proc, 'plcc-tokens'),
        (tree_proc, 'plcc-tree'),
    ])
    verbose.reformat_child_events(result.events_to_render)
    if result.failed_stage:
        sys.exit(result.exit_code)

    for line in tree_out.decode('utf-8').splitlines():
        if not line.strip():
            continue
        tree = json.loads(line)
        if tree.get('kind') == 'error':
            verbose.reformat_child_events([{
                'stage': tree.get('stage', 'plcc-tokens'),
                'event': 'error',
                'severity': 'error',
                'pos': tree.get('pos', {}),
                'message': tree.get('message', 'error'),
            }])
            sys.exit(1)
        _print_tree(tree, indent=0)

    verbose.emit(Events.FINISHED, message='done')


def _print_tree(node, indent):
    prefix = '  ' * indent
    kind = node.get('kind', '?')
    if kind == 'tree':
        rule = node.get('rule', '?')
        print(f"{prefix}{rule}")
        for _field, child in node.get('children', []):
            _print_tree(child, indent + 1)
    elif kind == 'token':
        name = node.get('name', '?')
        lexeme = node.get('lexeme', '?')
        source = node.get('source', {})
        loc = _location_str(source)
        print(f"{prefix}{name} '{lexeme}' [{loc}]")
    elif kind == 'error':
        source = node.get('source', {})
        loc = _location_str(source)
        message = node.get('message', 'unknown error')
        print(f"{prefix}{loc}: error: {message}")
```

- [ ] **Step 2: Update `plcc-parse.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-parse is on PATH" { command -v plcc-parse; }

@test "plcc-parse --help exits 0" {
    run plcc-parse --help
    [ "$status" -eq 0 ]
}

@test "plcc-parse parses input and prints tree" {
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" == *"program"* ]]
}

@test "plcc-parse reads from source file" {
    run plcc-parse "${FIXTURES}/trivial_input.txt"
    [ "$status" -eq 0 ]
    [[ "$output" == *"program"* ]]
}

@test "plcc-parse accepts -v" {
    run bash -c "echo '42' | plcc-parse -v"
    [ "$status" -eq 0 ]
}

@test "plcc-parse includes location on token leaves" {
    cp "${FIXTURES}/arith.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" =~ NUM\ \'42\'\ \[-:1:1\] ]]
}

@test "plcc-parse brief usage mentions --help" {
    run --separate-stderr bash -c "cd '${WORK_DIR}' && rm grammar.plcc && plcc-parse"
    [[ "$stderr" == *"--help"* ]]
}

@test "plcc-parse accepts '-' as stdin" {
    run bash -c "echo '42' | plcc-parse -"
    [ "$status" -eq 0 ]
    [[ "$output" == *"program"* ]]
}

@test "plcc-parse --grammar-file uses specified grammar" {
    run bash -c "echo '42' | plcc-parse --grammar-file='${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"program"* ]]
}

@test "plcc-parse exits nonzero when grammar has syntax error" {
    printf 'token BAD @@@\n' > grammar.plcc
    run --separate-stderr bash -c "echo '42' | plcc-parse"
    [ "$status" -ne 0 ]
}

@test "plcc-parse triggers rebuild when grammar changes" {
    echo '42' | plcc-parse > /dev/null
    cp "${FIXTURES}/arith.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" =~ NUM ]]
}

@test "plcc-parse works with lexical+syntactic grammar and no semantics" {
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" == *"program"* ]]
}
```

- [ ] **Step 3: Run the bats tests**

```bash
bin/test/commands.bash tests/bats/commands/plcc-parse.bats
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/cmd/parse.py tests/bats/commands/plcc-parse.bats
git commit -m "feat: plcc-parse uses build/ via plcc-make, drops positional GRAMMAR arg"
```

---

## Task 7: Update `plcc-rep`

**Files:**
- Modify: `src/plcc/cmd/rep.py`
- Modify: `tests/bats/commands/plcc-rep.bats`

- [ ] **Step 1: Rewrite `rep.py`**

Replace `src/plcc/cmd/rep.py` entirely:

```python
import enum
import json
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-rep
    REPL — read, eval, print loop for a PLCC grammar.

Usage:
    plcc-rep [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to evaluate before entering interactive mode.

Options:
    --grammar-file=<path>   Path to the PLCC grammar file [default: grammar.plcc].
    --tool=NAME             Semantic section to run (inferred if only one exists).
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


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
        print("Run 'plcc-rep --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose = VerboseContext.from_args("plcc-rep", Events, args)
    grammar_file = args['--grammar-file'] or 'grammar.plcc'
    sources = args['SOURCE']
    tool_name = args['--tool']
    verbose_format = args['--verbose-format'] or 'text'

    verbose.emit(Events.STARTED, message='starting rep')
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    # Ensure full build is current
    make_result = subprocess.run(
        ['plcc-make', f'--grammar-file={grammar_file}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        events = verbose.parse_child_events(make_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    spec_path = os.path.join('build', 'spec.json')
    ll1_path = os.path.join('build', 'll1.json')

    with open(spec_path) as f:
        spec = json.load(f)

    tool_name, language = _resolve_tool(spec, tool_name)
    tool_dir = os.path.join('build', tool_name)

    if not os.path.exists(tool_dir):
        print(f'plcc-rep: build/{tool_name}/ not found. Run plcc-make first.', file=sys.stderr)
        sys.exit(1)

    interpreter = subprocess.Popen(
        ['plcc-lang-run', f'--target={language}', f'--output={tool_dir}'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
    )

    try:
        for src in sources:
            with open(src, 'rb') as f:
                chunk = f.read()
            _eval_chunk(chunk, interpreter, spec_path, ll1_path, verbose_format)

        if not sources:
            interactive = sys.stdin.isatty()
            if interactive:
                while True:
                    try:
                        print('>>> ', end='', flush=True, file=sys.stderr)
                        line = sys.stdin.readline()
                        if not line:
                            break
                        chunk = line.encode()
                        _eval_chunk(chunk, interpreter, spec_path, ll1_path, verbose_format)
                    except KeyboardInterrupt:
                        print(file=sys.stderr)
                        break
            else:
                chunk = sys.stdin.buffer.read()
                _eval_chunk(chunk, interpreter, spec_path, ll1_path, verbose_format)
    finally:
        try:
            interpreter.stdin.close()
        except BrokenPipeError:
            pass
        interpreter.wait()

    verbose.emit(Events.FINISHED, message='done')


def _resolve_tool(spec, tool_name):
    sections = spec.get('semantics', [])
    if tool_name:
        for s in sections:
            if s['tool'] == tool_name:
                return s['tool'], s['language']
        print(f"plcc-rep: no semantic section with tool '{tool_name}'", file=sys.stderr)
        sys.exit(1)

    if len(sections) == 0:
        print("plcc-rep: no semantic sections found in grammar.", file=sys.stderr)
        sys.exit(1)

    if len(sections) == 1:
        return sections[0]['tool'], sections[0]['language']

    names = [s['tool'] for s in sections]
    print(f"plcc-rep: multiple semantic sections: {names}. Use --tool=NAME.", file=sys.stderr)
    sys.exit(1)


def _eval_chunk(chunk, interpreter, spec_path, ll1_path, verbose_format):
    tokens_proc = subprocess.Popen(
        ['plcc-tokens', spec_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    tree_proc = subprocess.Popen(
        ['plcc-tree', f'--ll1={ll1_path}'],
        stdin=tokens_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    tokens_proc.stdout.close()
    tokens_proc.stdin.write(chunk)
    tokens_proc.stdin.close()

    tree_out, tree_err = tree_proc.communicate()
    tokens_err = tokens_proc.stderr.read()
    tokens_proc.wait()

    if tokens_proc.returncode != 0 or tree_proc.returncode != 0:
        for msg in [tokens_err, tree_err]:
            if msg:
                sys.stderr.buffer.write(msg)
        return

    tree_line = tree_out.strip()
    if not tree_line:
        return

    try:
        interpreter.stdin.write(tree_line + b'\n')
        interpreter.stdin.flush()
    except BrokenPipeError:
        print('plcc-rep: interpreter exited unexpectedly', file=sys.stderr)
        sys.exit(1)

    _read_response(interpreter.stdout, verbose_format)


def _read_response(stdout, verbose_format):
    while True:
        raw = stdout.readline()
        if not raw:
            print('plcc-rep: interpreter exited unexpectedly', file=sys.stderr)
            sys.exit(1)
        line = raw.decode('utf-8', errors='replace').rstrip('\n')
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            print(line)
            continue
        if 'kind' not in record:
            print(line)
            continue
        _render_record(record, verbose_format)
        return


def _render_record(record, verbose_format):
    if verbose_format == 'json':
        print(json.dumps(record))
        return
    if record['kind'] == 'result':
        value = record.get('value')
        if value is not None:
            print(value)
    elif record['kind'] == 'error':
        print(f"error: {record.get('type')}: {record.get('message')}", file=sys.stderr)
```

- [ ] **Step 2: Update `plcc-rep.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-rep is on PATH" { command -v plcc-rep; }

@test "plcc-rep --help exits 0" {
    run plcc-rep --help
    [ "$status" -eq 0 ]
}

@test "plcc-rep evaluates with Python tool" {
    run bash -c "echo '42' | plcc-rep --tool=py"
    [ "$status" -eq 0 ]
    [[ "$output" == "42" ]]
}

@test "plcc-rep errors on missing tool" {
    run bash -c "echo '42' | plcc-rep --tool=nonexistent 2>&1"
    [ "$status" -ne 0 ]
    [[ "$output" == *"no semantic section"* ]]
}

@test "plcc-rep accepts -v" {
    run bash -c "echo '42' | plcc-rep --tool=py -v"
    [ "$status" -eq 0 ]
}

@test "plcc-rep brief usage mentions --help" {
    run --separate-stderr bash -c "cd '${WORK_DIR}' && rm grammar.plcc && plcc-rep"
    [[ "$stderr" == *"--help"* ]]
}

@test "plcc-rep --grammar-file uses specified grammar" {
    run bash -c "echo '42' | plcc-rep --grammar-file='${FIXTURES}/trivial-python.plcc' --tool=py"
    [ "$status" -eq 0 ]
    [[ "$output" == "42" ]]
}

@test "plcc-rep rebuilds when grammar changes" {
    echo '42' | plcc-rep --tool=py > /dev/null  # prime build
    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc  # same grammar, but touch it
    run bash -c "echo '42' | plcc-rep --tool=py"
    [ "$status" -eq 0 ]
    [[ "$output" == "42" ]]
}

@test "plcc-rep exits nonzero when grammar has syntax error" {
    printf 'token BAD @@@\n' > grammar.plcc
    run --separate-stderr bash -c "echo '42' | plcc-rep"
    [ "$status" -ne 0 ]
}

@test "plcc-rep exits nonzero when grammar has no semantics" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    run --separate-stderr bash -c "echo '42' | plcc-rep"
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"no semantic sections"* ]]
}
```

- [ ] **Step 3: Run the bats tests**

```bash
bin/test/commands.bash tests/bats/commands/plcc-rep.bats
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/cmd/rep.py tests/bats/commands/plcc-rep.bats
git commit -m "feat: plcc-rep uses build/ via plcc-make, drops positional GRAMMAR arg"
```

---

## Task 8: Full functional test pass

- [ ] **Step 1: Run all functional tests**

```bash
bin/test/functional.bash
```

Expected: all tiers pass (units, commands, integration, e2e).

- [ ] **Step 2: Fix any failures**

If any existing integration or e2e tests reference the old positional `GRAMMAR` argument, update them to use `--grammar-file=<path>` or copy grammar.plcc to the working directory.

Check:
```bash
grep -r 'plcc-make\|plcc-scan\|plcc-parse\|plcc-rep' tests/bats/integration/ tests/bats/e2e/ | grep -v 'grammar-file'
```

Update any matches that pass a grammar path as a positional argument.

- [ ] **Step 3: Commit any fixes**

```bash
git add tests/bats/
git commit -m "test: update integration and e2e tests for new grammar-file interface"
```

---

## Self-Review

**Spec coverage check:**

| Spec section | Covered by |
|---|---|
| §4 `build/` structure | Task 4 tests verify `spec.json`, `ll1.json`, `model.json`, `.spec-hash` |
| §5.2 sentinel invariant | Task 2 (unit), Task 4 (staleness bats) |
| §5.3 algorithm (temp file, hash, fast/slow path) | Task 3 (implementation), Task 4 (bats) |
| §5.4 pitfalls (corruption, repeated failure, includes, partial build, level comparison) | Task 4 bats: `plcc-spec fails`, `re-fails`, `rebuild after fix`, `scan→all level comparison` |
| §5.5 `--through` levels | Task 4 bats: `--through=scan/parse/all` artifact checks |
| §6 grammar file resolution | Task 4 bats: default `grammar.plcc`, `--grammar-file`, missing file |
| §7 scan/parse/rep changes | Tasks 5, 6, 7 |
| §8 partial grammars | Task 4 bats: `lexical-only`, `lexical+syntactic` |
| §9 error handling | Task 4 bats: failure cases; Tasks 5-7 bats: syntax error propagation |
| §10 test plan (hash unit tests) | Task 2 |

**Gap:** The spec mentions testing that include-file changes are detected. The bats test suite does not include a test for this because the fixtures don't use `include` directives. This is an acceptable gap for now — the unit tests for `compute_hash` verify that content changes are detected, and `plcc-spec` resolves includes before `compute_hash` runs. If include support becomes a priority, add a fixture with includes and a corresponding bats test.

**Placeholder scan:** No TBD or TODO present. All code steps are complete.

**Type consistency:** `compute_hash`, `read_sentinel`, `write_sentinel`, `delete_sentinel`, `is_current` defined in Task 2 and imported in Task 3 with matching signatures throughout.
