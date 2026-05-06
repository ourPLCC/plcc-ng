# plcc-scan Issues (003, 004, 002, 001) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve `plcc-scan` and related Level 2 commands across four sequential PRs: add a `--help` hint to brief usage (003), accept `-` as stdin (004), continue scanning past lex errors (002), and stream tokens interactively (001).

**Architecture:** Each issue is its own branch and PR, implemented in order 003 → 004 → 002 → 001. Issues 003 and 004 touch multiple Level 2 commands uniformly. Issue 002 adds a `--continue-on-error` flag to `plcc-tokens` and updates `plcc-scan` to use it. Issue 001 replaces `subprocess.run()` with `Popen` + threading in `plcc-scan` for incremental output.

**Tech Stack:** Python 3, docopt-ng 0.9.0, subprocess, threading, pytest (unit tests via `bin/test/units.bash`), bats (CLI tests via `bin/test/commands.bash`)

---

## PR 1 — Issue 003: Brief usage message mentions `--help`

When `plcc-scan`, `plcc-parse`, or `plcc-rep` is invoked with wrong or missing arguments, docopt-ng raises `DocoptExit` (a `SystemExit` subclass) whose message is only the `Usage:` pattern — with no hint that `--help` exists. The fix intercepts `DocoptExit` before it propagates, appends the hint, and re-raises.

### Task 1: plcc-scan — hint in brief usage

**Files:**
- Modify: `tests/bats/commands/plcc-scan.bats`
- Modify: `src/plcc/cmd/scan.py`

- [ ] **Step 1: Add failing bats test**

Add to `tests/bats/commands/plcc-scan.bats`:

```bash
@test "plcc-scan brief usage mentions --help" {
    run --separate-stderr plcc-scan
    [[ "$stderr" == *"--help"* ]]
}
```

- [ ] **Step 2: Run to confirm failure**

```
bin/test/commands.bash tests/bats/commands/plcc-scan.bats
```

Expected: FAIL on `plcc-scan brief usage mentions --help`.

- [ ] **Step 3: Fix scan.py**

In `src/plcc/cmd/scan.py`, change the import line:

```python
from docopt import docopt
```

to:

```python
from docopt import docopt, DocoptExit
```

In `main()`, replace:

```python
    args = docopt(__doc__, argv)
```

with:

```python
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print("Run 'plcc-scan --help' for more information.", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 4: Run to confirm pass**

```
bin/test/commands.bash tests/bats/commands/plcc-scan.bats
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/bats/commands/plcc-scan.bats src/plcc/cmd/scan.py
git commit -m "fix(scan): brief usage mentions --help"
```

---

### Task 2: plcc-parse — hint in brief usage

**Files:**
- Modify: `tests/bats/commands/plcc-parse.bats`
- Modify: `src/plcc/cmd/parse.py`

- [ ] **Step 1: Add failing bats test**

Add to `tests/bats/commands/plcc-parse.bats`:

```bash
@test "plcc-parse brief usage mentions --help" {
    run --separate-stderr plcc-parse
    [[ "$stderr" == *"--help"* ]]
}
```

- [ ] **Step 2: Run to confirm failure**

```
bin/test/commands.bash tests/bats/commands/plcc-parse.bats
```

Expected: FAIL on `plcc-parse brief usage mentions --help`.

- [ ] **Step 3: Fix parse.py**

In `src/plcc/cmd/parse.py`, change:

```python
from docopt import docopt
```

to:

```python
from docopt import docopt, DocoptExit
```

In `main()`, replace:

```python
    args = docopt(__doc__, argv)
