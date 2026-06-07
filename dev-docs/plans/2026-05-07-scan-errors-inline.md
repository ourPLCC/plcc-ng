# Scan Errors Inline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `plcc-tokens` emit lex errors as `{"kind":"error"}` JSONL records on stdout (not stderr), so `plcc-scan` can print them inline with tokens in stream order.

**Architecture:** Lex errors are treated as data, not tool failures. `plcc-tokens` emits an error record for each unrecognized character and continues scanning, always exiting 0. `plcc-scan` reads these records from its existing stdout loop and prints them inline on its own stdout alongside token lines. The `--continue-on-error` flag is removed from both commands.

**Tech Stack:** Python, pytest (`bin/test/units.bash`), bats (`bin/test/commands.bash`, `bin/test/e2e.bash`), pyfakefs (`fs` fixture in unit tests).

---

## File Map

| File | Change |
|------|--------|
| `src/plcc/tokens/jsonl_formatter.py` | Add `format_error_record(lex_error)` |
| `src/plcc/tokens/jsonl_formatter_test.py` | Add `test_formats_error_record` |
| `src/plcc/tokens/tokens_cli.py` | Remove `--continue-on-error`, emit errors to stdout, exit 0 |
| `src/plcc/tokens/tokens_cli_test.py` | Remove 6 tests, add 2 new tests |
| `src/plcc/cmd/scan.py` | Remove `--continue-on-error` from subprocess call; handle `kind=="error"` records |
| `tests/bats/commands/plcc-tokens.bats` | Update lex error test |
| `tests/bats/commands/plcc-scan.bats` | Update 2 lex error tests |
| `tests/bats/e2e/error-propagation.bats` | Rewrite all 3 tests |

---

### Task 1: Add `format_error_record` to `jsonl_formatter.py`

**Files:**
- Modify: `src/plcc/tokens/jsonl_formatter_test.py`
- Modify: `src/plcc/tokens/jsonl_formatter.py`

- [ ] **Step 1: Write the failing test**

  In `src/plcc/tokens/jsonl_formatter_test.py`, add these three imports alongside the existing imports at the top of the file:

  ```python
  from ..scan.LexError import LexError
  from ..lines import Line
  from .jsonl_formatter import format_error_record
  ```

  Then add this test function at the bottom of the file:

  ```python
  def test_formats_error_record():
      line = Line(string='hello@world', number=3, file='src.txt')
      lex_error = LexError(line=line, column=6)  # '@' is at index 5, column 6
      result = json.loads(format_error_record(lex_error))
      assert result['kind'] == 'error'
      assert result['stage'] == 'plcc-tokens'
      assert result['severity'] == 'error'
      assert result['pos'] == {'file': 'src.txt', 'line': 3, 'column': 6}
      assert result['lexeme'] == '@'
      assert result['message'] == 'unrecognized character'
  ```

- [ ] **Step 2: Run the test and verify it fails**

  ```bash
  cd /workspaces/plcc-ng/.worktrees/scan-issues && bin/test/units.bash src/plcc/tokens/jsonl_formatter_test.py::test_formats_error_record -v
  ```

  Expected: `ImportError` or `FAILED` — `format_error_record` does not exist yet.

- [ ] **Step 3: Implement `format_error_record`**

  Add to `src/plcc/tokens/jsonl_formatter.py` below the existing `format_record` function:

  ```python
  def format_error_record(obj):
      return json.dumps({
          'kind': 'error',
          'stage': 'plcc-tokens',
          'severity': 'error',
          'pos': {
              'file': obj.line.file,
              'line': obj.line.number,
              'column': obj.column,
          },
          'lexeme': obj.line.string[obj.column - 1],
          'message': 'unrecognized character',
      })
  ```

- [ ] **Step 4: Run the test and verify it passes**

  ```bash
  cd /workspaces/plcc-ng/.worktrees/scan-issues && bin/test/units.bash src/plcc/tokens/jsonl_formatter_test.py -v
  ```

  Expected: all tests PASS.

