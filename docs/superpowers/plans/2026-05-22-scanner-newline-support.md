# Scanner Newline Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `\n` visible to scanner patterns in `plcc-tokens`, matching original PLCC behavior where unmatched newlines produce LexErrors and patterns like `\n` can match them.

**Architecture:** Remove the `.rstrip('\n')` call in `_lines_from_stream` so each line includes its trailing newline; strip `\n` only in the `source_line` display field in the formatter. Update existing tests that asserted on record counts using a spec with no whitespace skip, since those tests are now exposed to the new LexError.

**Tech Stack:** Python, pytest, pyfakefs (`fs` fixture for filesystem mocking), `io.StringIO` for stdin mocking.

---

## File map

| File | Change |
|------|--------|
| `src/plcc/tokens/tokens_cli_test.py` | Add 2 new tests; update 8 existing tests |
| `src/plcc/tokens/tokens_cli.py` | Remove `.rstrip('\n')` in `_lines_from_stream` |
| `src/plcc/tokens/jsonl_formatter.py` | Strip `\n` from `source_line` in `format_record` |

---

## Task 1: Write new failing tests for newline behavior

**Files:**
- Modify: `src/plcc/tokens/tokens_cli_test.py`

- [ ] **Step 1: Add `_SPEC_WITH_NL_TOKEN` fixture and two new tests**

  Open `src/plcc/tokens/tokens_cli_test.py`. After the existing `_SPEC_WITH_SKIP` dict (around line 106), add:

  ```python
  _SPEC_WITH_NL_TOKEN = {
      "lexical": {"ruleList": [
          {"name": "NUM", "pattern": "\\d+", "isSkip": False,
           "line": {"string": "", "number": 1, "file": None}},
          {"name": "NL", "pattern": "\\n", "isSkip": False,
           "line": {"string": "", "number": 2, "file": None}},
          {"name": "WS", "pattern": "[ \\t]+", "isSkip": True,
           "line": {"string": "", "number": 3, "file": None}},
      ]},
      "syntax": {"rules": []},
      "semantics": []
  }
  ```

  Then add two new tests at the end of the file:

  ```python
  def test_newline_matched_as_nl_token(capsys, monkeypatch, fs):
      fs.create_file('/spec.json', contents=json.dumps(_SPEC_WITH_NL_TOKEN))
      monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
      run_main(['/spec.json'])
      out, _ = capsys.readouterr()
      records = [json.loads(l) for l in out.strip().splitlines() if l]
      non_sentinel = [r for r in records if r.get('name') != 'eof']
      assert len(non_sentinel) == 2
      assert non_sentinel[0]['kind'] == 'token'
      assert non_sentinel[0]['name'] == 'NUM'
      assert non_sentinel[0]['lexeme'] == '42'
      assert non_sentinel[1]['kind'] == 'token'
      assert non_sentinel[1]['name'] == 'NL'
      assert non_sentinel[1]['lexeme'] == '\n'


  def test_unhandled_newline_produces_lex_error(capsys, monkeypatch, fs):
      # _SPEC has only NUM '\d+' — no whitespace or newline handler
      fs.create_file('/spec.json', contents=json.dumps(_SPEC))
      monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
      run_main(['/spec.json'])
      out, _ = capsys.readouterr()
      records = [json.loads(l) for l in out.strip().splitlines() if l]
      non_sentinel = [r for r in records if r.get('name') != 'eof']
      assert len(non_sentinel) == 2
      assert non_sentinel[0]['kind'] == 'token'
      assert non_sentinel[0]['name'] == 'NUM'
      assert non_sentinel[1]['kind'] == 'error'
      assert non_sentinel[1]['lexeme'] == '\n'
  ```

- [ ] **Step 2: Run the new tests and confirm they fail**

  ```bash
  bin/test/units.bash src/plcc/tokens/tokens_cli_test.py::test_newline_matched_as_nl_token src/plcc/tokens/tokens_cli_test.py::test_unhandled_newline_produces_lex_error -v
  ```

  Expected: both tests **FAIL**. The first fails because `NL` token never appears (the `\n` is stripped before scanning). The second fails because only 1 non-sentinel record is produced instead of 2.

---

## Task 2: Implement the root change

**Files:**
- Modify: `src/plcc/tokens/tokens_cli.py:80-82`

- [ ] **Step 1: Remove `.rstrip('\n')` from `_lines_from_stream`**

  In `src/plcc/tokens/tokens_cli.py`, find `_lines_from_stream` (around line 80):

  ```python
  # before
  def _lines_from_stream(stream, file):
      for i, raw in enumerate(stream, start=1):
          yield Line(string=raw.rstrip('\n'), number=i, file=file)
  ```

  Change to:

  ```python
  # after
  def _lines_from_stream(stream, file):
      for i, raw in enumerate(stream, start=1):
          yield Line(string=raw, number=i, file=file)
  ```

  Python opens files and `sys.stdin` in text mode by default, normalizing `\r\n` → `\n` on all platforms. No explicit normalization is needed.

