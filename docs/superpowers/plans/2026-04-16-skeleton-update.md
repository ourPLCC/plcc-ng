# Skeleton Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the walking skeleton to reflect architectural amendments §17.3–§17.8 — new commands, verbose infrastructure, connected Level 2 orchestrators, and language plugin stubs.

**Architecture:** Bottom-up: shared verbose module first, then leaf stubs (Level 0 primitives, language plugins), then dispatchers, then Level 2 orchestrators. Each layer is testable in isolation before wiring to the next.

**Tech Stack:** Python 3.12+, pdm, pytest, docopt-ng, BATS, check-jsonschema

**Design spec:** `docs/design/2026-04-16-skeleton-update-design.md`

---

## Part 1 — Foundation

### Task 1: Verify green bar

**Files:**
- Run only: `bin/test/all.bash`

- [ ] **Step 1: Run the full test suite**

```bash
cd /workspaces/plcc-ng/.worktrees/multi-lang
bin/test/all.bash
```

Expected: all tests pass. Do not proceed until green. If any fail, fix them first.

- [ ] **Step 2: Note the test count**

Record the number of passing unit tests and BATS tests. These numbers must not decrease through this plan.

---

### Task 2: Create test fixtures

**Files:**
- Create: `tests/fixtures/trivial-java.plcc`
- Create: `tests/fixtures/trivial-python.plcc`
- Create: `tests/fixtures/trivial-full.plcc`
- Create: `tests/fixtures/trivial_input.txt`

- [ ] **Step 1: Create `tests/fixtures/trivial_input.txt`**

A single-line source file for testing commands that read source files:

```
42
```

- [ ] **Step 2: Create `tests/fixtures/trivial-java.plcc`**

```
token NUM '\d+'
%
<program> ::= NUM
% Java Java
```

- [ ] **Step 3: Create `tests/fixtures/trivial-python.plcc`**

```
token NUM '\d+'
%
<program> ::= NUM
% py Python
```

- [ ] **Step 4: Create `tests/fixtures/trivial-full.plcc`**

```
token NUM '\d+'
%
<program> ::= NUM
% Java Java
% py Python
% diagram PlantUML
```

- [ ] **Step 5: Verify fixtures parse without error**

```bash
plcc-spec tests/fixtures/trivial-java.plcc > /dev/null
plcc-spec tests/fixtures/trivial-python.plcc > /dev/null
plcc-spec tests/fixtures/trivial-full.plcc > /dev/null
```

Expected: all exit 0.

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/trivial_input.txt tests/fixtures/trivial-java.plcc tests/fixtures/trivial-python.plcc tests/fixtures/trivial-full.plcc
git commit -m "test(fixtures): add input file, Java, Python, and full trivial grammars for skeleton update"
```

---

### Task 3: Verbose infrastructure — `plcc.verbose`

**Files:**
- Create: `src/plcc/verbose.py`
- Create: `src/plcc/verbose_test.py`

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/verbose_test.py`:

```python
import enum
import json

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


class SampleEvents(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def test_verbose_options_is_a_string():
    assert isinstance(VERBOSE_OPTIONS, str)
    assert "--verbose" in VERBOSE_OPTIONS
    assert "--verbose-format" in VERBOSE_OPTIONS


def test_from_args_defaults():
    args = {"--verbose": "0", "--verbose-format": "text"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    assert ctx.stage == "plcc-test"
    assert ctx.level == 0
    assert ctx.fmt == "text"


def test_from_args_with_values():
    args = {"--verbose": "2", "--verbose-format": "json"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    assert ctx.level == 2
    assert ctx.fmt == "json"


def test_emit_text_format(capsys):
    args = {"--verbose": "1", "--verbose-format": "text"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    ctx.emit(SampleEvents.STARTED, message="reading spec")
    captured = capsys.readouterr()
    assert captured.out == ""  # nothing on stdout
    assert "plcc-test: started: reading spec" in captured.err


def test_emit_json_format(capsys):
    args = {"--verbose": "1", "--verbose-format": "json"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    ctx.emit(SampleEvents.STARTED, message="reading spec")
    captured = capsys.readouterr()
    assert captured.out == ""
    record = json.loads(captured.err.strip())
    assert record["stage"] == "plcc-test"
    assert record["event"] == "started"
    assert record["message"] == "reading spec"
    assert "time" in record


def test_emit_suppressed_when_level_too_low(capsys):
    args = {"--verbose": "0", "--verbose-format": "text"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    ctx.emit(SampleEvents.STARTED, level=1, message="should not appear")
    captured = capsys.readouterr()
    assert captured.err == ""


def test_child_flags_returns_unchanged():
    args = {"--verbose": "2", "--verbose-format": "text"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    flags = ctx.child_flags()
    assert "--verbose=2" in flags
    assert "--verbose-format=text" in flags


def test_child_flags_for_orchestrator_forces_json():
    args = {"--verbose": "1", "--verbose-format": "text"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    flags = ctx.child_flags_for_orchestrator(min_level=2)
    assert "--verbose=2" in flags
    assert "--verbose-format=json" in flags


def test_child_flags_for_orchestrator_keeps_higher_user_level():
    args = {"--verbose": "3", "--verbose-format": "text"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    flags = ctx.child_flags_for_orchestrator(min_level=1)
    assert "--verbose=3" in flags


def test_parse_child_events_roundtrip(capsys):
    args = {"--verbose": "1", "--verbose-format": "json"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    ctx.emit(SampleEvents.STARTED, message="hello")
    captured = capsys.readouterr()
    events = ctx.parse_child_events(captured.err)
    assert len(events) == 1
    assert events[0]["event"] == "started"


def test_reformat_child_events_to_text(capsys):
    json_line = json.dumps({"stage": "plcc-child", "time": 0, "event": "started", "message": "hi"})
    args = {"--verbose": "1", "--verbose-format": "text"}
    ctx = VerboseContext.from_args("plcc-parent", SampleEvents, args)
    events = ctx.parse_child_events(json_line + "\n")
    ctx.reformat_child_events(events)
    captured = capsys.readouterr()
    assert "plcc-child: started: hi" in captured.err


def test_parity_both_renderers_handle_all_events(capsys):
    """Every event in the enum is handled by both text and json renderers."""
    for fmt in ("text", "json"):
        args = {"--verbose": "1", "--verbose-format": fmt}
        ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
        for event in SampleEvents:
            ctx.emit(event, message="test")
        captured = capsys.readouterr()
        assert captured.err != ""
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/verbose_test.py
```

Expected: FAIL — `ModuleNotFoundError: No module named 'plcc.verbose'`

- [ ] **Step 3: Implement `src/plcc/verbose.py`**

