# Error Handling Redesign — Part 2: Stage-Local Code Changes (Sonnet)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Model:** Sonnet. This part is well-specified TDD on Level 0 stages — extending `verbose.emit_error`, removing in-band error records, toggling `plcc-ll1`'s exit semantics. Mechanical, test-first, small blast radius per task.

**Goal:** Apply the code changes that Part 1's §17.9 amendment requires, limited to Level 0 stages and the intra-stage logic of `plcc-make`. After Part 2, `plcc-tokens` emits errors to stderr with nonzero exit; `plcc-ll1` always exits 0 and signals non-LL(1) via `is_ll1` in its output; `plcc-make` reads `build/ll1.json` and aborts when `is_ll1` is false.

**Design reference:** `docs/design/2026-04-12-multi-lang-pipeline.md` §17.9 (landed by Part 1).

**Predecessor:** `docs/plans/2026-04-17-error-handling-1-docs-opus.md` must be merged first. The schemas and contracts this plan modifies are described in the §17.9 amendment; without it, this plan is editing against a stale design.

**Successor:** `docs/plans/2026-04-17-error-handling-3-orchestrators-opus.md` — pipefail discipline and cascade-suppression in `plcc-scan`, `plcc-parse`, `plcc-rep`. Those orchestrators drive actual subprocess pipelines; `plcc-make` runs stages sequentially with file-mediated stdout, so its failure handling is simpler and lives in this plan.

**Tech stack:** Python 3.12+, pdm, pytest, docopt-ng, BATS, check-jsonschema.

---

## Task 1 — Verify green bar

**Files:**
- Run only: `bin/test/all.bash`

- [ ] **Step 1: Run the full test suite**

```bash
cd /workspaces/plcc-ng/.worktrees/multi-lang
bin/test/all.bash
```

Expected: all tests pass. Do not proceed until green.

- [ ] **Step 2: Record test counts**

Record passing unit tests and BATS tests. Unit counts will grow in this plan (new `emit_error` tests, rewritten lex-error tests); BATS counts should be stable or grow slightly (new integration coverage for the stderr error path).

---

## Task 2 — Extend `VerboseContext` with `emit_error`

**Files:**
- Edit: `src/plcc/verbose.py`
- Edit: `src/plcc/verbose_test.py`

Context: `VerboseContext.emit` already exists for level-gated diagnostic events. Errors are not level-gated (always emitted, §17.8.4) and have a distinct record shape. The cleanest addition is a sibling method `emit_error` that reuses the same text/json branching but ignores the level gate and always writes `"event": "error"` in JSON mode.

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/verbose_test.py`:

```python
def test_emit_error_text_format(capsys):
    ctx = VerboseContext("plcc-tokens", SampleEvents, level=0, fmt="text")
    ctx.emit_error(
        pos={"file": "prog.txt", "line": 4, "column": 12},
        message="unrecognized character '$'",
    )
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "plcc-tokens: prog.txt:4:12: error: unrecognized character '$'\n"


def test_emit_error_text_format_no_file(capsys):
    ctx = VerboseContext("plcc-tokens", SampleEvents, level=0, fmt="text")
    ctx.emit_error(
        pos={"file": None, "line": 1, "column": 1},
        message="unrecognized character",
    )
    _, err = capsys.readouterr()
    assert err == "plcc-tokens: <stdin>:1:1: error: unrecognized character\n"


def test_emit_error_json_format(capsys):
    ctx = VerboseContext("plcc-tokens", SampleEvents, level=0, fmt="json")
    ctx.emit_error(
        pos={"file": "prog.txt", "line": 4, "column": 12},
        message="unrecognized character '$'",
        codepoint=36,
    )
    out, err = capsys.readouterr()
    assert out == ""
    lines = [l for l in err.strip().splitlines() if l]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["stage"] == "plcc-tokens"
    assert record["event"] == "error"
    assert record["severity"] == "error"
    assert record["pos"] == {"file": "prog.txt", "line": 4, "column": 12}
    assert record["message"] == "unrecognized character '$'"
    assert record["codepoint"] == 36


def test_emit_error_ignores_verbose_level(capsys):
    # Even at level 0, errors must still emit.
    ctx = VerboseContext("plcc-tokens", SampleEvents, level=0, fmt="text")
    ctx.emit_error(
        pos={"file": "prog.txt", "line": 1, "column": 1},
        message="boom",
    )
    _, err = capsys.readouterr()
    assert "error: boom" in err