- [ ] **Step 2: Run the two new tests and confirm they now pass**

  ```bash
  bin/test/units.bash src/plcc/tokens/tokens_cli_test.py::test_newline_matched_as_nl_token src/plcc/tokens/tokens_cli_test.py::test_unhandled_newline_produces_lex_error -v
  ```

  Expected: both **PASS**.

- [ ] **Step 3: Run the full unit suite and note the failures — do not fix yet**

  ```bash
  bin/test/units.bash src/plcc/tokens/ -v
  ```

  Expected: the two new tests pass, but these eight existing tests now fail:

  - `test_outputs_token_jsonl`
  - `test_lex_error_emits_error_record_to_stdout`
  - `test_lex_error_and_token_appear_in_stream_order`
  - `test_stdin_labels_tokens_with_dash`
  - `test_named_file_arg_labels_tokens_with_filename`
  - `test_default_omits_regex_and_source_line`
  - `test_trace_includes_regex_and_source_line`
  - `test_source_name_overrides_stdin_label`

  These fail because they use `_SPEC` (no whitespace skip) with newline-terminated input, so the trailing `\n` now produces a `LexError` that their count assertions didn't account for. This is expected breakage — Tasks 3 and 4 fix them.

---

## Task 3: Fix `source_line` display in the formatter

**Files:**
- Modify: `src/plcc/tokens/jsonl_formatter.py:25`

The `source_line` field in `--trace` output is for human display. Without this fix, `source_line` would contain a trailing `\n`, making trace output hard to read and breaking `test_trace_includes_regex_and_source_line`.

- [ ] **Step 1: Strip `\n` from `source_line` before serializing**

  In `src/plcc/tokens/jsonl_formatter.py`, find `format_record` (around line 10). In the `if show_all:` block:

  ```python
  # before
  if show_all:
      record['regex'] = obj.pattern
      record['source_line'] = obj.line.string
  ```

  Change to:

  ```python
  # after
  if show_all:
      record['regex'] = obj.pattern
      record['source_line'] = obj.line.string.rstrip('\n')
  ```

- [ ] **Step 2: Run the formatter unit tests**

  ```bash
  bin/test/units.bash src/plcc/tokens/jsonl_formatter_test.py -v
  ```

  Expected: all **PASS** (the formatter tests do not depend on `\n` in line strings).

---

## Task 4: Update eight existing tests broken by the root change

**Files:**
- Modify: `src/plcc/tokens/tokens_cli_test.py`

All eight tests fail because they use `_SPEC` (only `token NUM '\d+'`, no whitespace skip) with newline-terminated input. After the root change, the trailing `\n` is now a `LexError`, which their count assertions did not expect.

Fix strategy:
- Seven tests: switch from `_SPEC` to `_SPEC_WITH_SKIP` (which has `skip WS '\s+'`). The whitespace skip silently consumes `\n`, so record counts stay the same.
- One test (`test_lex_error_emits_error_record_to_stdout`): change the input from `'@\n'` to `'@'` (no trailing newline). This keeps the test focused on the `@` error without a second error from `\n`.

- [ ] **Step 1: Update `test_outputs_token_jsonl`**

  ```python
  def test_outputs_token_jsonl(capsys, monkeypatch, fs):
      fs.create_file('/spec.json', contents=json.dumps(_SPEC_WITH_SKIP))  # changed
      monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
      run_main(['/spec.json'])
      out, err = capsys.readouterr()
      lines = [l for l in out.strip().splitlines() if l]
      records = [json.loads(l) for l in lines]
      non_sentinel = [r for r in records if r.get('name') != 'eof']
      assert len(non_sentinel) == 1
      record = non_sentinel[0]
      assert record['kind'] == 'token'
      assert record['name'] == 'NUM'
      assert record['lexeme'] == '42'
  ```

- [ ] **Step 2: Update `test_lex_error_emits_error_record_to_stdout`**

  ```python
  def test_lex_error_emits_error_record_to_stdout(capsys, monkeypatch, fs):
      fs.create_file('/spec.json', contents=json.dumps(_SPEC))
      monkeypatch.setattr('sys.stdin', io.StringIO('@'))  # changed: no trailing \n
      try:
          run_main(['/spec.json'])
      except SystemExit as e:
          pytest.fail(f"run_main raised SystemExit({e.code}), expected normal return")
      out, err = capsys.readouterr()
      lines = [l for l in out.strip().splitlines() if l]
      records = [json.loads(l) for l in lines]
      error_records = [r for r in records if r.get('kind') == 'error']
      assert len(error_records) == 1
      record = error_records[0]
      assert record['kind'] == 'error'
      assert record['stage'] == 'plcc-tokens'
      assert record['severity'] == 'error'
      assert record['lexeme'] == '@'
      assert record['source'] == {'file': '-', 'line': 1, 'column': 1}
      assert record['message'] == "unrecognized character '@'"
      assert err == ''
  ```