```python
"""Shared verbose infrastructure for the PLCC pipeline.

Every command accepts --verbose and --verbose-format. This module provides
the VerboseContext object and the VERBOSE_OPTIONS docopt fragment.
"""

import json
import sys
import time


VERBOSE_OPTIONS = """
    --verbose=LEVEL         Verbosity level 0-3 [default: 0].
    --verbose-format=FMT    Output format: text or json [default: text].
"""


class VerboseContext:
    """Holds verbosity settings for one command invocation."""

    def __init__(self, stage, events_enum, level=0, fmt="text"):
        self.stage = stage
        self.events_enum = events_enum
        self.level = level
        self.fmt = fmt

    @classmethod
    def from_args(cls, stage, events_enum, args):
        level = int(args.get("--verbose") or 0)
        fmt = args.get("--verbose-format") or "text"
        return cls(stage, events_enum, level, fmt)

    def emit(self, event, level=1, **payload):
        if self.level < level:
            return
        if self.fmt == "json":
            record = {
                "stage": self.stage,
                "time": time.monotonic_ns(),
                "event": event.value,
                **payload,
            }
            print(json.dumps(record), file=sys.stderr, flush=True)
        else:
            msg = payload.get("message", "")
            print(f"{self.stage}: {event.value}: {msg}", file=sys.stderr, flush=True)

    def child_flags(self):
        return [f"--verbose={self.level}", f"--verbose-format={self.fmt}"]

    def child_flags_for_orchestrator(self, min_level=None):
        level = max(self.level, min_level or 0)
        return [f"--verbose={level}", "--verbose-format=json"]

    def parse_child_events(self, stderr_text):
        events = []
        for line in stderr_text.splitlines():
            line = line.strip()
            if line:
                events.append(json.loads(line))
        return events

    def reformat_child_events(self, events):
        for ev in events:
            if self.fmt == "json":
                print(json.dumps(ev), file=sys.stderr, flush=True)
            else:
                stage = ev.get("stage", "unknown")
                event = ev.get("event", "unknown")
                msg = ev.get("message", "")
                print(f"{stage}: {event}: {msg}", file=sys.stderr, flush=True)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/verbose_test.py
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/verbose.py src/plcc/verbose_test.py
git commit -m "feat(verbose): add shared VerboseContext infrastructure"
```

---

## Part 2 — New Leaf Stubs (Level 0 Primitives)

### Task 4: `plcc-ll1` stub and ll1 schema

**Files:**
- Create: `src/plcc/ll1/__init__.py`
- Create: `src/plcc/ll1/ll1_cli.py`
- Create: `src/plcc/schemas/ll1.schema.json`
- Modify: `pyproject.toml`

- [ ] **Step 1: Create the ll1 schema**

Create `src/plcc/schemas/ll1.schema.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LL1Analysis",
  "description": "Output of plcc-ll1: LL(1) analysis of a grammar.",
  "type": "object",
  "required": ["first_sets", "follow_sets", "predict_sets", "parse_table", "conflicts", "left_recursion"],
  "properties": {
    "first_sets":     { "type": "object" },
    "follow_sets":    { "type": "object" },
    "predict_sets":   { "type": "object" },
    "parse_table":    { "type": "object" },
    "conflicts":      { "type": "array" },
    "left_recursion": { "type": "array" }
  }
}
```

- [ ] **Step 2: Create `src/plcc/ll1/__init__.py`**

```python
```

(Empty file.)

- [ ] **Step 3: Create `src/plcc/ll1/ll1_cli.py`**

```python
"""plcc-ll1
    Perform LL(1) analysis on a grammar spec.

Usage:
    plcc-ll1 [options] [SPEC_JSON]

Arguments:
    SPEC_JSON   Path to spec JSON file. Use - or omit to read from stdin.

Options:
    --format=FMT    Output format: json or human [default: json].
    -h --help       Show this message.
""" + VERBOSE_OPTIONS

import enum
import json
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-ll1", Events, args)
    verbose.emit(Events.STARTED, message="reading spec")
    # Stub: emit minimal ll1.json with empty sets
    result = {
        "first_sets": {},
        "follow_sets": {},
        "predict_sets": {},
        "parse_table": {},
        "conflicts": [],
        "left_recursion": [],
    }
    print(json.dumps(result, indent=2))
    verbose.emit(Events.FINISHED, message="done")
```

- [ ] **Step 4: Add console script to `pyproject.toml`**

Add this line to the `[project.scripts]` section:

```toml
plcc-ll1 = "plcc.ll1.ll1_cli:main"
```

- [ ] **Step 5: Reinstall and verify entry point**

```bash
pdm install -q && plcc-ll1 --help
```

Expected: help text prints, exit 0.

- [ ] **Step 6: Write BATS command test**

Create `tests/bats/commands/plcc-ll1.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/ll1.schema.json"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() { rm -f "${SPEC_JSON}"; }

@test "plcc-ll1 is on PATH" { command -v plcc-ll1; }

@test "plcc-ll1 --help exits 0" {
    run plcc-ll1 --help
    [ "$status" -eq 0 ]
}

@test "plcc-ll1 produces schema-valid output" {
    run plcc-ll1 "${SPEC_JSON}"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-ll1 reads from stdin" {
    run bash -c "cat '${SPEC_JSON}' | plcc-ll1"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-ll1 accepts --verbose without error" {
    run plcc-ll1 --verbose=1 "${SPEC_JSON}"
    [ "$status" -eq 0 ]
}

@test "plcc-ll1 accepts --verbose-format without error" {
    run plcc-ll1 --verbose=1 --verbose-format=json "${SPEC_JSON}"
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 7: Run BATS test**

```bash
bin/test/commands.bash
```

Expected: all plcc-ll1 tests pass.

- [ ] **Step 8: Commit**

```bash
git add src/plcc/ll1/ src/plcc/schemas/ll1.schema.json tests/bats/commands/plcc-ll1.bats pyproject.toml
git commit -m "feat(ll1): add plcc-ll1 stub with empty LL(1) analysis output"
```

---

### Task 5: `plcc-parser-table` stub

**Files:**
- Create: `src/plcc/parser/__init__.py`
- Create: `src/plcc/parser/table_cli.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Create `src/plcc/parser/__init__.py`**

```python
```

(Empty file.)

- [ ] **Step 2: Create `src/plcc/parser/table_cli.py`**

This moves the Phase 1 `plcc-tree` pass-through logic here:

```python
"""plcc-parser-table
    Table-driven LL(1) parser. Reads token JSONL, emits a parse tree.

Usage:
    plcc-parser-table [options] --ll1=LL1_JSON

Options:
    --ll1=LL1_JSON          Path to LL(1) analysis JSON (required).
    -h --help               Show this message.
""" + VERBOSE_OPTIONS

import enum
import json
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-parser-table", Events, args)
    ll1_path = args["--ll1"]
    verbose.emit(Events.STARTED, message=f"parsing with table from {ll1_path}")
    # Stub: wrap each token in a minimal tree, pass errors through unchanged.
    # This is the Phase 1 plcc-tree behavior, relocated here.
    children = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        if record.get("kind") == "error":
            children.append(record)
        else:
            children.append(record)
    tree = {
        "kind": "tree",
        "rule": "program",
        "children": children,
    }
    print(json.dumps(tree), flush=True)
    verbose.emit(Events.FINISHED, message="done")
```

- [ ] **Step 3: Add console script to `pyproject.toml`**

Add to `[project.scripts]`:

```toml
plcc-parser-table = "plcc.parser.table_cli:main"
```

- [ ] **Step 4: Reinstall and verify**

```bash
pdm install -q && plcc-parser-table --help
```

Expected: help text, exit 0.

- [ ] **Step 5: Write BATS command test**

Create `tests/bats/commands/plcc-parser-table.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    TREE_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/tree.schema.json"
    SPEC_JSON="$(mktemp)"
    LL1_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    plcc-ll1 "${SPEC_JSON}" > "${LL1_JSON}"
}

teardown() { rm -f "${SPEC_JSON}" "${LL1_JSON}"; }

@test "plcc-parser-table is on PATH" { command -v plcc-parser-table; }

@test "plcc-parser-table --help exits 0" {
    run plcc-parser-table --help
    [ "$status" -eq 0 ]
}

@test "plcc-parser-table requires --ll1" {
    run bash -c "echo '{}' | plcc-parser-table"
    [ "$status" -ne 0 ]
}

@test "plcc-parser-table produces schema-valid tree" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${TREE_SCHEMA}" -
}

@test "plcc-parser-table accepts --verbose without error" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}' --verbose=1"
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 6: Run BATS test**

```bash
bin/test/commands.bash
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add src/plcc/parser/ tests/bats/commands/plcc-parser-table.bats pyproject.toml
git commit -m "feat(parser): add plcc-parser-table stub (relocated pass-through logic)"
```

---

### Task 6: `plcc-parser-list`

**Files:**
- Create: `src/plcc/parser/list_cli.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Create `src/plcc/parser/list_cli.py`**

