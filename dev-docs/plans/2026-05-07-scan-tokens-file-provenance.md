# Scan Token File Provenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Include the source filename on every token and error line emitted by `plcc-scan`, and make `plcc-tokens` accept `[SOURCE ...]` file arguments so it can label each line with its originating file.

**Architecture:** `plcc-tokens` gains optional `[SOURCE ...]` positional args and two private helpers (`_lines_from_sources`, `_lines_from_stream`) that replace the existing `_read_stdin_as_lines`. With no SOURCE args it reads stdin and labels lines `file='-'`; with SOURCE args it opens each file (or `-` for stdin) in order. `plcc-scan` drops the stdin-pipe/feed-thread machinery and instead passes its SOURCE args (or `["-"]`) directly to `plcc-tokens`. `_location_str` in `scan.py` is simplified to always emit `file:line:col`.

**Tech Stack:** Python 3, docopt, pytest, pyfakefs (`fs` fixture), bats

---

## File map

| File | What changes |
|---|---|
| `src/plcc/tokens/tokens_cli.py` | Add `[SOURCE ...]` to docopt; replace `_read_stdin_as_lines` with `_lines_from_sources` + `_lines_from_stream`; update `main` |
| `src/plcc/tokens/tokens_cli_test.py` | Update `file='<stdin>'` → `file='-'`; add two new unit tests |
| `src/plcc/cmd/scan.py` | Remove `_feed_input` function and `feed_thread`; update `Popen` call; simplify `_location_str` |
| `tests/bats/commands/plcc-scan.bats` | Update format-assertion test name and regex; add filename-in-output test |
| `tests/bats/commands/plcc-tokens.bats` | Add two file-provenance tests |

> **Note:** Do NOT use `scan.source.Source` for reading source code in `plcc-tokens`. `Source` calls `line.strip()` which removes leading whitespace and corrupts column numbers. The new helpers use `rstrip('\n')` to preserve leading whitespace.

---

## Task 1: Write failing unit tests for `tokens_cli` changes

**Files:**
- Modify: `src/plcc/tokens/tokens_cli_test.py`

- [ ] **Step 1: Add two failing tests to `tokens_cli_test.py`**

Open `src/plcc/tokens/tokens_cli_test.py` and append these two tests after the existing ones:

```python
def test_stdin_labels_tokens_with_dash(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
    run_main(['/spec.json'])
    out, _ = capsys.readouterr()
    record = json.loads(out.strip())
    assert record['source']['file'] == '-'


def test_named_file_arg_labels_tokens_with_filename(capsys, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    fs.create_file('/src.txt', contents='42\n')
    run_main(['/spec.json', '/src.txt'])
    out, _ = capsys.readouterr()
    record = json.loads(out.strip())
    assert record['source']['file'] == '/src.txt'
```

- [ ] **Step 2: Run the new tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/tokens/tokens_cli_test.py::test_stdin_labels_tokens_with_dash src/plcc/tokens/tokens_cli_test.py::test_named_file_arg_labels_tokens_with_filename -v
```

Expected: both FAIL. `test_stdin_labels_tokens_with_dash` will get `file='<stdin>'` instead of `'-'`. `test_named_file_arg_labels_tokens_with_filename` will fail because `run_main` raises a `docopt.DocoptExit` (unknown argument).

---

## Task 2: Implement `tokens_cli.py` changes

**Files:**
- Modify: `src/plcc/tokens/tokens_cli.py`
- Modify: `src/plcc/tokens/tokens_cli_test.py`

- [ ] **Step 1: Replace the full content of `tokens_cli.py`**

```python
import enum
import sys

from docopt import docopt

from ..lines import Line
from ..scan.matcher import Matcher
from ..scan.scanner import Scanner
from ..scan.Skip import Skip
from ..scan.LexError import LexError
from .spec_loader import load_lexical_rules
from .jsonl_formatter import format_record, format_error_record
from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-tokens
    Tokenize source files given a spec JSON file, output token JSONL.

