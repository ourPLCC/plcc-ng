# 035 — plcc-diagram Interface Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hanging `plcc-diagram --output=build` with a properly-levelled architecture: a Level 2 `plcc-diagram` command that orchestrates via `plcc-make`, Level 0 dispatchers (`plcc-diagram-emit`, `plcc-diagram-build`, `plcc-diagram-run`), and a default Mermaid plugin.

**Architecture:** `plcc-diagram` (Level 2) mirrors `plcc-scan`/`plcc-parse` — it calls `plcc-make --through=diagram` then opens the result. `plcc-make` gains a diagram step that calls `plcc-diagram-emit` (model JSON → Mermaid source) then `plcc-diagram-build` (source → PNG). The set-based staleness sentinel replaces the current linear `_LEVELS` dict to correctly handle parallel stages.

**Tech Stack:** Python 3.12, docopt-ng, mmdc (optional, `pip install plcc[diagram]`), pytest, bats.

---

## File Map

**Modified:**

- `src/plcc/build/staleness.py` — replace `_LEVELS`/linear comparison with set-based API
- `src/plcc/build/staleness_test.py` — rewrite for new API
- `src/plcc/cmd/make.py` — add `--diagram-format`, `--through=diagram`, updated staleness
- `src/plcc/cmd/make_test.py` — add tests for new flag and stage
- `src/plcc/diagram/dispatch.py` → renamed to `src/plcc/diagram/emit.py` — update command names and interface
- `src/plcc/diagram/dispatch_test.py` → renamed to `src/plcc/diagram/emit_test.py`
- `src/plcc/diagram/plantuml/emit.py` — update `__doc__` command name
- `src/plcc/diagram/list.py` — update pattern `plcc-*-diagram` → `plcc-*-diagram-emit`
- `src/plcc/diagram/list_test.py` — update for new pattern
- `tests/bats/commands/plcc-diagram.bats` — rewrite for Level 2 interface
- `tests/bats/commands/plcc-diagram-list.bats` — update for new pattern
- `pyproject.toml` — rename entry points, add new ones, add `[diagram]` optional extra

**Created:**

- `src/plcc/diagram/build.py` — `plcc-diagram-build` dispatcher
- `src/plcc/diagram/build_test.py`
- `src/plcc/diagram/run.py` — `plcc-diagram-run` dispatcher
- `src/plcc/diagram/run_test.py`
- `src/plcc/diagram/mermaid/__init__.py`
- `src/plcc/diagram/mermaid/emit.py` — `plcc-mermaid-diagram-emit`
- `src/plcc/diagram/mermaid/emit_test.py`
- `src/plcc/diagram/mermaid/build.py` — `plcc-mermaid-diagram-build`
- `src/plcc/diagram/mermaid/build_test.py`
- `src/plcc/diagram/mermaid/run.py` — `plcc-mermaid-diagram-run`
- `src/plcc/diagram/mermaid/run_test.py`
- `src/plcc/cmd/diagram.py` — `plcc-diagram` Level 2
- `src/plcc/cmd/diagram_test.py`
- `tests/bats/commands/plcc-diagram-build.bats`
- `tests/bats/commands/plcc-diagram-run.bats`

---

## Task 1: Rewrite `staleness.py` — set-based sentinel

**Files:**

- Modify: `src/plcc/build/staleness.py`
- Modify: `src/plcc/build/staleness_test.py`

- [ ] **Step 1: Replace staleness_test.py with tests for the new API**

```python
# src/plcc/build/staleness_test.py
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
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text("hello")
    b.write_text("hello")
    assert compute_hash(a) == compute_hash(b)


def test_compute_hash_different_content_different_hash(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text("hello")
    b.write_text("world")
    assert compute_hash(a) != compute_hash(b)


def test_read_sentinel_returns_none_when_absent(tmp_path):
    assert read_sentinel(tmp_path) is None


def test_read_sentinel_returns_none_on_malformed_json(tmp_path):
    (tmp_path / ".spec-hash").write_text("not json")
    assert read_sentinel(tmp_path) is None


def test_write_then_read_sentinel_roundtrips(tmp_path):
    write_sentinel(tmp_path, "abc123", {"scan", "parse"})
    s = read_sentinel(tmp_path)
    assert s == {"hash": "abc123", "stages": ["parse", "scan"]}  # sorted


def test_delete_sentinel_removes_file(tmp_path):
    write_sentinel(tmp_path, "abc123", {"scan"})
    delete_sentinel(tmp_path)
    assert read_sentinel(tmp_path) is None


def test_delete_sentinel_is_idempotent(tmp_path):
    delete_sentinel(tmp_path)


def test_is_current_false_when_sentinel_none():
    assert not is_current(None, "abc", {"scan"})


def test_is_current_false_when_hash_differs():
    s = {"hash": "old", "stages": ["scan", "parse"]}
    assert not is_current(s, "new", {"scan"})


def test_is_current_true_when_required_stages_are_subset_of_completed():
    s = {"hash": "abc", "stages": ["scan", "parse", "model", "diagram"]}
    assert is_current(s, "abc", {"scan"})
    assert is_current(s, "abc", {"scan", "parse"})
    assert is_current(s, "abc", {"scan", "model", "diagram"})
    assert is_current(s, "abc", {"scan", "parse", "model", "diagram"})


def test_is_current_false_when_required_stage_missing():
    s = {"hash": "abc", "stages": ["scan", "parse"]}
    assert not is_current(s, "abc", {"scan", "parse", "model"})
    assert not is_current(s, "abc", {"scan", "model", "diagram"})


def test_is_current_false_when_unknown_stage_required():
    s = {"hash": "abc", "stages": ["scan", "parse", "model", "diagram"]}
    assert not is_current(s, "abc", {"scan", "java"})


def test_all_stages_present_is_current():
    s = {"hash": "abc", "stages": ["scan", "parse", "model", "diagram", "java"]}
    assert is_current(s, "abc", {"scan", "parse", "model", "diagram", "java"})


def test_diagram_stored_is_not_current_for_all_with_tools():
    s = {"hash": "abc", "stages": ["scan", "model", "diagram"]}
    assert not is_current(s, "abc", {"scan", "parse", "model", "diagram", "java"})


def test_all_stored_is_current_for_diagram():
    s = {"hash": "abc", "stages": ["scan", "parse", "model", "diagram", "java"]}
    assert is_current(s, "abc", {"scan", "model", "diagram"})
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/build/staleness_test.py
```