```

with:

```python
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print("Run 'plcc-parse --help' for more information.", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 4: Run to confirm pass**

```
bin/test/commands.bash tests/bats/commands/plcc-parse.bats
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/bats/commands/plcc-parse.bats src/plcc/cmd/parse.py
git commit -m "fix(parse): brief usage mentions --help"
```

---

### Task 3: plcc-rep — hint in brief usage

**Files:**
- Modify: `tests/bats/commands/plcc-rep.bats`
- Modify: `src/plcc/cmd/rep.py`

- [ ] **Step 1: Add failing bats test**

Add to `tests/bats/commands/plcc-rep.bats`:

```bash
@test "plcc-rep brief usage mentions --help" {
    run --separate-stderr plcc-rep
    [[ "$stderr" == *"--help"* ]]
}
```

- [ ] **Step 2: Run to confirm failure**

```
bin/test/commands.bash tests/bats/commands/plcc-rep.bats
```

Expected: FAIL on `plcc-rep brief usage mentions --help`.

- [ ] **Step 3: Fix rep.py**

In `src/plcc/cmd/rep.py`, change:

```python
from docopt import docopt
```

to:

```python
from docopt import docopt, DocoptExit
```

In `main()`, replace:

```python
    args = docopt(__doc__, argv)
```

with:

```python
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print("Run 'plcc-rep --help' for more information.", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 4: Run to confirm pass**

```
bin/test/commands.bash tests/bats/commands/plcc-rep.bats
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/bats/commands/plcc-rep.bats src/plcc/cmd/rep.py
git commit -m "fix(rep): brief usage mentions --help"
```

---

## PR 2 — Issue 004: Accept `-` as stdin

`plcc-scan` and `plcc-parse` read named SOURCE files, falling back to stdin only when no sources are given. Adding `-` support means treating `-` in the source list as "read from stdin at this position." `plcc-rep` is deferred.

The input-reading loop in both commands currently:
```python
input_data = b""
for src in sources:
    with open(src, "rb") as sf:
        input_data += sf.read()
if not sources:
    input_data = sys.stdin.buffer.read()
```

Replace with:
```python
input_data = b""
for src in sources:
    if src == '-':
        input_data += sys.stdin.buffer.read()
    else:
        with open(src, "rb") as sf:
            input_data += sf.read()
if not sources:
    input_data = sys.stdin.buffer.read()
```

### Task 4: plcc-scan — accept `-` as stdin

**Files:**
- Modify: `tests/bats/commands/plcc-scan.bats`
- Modify: `src/plcc/cmd/scan.py`

- [ ] **Step 1: Add failing bats tests**

Add to `tests/bats/commands/plcc-scan.bats`:

```bash
@test "plcc-scan accepts '-' as stdin" {
    run bash -c "echo '42' | plcc-scan '${FIXTURES}/trivial.plcc' -"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
    [[ "$output" == *"42"* ]]
}

@test "plcc-scan '-' interleaved with file reads both" {
    run bash -c "echo '99' | plcc-scan '${FIXTURES}/trivial.plcc' '${FIXTURES}/trivial_input.txt' -"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"99"* ]]
}
```

- [ ] **Step 2: Run to confirm failure**

```
bin/test/commands.bash tests/bats/commands/plcc-scan.bats
```

Expected: FAIL on both new tests.

- [ ] **Step 3: Fix the input loop in scan.py**

In `src/plcc/cmd/scan.py`, find the input-building block (after the `plcc-spec` subprocess call, before the `plcc-tokens` call):

```python
        # Build input: concatenate source files, then stdin
        input_data = b""
        for src in sources:
            with open(src, "rb") as sf:
                input_data += sf.read()
        if not sources:
            input_data = sys.stdin.buffer.read()
```

Replace it with:

```python
        # Build input: concatenate source files/stdin in order
        input_data = b""
        for src in sources:
            if src == '-':
                input_data += sys.stdin.buffer.read()
            else:
                with open(src, "rb") as sf:
                    input_data += sf.read()
        if not sources:
            input_data = sys.stdin.buffer.read()
```

- [ ] **Step 4: Run to confirm pass**

```
bin/test/commands.bash tests/bats/commands/plcc-scan.bats
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/bats/commands/plcc-scan.bats src/plcc/cmd/scan.py
git commit -m "feat(scan): accept '-' as stdin"
```

---

### Task 5: plcc-parse — accept `-` as stdin

**Files:**
- Modify: `tests/bats/commands/plcc-parse.bats`
- Modify: `src/plcc/cmd/parse.py`

- [ ] **Step 1: Add failing bats test**

Add to `tests/bats/commands/plcc-parse.bats`:

```bash
@test "plcc-parse accepts '-' as stdin" {
    run bash -c "echo '42' | plcc-parse '${FIXTURES}/trivial.plcc' -"
    [ "$status" -eq 0 ]
    [[ "$output" == *"program"* ]]
}
```

- [ ] **Step 2: Run to confirm failure**

```
bin/test/commands.bash tests/bats/commands/plcc-parse.bats
```

Expected: FAIL on `plcc-parse accepts '-' as stdin`.

- [ ] **Step 3: Fix the input loop in parse.py**

In `src/plcc/cmd/parse.py`, find the input-building block (after `_run_child` for `plcc-ll1`, before the Popen calls):

```python
        # Build input
        input_data = b""
        for src in sources:
            with open(src, "rb") as sf:
                input_data += sf.read()
        if not sources:
            input_data = sys.stdin.buffer.read()