```python
"""plcc-parser-list
    List installed parser plugins.

Usage:
    plcc-parser-list

Options:
    -h --help   Show this message.
"""

import os
import re
import sys

from docopt import docopt

_PARSER_PATTERN = re.compile(r"^plcc-parser-(.+)$")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    docopt(__doc__, argv)
    for kind in sorted(find_parsers()):
        print(kind)


def find_parsers():
    parsers = []
    seen = set()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        try:
            for entry in os.scandir(directory):
                name = _extract_parser_kind(entry.name)
                if name and name not in seen and entry.is_file() and os.access(entry.path, os.X_OK):
                    parsers.append(name)
                    seen.add(name)
        except (PermissionError, FileNotFoundError):
            continue
    return parsers


def _extract_parser_kind(command_name):
    m = _PARSER_PATTERN.match(command_name)
    if m:
        kind = m.group(1)
        if kind != "list":
            return kind
    return None
```

- [ ] **Step 2: Add console script to `pyproject.toml`**

```toml
plcc-parser-list = "plcc.parser.list_cli:main"
```

- [ ] **Step 3: Reinstall and verify**

```bash
pdm install -q && plcc-parser-list
```

Expected: prints `table` (since `plcc-parser-table` is now installed).

- [ ] **Step 4: Write BATS command test**

Create `tests/bats/commands/plcc-parser-list.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-parser-list is on PATH" { command -v plcc-parser-list; }

@test "plcc-parser-list finds plcc-parser-table" {
    run plcc-parser-list
    [ "$status" -eq 0 ]
    [[ "$output" == *"table"* ]]
}
```

- [ ] **Step 5: Run and verify**

```bash
bin/test/commands.bash
```

- [ ] **Step 6: Commit**

```bash
git add src/plcc/parser/list_cli.py tests/bats/commands/plcc-parser-list.bats pyproject.toml
git commit -m "feat(parser): add plcc-parser-list (PATH scan for parser plugins)"
```

---

## Part 3 — Language Plugin Stubs

### Task 7: Python language plugin

**Files:**
- Create: `src/plcc/lang/ext/python/__init__.py`
- Create: `src/plcc/lang/ext/python/emit.py`
- Create: `src/plcc/lang/ext/python/run.py`
- Create: `src/plcc/lang/ext/python/runtime/main.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Create `src/plcc/lang/ext/python/__init__.py`**

```python
```

(Empty file.)

- [ ] **Step 2: Create the stub runtime template**

Create `src/plcc/lang/ext/python/runtime/main.py`:

```python
"""Stub Python interpreter — reads parse-tree JSONL, prints evaluation lines."""

import json
import sys


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        tree = json.loads(line)
        kind = tree.get("kind", "unknown")
        rule = tree.get("rule", "unknown")
        print(f"evaluated: {rule} ({kind})", flush=True)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Create `src/plcc/lang/ext/python/emit.py`**

```python
"""plcc-python-emit
    Emit a stub Python interpreter from model JSON.

Usage:
    plcc-python-emit --output=DIR [options]

Options:
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS

import enum
import os
import shutil
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-python-emit", Events, args)
    output_dir = args["--output"]
    verbose.emit(Events.STARTED, message=f"emitting to {output_dir}")
    # Read and discard model JSON from stdin (required by contract)
    sys.stdin.read()
    os.makedirs(output_dir, exist_ok=True)
    runtime_dir = os.path.join(os.path.dirname(__file__), "runtime")
    shutil.copy2(os.path.join(runtime_dir, "main.py"), os.path.join(output_dir, "main.py"))
    verbose.emit(Events.FINISHED, message="done")
```

- [ ] **Step 4: Create `src/plcc/lang/ext/python/run.py`**

```python
"""plcc-python-run
    Run a generated Python interpreter.

Usage:
    plcc-python-run --output=DIR [options]

Options:
    --output=DIR    Directory containing generated Python files.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS

import enum
import os
import subprocess
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-python-run", Events, args)
    output_dir = args["--output"]
    main_py = os.path.join(output_dir, "main.py")
    verbose.emit(Events.STARTED, message=f"running {main_py}")
    result = subprocess.run(
        [sys.executable, main_py],
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    verbose.emit(Events.FINISHED, message=f"exit {result.returncode}")
    sys.exit(result.returncode)
```

- [ ] **Step 5: Add console scripts to `pyproject.toml`**

```toml
plcc-python-emit = "plcc.lang.ext.python.emit:main"
plcc-python-run = "plcc.lang.ext.python.run:main"
```

- [ ] **Step 6: Reinstall and verify**

```bash
pdm install -q && plcc-python-emit --help && plcc-python-run --help
```

- [ ] **Step 7: Write BATS command tests**

Create `tests/bats/commands/plcc-python-emit.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial-python.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
}

teardown() { rm -rf "${WORK_DIR}" "${SPEC_JSON}" "${MODEL_JSON}"; }

@test "plcc-python-emit is on PATH" { command -v plcc-python-emit; }

@test "plcc-python-emit produces main.py" {
    plcc-python-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
    [ -f "${WORK_DIR}/main.py" ]
}

@test "plcc-python-emit accepts --verbose" {
    run bash -c "plcc-python-emit --output='${WORK_DIR}' --verbose=1 < '${MODEL_JSON}'"
    [ "$status" -eq 0 ]
}
```

Create `tests/bats/commands/plcc-python-run.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial-python.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
    plcc-python-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
}

teardown() { rm -rf "${WORK_DIR}" "${SPEC_JSON}" "${MODEL_JSON}"; }

@test "plcc-python-run is on PATH" { command -v plcc-python-run; }

@test "plcc-python-run evaluates parse-tree JSONL" {
    TREE='{"kind":"tree","rule":"program","children":[]}'
    run bash -c "echo '${TREE}' | plcc-python-run --output='${WORK_DIR}'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"evaluated"* ]]
}
```

- [ ] **Step 8: Run tests**

```bash
bin/test/commands.bash
```

- [ ] **Step 9: Commit**

```bash
git add src/plcc/lang/ext/python/ tests/bats/commands/plcc-python-emit.bats tests/bats/commands/plcc-python-run.bats pyproject.toml
git commit -m "feat(lang): add Python language plugin stubs (emit + run)"
```

---

### Task 8: Java language plugin

**Files:**
- Create: `src/plcc/lang/ext/java/__init__.py`
- Create: `src/plcc/lang/ext/java/emit.py`
- Create: `src/plcc/lang/ext/java/build.py`
- Create: `src/plcc/lang/ext/java/run.py`
- Create: `src/plcc/lang/ext/java/runtime/Main.java`
- Modify: `pyproject.toml`

- [ ] **Step 1: Create `src/plcc/lang/ext/java/__init__.py`**

```python
```

(Empty file.)

- [ ] **Step 2: Create the stub runtime template**

Create `src/plcc/lang/ext/java/runtime/Main.java`:

```java
import java.io.BufferedReader;
import java.io.InputStreamReader;

public class Main {
    public static void main(String[] args) throws Exception {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line;
        while ((line = reader.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty()) continue;
            // Stub: just acknowledge each tree
            System.out.println("evaluated: program (tree)");
            System.out.flush();
        }
    }
}
```

- [ ] **Step 3: Create `src/plcc/lang/ext/java/emit.py`**

