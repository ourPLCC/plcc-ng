# tokens-cli UnclosedBlockError Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Handle `UnclosedBlockError` in `tokens_cli.py` by emitting a JSONL error record instead of crashing.

**Architecture:** Add `format_unclosed_block_error_record` to `jsonl_formatter.py` following the existing pattern of `format_error_record`. Add one `isinstance` branch in `tokens_cli.py` to route `UnclosedBlockError` through it.

**Tech Stack:** Python, pytest, pyfakefs (`fs` fixture used in CLI tests)

---

## File Map

- Modify: `src/plcc/tokens/jsonl_formatter.py` — add `format_unclosed_block_error_record`
- Modify: `src/plcc/tokens/jsonl_formatter_test.py` — unit tests for the new function
- Modify: `src/plcc/tokens/tokens_cli.py` — add `UnclosedBlockError` dispatch branch
- Modify: `src/plcc/tokens/tokens_cli_test.py` — CLI integration test for unclosed block

---

### Task 1: `format_unclosed_block_error_record` in `jsonl_formatter.py`

**Files:**
- Modify: `src/plcc/tokens/jsonl_formatter_test.py`
- Modify: `src/plcc/tokens/jsonl_formatter.py`

- [ ] **Step 1: Write the failing tests**

Add to the bottom of `src/plcc/tokens/jsonl_formatter_test.py`:

```python
from ..scan.UnclosedBlockError import UnclosedBlockError
from ..spec.lexical.TokenRule import TokenRule
from .jsonl_formatter import format_unclosed_block_error_record


def _unclosed_block_error():
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    line = Line(string='<<<hello', number=2, file='src.txt')
    return UnclosedBlockError(line=line, column=1, rule=rule)


def test_format_unclosed_block_error_record_fields():
    err = _unclosed_block_error()
    result = json.loads(format_unclosed_block_error_record(err))
    assert result['kind'] == 'error'
    assert result['stage'] == 'plcc-tokens'
    assert result['severity'] == 'error'
    assert result['source'] == {'file': 'src.txt', 'line': 2, 'column': 1}
    assert result['lexeme'] == r'<<<'
    assert result['message'] == "unclosed block 'BODY': no closing pattern found"


def test_format_unclosed_block_error_record_rejects_non_unclosed_block():
    err = LexError(line=Line(string='abc', number=1, file=None), column=1)
    with pytest.raises(TypeError):
        format_unclosed_block_error_record(err)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/tokens/jsonl_formatter_test.py -v -k "unclosed_block"
```

Expected: `ImportError` or `FAILED` — `format_unclosed_block_error_record` does not exist yet.

- [ ] **Step 3: Implement `format_unclosed_block_error_record`**

In `src/plcc/tokens/jsonl_formatter.py`, add the import and the function. The file currently imports `Token`, `Skip`, `LexError`. Add `UnclosedBlockError` to the imports and append the new function:

```python
from ..scan.UnclosedBlockError import UnclosedBlockError


def format_unclosed_block_error_record(obj):
    if not isinstance(obj, UnclosedBlockError):
        raise TypeError(f'Unexpected type: {type(obj)}')
    return json.dumps({
        'kind': 'error',
        'stage': 'plcc-tokens',
        'severity': 'error',
        'source': {
            'file': obj.line.file,
            'line': obj.line.number,
            'column': obj.column,
        },
        'lexeme': obj.rule.pattern,
        'message': f"unclosed block '{obj.rule.name}': no closing pattern found",
    })
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/tokens/jsonl_formatter_test.py -v -k "unclosed_block"
```

Expected: both new tests PASS.

- [ ] **Step 5: Run the full formatter test file to check for regressions**

```bash
bin/test/units.bash src/plcc/tokens/jsonl_formatter_test.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/tokens/jsonl_formatter.py src/plcc/tokens/jsonl_formatter_test.py
git commit -m "feat(062): add format_unclosed_block_error_record to jsonl_formatter"
```

---

### Task 2: Dispatch `UnclosedBlockError` in `tokens_cli.py`

**Files:**
- Modify: `src/plcc/tokens/tokens_cli_test.py`
- Modify: `src/plcc/tokens/tokens_cli.py`

- [ ] **Step 1: Write the failing test**

Add the spec fixture and test to the bottom of `src/plcc/tokens/tokens_cli_test.py`:

```python
_SPEC_WITH_BLOCK = {
    "lexical": {"ruleList": [
        {"name": "BODY", "pattern": "<<<", "close_pattern": ">>>", "isSkip": False,
         "line": {"string": "", "number": 1, "file": None}},
        {"name": "WS", "pattern": "\\s+", "isSkip": True,
         "line": {"string": "", "number": 2, "file": None}},
    ]},
    "syntax": {"rules": []},
    "semantics": []
}


def test_unclosed_block_emits_error_record(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC_WITH_BLOCK))
    monkeypatch.setattr('sys.stdin', io.StringIO('<<<hello'))  # no closing >>>
    run_main(['/spec.json'])
    out, err = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    records = [json.loads(l) for l in lines]
    error_records = [r for r in records if r.get('kind') == 'error']
    assert len(error_records) == 1
    record = error_records[0]
    assert record['stage'] == 'plcc-tokens'
    assert record['severity'] == 'error'
    assert 'BODY' in record['message']
    assert err == ''
```

- [ ] **Step 2: Run test to verify it fails**

```bash
bin/test/units.bash src/plcc/tokens/tokens_cli_test.py -v -k "unclosed_block"
```

Expected: `FAILED` — the CLI crashes with `AttributeError` or `TypeError` because `UnclosedBlockError` falls through to `format_record`.

- [ ] **Step 3: Add the dispatch branch to `tokens_cli.py`**

In `src/plcc/tokens/tokens_cli.py`, add two imports near the top alongside the existing `LexError` import:

```python
from ..scan.UnclosedBlockError import UnclosedBlockError
from .jsonl_formatter import format_record, format_error_record, format_unclosed_block_error_record
```

Then in the `for obj in scanner.scan(lines)` loop, add the new branch **after** the `LexError` branch and **before** the fall-through to `format_record`:

```python
        if isinstance(obj, UnclosedBlockError):
            print(format_unclosed_block_error_record(obj), flush=True)
            continue
```

The full loop body should read:

```python
    for obj in scanner.scan(lines):
        if isinstance(obj, Skip):
            if trace:
                last_source = {"file": obj.line.file, "line": obj.line.number, "column": obj.column}
                print(format_record(obj, show_all=True), flush=True)
            continue
        if isinstance(obj, LexError):
            print(format_error_record(obj), flush=True)
            continue
        if isinstance(obj, UnclosedBlockError):
            print(format_unclosed_block_error_record(obj), flush=True)
            continue
        last_source = {"file": obj.line.file, "line": obj.line.number, "column": obj.column}
        print(format_record(obj, show_all=trace), flush=True)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
bin/test/units.bash src/plcc/tokens/tokens_cli_test.py -v -k "unclosed_block"
```

Expected: PASS.

- [ ] **Step 5: Run the full CLI test file to check for regressions**

```bash
bin/test/units.bash src/plcc/tokens/tokens_cli_test.py src/plcc/tokens/tokens_cli_sentinel_test.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Run the full unit suite**

```bash
bin/test/units.bash
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/plcc/tokens/tokens_cli.py src/plcc/tokens/tokens_cli_test.py
git commit -m "fix(062): handle UnclosedBlockError in tokens_cli — emit error record"
```