Usage:
    plcc-tokens [options] SPEC_JSON [SOURCE ...]

Arguments:
    SPEC_JSON   Path to spec JSON file (output of plcc-spec).
    SOURCE      Source files to tokenize. Use '-' for stdin. Defaults to stdin.

Options:
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-tokens", Events, args)
    rules = load_lexical_rules(args['SPEC_JSON'])
    matcher = Matcher(rules)
    scanner = Scanner(matcher)
    sources = args['SOURCE'] or ['-']
    lines = _lines_from_sources(sources)
    for obj in scanner.scan(lines):
        if isinstance(obj, Skip):
            continue
        if isinstance(obj, LexError):
            print(format_error_record(obj), flush=True)
            continue
        print(format_record(obj), flush=True)


def _lines_from_sources(sources):
    for file in sources:
        if file == '-':
            yield from _lines_from_stream(sys.stdin, '-')
        else:
            with open(file, 'r') as f:
                yield from _lines_from_stream(f, file)


def _lines_from_stream(stream, file):
    for i, raw in enumerate(stream, start=1):
        yield Line(string=raw.rstrip('\n'), number=i, file=file)
```

- [ ] **Step 2: Update the existing test that asserts `file='<stdin>'`**

In `src/plcc/tokens/tokens_cli_test.py`, find `test_lex_error_emits_error_record_to_stdout` and change:

```python
    assert record['pos'] == {'file': '<stdin>', 'line': 1, 'column': 1}
```

to:

```python
    assert record['pos'] == {'file': '-', 'line': 1, 'column': 1}
```

- [ ] **Step 3: Run all `tokens_cli` unit tests to verify they pass**

```bash
bin/test/units.bash src/plcc/tokens/tokens_cli_test.py -v
```

Expected: all PASS.

- [ ] **Step 4: Run the full unit test suite to check for regressions**

```bash
bin/test/units.bash
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/tokens/tokens_cli.py src/plcc/tokens/tokens_cli_test.py
git commit -m "feat(tokens): accept SOURCE file args; label stdin lines with file='-'"
```

---

## Task 3: Implement `scan.py` changes

**Files:**
- Modify: `src/plcc/cmd/scan.py`

- [ ] **Step 1: Replace `_location_str` in `scan.py`**

Find and replace the existing `_location_str` function (near the top of the file):

Old:
```python
def _location_str(source):
    file = source.get("file")
    line = source.get("line", "?")
    col = source.get("column", "?")
    if file and file != "<stdin>":
        return f"{file}:{line}:{col}"
    return f"{line}:{col}"
```

New:
```python
def _location_str(source):
    file = source.get("file", "?")
    line = source.get("line", "?")
    col = source.get("column", "?")
    return f"{file}:{line}:{col}"