```python
"""plcc-java-emit
    Emit a stub Java interpreter from model JSON.

Usage:
    plcc-java-emit --output=DIR [options]

Options:
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS

import enum
import os
import shutil
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-java-emit", Events, args)
    output_dir = args["--output"]
    verbose.emit(Events.STARTED, message=f"emitting to {output_dir}")
    sys.stdin.read()
    os.makedirs(output_dir, exist_ok=True)
    runtime_dir = os.path.join(os.path.dirname(__file__), "runtime")
    shutil.copy2(os.path.join(runtime_dir, "Main.java"), os.path.join(output_dir, "Main.java"))
    verbose.emit(Events.FINISHED, message="done")
```

- [ ] **Step 4: Create `src/plcc/lang/ext/java/build.py`**

```python
"""plcc-java-build
    Compile generated Java source files.

Usage:
    plcc-java-build --output=DIR [options]

Options:
    --output=DIR    Directory containing generated Java files.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS

import enum
import glob
import os
import subprocess
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-java-build", Events, args)
    output_dir = args["--output"]
    verbose.emit(Events.STARTED, message=f"compiling in {output_dir}")
    java_files = glob.glob(os.path.join(output_dir, "*.java"))
    if not java_files:
        verbose.emit(Events.FINISHED, message="no .java files found")
        return
    result = subprocess.run(["javac"] + java_files, cwd=output_dir)
    if result.returncode != 0:
        print("plcc-java-build: javac failed", file=sys.stderr)
        sys.exit(result.returncode)
    verbose.emit(Events.FINISHED, message="done")
```

- [ ] **Step 5: Create `src/plcc/lang/ext/java/run.py`**

```python
"""plcc-java-run
    Run a compiled Java interpreter.

Usage:
    plcc-java-run --output=DIR [options]

Options:
    --output=DIR    Directory containing compiled Java class files.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS

import enum
import subprocess
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-java-run", Events, args)
    output_dir = args["--output"]
    verbose.emit(Events.STARTED, message=f"running Main in {output_dir}")
    result = subprocess.run(
        ["java", "-cp", output_dir, "Main"],
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    verbose.emit(Events.FINISHED, message=f"exit {result.returncode}")
    sys.exit(result.returncode)
```

- [ ] **Step 6: Add console scripts to `pyproject.toml`**

```toml
plcc-java-emit  = "plcc.lang.ext.java.emit:main"
plcc-java-build = "plcc.lang.ext.java.build:main"
plcc-java-run   = "plcc.lang.ext.java.run:main"
```

- [ ] **Step 7: Reinstall and verify**

```bash
pdm install -q && plcc-java-emit --help && plcc-java-build --help && plcc-java-run --help
```

- [ ] **Step 8: Write BATS command tests**

Create `tests/bats/commands/plcc-java-emit.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial-java.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
}

teardown() { rm -rf "${WORK_DIR}" "${SPEC_JSON}" "${MODEL_JSON}"; }

@test "plcc-java-emit is on PATH" { command -v plcc-java-emit; }

@test "plcc-java-emit produces Main.java" {
    plcc-java-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
    [ -f "${WORK_DIR}/Main.java" ]
}
```

Create `tests/bats/commands/plcc-java-build.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    if ! command -v javac &>/dev/null; then skip "JDK not available"; fi
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial-java.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
    plcc-java-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
}

teardown() { rm -rf "${WORK_DIR}" "${SPEC_JSON}" "${MODEL_JSON}"; }

@test "plcc-java-build is on PATH" { command -v plcc-java-build; }

@test "plcc-java-build compiles Main.java" {
    run plcc-java-build --output="${WORK_DIR}"
    [ "$status" -eq 0 ]
    [ -f "${WORK_DIR}/Main.class" ]
}
```

Create `tests/bats/commands/plcc-java-run.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    if ! command -v javac &>/dev/null; then skip "JDK not available"; fi
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial-java.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
    plcc-java-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
    plcc-java-build --output="${WORK_DIR}"
}

teardown() { rm -rf "${WORK_DIR}" "${SPEC_JSON}" "${MODEL_JSON}"; }

@test "plcc-java-run is on PATH" { command -v plcc-java-run; }

@test "plcc-java-run evaluates parse-tree JSONL" {
    TREE='{"kind":"tree","rule":"program","children":[]}'
    run bash -c "echo '${TREE}' | plcc-java-run --output='${WORK_DIR}'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"evaluated"* ]]
}
```

- [ ] **Step 9: Run tests**

```bash
bin/test/commands.bash
```

- [ ] **Step 10: Commit**

```bash
git add src/plcc/lang/ext/java/ tests/bats/commands/plcc-java-emit.bats tests/bats/commands/plcc-java-build.bats tests/bats/commands/plcc-java-run.bats pyproject.toml
git commit -m "feat(lang): add Java language plugin stubs (emit + build + run)"
```

---

## Part 4 — Dispatchers

### Task 9: `plcc-lang-run` dispatcher

**Files:**
- Create: `src/plcc/lang/run.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Create `src/plcc/lang/run.py`**

```python
"""plcc-lang-run
    Dispatch to the appropriate plcc-<lang>-run command.

Usage:
    plcc-lang-run --target=LANG --output=DIR [options]

Options:
    --target=LANG   Target language (e.g. Python, Java).
    --output=DIR    Directory containing built artifacts.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS

import enum
import shutil
import subprocess
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-lang-run", Events, args)
    lang = args["--target"]
    output = args["--output"]
    cmd = f"plcc-{lang.lower()}-run"
    if not shutil.which(cmd):
        # No-op pattern: exit 0 silently if no runner for this language
        sys.exit(0)
    verbose.emit(Events.STARTED, message=f"dispatching to {cmd}")
    child_cmd = [cmd, f"--output={output}"] + verbose.child_flags()
    result = subprocess.run(child_cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
    verbose.emit(Events.FINISHED, message=f"exit {result.returncode}")
    sys.exit(result.returncode)
```

- [ ] **Step 2: Add console script to `pyproject.toml`**

```toml
plcc-lang-run = "plcc.lang.run:main"
```

- [ ] **Step 3: Reinstall and verify**

```bash
pdm install -q && plcc-lang-run --help
```

- [ ] **Step 4: Write BATS command test**

Create `tests/bats/commands/plcc-lang-run.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial-python.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
    plcc-python-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
}

teardown() { rm -rf "${WORK_DIR}" "${SPEC_JSON}" "${MODEL_JSON}"; }

@test "plcc-lang-run is on PATH" { command -v plcc-lang-run; }

@test "plcc-lang-run --help exits 0" {
    run plcc-lang-run --help
    [ "$status" -eq 0 ]
}

@test "plcc-lang-run dispatches to plcc-python-run" {
    TREE='{"kind":"tree","rule":"program","children":[]}'
    run bash -c "echo '${TREE}' | plcc-lang-run --target=Python --output='${WORK_DIR}'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"evaluated"* ]]
}

@test "plcc-lang-run exits 0 for missing runner (no-op)" {
    run plcc-lang-run --target=PlantUML --output="${WORK_DIR}" < /dev/null
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 5: Run and verify**

```bash
bin/test/commands.bash
```

- [ ] **Step 6: Commit**

```bash
git add src/plcc/lang/run.py tests/bats/commands/plcc-lang-run.bats pyproject.toml
git commit -m "feat(lang): add plcc-lang-run dispatcher (no-op for missing runners)"
```

---

### Task 10: Rewrite `plcc-tree` as dispatcher

**Files:**
- Modify: `src/plcc/tree/tree_cli.py`
- Modify: `tests/bats/commands/plcc-tree.bats`
- Modify: `tests/bats/integration/tokens-tree.bats`

- [ ] **Step 1: Rewrite `src/plcc/tree/tree_cli.py`**

```python
"""plcc-tree
    Dispatch to a parser plugin. Reads token JSONL, emits a parse tree.

Usage:
    plcc-tree [options] --ll1=LL1_JSON