```

- [ ] **Step 2: Run the tests, confirm they fail**

```bash
bin/test/units.bash src/plcc/verbose_test.py
```

Expected: four tests fail (method does not exist yet).

- [ ] **Step 3: Implement `emit_error` in `VerboseContext`**

Edit `src/plcc/verbose.py`. Add a method on `VerboseContext`:

```python
def emit_error(self, pos, message, **fields):
    """Emit a structured error. Never level-gated; always goes to stderr."""
    if self.fmt == "json":
        record = {
            "stage": self.stage,
            "time": time.monotonic_ns(),
            "event": "error",
            "severity": "error",
            "pos": pos,
            "message": message,
            **fields,
        }
        print(json.dumps(record), file=sys.stderr, flush=True)
    else:
        file = pos.get("file") or "<stdin>"
        line = pos.get("line", 0)
        col = pos.get("column", 0)
        print(
            f"{self.stage}: {file}:{line}:{col}: error: {message}",
            file=sys.stderr,
            flush=True,
        )
```

Place it next to `emit`.

- [ ] **Step 4: Run the tests, confirm they pass**

```bash
bin/test/units.bash src/plcc/verbose_test.py
```

Expected: all four new tests pass; existing tests still pass.

- [ ] **Step 5: Run the full unit suite**

```bash
bin/test/units.bash
```

Expected: green.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/verbose.py src/plcc/verbose_test.py
git commit -m "feat(verbose): add VerboseContext.emit_error for stderr + exit-code error path per §17.9"
```

---

## Task 3 — Remove in-band errors from token pipeline

**Files:**
- Edit: `src/plcc/schemas/token.schema.json`
- Edit: `src/plcc/tokens/jsonl_formatter.py`
- Edit: `src/plcc/tokens/jsonl_formatter_test.py`
- Edit: `src/plcc/tokens/tokens_cli.py`
- Edit: `src/plcc/tokens/tokens_cli_test.py`
- Edit (if present): `tests/bats/commands/plcc-tokens.bats`

Context: `plcc-tokens` currently emits `{"kind": "error", ...}` records in-band on unrecognized input, per the now-retired §8. Under §17.9, the tool stops at the first lex error, writes a structured error to stderr via `VerboseContext.emit_error`, and exits nonzero. `format_record` stops handling `LexError`. The schema's `oneOf` collapses to a single token shape.

- [ ] **Step 1: Rewrite the failing test**

In `src/plcc/tokens/tokens_cli_test.py`, replace `test_lex_error_is_inband` (and the later `assert err == ''` assertion) with the new contract:

```python
def test_lex_error_goes_to_stderr_and_exits_nonzero(capsys, monkeypatch, fs):
    spec = {
        "lexical": {"ruleList": [
            {"name": "NUM", "pattern": "\\d+", "isSkip": False,
             "line": {"string": "", "number": 1, "file": None}}
        ]},
        "syntax": {"rules": []},
        "semantics": []
    }
    import json as _json
    fs.create_file('/spec.json', contents=_json.dumps(spec))
    monkeypatch.setattr('sys.stdin', io.StringIO('abc\n'))  # not a NUM
    with pytest.raises(SystemExit) as excinfo:
        run_main(['/spec.json'])
    assert excinfo.value.code != 0
    out, err = capsys.readouterr()
    # stdout may contain zero or more token lines but no error records
    for line in out.strip().splitlines():
        if not line:
            continue
        record = json.loads(line)
        assert record['kind'] == 'token'
    # stderr carries the error
    assert 'error' in err
    assert 'plcc-tokens' in err
```

Also add a test for JSON-format error output:

```python
def test_lex_error_json_format(capsys, monkeypatch, fs):
    spec = {
        "lexical": {"ruleList": [
            {"name": "NUM", "pattern": "\\d+", "isSkip": False,
             "line": {"string": "", "number": 1, "file": None}}
        ]},
        "syntax": {"rules": []},
        "semantics": []
    }
    import json as _json
    fs.create_file('/spec.json', contents=_json.dumps(spec))
    monkeypatch.setattr('sys.stdin', io.StringIO('abc\n'))
    with pytest.raises(SystemExit):
        run_main(['/spec.json', '--verbose-format=json'])
    _, err = capsys.readouterr()
    records = [json.loads(l) for l in err.strip().splitlines() if l.strip()]
    error_records = [r for r in records if r.get('event') == 'error']
    assert len(error_records) >= 1
    assert error_records[0]['stage'] == 'plcc-tokens'
    assert error_records[0]['severity'] == 'error'
    assert 'pos' in error_records[0]
```