```

- [ ] **Step 2: Replace the subprocess block in `scan.py`**

Inside the `try:` block in `main`, find the section that starts with `proc = subprocess.Popen(...)` and runs through `feed_thread.start()`. Replace everything from `proc = subprocess.Popen(` through `feed_thread.start()` with:

```python
        token_sources = sources if sources else ["-"]
        proc = subprocess.Popen(
            ["plcc-tokens", spec_path] + token_sources + child_flags,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
```

Then delete the `_feed_input` function definition and the `feed_thread` lines entirely. The `stderr_thread` and its `_drain_stderr` helper are unchanged.

After the edit, the full subprocess section should look like:

```python
        token_sources = sources if sources else ["-"]
        proc = subprocess.Popen(
            ["plcc-tokens", spec_path] + token_sources + child_flags,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stderr_chunks = []

        def _drain_stderr():
            stderr_chunks.append(proc.stderr.read())

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()

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
                print(f"{loc} {name} '{lexeme}'", flush=True)
            elif record.get("kind") == "error":
                loc = _location_str(record.get("pos", {}))
                lexeme = record.get("lexeme", "?")
                message = record.get("message", "unrecognized character")
                print(f"{loc}: error: {message} '{lexeme}'", flush=True)

        stderr_thread.join()
        proc.wait()
```

- [ ] **Step 3: Run the full unit test suite**

```bash
bin/test/units.bash
```

Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/cmd/scan.py
git commit -m "feat(scan): pass SOURCE args to plcc-tokens; always include file in location"
```

---

## Task 4: Update and add bats tests

**Files:**
- Modify: `tests/bats/commands/plcc-scan.bats`
- Modify: `tests/bats/commands/plcc-tokens.bats`

- [ ] **Step 1: Update the format-assertion test in `plcc-scan.bats`**

Find the test named `"plcc-scan includes line:col in token output"` and replace it:

Old:
```bash
@test "plcc-scan includes line:col in token output" {
    run bash -c "echo '42' | plcc-scan '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^1:1\ NUM\ \'42\'$ ]]
}
```

New:
```bash
@test "plcc-scan includes file:line:col in token output" {
    run bash -c "echo '42' | plcc-scan '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^-:1:1\ NUM\ \'42\'$ ]]
}
```

- [ ] **Step 2: Add a filename-in-output test to `plcc-scan.bats`**

Append after the last `@test` block in `plcc-scan.bats`:

```bash
@test "plcc-scan includes source filename in token output for named file" {
    run plcc-scan "${FIXTURES}/trivial.plcc" "${FIXTURES}/trivial_input.txt"
    [ "$status" -eq 0 ]
    [[ "$output" == *"trivial_input.txt"* ]]
}
```

- [ ] **Step 3: Add file-provenance tests to `plcc-tokens.bats`**

Append after the last `@test` block in `tests/bats/commands/plcc-tokens.bats`:

```bash
@test "plcc-tokens with no SOURCE args labels tokens with file=-" {
    result=$(echo '42' | plcc-tokens "${SPEC_JSON}")
    file_val=$(echo "$result" | python3 -c "import json,sys; r=json.load(sys.stdin); print(r['source']['file'])")
    [ "$file_val" = "-" ]
}

@test "plcc-tokens with SOURCE file arg labels tokens with that filename" {
    tmp=$(mktemp)
    echo "42" > "$tmp"
    result=$(plcc-tokens "${SPEC_JSON}" "$tmp")
    file_val=$(echo "$result" | python3 -c "import json,sys; r=json.load(sys.stdin); print(r['source']['file'])")
    [ "$file_val" = "$tmp" ]
    rm -f "$tmp"
}
```

- [ ] **Step 4: Run the commands bats tier**

```bash
bin/test/commands.bash
```

Expected: all PASS, including the updated and new tests.

- [ ] **Step 5: Run the integration and e2e tiers to check for regressions**

```bash
bin/test/integration.bash && bin/test/e2e.bash
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/bats/commands/plcc-scan.bats tests/bats/commands/plcc-tokens.bats
git commit -m "test(scan,tokens): update and add file-provenance bats tests"
```

---

## Self-review

**Spec coverage:**
- ✅ `plcc-tokens` accepts `[SOURCE ...]` — Task 2
- ✅ Stdin defaults to `file='-'` — Task 2
- ✅ Named files get correct `source.file` — Task 2
- ✅ `plcc-scan` passes SOURCE args through, removes feed thread — Task 3
- ✅ `_location_str` always emits `file:line:col` — Task 3
- ✅ `plcc-scan.bats` format assertion updated — Task 4
- ✅ `tokens_cli_test.py` `file='<stdin>'` updated — Task 2
- ✅ New bats tests for named file in both commands — Task 4

**Placeholder scan:** None found.

**Type consistency:** `_lines_from_sources` and `_lines_from_stream` are defined in Task 2 Step 1 and only referenced in `main` in the same file. `token_sources` in Task 3 matches the list type expected by `Popen`. All good.