- [ ] **Step 3: Update `test_lex_error_and_token_appear_in_stream_order`**

  ```python
  def test_lex_error_and_token_appear_in_stream_order(capsys, monkeypatch, fs):
      fs.create_file('/spec.json', contents=json.dumps(_SPEC_WITH_SKIP))  # changed
      # '@' is unrecognized, then '42' is a valid NUM token
      monkeypatch.setattr('sys.stdin', io.StringIO('@42\n'))
      run_main(['/spec.json'])
      out, err = capsys.readouterr()
      lines = [l for l in out.strip().splitlines() if l]
      records = [json.loads(l) for l in lines]
      non_sentinel = [r for r in records if r.get('name') != 'eof']
      assert len(non_sentinel) == 2
      assert non_sentinel[0]['kind'] == 'error'
      assert non_sentinel[1]['kind'] == 'token'
      assert non_sentinel[1]['name'] == 'NUM'
  ```

- [ ] **Step 4: Update `test_stdin_labels_tokens_with_dash`**

  ```python
  def test_stdin_labels_tokens_with_dash(capsys, monkeypatch, fs):
      fs.create_file('/spec.json', contents=json.dumps(_SPEC_WITH_SKIP))  # changed
      monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
      run_main(['/spec.json'])
      out, _ = capsys.readouterr()
      records = [json.loads(l) for l in out.strip().splitlines() if l]
      token_records = [r for r in records if r.get('name') != 'eof']
      assert len(token_records) == 1
      assert token_records[0]['source']['file'] == '-'
  ```

- [ ] **Step 5: Update `test_named_file_arg_labels_tokens_with_filename`**

  ```python
  def test_named_file_arg_labels_tokens_with_filename(capsys, fs):
      fs.create_file('/spec.json', contents=json.dumps(_SPEC_WITH_SKIP))  # changed
      fs.create_file('/src.txt', contents='42\n')
      run_main(['/spec.json', '/src.txt'])
      out, _ = capsys.readouterr()
      records = [json.loads(l) for l in out.strip().splitlines() if l]
      token_records = [r for r in records if r.get('name') != 'eof']
      assert len(token_records) == 1
      assert token_records[0]['source']['file'] == '/src.txt'
  ```

- [ ] **Step 6: Update `test_default_omits_regex_and_source_line`**

  ```python
  def test_default_omits_regex_and_source_line(capsys, monkeypatch, fs):
      fs.create_file('/spec.json', contents=json.dumps(_SPEC_WITH_SKIP))  # changed
      monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
      run_main(['/spec.json'])
      out, _ = capsys.readouterr()
      records = [json.loads(l) for l in out.strip().splitlines() if l]
      token_records = [r for r in records if r.get('name') != 'eof']
      assert len(token_records) == 1
      record = token_records[0]
      assert 'regex' not in record
      assert 'source_line' not in record
  ```

- [ ] **Step 7: Update `test_trace_includes_regex_and_source_line`**

  This test also checks `source_line == '42'`. That assertion continues to pass because Task 3 strips `\n` from `source_line` in the formatter.

  ```python
  def test_trace_includes_regex_and_source_line(capsys, monkeypatch, fs):
      fs.create_file('/spec.json', contents=json.dumps(_SPEC_WITH_SKIP))  # changed
      monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
      run_main(['--trace', '/spec.json'])
      out, _ = capsys.readouterr()
      records = [json.loads(l) for l in out.strip().splitlines() if l]
      token_records = [r for r in records if r.get('name') != 'eof']
      assert len(token_records) == 1
      record = token_records[0]
      assert record['regex'] == '\\d+'
      assert record['source_line'] == '42'
  ```

- [ ] **Step 8: Update `test_source_name_overrides_stdin_label`**

  ```python
  def test_source_name_overrides_stdin_label(capsys, monkeypatch, fs):
      fs.create_file('/spec.json', contents=json.dumps(_SPEC_WITH_SKIP))  # changed
      monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
      run_main(['/spec.json', '--source-name=myfile.txt', '-'])
      out, _ = capsys.readouterr()
      records = [json.loads(l) for l in out.strip().splitlines() if l]
      token_records = [r for r in records if r.get('name') != 'eof']
      assert len(token_records) == 1
      assert token_records[0]['source']['file'] == 'myfile.txt'
  ```

- [ ] **Step 9: Run the full token unit suite and confirm all pass**

  ```bash
  bin/test/units.bash src/plcc/tokens/ -v
  ```

  Expected: all tests **PASS**, including the two new tests from Task 1.

- [ ] **Step 10: Run the full unit suite**

  ```bash
  bin/test/units.bash
  ```

  Expected: all tests **PASS**.

- [ ] **Step 11: Commit**

  ```bash
  git add src/plcc/tokens/tokens_cli.py \
          src/plcc/tokens/jsonl_formatter.py \
          src/plcc/tokens/tokens_cli_test.py
  git commit -m "$(cat <<'EOF'
  feat(scan): preserve newlines in scanner input, matching original PLCC behavior

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```