Options:
    --ll1=LL1_JSON          Path to LL(1) analysis JSON (required).
    --parser=KIND           Parser plugin to use [default: table].
    -h --help               Show this message.
""" + VERBOSE_OPTIONS

import enum
import shutil
import subprocess
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-tree", Events, args)
    ll1_path = args["--ll1"]
    parser_kind = args["--parser"]
    cmd = f"plcc-parser-{parser_kind}"
    if not shutil.which(cmd):
        print(
            f"plcc-tree: parser plugin '{cmd}' not found on PATH.\n"
            f"Run plcc-parser-list to see what is available.",
            file=sys.stderr,
        )
        sys.exit(1)
    verbose.emit(Events.STARTED, message=f"dispatching to {cmd}")
    child_cmd = [cmd, f"--ll1={ll1_path}"] + verbose.child_flags()
    result = subprocess.run(child_cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
    verbose.emit(Events.FINISHED, message=f"exit {result.returncode}")
    sys.exit(result.returncode)
```

- [ ] **Step 2: Update `tests/bats/commands/plcc-tree.bats`**

Replace the entire file:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    TREE_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/tree.schema.json"
    SPEC_JSON="$(mktemp)"
    LL1_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    plcc-ll1 "${SPEC_JSON}" > "${LL1_JSON}"
}

teardown() { rm -f "${SPEC_JSON}" "${LL1_JSON}"; }

@test "plcc-tree is on PATH" { command -v plcc-tree; }

@test "plcc-tree --help exits 0" {
    run plcc-tree --help
    [ "$status" -eq 0 ]
}

@test "plcc-tree requires --ll1" {
    run bash -c "echo '{}' | plcc-tree"
    [ "$status" -ne 0 ]
}

@test "plcc-tree dispatches to plcc-parser-table by default" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-tree --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${TREE_SCHEMA}" -
}

@test "plcc-tree errors on missing parser plugin" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-tree --ll1='${LL1_JSON}' --parser=nonexistent 2>&1"
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]]
}

@test "plcc-tree passes error records through" {
    ERROR='{"kind":"error","stage":"plcc-tokens","source":{"file":null,"line":1,"column":1}}'
    run bash -c "echo '${ERROR}' | plcc-tree --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | python3 -c "import json,sys; r=json.load(sys.stdin); assert 'error' in json.dumps(r)"
}

@test "plcc-tree accepts --verbose without error" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-tree --ll1='${LL1_JSON}' --verbose=1"
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 3: Update `tests/bats/integration/tokens-tree.bats`**

Read the file first, then update `--spec` references to `--ll1`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    TREE_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/tree.schema.json"
    SPEC_JSON="$(mktemp)"
    LL1_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    plcc-ll1 "${SPEC_JSON}" > "${LL1_JSON}"
}

teardown() { rm -f "${SPEC_JSON}" "${LL1_JSON}"; }

@test "plcc-tokens | plcc-tree produces schema-valid tree" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-tree --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${TREE_SCHEMA}" -
}
```

- [ ] **Step 4: Run all tests**

```bash
bin/test/functional.bash
```

Expected: all pass. The old `plcc-tree` tests now use the new interface.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/tree/tree_cli.py tests/bats/commands/plcc-tree.bats tests/bats/integration/tokens-tree.bats
git commit -m "refactor(tree): rewrite plcc-tree as parser dispatcher (--ll1, --parser)"
```

---

## Part 5 — Add Verbose to Existing Commands

### Task 11: Add verbose flags to existing Level 0 commands

**Files:**
- Modify: `src/plcc/spec/plcc_spec_cli.py`
- Modify: `src/plcc/tokens/tokens_cli.py`
- Modify: `src/plcc/model/model_cli.py`
- Modify: `src/plcc/lang/emit.py`
- Modify: `src/plcc/lang/build.py`
- Modify: `src/plcc/lang/list.py`
- Modify: `src/plcc/lang/ext/plantuml/emit.py`

Each command gets the same treatment: add `+ VERBOSE_OPTIONS` to the docstring, import `VerboseContext` and `VERBOSE_OPTIONS`, create a `VerboseContext` in `main()`, and for dispatchers, forward `verbose.child_flags()` to children.

- [ ] **Step 1: Update `src/plcc/spec/plcc_spec_cli.py`**

Add to imports:

```python
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
```

Append `+ VERBOSE_OPTIONS` to the module docstring (after the last `"""`). Add to `main()` after `args = docopt(...)`:

```python
import enum

class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"
```

Add in `main()` after `args = docopt(__doc__, argv)`:

```python
verbose = VerboseContext.from_args("plcc-spec", Events, args)
```

The docstring becomes:

```python
"""plcc-spec
    Parse, validate, and print a PLCC grammar file as JSON.

Usage:
    plcc-spec [options] FILE

Arguments:
    FILE    PLCC grammar file. Use - to read from stdin.

Options:
    --no-json       Do not print JSON to stdout.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS
```

- [ ] **Step 2: Apply the same pattern to `src/plcc/tokens/tokens_cli.py`**

Stage name: `"plcc-tokens"`. Same pattern: import, docstring append, create `VerboseContext` in `main()`.

- [ ] **Step 3: Apply to `src/plcc/model/model_cli.py`**

Stage name: `"plcc-model"`.

- [ ] **Step 4: Apply to `src/plcc/lang/emit.py`**

Stage name: `"plcc-lang-emit"`. This is a dispatcher — also forward `verbose.child_flags()` to the child subprocess. Change the `subprocess.run` call to include the verbose flags:

```python
result = subprocess.run(
    [cmd, f'--output={output}'] + verbose.child_flags(),
    stdin=sys.stdin,
)
```

- [ ] **Step 5: Apply to `src/plcc/lang/build.py`**

Stage name: `"plcc-lang-build"`. Also forward `verbose.child_flags()`:

```python
result = subprocess.run([cmd, f'--output={output}'] + verbose.child_flags())
```

- [ ] **Step 6: Apply to `src/plcc/lang/list.py`**

Stage name: `"plcc-lang-list"`. No children to forward to — just accept the flags.

- [ ] **Step 7: Apply to `src/plcc/lang/ext/plantuml/emit.py`**

Stage name: `"plcc-plantuml-emit"`.

- [ ] **Step 8: Run all tests**

```bash
bin/test/functional.bash
```

Expected: all pass. Existing tests should not break since the new flags have defaults.

- [ ] **Step 9: Commit**

```bash
git add src/plcc/spec/plcc_spec_cli.py src/plcc/tokens/tokens_cli.py src/plcc/model/model_cli.py src/plcc/lang/emit.py src/plcc/lang/build.py src/plcc/lang/list.py src/plcc/lang/ext/plantuml/emit.py
git commit -m "feat(verbose): add --verbose/--verbose-format to all existing Level 0 commands"
```

---

## Part 6 — Level 2 Orchestrators

### Task 12: Update `plcc-make` with ll1 step and Level 2 verbose

**Files:**
- Modify: `src/plcc/cmd/make.py`
- Modify: `tests/bats/commands/plcc-make.bats`
- Modify: `tests/bats/e2e/happy-path.bats`

- [ ] **Step 1: Rewrite `src/plcc/cmd/make.py`**

```python
"""plcc-make
    Build a PLCC project from a grammar file.

Usage:
    plcc-make [options] GRAMMAR

Arguments:
    GRAMMAR     Path to the PLCC grammar file.

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS

import contextlib
import enum
import json
import os
import re
import shutil
import subprocess
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

_TOOL_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')