Expected: multiple failures — `write_sentinel` and `is_current` signatures differ.

- [ ] **Step 3: Rewrite `staleness.py`**

```python
# src/plcc/build/staleness.py
import hashlib
import json
from pathlib import Path

_SENTINEL = ".spec-hash"


def compute_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_sentinel(build_dir):
    p = Path(build_dir) / _SENTINEL
    try:
        return json.loads(p.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def write_sentinel(build_dir, hash_, stages):
    (Path(build_dir) / _SENTINEL).write_text(
        json.dumps({"hash": hash_, "stages": sorted(stages)})
    )


def delete_sentinel(build_dir):
    try:
        (Path(build_dir) / _SENTINEL).unlink()
    except FileNotFoundError:
        pass


def is_current(sentinel, hash_, required_stages):
    if sentinel is None:
        return False
    if sentinel.get("hash") != hash_:
        return False
    completed = set(sentinel.get("stages", []))
    return required_stages.issubset(completed)
```

- [ ] **Step 4: Run tests and confirm they pass**

```bash
bin/test/units.bash src/plcc/build/staleness_test.py
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add src/plcc/build/staleness.py src/plcc/build/staleness_test.py
git -C "$(git rev-parse --show-toplevel)" commit -m "refactor(build): replace linear staleness levels with set-based sentinel"
```

---

## Task 2: Update `plcc-make` — `--diagram-format`, `--through=diagram`, new staleness

**Files:**

- Modify: `src/plcc/cmd/make.py`
- Modify: `src/plcc/cmd/make_test.py`

- [ ] **Step 1: Add failing tests for new `plcc-make` behaviour**

Add to `src/plcc/cmd/make_test.py`:

```python
def test_invalid_through_diagram_is_now_valid(tmp_path, monkeypatch):
    # 'diagram' must not be rejected as invalid
    monkeypatch.chdir(tmp_path)
    # grammar file missing → exits, but not with "invalid --through"
    with pytest.raises(SystemExit):
        run_main(['--through=diagram'])
    _, err = capsys.readouterr()  # NOTE: add capsys to function signature
    assert "invalid --through" not in err


def test_diagram_format_flag_accepted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main(['--diagram-format=mermaid'])
    # exits because grammar.plcc not found, not because of unknown flag
    assert exc.value.code != 0


def test_invalid_through_error_message_includes_diagram(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main(['--through=typo'])
    _, err = capsys.readouterr()
    assert "diagram" in err
```

- [ ] **Step 2: Run to confirm new tests fail**

```bash
bin/test/units.bash src/plcc/cmd/make_test.py
```

Expected: the three new tests fail.

- [ ] **Step 3: Update `make.py`**

Replace the `__doc__` string, validation block, staleness block, and add the diagram step. The full updated `main()` function:

```python
__doc__ = """plcc-make
    Build a PLCC project from a grammar file.

Usage:
    plcc-make [-v ...] [options]

Options:
    --grammar-file=<path>   Path to the PLCC grammar file [default: grammar.plcc].
    --through=<level>       Build up to this level: scan, parse, diagram, or all [default: all].
    --diagram-format=FMT    Diagram format for --through=diagram or --through=all [default: mermaid].
    -h --help               Show this message.
""" + VERBOSE_OPTIONS
```

Replace the `through` validation:

```python
if through not in ('scan', 'parse', 'diagram', 'all'):
    print(
        f"plcc-make: invalid --through value '{through}'; "
        "must be scan, parse, diagram, or all",
        file=sys.stderr,
    )
    sys.exit(1)
```