- [ ] **Step 2: Rewrite the formatter test**

In `src/plcc/tokens/jsonl_formatter_test.py`, delete `test_formats_lex_error` entirely. Add a test that `format_record` raises `TypeError` on anything that is not a `Token`:

```python
def test_format_record_rejects_lex_error():
    from plcc.scan.LexError import LexError
    from plcc.lines import Line
    err = LexError(line=Line(string="abc", number=1, file=None), column=1)
    with pytest.raises(TypeError):
        format_record(err)
```

- [ ] **Step 3: Run the failing tests**

```bash
bin/test/units.bash src/plcc/tokens/
```

Expected: the new tests fail (in-band error path still exists); existing token-formatter tests may also fail where they asserted the error shape.

- [ ] **Step 4: Update the schema**

Edit `src/plcc/schemas/token.schema.json`. Remove the second `oneOf` branch (the error record) and collapse to a single shape. The result:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TokenRecord",
  "description": "One JSONL record from plcc-tokens.",
  "type": "object",
  "required": ["kind", "name", "lexeme", "source"],
  "properties": {
    "kind":   { "type": "string", "const": "token" },
    "name":   { "type": "string" },
    "lexeme": { "type": "string" },
    "source": {
      "type": "object",
      "required": ["file", "line", "column"],
      "properties": {
        "file":   { "type": ["string", "null"] },
        "line":   { "type": "integer", "minimum": 1 },
        "column": { "type": "integer", "minimum": 1 }
      }
    }
  }
}
```

- [ ] **Step 5: Update `jsonl_formatter.py`**

Replace the body of `format_record` with:

```python
def format_record(obj):
    """Return a single-line JSON string for a token. Errors do not pass through here."""
    if isinstance(obj, Token):
        return json.dumps({
            'kind': 'token',
            'name': obj.name,
            'lexeme': obj.lexeme,
            'source': {
                'file': obj.line.file,
                'line': obj.line.number,
                'column': obj.column,
            },
        })
    raise TypeError(f'Unexpected type: {type(obj)}')
```

Remove the `LexError` import if it is no longer used in this module.

- [ ] **Step 6: Update `tokens_cli.py`**

Edit the main loop to stop at the first `LexError`, emit to stderr via `emit_error`, and exit nonzero. Replace the loop:

```python
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
            message=f"unrecognized character at {obj.line.file or '<stdin>'}:{obj.line.number}:{obj.column}",
        )
        sys.exit(1)
    print(format_record(obj), flush=True)
```

Add `from ..scan.LexError import LexError` to the imports. The message format may be refined in a follow-up — what matters now is that an error is structured, reaches stderr, and the process exits nonzero.

- [ ] **Step 7: Run the failing tests, confirm they pass**

```bash
bin/test/units.bash src/plcc/tokens/
```

Expected: all new and updated tests pass. If the scanner's `_scanLine` still advances past a bad char (it does), that is fine — the CLI's `sys.exit(1)` stops the iteration before the scanner can yield any more tokens.

- [ ] **Step 8: Update BATS coverage**

Open `tests/bats/commands/plcc-tokens.bats`. If it has a test asserting that errors are in-band on stdout, rewrite it to assert:

- nonzero exit
- no `"kind": "error"` records on stdout
- `error` text or a `"event": "error"` JSONL record on stderr, per `--verbose-format`

If no such test exists, add one covering an unrecognized-character input.

- [ ] **Step 9: Run the full test suite**

```bash
bin/test/functional.bash
```

Expected: green.

- [ ] **Step 10: Commit**

```bash
git add src/plcc/schemas/token.schema.json src/plcc/tokens/ tests/bats/commands/plcc-tokens.bats
git commit -m "feat(tokens): route lex errors to stderr + exit nonzero per §17.9; drop in-band error schema"
```

---

## Task 4 — Remove `error` from the tree children enum

**Files:**
- Edit: `src/plcc/schemas/tree.schema.json`
- Edit (if needed): `tests/bats/commands/plcc-tree.bats`

Context: the tree schema currently allows children of kind `token`, `tree`, or `error`. Under §17.9 plus the Part 1 simplification, trees are made of tokens and subtrees only; errors go to stderr.

- [ ] **Step 1: Edit `tree.schema.json`**

Change the children `kind` enum from `["token", "tree", "error"]` to `["token", "tree"]`.

- [ ] **Step 2: Check BATS tests**

```bash
grep -n '"error"' tests/bats/commands/plcc-tree.bats
```

If any test asserts an `"error"` node in tree output, rewrite it to assert the nonzero-exit + stderr contract instead. If none do, no change needed.

- [ ] **Step 3: Run the full test suite**

```bash
bin/test/functional.bash
```

Expected: green.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/schemas/tree.schema.json tests/bats/commands/plcc-tree.bats
git commit -m "refactor(tree): drop 'error' from children kind enum; errors go to stderr per §17.9"
```