class Events(enum.Enum):
    STARTED = "started"
    PHASE = "phase"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-make", Events, args)
    grammar = args['GRAMMAR']
    build_dir = 'build'

    verbose.emit(Events.STARTED, message=f"building {grammar}")

    # 1. Clean
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    # 2. Spec
    verbose.emit(Events.PHASE, message="spec")
    spec_json = os.path.join(build_dir, 'spec.json')
    _run_or_die(['plcc-spec', grammar] + child_flags, stdout_file=spec_json, verbose=verbose)

    # 3. LL(1)
    verbose.emit(Events.PHASE, message="ll1")
    ll1_json = os.path.join(build_dir, 'll1.json')
    _run_or_die(['plcc-ll1', spec_json] + child_flags, stdout_file=ll1_json, verbose=verbose)

    # 4. Model
    verbose.emit(Events.PHASE, message="model")
    model_json = os.path.join(build_dir, 'model.json')
    _run_or_die(['plcc-model', spec_json] + child_flags, stdout_file=model_json, verbose=verbose)

    # 5 & 6. Emit and build per semantic section
    with open(spec_json) as f:
        spec = json.load(f)
    for section in spec.get('semantics', []):
        tool = section['tool']
        lang = section['language']
        try:
            validate_tool_name(tool)
        except ValueError as e:
            print(f"plcc-make: {e}", file=sys.stderr)
            sys.exit(1)
        output_dir = os.path.join(build_dir, tool)
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

    verbose.emit(Events.FINISHED, message="done")


def validate_tool_name(name):
    if not name or not _TOOL_NAME_RE.match(name):
        raise ValueError(
            f"Invalid tool name '{name}'. "
            "Tool names must match [a-zA-Z0-9_-]+ to prevent path traversal."
        )