- [ ] **Step 5: Commit**

  ```bash
  cd /workspaces/plcc-ng/.worktrees/scan-issues && git add src/plcc/tokens/jsonl_formatter.py src/plcc/tokens/jsonl_formatter_test.py && git commit -m "feat(tokens): add format_error_record to jsonl_formatter"
  ```

---

### Task 2: Update `tokens_cli.py` to emit errors on stdout, exit 0, drop `--continue-on-error`

**Files:**
- Modify: `src/plcc/tokens/tokens_cli_test.py`
- Modify: `src/plcc/tokens/tokens_cli.py`

- [ ] **Step 1: Replace the error-related tests in `tokens_cli_test.py`**

  **Remove** these six functions entirely from `src/plcc/tokens/tokens_cli_test.py`:
  - `test_lex_error_goes_to_stderr_and_exits_nonzero`
  - `test_lex_error_json_format`
  - `test_continue_on_error_continues_after_bad_char`
  - `test_continue_on_error_bad_char_only_exits_nonzero`
  - `test_continue_on_error_valid_input_exits_zero`
  - `test_default_still_exits_on_first_error`

  **Add** these two functions at the bottom of the file:

  ```python
  def test_lex_error_emits_error_record_to_stdout(capsys, monkeypatch, fs):
      fs.create_file('/spec.json', contents=json.dumps(_SPEC))
      monkeypatch.setattr('sys.stdin', io.StringIO('@\n'))
      run_main(['/spec.json'])
      out, err = capsys.readouterr()
      lines = [l for l in out.strip().splitlines() if l]
      assert len(lines) == 1
      record = json.loads(lines[0])
      assert record['kind'] == 'error'
      assert record['stage'] == 'plcc-tokens'
      assert record['severity'] == 'error'
      assert record['lexeme'] == '@'
      assert record['pos'] == {'file': '<stdin>', 'line': 1, 'column': 1}
      assert record['message'] == 'unrecognized character'
      assert err == ''


  def test_lex_error_and_token_appear_in_stream_order(capsys, monkeypatch, fs):
      fs.create_file('/spec.json', contents=json.dumps(_SPEC))
      # '@' is unrecognized, then '42' is a valid NUM token
      monkeypatch.setattr('sys.stdin', io.StringIO('@42\n'))
      run_main(['/spec.json'])
      out, err = capsys.readouterr()
      lines = [l for l in out.strip().splitlines() if l]
      assert len(lines) == 2
      assert json.loads(lines[0])['kind'] == 'error'
      assert json.loads(lines[1])['kind'] == 'token'
      assert json.loads(lines[1])['name'] == 'NUM'
  ```

- [ ] **Step 2: Run the new tests and verify they fail**

  ```bash
  cd /workspaces/plcc-ng/.worktrees/scan-issues && bin/test/units.bash src/plcc/tokens/tokens_cli_test.py::test_lex_error_emits_error_record_to_stdout src/plcc/tokens/tokens_cli_test.py::test_lex_error_and_token_appear_in_stream_order -v
  ```

  Expected: both FAIL — current code sends errors to stderr and exits nonzero.