---

## Task 5 — `plcc-ll1`: add `is_ll1` field; always exit 0

**Files:**
- Edit: `src/plcc/ll1/ll1_cli.py`
- Create or edit: `src/plcc/ll1/ll1_cli_test.py` (create if missing)

Context: `plcc-ll1` is currently a stub that emits empty sets and exits 0 (except on tool failures such as missing input). Under §17.9, its output must carry `is_ll1` (boolean), plus `conflicts` and `left_recursion` arrays (already present in the stub as empty). Since the stub does no real analysis, `is_ll1` defaults to `true`. Real LL(1) computation remains a Phase 2 Part 1 implementation item; this plan only commits to the stub-level contract.

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/ll1/ll1_cli_test.py` (or extend an existing test file if present):

```python
import io
import json
import pytest

from plcc.ll1.ll1_cli import main as run_main


def test_stub_emits_is_ll1_true_and_exits_zero(capsys, monkeypatch, fs):
    spec = {"lexical": {"ruleList": []}, "syntax": {"rules": []}, "semantics": []}
    fs.create_file('/spec.json', contents=json.dumps(spec))
    run_main(['/spec.json'])
    out, err = capsys.readouterr()
    record = json.loads(out)
    assert record['is_ll1'] is True
    assert record['conflicts'] == []
    assert record['left_recursion'] == []


def test_stub_accepts_stdin(capsys, monkeypatch):
    spec = {"lexical": {"ruleList": []}, "syntax": {"rules": []}, "semantics": []}
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(spec)))
    run_main(['-'])
    out, _ = capsys.readouterr()
    record = json.loads(out)
    assert record['is_ll1'] is True
```

- [ ] **Step 2: Run, confirm failure**

```bash
bin/test/units.bash src/plcc/ll1/
```

Expected: new tests fail because `is_ll1` is not yet emitted.

- [ ] **Step 3: Update `ll1_cli.py`**

Add `is_ll1` to the result dict:

```python
result = {
    "is_ll1": not (conflicts or left_recursion),  # stub: both empty -> True
    "first_sets": {},
    "follow_sets": {},
    "predict_sets": {},
    "parse_table": {},
    "conflicts": [],
    "left_recursion": [],
}
```

For the stub, `conflicts` and `left_recursion` are always empty, so `is_ll1` is always `true`. When real analysis lands in Phase 2 Part 1, the field will track the actual result.

- [ ] **Step 4: Run, confirm pass**

```bash
bin/test/units.bash src/plcc/ll1/
```

Expected: green.

- [ ] **Step 5: Update BATS coverage**

Check for a BATS test for `plcc-ll1`. If one exists, add an assertion that the output JSON contains `"is_ll1"`. If none exists, add a small one:

```bash
# tests/bats/commands/plcc-ll1.bats (create if missing)
@test "plcc-ll1 stub: is_ll1 is true for empty spec" {
    run bash -c "echo '{\"lexical\":{\"ruleList\":[]},\"syntax\":{\"rules\":[]},\"semantics\":[]}' | plcc-ll1 -"
    [ "$status" -eq 0 ]
    echo "$output" | grep -q '"is_ll1": *true'
}
```

- [ ] **Step 6: Run the full functional suite**

```bash
bin/test/functional.bash
```

Expected: green.

- [ ] **Step 7: Commit**

```bash
git add src/plcc/ll1/ tests/bats/commands/plcc-ll1.bats
git commit -m "feat(ll1): emit is_ll1 field; keep exit 0 on non-LL(1) per §17.9 (stub)"
```

---

## Task 6 — `plcc-make`: abort on `is_ll1: false`

**Files:**
- Edit: `src/plcc/cmd/make.py`
- Edit: `src/plcc/cmd/make_test.py`

Context: `plcc-make` already runs `plcc-ll1` and redirects stdout to `build/ll1.json`. Under §17.9, after that run succeeds, make must read the file back, check `is_ll1`, and abort with a human-readable conflict summary on stderr if it is false.

- [ ] **Step 1: Write the failing test**

Extend `src/plcc/cmd/make_test.py` (or create if missing):

```python
def test_make_aborts_when_ll1_false(tmp_path, monkeypatch):
    # Arrange: a ll1.json with is_ll1 false
    # Arrange: a shim plcc-ll1 that writes that file
    # (exact shim layout depends on how make_test already stubs subprocesses —
    # follow the existing pattern)
    ...
    # Act + Assert: plcc-make should exit nonzero and stderr should mention
    # the conflict (nonterminal, lookahead, competing productions).