def _run_or_die(cmd, stdout_file=None, stdin_file=None, verbose=None):
    with contextlib.ExitStack() as stack:
        stdin = stack.enter_context(open(stdin_file)) if stdin_file else None
        stdout = stack.enter_context(open(stdout_file, 'w')) if stdout_file else None
        result = subprocess.run(cmd, stdin=stdin, stdout=stdout, stderr=subprocess.PIPE)
    if verbose and result.stderr:
        events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
        verbose.reformat_child_events(events)
    if result.returncode != 0:
        print(f"plcc-make: {cmd[0]} failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)
```

- [ ] **Step 2: Update `tests/bats/commands/plcc-make.bats`**

Add a test for `build/ll1.json`:

```bash
@test "plcc-make plantuml_only grammar produces ll1.json" {
    run plcc-make "${FIXTURES}/plantuml_only.plcc"
    [ "$status" -eq 0 ]
    [ -f "${WORK_DIR}/build/ll1.json" ]
}

@test "plcc-make accepts --verbose" {
    run plcc-make --verbose=1 "${FIXTURES}/plantuml_only.plcc"
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 3: Update `tests/bats/e2e/happy-path.bats`**

Add ll1.json check to the existing setup/tests:

```bash
@test "plcc-make produces build/ll1.json" {
    [ -f build/ll1.json ]
}
```

- [ ] **Step 4: Run all tests**

```bash
bin/test/functional.bash
```

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/make.py tests/bats/commands/plcc-make.bats tests/bats/e2e/happy-path.bats
git commit -m "feat(make): add plcc-ll1 step and Level 2 verbose propagation"
```

---

### Task 13: `plcc-scan` connected skeleton

**Files:**
- Modify: `src/plcc/cmd/scan.py`
- Delete: `tests/bats/commands/plcc-skeletons.bats`
- Create: `tests/bats/commands/plcc-scan.bats`

- [ ] **Step 1: Rewrite `src/plcc/cmd/scan.py`**

```python
"""plcc-scan
    Tokenize source input and print tokens in human-readable format.

Usage:
    plcc-scan [options] GRAMMAR [SOURCE ...]

Arguments:
    GRAMMAR     Path to the PLCC grammar file.
    SOURCE      Source files to tokenize. Reads stdin if none given.

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS

import enum
import json
import os
import subprocess
import sys
import tempfile

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-scan", Events, args)
    grammar = args["GRAMMAR"]
    sources = args["SOURCE"]

    verbose.emit(Events.STARTED, message=f"scanning with {grammar}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        spec_path = f.name
    try:
        # plcc-spec grammar > spec.json
        result = subprocess.run(
            ["plcc-spec", grammar] + child_flags,
            stdout=open(spec_path, "w"),
            stderr=subprocess.PIPE,
        )
        if verbose and result.stderr:
            events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
            verbose.reformat_child_events(events)
        if result.returncode != 0:
            print(f"plcc-scan: plcc-spec failed (exit {result.returncode})", file=sys.stderr)
            sys.exit(result.returncode)

        # Build input: concatenate source files, then stdin
        input_data = b""
        for src in sources:
            with open(src, "rb") as sf:
                input_data += sf.read()
        if not sources:
            input_data = sys.stdin.buffer.read()

        # plcc-tokens spec.json < input
        result = subprocess.run(
            ["plcc-tokens", spec_path] + child_flags,
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if verbose and result.stderr:
            events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
            verbose.reformat_child_events(events)
        if result.returncode != 0:
            print(f"plcc-scan: plcc-tokens failed (exit {result.returncode})", file=sys.stderr)
            sys.exit(result.returncode)

        # Print tokens in human-readable format
        for line in result.stdout.decode("utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("kind") == "token":
                name = record.get("name", "?")
                lexeme = record.get("lexeme", "?")
                print(f"{name} '{lexeme}'")
            elif record.get("kind") == "error":
                print(f"ERROR: {record}")
    finally:
        os.unlink(spec_path)

    verbose.emit(Events.FINISHED, message="done")
```

- [ ] **Step 2: Delete `tests/bats/commands/plcc-skeletons.bats`**

```bash
git rm tests/bats/commands/plcc-skeletons.bats
```

- [ ] **Step 3: Create `tests/bats/commands/plcc-scan.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
}

@test "plcc-scan is on PATH" { command -v plcc-scan; }

@test "plcc-scan --help exits 0" {
    run plcc-scan --help
    [ "$status" -eq 0 ]
}

@test "plcc-scan tokenizes input" {
    run bash -c "echo '42' | plcc-scan '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
    [[ "$output" == *"42"* ]]
}

@test "plcc-scan reads from source file" {
    run plcc-scan "${FIXTURES}/trivial.plcc" "${FIXTURES}/trivial_input.txt"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
}

@test "plcc-scan accepts --verbose" {
    run bash -c "echo '42' | plcc-scan --verbose=1 '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 4: Run tests**

```bash
bin/test/functional.bash
```

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/scan.py tests/bats/commands/plcc-scan.bats
git rm tests/bats/commands/plcc-skeletons.bats
git commit -m "feat(scan): promote plcc-scan to connected skeleton with Level 2 verbose"
```

---

### Task 14: `plcc-parse` connected skeleton

**Files:**
- Modify: `src/plcc/cmd/parse.py`
- Create: `tests/bats/commands/plcc-parse.bats`

- [ ] **Step 1: Rewrite `src/plcc/cmd/parse.py`**

```python
"""plcc-parse
    Parse source input and print parse tree in human-readable format.

Usage:
    plcc-parse [options] GRAMMAR [SOURCE ...]

Arguments:
    GRAMMAR     Path to the PLCC grammar file.
    SOURCE      Source files to parse. Reads stdin if none given.

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS

import enum
import json
import os
import subprocess
import sys
import tempfile

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-parse", Events, args)
    grammar = args["GRAMMAR"]
    sources = args["SOURCE"]

    verbose.emit(Events.STARTED, message=f"parsing with {grammar}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    spec_path = tempfile.mktemp(suffix=".json")
    ll1_path = tempfile.mktemp(suffix=".json")
    try:
        # plcc-spec
        _run_child(["plcc-spec", grammar] + child_flags, stdout_file=spec_path, verbose=verbose, label="plcc-spec")
        # plcc-ll1
        _run_child(["plcc-ll1", spec_path] + child_flags, stdout_file=ll1_path, verbose=verbose, label="plcc-ll1")

        # Build input
        input_data = b""
        for src in sources:
            with open(src, "rb") as sf:
                input_data += sf.read()
        if not sources:
            input_data = sys.stdin.buffer.read()

        # plcc-tokens | plcc-tree
        tokens_proc = subprocess.Popen(
            ["plcc-tokens", spec_path] + child_flags,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        tree_proc = subprocess.Popen(
            ["plcc-tree", f"--ll1={ll1_path}"] + child_flags,
            stdin=tokens_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        tokens_proc.stdout.close()
        tokens_proc.stdin.write(input_data)
        tokens_proc.stdin.close()

        tree_out, tree_err = tree_proc.communicate()
        tokens_proc.wait()
        tokens_err = tokens_proc.stderr.read()

        # Reformat child verbose output
        for stderr_bytes in (tokens_err, tree_err):
            if stderr_bytes:
                events = verbose.parse_child_events(stderr_bytes.decode("utf-8", errors="replace"))
                verbose.reformat_child_events(events)

        if tokens_proc.returncode != 0:
            print(f"plcc-parse: plcc-tokens failed (exit {tokens_proc.returncode})", file=sys.stderr)
            sys.exit(tokens_proc.returncode)
        if tree_proc.returncode != 0:
            print(f"plcc-parse: plcc-tree failed (exit {tree_proc.returncode})", file=sys.stderr)
            sys.exit(tree_proc.returncode)

        # Print tree in human-readable format
        for line in tree_out.decode("utf-8").splitlines():
            if not line.strip():
                continue
            tree = json.loads(line)
            _print_tree(tree, indent=0)
    finally:
        for p in (spec_path, ll1_path):
            if os.path.exists(p):
                os.unlink(p)

    verbose.emit(Events.FINISHED, message="done")


def _run_child(cmd, stdout_file, verbose, label):
    with open(stdout_file, "w") as out:
        result = subprocess.run(cmd, stdout=out, stderr=subprocess.PIPE)
    if result.stderr:
        events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
        verbose.reformat_child_events(events)
    if result.returncode != 0:
        print(f"plcc-parse: {label} failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)


def _print_tree(node, indent):
    prefix = "  " * indent
    kind = node.get("kind", "?")
    if kind == "tree":
        rule = node.get("rule", "?")
        print(f"{prefix}{rule}")
        for child in node.get("children", []):
            _print_tree(child, indent + 1)
    elif kind == "token":
        name = node.get("name", "?")
        lexeme = node.get("lexeme", "?")
        print(f"{prefix}{name} '{lexeme}'")
    elif kind == "error":
        print(f"{prefix}ERROR: {node}")
```

- [ ] **Step 2: Create `tests/bats/commands/plcc-parse.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
}

@test "plcc-parse is on PATH" { command -v plcc-parse; }

@test "plcc-parse --help exits 0" {
    run plcc-parse --help
    [ "$status" -eq 0 ]
}

@test "plcc-parse parses input and prints tree" {
    run bash -c "echo '42' | plcc-parse '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"program"* ]]
}

@test "plcc-parse reads from source file" {
    run plcc-parse "${FIXTURES}/trivial.plcc" "${FIXTURES}/trivial_input.txt"
    [ "$status" -eq 0 ]
    [[ "$output" == *"program"* ]]
}

@test "plcc-parse accepts --verbose" {
    run bash -c "echo '42' | plcc-parse --verbose=1 '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 3: Run tests**

```bash
bin/test/functional.bash
```

- [ ] **Step 4: Commit**

```bash
git add src/plcc/cmd/parse.py tests/bats/commands/plcc-parse.bats
git commit -m "feat(parse): promote plcc-parse to connected skeleton with Level 2 verbose"
```

---

### Task 15: `plcc-rep` connected skeleton

**Files:**
- Modify: `src/plcc/cmd/rep.py`
- Create: `tests/bats/commands/plcc-rep.bats`

- [ ] **Step 1: Rewrite `src/plcc/cmd/rep.py`**

```python
"""plcc-rep
    REPL — read, eval, print loop for a PLCC grammar.

Usage:
    plcc-rep [options] GRAMMAR [SOURCE ...]

Arguments:
    GRAMMAR     Path to the PLCC grammar file.
    SOURCE      Source files to evaluate before entering interactive mode.

Options:
    --tool=NAME     Semantic section to run [default: Java].
    -h --help       Show this message.
""" + VERBOSE_OPTIONS

import enum
import json
import os
import subprocess
import sys
import tempfile

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-rep", Events, args)
    grammar = args["GRAMMAR"]
    sources = args["SOURCE"]
    tool_name = args["--tool"]

    verbose.emit(Events.STARTED, message=f"rep with {grammar}, tool={tool_name}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    spec_path = tempfile.mktemp(suffix=".json")
    ll1_path = tempfile.mktemp(suffix=".json")
    build_dir = tempfile.mkdtemp(prefix="plcc-rep-build-")
    try:
        # plcc-spec
        _run_child(["plcc-spec", grammar] + child_flags, stdout_file=spec_path, verbose=verbose, label="plcc-spec")
        # plcc-ll1
        _run_child(["plcc-ll1", spec_path] + child_flags, stdout_file=ll1_path, verbose=verbose, label="plcc-ll1")

        # Resolve tool -> language
        with open(spec_path) as f:
            spec = json.load(f)
        lang, tool_dir = _resolve_tool(spec, tool_name, build_dir)

        # Emit and build
        model_path = tempfile.mktemp(suffix=".json")
        _run_child(["plcc-model", spec_path] + child_flags, stdout_file=model_path, verbose=verbose, label="plcc-model")
        os.makedirs(tool_dir, exist_ok=True)
        _run_child_with_stdin(
            ["plcc-lang-emit", f"--target={lang}", f"--output={tool_dir}"] + child_flags,
            stdin_file=model_path, verbose=verbose, label="plcc-lang-emit",
        )
        _run_child(
            ["plcc-lang-build", f"--target={lang}", f"--output={tool_dir}"] + child_flags,
            verbose=verbose, label="plcc-lang-build",
        )

        # Build input
        input_data = b""
        for src in sources:
            with open(src, "rb") as sf:
                input_data += sf.read()
        if not sources:
            input_data = sys.stdin.buffer.read()

        # plcc-tokens | plcc-tree | plcc-lang-run
        tokens_proc = subprocess.Popen(
            ["plcc-tokens", spec_path] + child_flags,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        tree_proc = subprocess.Popen(
            ["plcc-tree", f"--ll1={ll1_path}"] + child_flags,
            stdin=tokens_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        tokens_proc.stdout.close()
        run_proc = subprocess.Popen(
            ["plcc-lang-run", f"--target={lang}", f"--output={tool_dir}"] + child_flags,
            stdin=tree_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        tree_proc.stdout.close()

        tokens_proc.stdin.write(input_data)
        tokens_proc.stdin.close()

        run_out, run_err = run_proc.communicate()
        tree_proc.wait()
        tokens_proc.wait()

        # Reformat child verbose output
        for proc in (tokens_proc, tree_proc):
            stderr_bytes = proc.stderr.read()
            if stderr_bytes:
                events = verbose.parse_child_events(stderr_bytes.decode("utf-8", errors="replace"))
                verbose.reformat_child_events(events)
        if run_err:
            events = verbose.parse_child_events(run_err.decode("utf-8", errors="replace"))
            verbose.reformat_child_events(events)

        # Print evaluation output
        sys.stdout.buffer.write(run_out)
        sys.stdout.flush()

        if os.path.exists(model_path):
            os.unlink(model_path)
    finally:
        for p in (spec_path, ll1_path):
            if os.path.exists(p):
                os.unlink(p)
        import shutil
        shutil.rmtree(build_dir, ignore_errors=True)

    verbose.emit(Events.FINISHED, message="done")


def _resolve_tool(spec, tool_name, build_dir):
    for section in spec.get("semantics", []):
        if section["tool"] == tool_name:
            return section["language"], os.path.join(build_dir, tool_name)
    print(f"plcc-rep: no semantic section with tool '{tool_name}' found", file=sys.stderr)
    sys.exit(1)


def _run_child(cmd, stdout_file=None, verbose=None, label="child"):
    kwargs = {"stderr": subprocess.PIPE}
    if stdout_file:
        kwargs["stdout"] = open(stdout_file, "w")
    result = subprocess.run(cmd, **kwargs)
    if stdout_file and "stdout" in kwargs:
        kwargs["stdout"].close()
    if result.stderr:
        events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
        verbose.reformat_child_events(events)
    if result.returncode != 0:
        print(f"plcc-rep: {label} failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)


def _run_child_with_stdin(cmd, stdin_file, verbose=None, label="child"):
    with open(stdin_file) as f:
        result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE)
    if result.stderr:
        events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
        verbose.reformat_child_events(events)
    if result.returncode != 0:
        print(f"plcc-rep: {label} failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)
```

- [ ] **Step 2: Create `tests/bats/commands/plcc-rep.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
}

@test "plcc-rep is on PATH" { command -v plcc-rep; }

@test "plcc-rep --help exits 0" {
    run plcc-rep --help
    [ "$status" -eq 0 ]
}

@test "plcc-rep evaluates with Python tool" {
    run bash -c "echo '42' | plcc-rep --tool=py '${FIXTURES}/trivial-python.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"evaluated"* ]]
}

@test "plcc-rep errors on missing tool" {
    run bash -c "echo '42' | plcc-rep --tool=nonexistent '${FIXTURES}/trivial-python.plcc' 2>&1"
    [ "$status" -ne 0 ]
    [[ "$output" == *"no semantic section"* ]]
}

@test "plcc-rep accepts --verbose" {
    run bash -c "echo '42' | plcc-rep --tool=py --verbose=1 '${FIXTURES}/trivial-python.plcc'"
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 3: Run tests**

```bash
bin/test/functional.bash
```

- [ ] **Step 4: Commit**

```bash
git add src/plcc/cmd/rep.py tests/bats/commands/plcc-rep.bats
git commit -m "feat(rep): promote plcc-rep to connected skeleton with --tool and Level 2 verbose"
```

---

## Part 7 — Integration Tests and Final Verification

### Task 16: New integration tests

**Files:**
- Create: `tests/bats/integration/spec-ll1.bats`
- Create: `tests/bats/integration/ll1-tree.bats`

- [ ] **Step 1: Create `tests/bats/integration/spec-ll1.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    LL1_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/ll1.schema.json"
}

@test "plcc-spec | plcc-ll1 produces schema-valid ll1 JSON" {
    run bash -c "plcc-spec '${FIXTURES}/trivial.plcc' | plcc-ll1"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${LL1_SCHEMA}" -
}
```

- [ ] **Step 2: Create `tests/bats/integration/ll1-tree.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    TREE_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/tree.schema.json"
    SPEC_JSON="$(mktemp)"
    LL1_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    plcc-ll1 "${SPEC_JSON}" > "${LL1_JSON}"
}

teardown() { rm -f "${SPEC_JSON}" "${LL1_JSON}"; }

@test "plcc-tokens | plcc-tree with ll1 produces schema-valid tree" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-tree --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${TREE_SCHEMA}" -
}
```

- [ ] **Step 3: Run integration tests**

```bash
bin/test/integration.bash
```

- [ ] **Step 4: Commit**

```bash
git add tests/bats/integration/spec-ll1.bats tests/bats/integration/ll1-tree.bats
git commit -m "test(integration): add spec|ll1 and ll1|tree pipeline pair tests"
```

---

### Task 17: Update e2e tests for full pipeline

**Files:**
- Modify: `tests/bats/e2e/happy-path.bats`

- [ ] **Step 1: Add full-pipeline e2e test**

Add these tests to `tests/bats/e2e/happy-path.bats`:

```bash
@test "plcc-make trivial-full produces build output for all three languages" {
    FULL_DIR="$(mktemp -d)"
    cd "${FULL_DIR}"
    plcc-make "${FIXTURES}/trivial-full.plcc"
    [ -f build/ll1.json ]
    [ -d build/Java ]
    [ -d build/py ]
    [ -d build/diagram ]
    rm -rf "${FULL_DIR}"
}
```

- [ ] **Step 2: Run e2e tests**

```bash
bin/test/e2e.bash
```

- [ ] **Step 3: Commit**

```bash
git add tests/bats/e2e/happy-path.bats
git commit -m "test(e2e): verify plcc-make produces output for all three language plugins"
```

---

### Task 18: Clean up old test references and run full suite

**Files:**
- Modify: `src/plcc/tree/tree_cli_test.py` (if it references old `--spec` interface)
- Modify: `src/plcc/cmd/make_test.py` (if it references old make behavior)
- Modify: `src/plcc/cmd/skeleton_test.py` (if it tests old stub behavior)

- [ ] **Step 1: Check for stale unit tests**

```bash
grep -r '\-\-spec' src/plcc/tree/ src/plcc/cmd/
```

Fix any references to the old `--spec` flag. Update or remove tests for the old stub behavior.

- [ ] **Step 2: Run the full test suite**

```bash
bin/test/all.bash
```

Expected: all tests pass. The test count should be higher than Task 1 (new tests added, no tests lost).

- [ ] **Step 3: Commit any remaining fixes**

```bash
git add -u
git commit -m "test: update stale test references for skeleton update"
```

---

### Task 19: Packaging verification

**Files:**
- Run only: `bin/test/packaging.bash`

- [ ] **Step 1: Run the packaging test**

```bash
bin/test/packaging.bash
```

This builds a wheel, installs it into a fresh venv, and verifies all entry points resolve. All 21 console scripts should be present:

```
plcc-spec, plcc-tokens, plcc-tree, plcc-model, plcc-ll1,
plcc-parser-table, plcc-parser-list,
plcc-lang-emit, plcc-lang-build, plcc-lang-run, plcc-lang-list,
plcc-plantuml-emit, plcc-python-emit, plcc-python-run,
plcc-java-emit, plcc-java-build, plcc-java-run,
plcc-make, plcc-scan, plcc-parse, plcc-rep
```

- [ ] **Step 2: Fix any packaging issues**

If any entry point fails to resolve, check `pyproject.toml` for typos in the `[project.scripts]` section.

- [ ] **Step 3: Final commit if needed**

```bash
git add -u
git commit -m "fix: resolve packaging issues from skeleton update"
```

---

## Summary

| Part | Tasks | What it delivers |
|---|---|---|
| 1. Foundation | 1–3 | Green bar, fixtures, verbose module |
| 2. Leaf stubs | 4–6 | `plcc-ll1`, `plcc-parser-table`, `plcc-parser-list` |
| 3. Language plugins | 7–8 | Python and Java plugin stubs |
| 4. Dispatchers | 9–10 | `plcc-lang-run`, `plcc-tree` rewrite |
| 5. Verbose retrofit | 11 | All existing commands accept verbose flags |
| 6. Level 2 orchestrators | 12–15 | `plcc-make` updated, `plcc-scan`/`plcc-parse`/`plcc-rep` connected |
| 7. Integration & verification | 16–19 | New integration/e2e tests, packaging check |