Add `diagram_fmt = args['--diagram-format'] or 'mermaid'` after the `through` line.

Replace the staleness block (after `compute_hash` and `read_sentinel` calls, before the early return):

```python
# Read spec for tool names needed to compute required stages
with open(tmp_spec) as f:
    spec_data = json.load(f)
tool_stages = {s['tool'] for s in spec_data.get('semantics', [])}

_REQUIRED = {
    'scan':    {'scan'},
    'parse':   {'scan', 'parse'},
    'diagram': {'scan', 'model', 'diagram'},
    'all':     {'scan', 'parse', 'model', 'diagram'} | tool_stages,
}
required_stages = _REQUIRED[through]

if is_current(sentinel, new_hash, required_stages):
    os.unlink(tmp_spec)
    verbose.emit(Events.FINISHED, message="build is current")
    return
```

After the `os.replace(tmp_spec, ...)` line, update the `if through` blocks:

```python
if through in ('parse', 'all'):
    verbose.emit(Events.PHASE, message="ll1")
    ll1_json = str(build_dir / 'll1.json')
    _run_or_die(['plcc-ll1'] + child_flags, stdin_file=spec_json, stdout_file=ll1_json, verbose=verbose)
    with open(ll1_json) as f:
        ll1 = json.load(f)
    if not ll1.get("is_ll1", True):
        _report_ll1_failure(ll1, ll1_json)
        sys.exit(1)

if through in ('diagram', 'all'):
    verbose.emit(Events.PHASE, message="model")
    model_json = str(build_dir / 'model.json')
    _run_or_die(['plcc-model', spec_json] + child_flags, stdout_file=model_json, verbose=verbose)

if through == 'all':
    for section in spec_data.get('semantics', []):
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

if through in ('diagram', 'all'):
    verbose.emit(Events.PHASE, message="diagram emit")
    (build_dir / 'diagram').mkdir(exist_ok=True)
    _run_or_die(
        ['plcc-diagram-emit', f'--format={diagram_fmt}'] + child_flags,
        stdin_file=model_json,
        stdout_file=str(build_dir / 'diagram' / 'diagram.mmd'),
        verbose=verbose,
    )
    verbose.emit(Events.PHASE, message="diagram build")
    _run_or_die(
        ['plcc-diagram-build', f'--format={diagram_fmt}',
         f'--input={build_dir / "diagram" / "diagram.mmd"}',
         f'--output={build_dir / "diagram" / "diagram.png"}'] + child_flags,
        verbose=verbose,
    )
```

Replace `write_sentinel(build_dir, new_hash, through)` at the end:

```python
completed = {'scan'}
if through in ('parse', 'all'):
    completed.add('parse')
if through in ('diagram', 'all'):
    completed.add('model')
    completed.add('diagram')
if through == 'all':
    completed |= tool_stages
write_sentinel(build_dir, new_hash, completed)
```

Also remove the now-unused `with open(spec_json) as f: spec = json.load(f)` block inside `if through == 'all'` (we use `spec_data` read earlier).

- [ ] **Step 4: Run all make tests**

```bash
bin/test/units.bash src/plcc/cmd/make_test.py
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(make): add --through=diagram, --diagram-format, and set-based staleness"
```

---

## Task 3: Rename `plcc-diagram` dispatcher → `plcc-diagram-emit`

The current `src/plcc/diagram/dispatch.py` dispatches to `plcc-{fmt}-diagram`. Rename the file, update the command name, change the default format to `mermaid`, and drop `--output=DIR`.

**Files:**

- Rename `src/plcc/diagram/dispatch.py` → `src/plcc/diagram/emit.py`
- Rename `src/plcc/diagram/dispatch_test.py` → `src/plcc/diagram/emit_test.py`

- [ ] **Step 1: Write the new `emit_test.py`**

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