```

If `make_test.py` does not yet exercise the ll1 phase end-to-end, model the new test after whatever pattern is already in use for testing `_run_or_die`. The test's essential assertions:

- `plcc-make` exits nonzero.
- `build/ll1.json` exists and contains `is_ll1: false` plus the conflict detail.
- stderr contains `plcc-make: error:` plus a reference to the conflict.

- [ ] **Step 2: Update `make.py`**

After the LL(1) phase, add a check:

```python
# 3. LL(1)
verbose.emit(Events.PHASE, message="ll1")
ll1_json = os.path.join(build_dir, 'll1.json')
_run_or_die(['plcc-ll1', spec_json] + child_flags, stdout_file=ll1_json, verbose=verbose)

with open(ll1_json) as f:
    ll1 = json.load(f)
if not ll1.get("is_ll1", True):
    _report_ll1_failure(ll1, ll1_json, verbose)
    sys.exit(1)
```

And the helper:

```python
def _report_ll1_failure(ll1, path, verbose):
    print(
        f"plcc-make: error: grammar is not LL(1); see {path}",
        file=sys.stderr,
    )
    for conflict in ll1.get("conflicts", []):
        print(
            f"plcc-make: error: conflict at "
            f"{conflict.get('nonterminal', '?')} on "
            f"{conflict.get('lookahead', '?')}: "
            f"{conflict.get('competing', [])}",
            file=sys.stderr,
        )
    for cycle in ll1.get("left_recursion", []):
        print(
            f"plcc-make: error: left-recursion cycle: {' -> '.join(cycle)}",
            file=sys.stderr,
        )
```

(Exact key names on `conflicts` and `left_recursion` entries are Phase 2 Part 1's decision; adjust to match whatever `plcc-ll1` emits when it gains real analysis. For now, the helper tolerates missing keys via `.get`.)

- [ ] **Step 3: Run, confirm pass**

```bash
bin/test/units.bash src/plcc/cmd/make_test.py
bin/test/functional.bash
```

Expected: green.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
git commit -m "feat(make): abort on is_ll1:false with human-readable conflict summary per §17.9"
```

---

## Task 7 — Final verification

- [ ] **Step 1: Full suite**

```bash
bin/test/all.bash
```

Expected: green. Unit count grew from Task 1; BATS count stable or grew.

- [ ] **Step 2: Manual smoke test — token error**

```bash
echo 'abc' | plcc-tokens build/spec.json
echo "exit: $?"
```

Expected: `exit: 1`, error line on stderr of the form `plcc-tokens: <stdin>:...: error: ...`.

- [ ] **Step 3: Manual smoke test — `plcc-ll1` stub**

```bash
echo '{"lexical":{"ruleList":[]},"syntax":{"rules":[]},"semantics":[]}' | plcc-ll1 -
echo "exit: $?"
```

Expected: `exit: 0`, stdout JSON contains `"is_ll1": true`.

- [ ] **Step 4: Manual smoke test — `plcc-make` happy path**

```bash
bin/test/e2e.bash
```

Expected: green. Verifies that the build/ll1.json change has not broken end-to-end builds.

## Handoff

When this plan is complete and committed:

1. Hand off to `docs/plans/2026-04-17-error-handling-3-orchestrators-opus.md` (fresh Opus session).
2. Part 3 wires pipefail discipline and cascade suppression into `plcc-scan`, `plcc-parse`, and `plcc-rep` — the orchestrators that drive actual subprocess pipelines.
3. After Part 3, the full error contract described by §17.9 is in force end-to-end.