```

Replace it with:

```python
        # Build input: concatenate source files/stdin in order
        input_data = b""
        for src in sources:
            if src == '-':
                input_data += sys.stdin.buffer.read()
            else:
                with open(src, "rb") as sf:
                    input_data += sf.read()
        if not sources:
            input_data = sys.stdin.buffer.read()
```

- [ ] **Step 4: Run to confirm pass**

```
bin/test/commands.bash tests/bats/commands/plcc-parse.bats
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/bats/commands/plcc-parse.bats src/plcc/cmd/parse.py
git commit -m "feat(parse): accept '-' as stdin"
```

---

## PR 3 — Issue 002: Continue scanning after unrecognized character

`plcc-tokens` exits immediately on the first `LexError`. Adding `--continue-on-error` changes this: errors are emitted but scanning continues, and the exit code reflects whether any errors occurred. `plcc-scan` then passes this flag and processes `plcc-tokens` stdout regardless of exit code (currently it discards stdout on non-zero exit).

### Task 6: plcc-tokens — add `--continue-on-error` flag

**Files:**
- Modify: `src/plcc/tokens/tokens_cli.py`
- Modify: `src/plcc/tokens/tokens_cli_test.py`

- [ ] **Step 1: Write failing unit tests**

Add to `src/plcc/tokens/tokens_cli_test.py`:

```python
def test_continue_on_error_continues_after_bad_char(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('@ 42\n'))
    with pytest.raises(SystemExit) as excinfo:
        run_main(['/spec.json', '--continue-on-error'])
    assert excinfo.value.code != 0
    out, err = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record['kind'] == 'token'
    assert record['name'] == 'NUM'
    assert record['lexeme'] == '42'
    assert 'error' in err


def test_continue_on_error_bad_char_only_exits_nonzero(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('@\n'))
    with pytest.raises(SystemExit) as excinfo:
        run_main(['/spec.json', '--continue-on-error'])
    assert excinfo.value.code != 0
    out, err = capsys.readouterr()
    assert 'error' in err


def test_default_still_exits_on_first_error(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('@ 42\n'))
    with pytest.raises(SystemExit) as excinfo:
        run_main(['/spec.json'])
    assert excinfo.value.code != 0
    out, _ = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 0