- [ ] **Step 3: Rewrite `tokens_cli.py`**

  Replace the entire contents of `src/plcc/tokens/tokens_cli.py` with:

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
      Tokenize stdin given a spec JSON file, output token JSONL.

  Usage:
      plcc-tokens [options] SPEC_JSON

  Arguments:
      SPEC_JSON   Path to spec JSON file (output of plcc-spec).

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
      lines = _read_stdin_as_lines()
      for obj in scanner.scan(lines):
          if isinstance(obj, Skip):
              continue
          if isinstance(obj, LexError):
              print(format_error_record(obj), flush=True)
              continue
          print(format_record(obj), flush=True)


  def _read_stdin_as_lines():
      for i, raw in enumerate(sys.stdin, start=1):
          yield Line(string=raw.rstrip('\n'), number=i, file='<stdin>')
  ```

- [ ] **Step 4: Run the full unit test suite and verify all pass**

  ```bash
  cd /workspaces/plcc-ng/.worktrees/scan-issues && bin/test/units.bash src/plcc/tokens/ -v
  ```

  Expected: all tests PASS (including the two new ones; the six removed tests are gone).

- [ ] **Step 5: Commit**

  ```bash
  cd /workspaces/plcc-ng/.worktrees/scan-issues && git add src/plcc/tokens/tokens_cli.py src/plcc/tokens/tokens_cli_test.py && git commit -m "feat(tokens): emit lex errors as stdout records, exit 0, drop --continue-on-error"
  ```

---

### Task 3: Update `plcc-scan` to handle error records and drop `--continue-on-error`

There is no unit test for `cmd/scan.py` (it is an orchestrator that spawns subprocesses; the bats command tier covers it). Implement the change, then verify with the full unit suite to check for regressions.

**Files:**
- Modify: `src/plcc/cmd/scan.py`

- [ ] **Step 1: Remove `--continue-on-error` from the `plcc-tokens` subprocess call**

  In `src/plcc/cmd/scan.py` at line 77, change:

  ```python
  proc = subprocess.Popen(
      ["plcc-tokens", spec_path, "--continue-on-error"] + child_flags,
  ```

  to:

  ```python
  proc = subprocess.Popen(
      ["plcc-tokens", spec_path] + child_flags,
  ```

- [ ] **Step 2: Add an error record handler in the stdout loop**

  In `src/plcc/cmd/scan.py`, the `for raw in proc.stdout:` loop currently contains:

  ```python
  record = json.loads(line)
  if record.get("kind") == "token":
      name = record.get("name", "?")
      lexeme = record.get("lexeme", "?")
      source = record.get("source", {})
      loc = _location_str(source)
      print(f"{loc} {name} '{lexeme}'", flush=True)
  ```

  Add an `elif` branch immediately after the `if` block:

  ```python
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
      print(f"{loc}: error: unrecognized character '{lexeme}'", flush=True)
  ```

- [ ] **Step 3: Run unit tests to confirm no regressions**

  ```bash
  cd /workspaces/plcc-ng/.worktrees/scan-issues && bin/test/units.bash -v
  ```

  Expected: all tests PASS.

- [ ] **Step 4: Commit**

  ```bash
  cd /workspaces/plcc-ng/.worktrees/scan-issues && git add src/plcc/cmd/scan.py && git commit -m "fix(scan): handle error records inline, drop --continue-on-error from plcc-tokens call"
  ```

---

### Task 4: Update bats tests to match new behavior

The CLI contract for `plcc-tokens` and `plcc-scan` has changed. Update the three bats files to reflect the new protocol, then run the commands and e2e test tiers to verify.

**Files:**
- Modify: `tests/bats/commands/plcc-tokens.bats`
- Modify: `tests/bats/commands/plcc-scan.bats`
- Modify: `tests/bats/e2e/error-propagation.bats`

- [ ] **Step 1: Update `plcc-tokens.bats`**

  In `tests/bats/commands/plcc-tokens.bats`, replace the test:

  ```bash
  @test "plcc-tokens lex error exits nonzero and writes error to stderr" {
      run --separate-stderr bash -c "echo 'xyz' | plcc-tokens '${SPEC_JSON}'"
      [ "$status" -ne 0 ]
      # stderr carries the error message
      [[ "$stderr" == *"error"* ]]
      [[ "$stderr" == *"plcc-tokens"* ]]
      # stdout has no error records
      for line in $output; do
          [ -z "$line" ] && continue
          echo "$line" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='token', f\"unexpected kind={r['kind']} on stdout\""
      done
  }
  ```

  with:

  ```bash
  @test "plcc-tokens lex error exits 0 and writes error record to stdout" {
      run --separate-stderr bash -c "echo 'xyz' | plcc-tokens '${SPEC_JSON}'"
      [ "$status" -eq 0 ]
      [ -z "$stderr" ]
      # every output line is a valid JSON record with kind=error
      for line in $output; do
          [ -z "$line" ] && continue
          echo "$line" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='error', f\"expected kind=error, got {r['kind']}\""
      done
  }
  ```

- [ ] **Step 2: Update `plcc-scan.bats` — lex error exit test**

  In `tests/bats/commands/plcc-scan.bats`, replace:

  ```bash
  @test "plcc-scan exits 0 on lex error in source" {
      run --separate-stderr bash -c "echo 'abc' | plcc-scan '${FIXTURES}/trivial.plcc'"
      [ "$status" -eq 0 ]
      [[ "$stderr" =~ error ]]
  }
  ```

  with:

  ```bash
  @test "plcc-scan exits 0 on lex error in source" {
      run --separate-stderr bash -c "echo 'abc' | plcc-scan '${FIXTURES}/trivial.plcc'"
      [ "$status" -eq 0 ]
      [[ "$output" == *"error"* ]]
  }
  ```

- [ ] **Step 3: Update `plcc-scan.bats` — tokens before and after error test**

  In `tests/bats/commands/plcc-scan.bats`, replace:

  ```bash
  @test "plcc-scan prints tokens before and after a lex error" {
      run --separate-stderr bash -c "printf '42 @ 99\n' | plcc-scan '${FIXTURES}/trivial.plcc'"
      [ "$status" -eq 0 ]
      [[ "$output" == *"42"* ]]
      [[ "$output" == *"99"* ]]
      [[ "$stderr" == *"error"* ]]
  }
  ```

  with:

  ```bash
  @test "plcc-scan prints tokens before and after a lex error" {
      run --separate-stderr bash -c "printf '42 @ 99\n' | plcc-scan '${FIXTURES}/trivial.plcc'"
      [ "$status" -eq 0 ]
      [[ "$output" == *"42"* ]]
      [[ "$output" == *"99"* ]]
      [[ "$output" == *"error"* ]]
  }
  ```

- [ ] **Step 4: Rewrite `error-propagation.bats`**

  Replace the entire contents of `tests/bats/e2e/error-propagation.bats` with:

  ```bash
  #!/usr/bin/env bats

  bats_require_minimum_version 1.5.0

  # Tests that lex errors are emitted as error records on plcc-tokens stdout.

  setup() {
      FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
      SPEC_JSON="$(mktemp)"
      LL1_JSON="$(mktemp)"
      plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
      plcc-ll1 < "${SPEC_JSON}" > "${LL1_JSON}"
  }

  teardown() { rm -f "${SPEC_JSON}" "${LL1_JSON}"; }

  @test "lex error causes plcc-tokens to exit 0" {
      run bash -c "echo 'abc' | plcc-tokens '${SPEC_JSON}'"
      [ "$status" -eq 0 ]
  }

  @test "lex error writes error record to stdout" {
      run --separate-stderr bash -c "echo 'abc' | plcc-tokens '${SPEC_JSON}'"
      [ -z "$stderr" ]
      for line in $output; do
          [ -z "$line" ] && continue
          echo "$line" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='error', f\"expected kind=error, got {r['kind']}\""
      done
  }

  @test "lex error record has expected fields" {
      result=$(echo '@' | plcc-tokens "${SPEC_JSON}" | head -1)
      echo "$result" | python3 -c "
  import json, sys
  r = json.load(sys.stdin)
  assert r['kind'] == 'error'
  assert r['stage'] == 'plcc-tokens'
  assert r['severity'] == 'error'
  assert r['lexeme'] == '@'
  assert 'pos' in r
  assert r['message'] == 'unrecognized character'
  "
  }
  ```

- [ ] **Step 5: Run the commands test tier**

  ```bash
  cd /workspaces/plcc-ng/.worktrees/scan-issues && bin/test/commands.bash
  ```

  Expected: all command tests PASS.

- [ ] **Step 6: Run the e2e test tier**

  ```bash
  cd /workspaces/plcc-ng/.worktrees/scan-issues && bin/test/e2e.bash
  ```

  Expected: all e2e tests PASS.

- [ ] **Step 7: Commit**

  ```bash
  cd /workspaces/plcc-ng/.worktrees/scan-issues && git add tests/bats/commands/plcc-tokens.bats tests/bats/commands/plcc-scan.bats tests/bats/e2e/error-propagation.bats && git commit -m "test(bats): update lex error tests for new stdout-record protocol"
  ```
