# Stop Error Cascade in plcc-parser-table Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the error-cascade loop in `plcc-parser-table` with a clean stop-on-first-error, so students see exactly one error message per bad input rather than a chain of cascaded errors.

**Architecture:** One word changes in `table_cli.py` (`cursor += 1` → `break`); one existing test is renamed and updated (cascade-then-tree test now expects error-only); two new tests are added covering the core scenarios from the spec. No other runtime code paths change.

**Tech Stack:** Python, pytest (`bin/test/units.bash` for the TDD loop)

---

## Files

- Modify: `src/plcc/parser/table_cli.py` — remove cascade; simplify error branch
- Modify: `src/plcc/parser/table_cli_test.py` — update one test; add three new tests

---

### Task 1: Update the cascade test to expect error-only (failing test)

The existing test `test_skip_and_retry_emits_error_then_tree` tests the OLD cascade
behaviour — error followed by a tree recovered from the next token. Rename and
rewrite it to assert the NEW behaviour: error stops the loop, no tree follows.

**Files:**
- Modify: `src/plcc/parser/table_cli_test.py`

- [ ] **Step 1: Replace the test**

In [src/plcc/parser/table_cli_test.py](src/plcc/parser/table_cli_test.py), find and
replace `test_skip_and_retry_emits_error_then_tree` (around line 259) with:

```python
def test_non_eof_error_stops_loop(capsys, monkeypatch):
    # Grammar: program → NUM; tokens: [PLUS, NUM, eof]
    # PLUS is not a valid start token. With the cascade removed, the loop breaks
    # immediately on the PLUS error and never attempts to parse NUM.
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        tokens = [_tok("PLUS", "+"), _tok("NUM", "42"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        errors = [r for r in records if r.get("kind") == "error"]
        trees  = [r for r in records if r.get("kind") == "tree"]
        assert len(errors) == 1
        assert len(trees) == 0
    finally:
        os.unlink(ll1_file.name)
```

- [ ] **Step 2: Run and confirm it fails**

```bash
bin/test/units.bash src/plcc/parser/table_cli_test.py::test_non_eof_error_stops_loop -v
```

Expected: **FAIL** — current code still cascades, so a tree is produced after the
error. The assertion `len(trees) == 0` fails.

---

### Task 2: Add test — three bad tokens produce one error

Covers the `3 2 1` scenario from the spec: a grammar expecting `NUM PLUS NUM`, given
three consecutive integers, should emit exactly one error and stop.

**Files:**
- Modify: `src/plcc/parser/table_cli_test.py`

- [ ] **Step 1: Add the test**

Append to [src/plcc/parser/table_cli_test.py](src/plcc/parser/table_cli_test.py):

```python
def test_three_invalid_tokens_emit_one_error(capsys, monkeypatch):
    # Grammar: program → NUM PLUS NUM; tokens: [NUM(3), NUM(2), NUM(1), eof]
    # cursor=0: parse NUM(3), expect PLUS, find NUM(2) → error (found="NUM").
    # With cascade: cursor advances, two more errors follow. Without cascade: one error.
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_ADDITION_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        tokens = [_tok("NUM", "3"), _tok("NUM", "2"), _tok("NUM", "1"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        errors = [r for r in records if r.get("kind") == "error"]
        trees  = [r for r in records if r.get("kind") == "tree"]
        assert len(errors) == 1
        assert len(trees) == 0
        assert errors[0].get("found") != "eof"
    finally:
        os.unlink(ll1_file.name)
```

- [ ] **Step 2: Run and confirm it fails**

```bash
bin/test/units.bash src/plcc/parser/table_cli_test.py::test_three_invalid_tokens_emit_one_error -v
```

Expected: **FAIL** — current code cascades through all three tokens, emitting three
errors. The assertion `len(errors) == 1` fails.

---

### Task 3: Add test — error after success stops further parsing

Covers the batch-file scenario: after one successful tree, a bad token should produce
one error and stop — not cascade to recover a second tree.

**Files:**
- Modify: `src/plcc/parser/table_cli_test.py`

- [ ] **Step 1: Add the test**

Append to [src/plcc/parser/table_cli_test.py](src/plcc/parser/table_cli_test.py):

```python
def test_error_after_success_stops_further_parsing(capsys, monkeypatch):
    # Grammar: program → NUM; tokens: [NUM(1), PLUS(+), NUM(2), eof]
    # cursor=0: parse NUM(1) → tree, cursor=1.
    # cursor=1: parse PLUS → error (found="PLUS"). Without cascade: stop.
    # With cascade: cursor=2, parse NUM(2) → second tree.
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        tokens = [_tok("NUM", "1"), _tok("PLUS", "+"), _tok("NUM", "2"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        errors = [r for r in records if r.get("kind") == "error"]
        trees  = [r for r in records if r.get("kind") == "tree"]
        assert len(trees) == 1
        assert len(errors) == 1
        assert records[0]["kind"] == "tree"
        assert records[1]["kind"] == "error"
    finally:
        os.unlink(ll1_file.name)
```

- [ ] **Step 2: Run and confirm it fails**

```bash
bin/test/units.bash src/plcc/parser/table_cli_test.py::test_error_after_success_stops_further_parsing -v
```

Expected: **FAIL** — current code cascades past the PLUS error and parses NUM(2),
producing two trees. The assertion `len(trees) == 1` fails.

---

### Task 4: Implement the fix

Remove the cascade. One logical change, two lines touched.

**Files:**
- Modify: `src/plcc/parser/table_cli.py`

- [ ] **Step 1: Apply the change**

In [src/plcc/parser/table_cli.py](src/plcc/parser/table_cli.py), find the
`except ParseError` block (around line 94) and replace it:

```python
        except ParseError as e:
            record = {
                "kind": "error",
                "message": str(e),
                "stage": "plcc-parser-table",
                "source": e.source,
            }
            if e.found:
                record["found"] = e.found
            print(json.dumps(record), flush=True)
            break
```

The `if e.found == "eof": break` branch is removed — both eof and non-eof errors now
simply break. The `cursor += 1` line is removed.

- [ ] **Step 2: Run all three new failing tests together**

```bash
bin/test/units.bash src/plcc/parser/table_cli_test.py::test_non_eof_error_stops_loop src/plcc/parser/table_cli_test.py::test_three_invalid_tokens_emit_one_error src/plcc/parser/table_cli_test.py::test_error_after_success_stops_further_parsing -v
```

Expected: all three **PASS**.

- [ ] **Step 3: Run the full unit suite**

```bash
bin/test/units.bash
```

Expected: all tests **PASS**. No regressions.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/parser/table_cli.py src/plcc/parser/table_cli_test.py
git commit -m "fix(parser): stop error cascade in plcc-parser-table"
```

---

### Task 5: Verify at the command tier

Run the bats command and integration tests to confirm the fix holds at the CLI
boundary and across the `plcc-tokens | plcc-trees` pipeline.

**Files:** none — read-only verification

- [ ] **Step 1: Run command tests**

```bash
bin/test/commands.bash
```

Expected: **PASS**.

- [ ] **Step 2: Run integration tests**

```bash
bin/test/integration.bash
```

Expected: **PASS**.

- [ ] **Step 3: If any bats test hardcodes cascaded-error counts, update it**

If a bats test fails because it expected multiple errors from one bad input, update
the assertion to expect one. The fix is correct; the test was encoding the old
(wrong) behaviour.

After any bats updates:

```bash
git add tests/bats/
git commit -m "test(bats): update cascade-error counts to expect single error"
```