def test_continue_on_error_valid_input_exits_zero(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
    run_main(['/spec.json', '--continue-on-error'])
    out, _ = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 1
    assert json.loads(lines[0])['name'] == 'NUM'
```

- [ ] **Step 2: Run to confirm failure**

```
bin/test/units.bash src/plcc/tokens/tokens_cli_test.py
```

Expected: 4 new tests FAIL (function not defined / flag not recognized).

- [ ] **Step 3: Add `--continue-on-error` to tokens_cli.py**

In `src/plcc/tokens/tokens_cli.py`, update `__doc__` to add the new option:

```python
__doc__ = """plcc-tokens
    Tokenize stdin given a spec JSON file, output token JSONL.

Usage:
    plcc-tokens [options] SPEC_JSON

Arguments:
    SPEC_JSON   Path to spec JSON file (output of plcc-spec).

Options:
    -h --help               Show this message.
    --continue-on-error     Continue scanning after an unrecognized character.
""" + VERBOSE_OPTIONS
```

Replace the scanner loop in `main()`:

```python
    lines = _read_stdin_as_lines()
    for obj in scanner.scan(lines):
        if isinstance(obj, Skip):
            continue
        if isinstance(obj, LexError):
            verbose.emit_error(
                pos={
                    "file": obj.line.file,
                    "line": obj.line.number,
                    "column": obj.column,
                },
                message="unrecognized character",
            )
            sys.exit(1)
        print(format_record(obj), flush=True)
```

with:

```python
    lines = _read_stdin_as_lines()
    continue_on_error = args['--continue-on-error']
    had_error = False
    for obj in scanner.scan(lines):
        if isinstance(obj, Skip):
            continue
        if isinstance(obj, LexError):
            verbose.emit_error(
                pos={
                    "file": obj.line.file,
                    "line": obj.line.number,
                    "column": obj.column,
                },
                message="unrecognized character",
            )
            if continue_on_error:
                had_error = True
                continue
            sys.exit(1)
        print(format_record(obj), flush=True)
    if had_error:
        sys.exit(1)
```

- [ ] **Step 4: Run to confirm pass**

```
bin/test/units.bash src/plcc/tokens/tokens_cli_test.py
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/tokens/tokens_cli.py src/plcc/tokens/tokens_cli_test.py
git commit -m "feat(tokens): add --continue-on-error flag"
```

---

### Task 7: plcc-scan — pass `--continue-on-error`, always print tokens

`plcc-scan` currently only prints tokens when `plcc-tokens` exits 0. With `--continue-on-error`, `plcc-tokens` exits 1 on lex errors but still emits tokens for valid characters. `plcc-scan` must process stdout regardless of exit code.

**Files:**
- Modify: `tests/bats/commands/plcc-scan.bats`
- Modify: `src/plcc/cmd/scan.py`

- [ ] **Step 1: Add failing bats test**

Add to `tests/bats/commands/plcc-scan.bats`:

```bash
@test "plcc-scan prints tokens before and after a lex error" {
    run --separate-stderr bash -c "printf '42 @ 99\n' | plcc-scan '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"99"* ]]
    [[ "$stderr" == *"error"* ]]
}
```

- [ ] **Step 2: Run to confirm failure**

```
bin/test/commands.bash tests/bats/commands/plcc-scan.bats
```

Expected: FAIL — currently `42` and `99` are not both printed when there is a lex error.

- [ ] **Step 3: Fix scan.py**

In `src/plcc/cmd/scan.py`, find the `plcc-tokens` subprocess call and the block that follows it. Currently:

```python
        # plcc-tokens spec.json < input
        result = subprocess.run(
            ["plcc-tokens", spec_path] + child_flags,
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.stderr:
            events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
            verbose.reformat_child_events(events)
        if result.returncode != 0:
            # lex error: plcc-tokens already emitted the error to stderr via verbose;
            # treat as non-fatal — pipeline completed with an error in-band
            pass
        else:
            for line in result.stdout.decode("utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("kind") == "token":
                    name = record.get("name", "?")
                    lexeme = record.get("lexeme", "?")
                    source = record.get("source", {})
                    loc = _location_str(source)
                    print(f"{loc} {name} '{lexeme}'")
                # forward-looking: plcc-tokens may emit error records inline in a future protocol
                elif record.get("kind") == "error":
                    source = record.get("source", {})
                    loc = _location_str(source)
                    message = record.get("message", "unknown error")
                    print(f"{loc}: error: {message}")
```

Replace it with:

```python
        # plcc-tokens spec.json < input
        result = subprocess.run(
            ["plcc-tokens", spec_path, "--continue-on-error"] + child_flags,
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.stderr:
            events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
            verbose.reformat_child_events(events)
        for line in result.stdout.decode("utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("kind") == "token":
                name = record.get("name", "?")
                lexeme = record.get("lexeme", "?")
                source = record.get("source", {})
                loc = _location_str(source)
                print(f"{loc} {name} '{lexeme}'")
            elif record.get("kind") == "error":
                source = record.get("source", {})
                loc = _location_str(source)
                message = record.get("message", "unknown error")
                print(f"{loc}: error: {message}")
```

- [ ] **Step 4: Run to confirm pass**

```
bin/test/commands.bash tests/bats/commands/plcc-scan.bats
```

Expected: all tests pass, including the new one and the existing `plcc-scan exits 0 on lex error in source`.

- [ ] **Step 5: Commit**

```bash
git add tests/bats/commands/plcc-scan.bats src/plcc/cmd/scan.py
git commit -m "fix(scan): print tokens before and after lex errors"
```

---

## PR 4 — Issue 001: Print tokens after each line (streaming)

`plcc-scan` currently buffers all input before starting `plcc-tokens`, then prints all output at the end. The fix uses `subprocess.Popen()` and two background threads: one feeds input line by line, another drains `plcc-tokens` stderr. The main thread reads stdout and prints tokens as they arrive.

This makes interactive use work: a student types a line, sees the tokens immediately.

### Task 8: plcc-scan — switch to Popen streaming

**Files:**
- Modify: `src/plcc/cmd/scan.py`

- [ ] **Step 1: Add a multi-line bats test**

Add to `tests/bats/commands/plcc-scan.bats`:

```bash
@test "plcc-scan outputs tokens for multi-line input" {
    run bash -c "printf '42\n99\n' | plcc-scan '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"99"* ]]
}
```

- [ ] **Step 2: Run to confirm the test currently passes (baseline)**

```
bin/test/commands.bash tests/bats/commands/plcc-scan.bats
```

Expected: all tests pass. (This test passes even before the streaming change; it verifies correctness is preserved after the change.)

- [ ] **Step 3: Add `threading` import to scan.py**

At the top of `src/plcc/cmd/scan.py`, the existing imports are:

```python
import enum
import json
import os
import subprocess
import sys
import tempfile
```

Add `import threading` so it becomes:

```python
import enum
import json
import os
import subprocess
import sys
import tempfile
import threading
```

- [ ] **Step 4: Rewrite the plcc-tokens section of scan.py**

Replace the entire `plcc-tokens` block (from the `# Build input` comment through the end of the `if/else` block that prints tokens):

```python
        # Build input: concatenate source files/stdin in order
        input_data = b""
        for src in sources:
            if src == '-':
                input_data += sys.stdin.buffer.read()
            else:
                with open(src, "rb") as sf:
                    input_data += sf.read()
        if not sources:
            input_data = sys.stdin.buffer.read()

        # plcc-tokens spec.json < input
        result = subprocess.run(
            ["plcc-tokens", spec_path, "--continue-on-error"] + child_flags,
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.stderr:
            events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
            verbose.reformat_child_events(events)
        for line in result.stdout.decode("utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("kind") == "token":
                name = record.get("name", "?")
                lexeme = record.get("lexeme", "?")
                source = record.get("source", {})
                loc = _location_str(source)
                print(f"{loc} {name} '{lexeme}'")
            elif record.get("kind") == "error":
                source = record.get("source", {})
                loc = _location_str(source)
                message = record.get("message", "unknown error")
                print(f"{loc}: error: {message}")
```

with:

```python
        proc = subprocess.Popen(
            ["plcc-tokens", spec_path, "--continue-on-error"] + child_flags,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stderr_chunks = []

        def _drain_stderr():
            stderr_chunks.append(proc.stderr.read())

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()

        def _feed_input():
            try:
                if sources:
                    for src in sources:
                        if src == '-':
                            for chunk in sys.stdin.buffer:
                                proc.stdin.write(chunk)
                                proc.stdin.flush()
                        else:
                            with open(src, "rb") as sf:
                                for chunk in sf:
                                    proc.stdin.write(chunk)
                                    proc.stdin.flush()
                else:
                    for chunk in sys.stdin.buffer:
                        proc.stdin.write(chunk)
                        proc.stdin.flush()
            finally:
                proc.stdin.close()

        feed_thread = threading.Thread(target=_feed_input, daemon=True)
        feed_thread.start()

        for raw in proc.stdout:
            line = raw.decode("utf-8").strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("kind") == "token":
                name = record.get("name", "?")
                lexeme = record.get("lexeme", "?")
                source = record.get("source", {})
                loc = _location_str(source)
                print(f"{loc} {name} '{lexeme}'")
            elif record.get("kind") == "error":
                source = record.get("source", {})
                loc = _location_str(source)
                message = record.get("message", "unknown error")
                print(f"{loc}: error: {message}")

        feed_thread.join()
        stderr_thread.join()
        proc.wait()

        stderr_data = b"".join(stderr_chunks)
        if stderr_data:
            events = verbose.parse_child_events(stderr_data.decode("utf-8", errors="replace"))
            verbose.reformat_child_events(events)
```

- [ ] **Step 5: Run all plcc-scan bats tests**

```
bin/test/commands.bash tests/bats/commands/plcc-scan.bats
```

Expected: all tests pass.

- [ ] **Step 6: Run the full functional test suite**

```
bin/test/functional.bash
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/plcc/cmd/scan.py tests/bats/commands/plcc-scan.bats
git commit -m "feat(scan): stream tokens line by line using Popen"
```