def test_dispatches_to_mermaid_diagram_emit_by_default(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    calls = []

    def fake_run(cmd, stdin, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-mermaid-diagram-emit'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([])

    assert calls[0][0] == 'plcc-mermaid-diagram-emit'


def test_custom_format_dispatches_to_correct_command(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    calls = []

    def fake_run(cmd, stdin, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-plantuml-diagram-emit'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main(['--format=plantuml'])

    assert calls[0][0] == 'plcc-plantuml-diagram-emit'


def test_missing_plugin_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))

    with patch('shutil.which', return_value=None):
        with pytest.raises(SystemExit) as exc:
            run_main(['--format=nonexistent'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'nonexistent' in err
```

- [ ] **Step 2: Create `emit.py`** (do not delete `dispatch.py` yet — keep it until pyproject.toml is updated in Task 11)

```python
# src/plcc/diagram/emit.py
import enum
import shutil
import subprocess
import sys

from docopt import docopt

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-emit
    Dispatch model JSON to the appropriate plcc-<fmt>-diagram-emit command.

Usage:
    plcc-diagram-emit [-v ...] [options]

Options:
    --format=FMT    Diagram format [default: mermaid].
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
    fmt = args['--format'] or 'mermaid'
    cmd = f'plcc-{fmt}-diagram-emit'
    if not shutil.which(cmd):
        print(
            f"No diagram plugin found for '{fmt}'. Is {cmd} installed?\n"
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

- [ ] **Step 3: Run tests**

```bash
bin/test/units.bash src/plcc/diagram/emit_test.py
```

Expected: all pass.

- [ ] **Step 4: Update `plcc-plantuml-diagram` `__doc__` name**

In `src/plcc/diagram/plantuml/emit.py`, change the first line of `__doc__` from `plcc-plantuml-diagram` to `plcc-plantuml-diagram-emit`. No other changes.

- [ ] **Step 5: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add src/plcc/diagram/emit.py src/plcc/diagram/emit_test.py src/plcc/diagram/plantuml/emit.py
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(diagram): add plcc-diagram-emit dispatcher (replaces plcc-diagram)"
```

---

## Task 4: Update `plcc-diagram-list` — new discovery pattern

**Files:**

- Modify: `src/plcc/diagram/list.py`
- Modify: `src/plcc/diagram/list_test.py`

- [ ] **Step 1: Write failing tests for new pattern**

Replace `src/plcc/diagram/list_test.py`:

```python
from .list import find_formats, extract_format_name


def test_extract_format_name_plantuml_emit():
    assert extract_format_name('plcc-plantuml-diagram-emit') == 'plantuml'


def test_extract_format_name_mermaid_emit():
    assert extract_format_name('plcc-mermaid-diagram-emit') == 'mermaid'


def test_extract_ignores_old_pattern():
    assert extract_format_name('plcc-plantuml-diagram') is None


def test_extract_ignores_dispatcher():
    assert extract_format_name('plcc-diagram-emit') is None


def test_extract_ignores_non_matching():
    assert extract_format_name('plcc-diagram-list') is None
    assert extract_format_name('python') is None


def test_find_formats_returns_list(monkeypatch):
    monkeypatch.setenv('PATH', '/fake/bin')
    result = find_formats()
    assert isinstance(result, list)


def test_main_prints_sorted_formats(capsys, monkeypatch):
    from .list import main
    monkeypatch.setattr('plcc.diagram.list.find_formats', lambda: ['plantuml', 'mermaid'])
    main([])
    out, _ = capsys.readouterr()
    assert out.splitlines() == ['mermaid', 'plantuml']
```

- [ ] **Step 2: Run to confirm failures**

```bash
bin/test/units.bash src/plcc/diagram/list_test.py
```

Expected: `test_extract_format_name_plantuml_emit` and `test_extract_format_name_mermaid_emit` fail; `test_extract_ignores_old_pattern` passes (old pattern still matches — will also break after the fix).

- [ ] **Step 3: Update `list.py`**

Change `_DIAGRAM_PATTERN`:

```python
_DIAGRAM_PATTERN = re.compile(r'^plcc-(.+)-diagram-emit$')
```

Update `extract_format_name` docstring:

```python
def extract_format_name(command_name):
    """Return format name from plcc-<fmt>-diagram-emit command name, or None."""
    m = _DIAGRAM_PATTERN.match(command_name)
    if m:
        fmt = m.group(1)
        if fmt != 'diagram':
            return fmt
    return None
```

- [ ] **Step 4: Run tests**

```bash
bin/test/units.bash src/plcc/diagram/list_test.py
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add src/plcc/diagram/list.py src/plcc/diagram/list_test.py
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(diagram): update plcc-diagram-list to discover plcc-*-diagram-emit plugins"
```

---

## Task 5: Create `plcc-diagram-build` dispatcher

**Files:**

- Create: `src/plcc/diagram/build.py`
- Create: `src/plcc/diagram/build_test.py`

- [ ] **Step 1: Write failing tests**

```python
# src/plcc/diagram/build_test.py
import pytest
from unittest.mock import patch, MagicMock

from .build import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_dispatches_to_mermaid_diagram_build(tmp_path):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n")
    out = tmp_path / "diagram.png"
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-mermaid-diagram-build'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--input={src}', f'--output={out}'])

    assert calls[0][0] == 'plcc-mermaid-diagram-build'
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

    with patch('shutil.which', return_value='/usr/bin/plcc-plantuml-diagram-build'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--input={src}', f'--output={out}', '--format=plantuml'])

    assert calls[0][0] == 'plcc-plantuml-diagram-build'


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

- [ ] **Step 2: Run to confirm failures**

```bash
bin/test/units.bash src/plcc/diagram/build_test.py
```

Expected: `ImportError` — module doesn't exist yet.

- [ ] **Step 3: Create `build.py`**

```python
# src/plcc/diagram/build.py
import enum
import shutil
import subprocess
import sys

from docopt import docopt

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-build
    Dispatch to the appropriate plcc-<fmt>-diagram-build command.

Usage:
    plcc-diagram-build --input=FILE --output=FILE [-v ...] [options]

Options:
    --format=FMT    Diagram format [default: mermaid].
    --input=FILE    Path to diagram source file.
    --output=FILE   Path to write image file.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-build", Events, args)
    fmt = args['--format'] or 'mermaid'
    input_file = args['--input']
    output_file = args['--output']
    cmd = f'plcc-{fmt}-diagram-build'
    if not shutil.which(cmd):
        print(
            f"No diagram build plugin found for '{fmt}'. Is {cmd} installed?\n"
            f"Run plcc-diagram-list to see what is available.",
            file=sys.stderr,
        )
        sys.exit(1)
    result = subprocess.run(
        [cmd, f'--input={input_file}', f'--output={output_file}'] + verbose.child_flags(),
    )
    if result.returncode != 0:
        sys.exit(result.returncode)
```

- [ ] **Step 4: Run tests**

```bash
bin/test/units.bash src/plcc/diagram/build_test.py
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add src/plcc/diagram/build.py src/plcc/diagram/build_test.py
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(diagram): add plcc-diagram-build dispatcher"
```

---

## Task 6: Create `plcc-diagram-run` dispatcher

**Files:**

- Create: `src/plcc/diagram/run.py`
- Create: `src/plcc/diagram/run_test.py`

- [ ] **Step 1: Write failing tests**

```python
# src/plcc/diagram/run_test.py
import pytest
from unittest.mock import patch, MagicMock

from .run import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_dispatches_to_mermaid_diagram_run(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-mermaid-diagram-run'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--input={img}'])

    assert calls[0][0] == 'plcc-mermaid-diagram-run'
    assert f'--input={img}' in calls[0]


def test_missing_plugin_exits_nonzero(tmp_path, capsys):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")

    with patch('shutil.which', return_value=None):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={img}', '--format=nonexistent'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'nonexistent' in err
```

- [ ] **Step 2: Run to confirm failures**

```bash
bin/test/units.bash src/plcc/diagram/run_test.py
```

Expected: `ImportError`.

- [ ] **Step 3: Create `run.py`**

```python
# src/plcc/diagram/run.py
import enum
import shutil
import subprocess
import sys

from docopt import docopt

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-run
    Dispatch to the appropriate plcc-<fmt>-diagram-run command.

Usage:
    plcc-diagram-run --input=FILE [-v ...] [options]

Options:
    --format=FMT    Diagram format [default: mermaid].
    --input=FILE    Path to diagram image file.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-run", Events, args)
    fmt = args['--format'] or 'mermaid'
    input_file = args['--input']
    cmd = f'plcc-{fmt}-diagram-run'
    if not shutil.which(cmd):
        print(
            f"No diagram run plugin found for '{fmt}'. Is {cmd} installed?\n"
            f"Run plcc-diagram-list to see what is available.",
            file=sys.stderr,
        )
        sys.exit(1)
    result = subprocess.run(
        [cmd, f'--input={input_file}'] + verbose.child_flags(),
    )
    if result.returncode != 0:
        sys.exit(result.returncode)
```

- [ ] **Step 4: Run tests**

```bash
bin/test/units.bash src/plcc/diagram/run_test.py
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add src/plcc/diagram/run.py src/plcc/diagram/run_test.py
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(diagram): add plcc-diagram-run dispatcher"
```

---

## Task 7: Create Mermaid emit plugin

**Files:**

- Create: `src/plcc/diagram/mermaid/__init__.py`
- Create: `src/plcc/diagram/mermaid/emit.py`
- Create: `src/plcc/diagram/mermaid/emit_test.py`

- [ ] **Step 1: Write failing tests**

```python
# src/plcc/diagram/mermaid/emit_test.py
import io
import json
import pytest

from .emit import build_diagram, main

_SIMPLE_MODEL = {
    "start": "expr",
    "classes": [
        {"name": "Expr", "abstract": True, "extends": None, "fields": []},
        {"name": "AddExpr", "abstract": False, "extends": "Expr",
         "fields": [{"name": "left", "type": "Expr"},
                    {"name": "right", "type": "Expr"}]},
    ],
    "semantic_sections": []
}


def test_build_diagram_starts_with_classDiagram():
    result = build_diagram(_SIMPLE_MODEL)
    assert result.startswith('classDiagram\n')


def test_build_diagram_ends_with_newline():
    result = build_diagram(_SIMPLE_MODEL)
    assert result.endswith('\n')


def test_build_diagram_abstract_class_has_annotation():
    result = build_diagram(_SIMPLE_MODEL)
    assert '<<abstract>>' in result
    assert 'class Expr' in result


def test_build_diagram_concrete_class_has_fields():
    result = build_diagram(_SIMPLE_MODEL)
    assert 'left: Expr' in result
    assert 'right: Expr' in result


def test_build_diagram_inheritance_arrow():
    result = build_diagram(_SIMPLE_MODEL)
    assert 'AddExpr --|> Expr' in result


def test_build_diagram_empty_model():
    model = {"classes": [], "semantic_sections": []}
    result = build_diagram(model)
    assert result == 'classDiagram\n'


def test_main_writes_diagram_to_stdout(monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_SIMPLE_MODEL)))
    main([])
    out, _ = capsys.readouterr()
    assert 'classDiagram' in out
    assert 'AddExpr --|> Expr' in out
```

- [ ] **Step 2: Run to confirm failures**

```bash
bin/test/units.bash src/plcc/diagram/mermaid/emit_test.py
```

Expected: `ImportError` — package doesn't exist yet.

- [ ] **Step 3: Create the package and `emit.py`**

```python
# src/plcc/diagram/mermaid/__init__.py
# (empty)
```

```python
# src/plcc/diagram/mermaid/emit.py
import enum
import json
import sys

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-mermaid-diagram-emit
    Emit a Mermaid class diagram from model JSON.

Usage:
    plcc-mermaid-diagram-emit [-v ...] [options]

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
    verbose = VerboseContext.from_args("plcc-mermaid-diagram-emit", Events, args)
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

- [ ] **Step 4: Run tests**

```bash
bin/test/units.bash src/plcc/diagram/mermaid/emit_test.py
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add src/plcc/diagram/mermaid/__init__.py src/plcc/diagram/mermaid/emit.py src/plcc/diagram/mermaid/emit_test.py
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(diagram): add plcc-mermaid-diagram-emit plugin"
```

---

## Task 8: Create Mermaid build plugin

**Files:**

- Create: `src/plcc/diagram/mermaid/build.py`
- Create: `src/plcc/diagram/mermaid/build_test.py`

- [ ] **Step 1: Write failing tests**

```python
# src/plcc/diagram/mermaid/build_test.py
import pytest
from unittest.mock import patch, MagicMock

from .build import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_missing_mmdc_prints_helpful_error(tmp_path, capsys):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n")
    out = tmp_path / "diagram.png"

    with patch.dict('sys.modules', {'mmdc': None}):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={src}', f'--output={out}'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'pip install plcc[diagram]' in err


def test_calls_mmdc_converter(tmp_path):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n    class Foo {}\n")
    out = tmp_path / "diagram.png"

    mock_converter = MagicMock()
    mock_converter.to_png.return_value = b'\x89PNG\r\n'
    mock_mmdc = MagicMock()
    mock_mmdc.MermaidConverter.return_value = mock_converter

    with patch.dict('sys.modules', {'mmdc': mock_mmdc}):
        run_main([f'--input={src}', f'--output={out}'])

    mock_converter.to_png.assert_called_once_with("classDiagram\n    class Foo {}\n")
    assert out.read_bytes() == b'\x89PNG\r\n'
```

- [ ] **Step 2: Run to confirm failures**

```bash
bin/test/units.bash src/plcc/diagram/mermaid/build_test.py
```

Expected: `ImportError`.

- [ ] **Step 3: Create `build.py`**

> **Note:** Verify the exact `mmdc` API before shipping. The test mocks `MermaidConverter().to_png(source_string)` returning `bytes`. Check `mmdc` docs/source to confirm the method signature and return type.

```python
# src/plcc/diagram/mermaid/build.py
import enum
import sys

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-mermaid-diagram-build
    Render a Mermaid diagram source file to a PNG image.

Usage:
    plcc-mermaid-diagram-build --input=FILE --output=FILE [-v ...] [options]

Options:
    --input=FILE    Path to .mmd source file.
    --output=FILE   Path to write .png image.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-mermaid-diagram-build", Events, args)
    input_file = args['--input']
    output_file = args['--output']
    verbose.emit(Events.STARTED, message=f"rendering {input_file}")
    try:
        from mmdc import MermaidConverter
    except ImportError:
        print(
            "plcc-mermaid-diagram-build: mmdc not installed — "
            "run: pip install plcc[diagram]",
            file=sys.stderr,
        )
        sys.exit(1)
    source = open(input_file).read()
    converter = MermaidConverter()
    png_bytes = converter.to_png(source)
    with open(output_file, 'wb') as f:
        f.write(png_bytes)
    verbose.emit(Events.FINISHED, message=f"wrote {output_file}")
```

- [ ] **Step 4: Run tests**

```bash
bin/test/units.bash src/plcc/diagram/mermaid/build_test.py
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add src/plcc/diagram/mermaid/build.py src/plcc/diagram/mermaid/build_test.py
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(diagram): add plcc-mermaid-diagram-build plugin"
```

---

## Task 9: Create Mermaid run plugin

**Files:**

- Create: `src/plcc/diagram/mermaid/run.py`
- Create: `src/plcc/diagram/mermaid/run_test.py`

- [ ] **Step 1: Write failing tests**

```python
# src/plcc/diagram/mermaid/run_test.py
import pytest
from unittest.mock import patch, MagicMock

from .run import main as run_main, _open_file


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_open_file_calls_open_on_macos(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    calls = []

    with patch('platform.system', return_value='Darwin'):
        with patch('subprocess.run', side_effect=lambda cmd, **kw: calls.append(cmd)):
            _open_file(str(img))

    assert calls[0] == ['open', str(img)]


def test_open_file_calls_xdg_open_on_linux(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    calls = []

    with patch('platform.system', return_value='Linux'):
        with patch('subprocess.run', side_effect=lambda cmd, **kw: calls.append(cmd)):
            _open_file(str(img))

    assert calls[0] == ['xdg-open', str(img)]


def test_main_calls_open_file(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")

    with patch('plcc.diagram.mermaid.run._open_file') as mock_open:
        run_main([f'--input={img}'])

    mock_open.assert_called_once_with(str(img))
```

- [ ] **Step 2: Run to confirm failures**

```bash
bin/test/units.bash src/plcc/diagram/mermaid/run_test.py
```

Expected: `ImportError`.

- [ ] **Step 3: Create `run.py`**

```python
# src/plcc/diagram/mermaid/run.py
import enum
import platform
import subprocess
import sys

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-mermaid-diagram-run
    Open a diagram image in the system viewer.

Usage:
    plcc-mermaid-diagram-run --input=FILE [-v ...] [options]

Options:
    --input=FILE    Path to image file to open.
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
    verbose.emit(Events.STARTED, message=f"opening {input_file}")
    _open_file(input_file)
    verbose.emit(Events.FINISHED)


def _open_file(path):
    system = platform.system()
    if system == 'Darwin':
        subprocess.run(['open', path], check=True)
    elif system == 'Windows':
        subprocess.run(['start', path], shell=True, check=True)
    else:
        subprocess.run(['xdg-open', path], check=True)
```

- [ ] **Step 4: Run tests**

```bash
bin/test/units.bash src/plcc/diagram/mermaid/run_test.py
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add src/plcc/diagram/mermaid/run.py src/plcc/diagram/mermaid/run_test.py
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(diagram): add plcc-mermaid-diagram-run plugin"
```

---

## Task 10: Create `plcc-diagram` Level 2 command

**Files:**

- Create: `src/plcc/cmd/diagram.py`
- Create: `src/plcc/cmd/diagram_test.py`

- [ ] **Step 1: Write failing tests**

```python
# src/plcc/cmd/diagram_test.py
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
    assert "grammar file not found" in err


def test_calls_plcc_make_with_through_diagram(tmp_path, monkeypatch):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    make_calls = []

    def fake_run(cmd, **kwargs):
        make_calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            # will exit after make because diagram.png doesn't exist
            run_main([])

    assert any('plcc-make' in str(c) for c in make_calls)
    assert any('--through=diagram' in str(c) for c in make_calls[0])


def test_default_format_is_mermaid(tmp_path, monkeypatch):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    make_calls = []

    def fake_run(cmd, **kwargs):
        make_calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main([])

    assert any('--diagram-format=mermaid' in str(c) for c in make_calls[0])
```

- [ ] **Step 2: Run to confirm failures**

```bash
bin/test/units.bash src/plcc/cmd/diagram_test.py
```

Expected: `ImportError`.

- [ ] **Step 3: Create `diagram.py`**

```python
# src/plcc/cmd/diagram.py
import enum
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram
    Generate and display a class diagram from a PLCC grammar file.

Usage:
    plcc-diagram [-v ...] [options]

Options:
    --grammar-file=<path>   Path to the PLCC grammar file [default: grammar.plcc].
    --format=FMT            Diagram format [default: mermaid].
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
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose = VerboseContext.from_args("plcc-diagram", Events, args)
    grammar_file = args['--grammar-file']
    fmt = args['--format'] or 'mermaid'

    if not os.path.exists(grammar_file):
        print(f"plcc-diagram: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message=f"generating diagram for {grammar_file}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ['plcc-make', '--through=diagram',
         f'--grammar-file={grammar_file}',
         f'--diagram-format={fmt}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        events = verbose.parse_child_events(
            make_result.stderr.decode('utf-8', errors='replace')
        )
        verbose.reformat_child_events(events)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    image_path = os.path.join('build', 'diagram', 'diagram.png')
    run_result = subprocess.run(
        ['plcc-diagram-run', f'--format={fmt}',
         f'--input={image_path}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if run_result.stderr:
        events = verbose.parse_child_events(
            run_result.stderr.decode('utf-8', errors='replace')
        )
        verbose.reformat_child_events(events)
    if run_result.returncode != 0:
        sys.exit(run_result.returncode)

    verbose.emit(Events.FINISHED, message="done")
```

- [ ] **Step 4: Run tests**

```bash
bin/test/units.bash src/plcc/cmd/diagram_test.py
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add src/plcc/cmd/diagram.py src/plcc/cmd/diagram_test.py
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(diagram): add plcc-diagram Level 2 command"
```

---

## Task 11: Update `pyproject.toml`, reinstall, run all unit tests

**Files:**

- Modify: `pyproject.toml`
- Delete: `src/plcc/diagram/dispatch.py`, `src/plcc/diagram/dispatch_test.py`

- [ ] **Step 1: Update `pyproject.toml`**

In `[project.scripts]`, make these changes:

Remove:
```toml
plcc-plantuml-diagram = "plcc.diagram.plantuml.emit:main"
plcc-diagram = "plcc.diagram.dispatch:main"
```

Add:
```toml
plcc-diagram = "plcc.cmd.diagram:main"
plcc-diagram-emit = "plcc.diagram.emit:main"
plcc-diagram-build = "plcc.diagram.build:main"
plcc-diagram-run = "plcc.diagram.run:main"
plcc-plantuml-diagram-emit = "plcc.diagram.plantuml.emit:main"
plcc-mermaid-diagram-emit = "plcc.diagram.mermaid.emit:main"
plcc-mermaid-diagram-build = "plcc.diagram.mermaid.build:main"
plcc-mermaid-diagram-run = "plcc.diagram.mermaid.run:main"
```

Add the optional extras section after `[project]` dependencies:

```toml
[project.optional-dependencies]
diagram = ["mmdc"]
```

- [ ] **Step 2: Delete the old dispatcher files**

```bash
git -C "$(git rev-parse --show-toplevel)" rm src/plcc/diagram/dispatch.py src/plcc/diagram/dispatch_test.py
```

- [ ] **Step 3: Reinstall**

```bash
pdm install
```

Expected: no errors.

- [ ] **Step 4: Run all unit tests**

```bash
bin/test/units.bash
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add pyproject.toml
git -C "$(git rev-parse --show-toplevel)" commit -m "build: update entry points for diagram redesign"
```

---

## Task 12: Update bats command tests

**Files:**

- Modify: `tests/bats/commands/plcc-diagram.bats`
- Modify: `tests/bats/commands/plcc-diagram-list.bats`
- Create: `tests/bats/commands/plcc-diagram-build.bats`
- Create: `tests/bats/commands/plcc-diagram-run.bats`

- [ ] **Step 1: Rewrite `plcc-diagram.bats` for the Level 2 interface**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram is on PATH" { command -v plcc-diagram; }

@test "plcc-diagram --help exits 0" {
    run plcc-diagram --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram fails when grammar file not found" {
    run bash -c "cd /tmp && plcc-diagram --grammar-file=nonexistent.plcc"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "grammar file not found" ]]
}
```

- [ ] **Step 2: Update `plcc-diagram-list.bats`**

Replace the test that checks for `plantuml` (old pattern) with one that checks for `mermaid` (new emit pattern):

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-list is on PATH" { command -v plcc-diagram-list; }

@test "plcc-diagram-list exits 0" {
    run plcc-diagram-list
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-list finds mermaid" {
    run plcc-diagram-list
    [ "$status" -eq 0 ]
    [[ "$output" =~ "mermaid" ]]
}
```

- [ ] **Step 3: Create `plcc-diagram-build.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-build is on PATH" { command -v plcc-diagram-build; }

@test "plcc-diagram-build --help exits 0" {
    run plcc-diagram-build --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-build requires --input and --output" {
    run plcc-diagram-build
    [ "$status" -ne 0 ]
}
```

- [ ] **Step 4: Create `plcc-diagram-run.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-run is on PATH" { command -v plcc-diagram-run; }

@test "plcc-diagram-run --help exits 0" {
    run plcc-diagram-run --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-run requires --input" {
    run plcc-diagram-run
    [ "$status" -ne 0 ]
}
```

- [ ] **Step 5: Run bats command tests**

```bash
bin/test/commands.bash tests/bats/commands/plcc-diagram.bats tests/bats/commands/plcc-diagram-list.bats tests/bats/commands/plcc-diagram-build.bats tests/bats/commands/plcc-diagram-run.bats
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add tests/bats/commands/plcc-diagram.bats tests/bats/commands/plcc-diagram-list.bats tests/bats/commands/plcc-diagram-build.bats tests/bats/commands/plcc-diagram-run.bats
git -C "$(git rev-parse --show-toplevel)" commit -m "test(diagram): update and add bats command tests for diagram redesign"
```

---

## Task 13: Run full test suite

- [ ] **Step 1: Run all functional tests**

```bash
bin/test/functional.bash
```

Expected: all pass.

- [ ] **Step 2: If anything fails, fix it before marking done**

Common things to check:

- Any test that still references `plcc-plantuml-diagram` (old name) should be updated to `plcc-plantuml-diagram-emit`
- Any test that references `plcc.diagram.dispatch` should be updated to `plcc.diagram.emit`
- The `plcc-diagram-emit` bats test in the existing `plcc-diagram.bats` may need a rename to `tests/bats/commands/plcc-diagram-emit.bats`

- [ ] **Step 3: Final commit if any fixes were needed**

```bash
git -C "$(git rev-parse --show-toplevel)" add -u
git -C "$(git rev-parse --show-toplevel)" commit -m "fix(diagram): address issues found in full test suite run"
```
