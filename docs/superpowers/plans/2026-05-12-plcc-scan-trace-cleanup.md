# plcc-scan Trace Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the four `--show-*` flags from `plcc-scan` and improve the `--trace` output format to use a clean `location: disposition: details` style.

**Architecture:** Two sequential commits on one branch — commit 1 removes the dead `--show-*` CLI surface (issue 007), commit 2 reformats the trace output (issue 006). The rendering logic lives entirely in `_render_record` in `scan.py`; bats tests cover the CLI contract.

**Tech Stack:** Python (docopt for CLI parsing), bats for CLI tests.

---

## File Map

| File | Changes |
|---|---|
| `src/plcc/cmd/scan.py` | Commit 1: remove `--show-*` from docstring and arg parsing. Commit 2: rewrite `_render_record` output. |
| `tests/bats/commands/plcc-scan.bats` | Commit 1: add removal test, delete 7 `--show-*` tests. Commit 2: add 7 new trace format tests, update 1 existing trace test. |

No new implementation files. The design doc and this plan are also committed on this branch.

---

## Commit 1 — Remove `--show-*` flags (issue 007)

### Task 1: Create a feature branch

- [ ] **Create branch**

```bash
git checkout -b fix-scan-trace-cleanup
```

---

### Task 2: Write a failing bats test asserting `--show-skips` is no longer valid

The flag currently exists, so this test will fail (exit 0 instead of nonzero).

- [ ] **Add this test to `tests/bats/commands/plcc-scan.bats`** — insert after the existing `plcc-scan --grammar-file uses specified grammar` test (around line 108):

```bash
@test "plcc-scan --show-skips is not a recognized flag" {
    run --separate-stderr bash -c "echo '42' | plcc-scan --show-skips"
    [ "$status" -ne 0 ]
}
```

- [ ] **Run to confirm it fails**

```bash
bin/test/commands.bash
```

Expected: the new test reports FAIL because `--show-skips` is currently valid.

---

### Task 3: Remove `--show-*` from `scan.py`

- [ ] **Replace the `__doc__` options block in `src/plcc/cmd/scan.py`**

Old:
```python
    --show-skips                Show skip records in output.
    --show-line                 Show source line and cursor before each token.
    --show-attempts             Show rule match attempts before each token.
    --show-regex                Show matched regex in each token line.
    -t --trace                  Enable all --show-* flags.
```

New:
```python
    -t --trace                  Show detailed scanning output.
```

- [ ] **Replace the flag-parsing block in `main()` in `src/plcc/cmd/scan.py`**

Old:
```python
    trace = args["--trace"]
    show_skips = args["--show-skips"] or trace
    show_line = args["--show-line"] or trace
    show_regex = args["--show-regex"] or trace
    show_attempts = args["--show-attempts"] or trace
    any_enrichment = show_skips or show_line or show_regex or show_attempts
```

New:
```python
    trace = args["--trace"]
    any_enrichment = trace
```

- [ ] **Replace the `_render_record` call in `main()` in `src/plcc/cmd/scan.py`**

Old:
```python
        _render_record(record, show_skips, show_line, show_regex, show_attempts)
```

New:
```python
        _render_record(record, trace, trace, trace)
```

- [ ] **Run commands tests to confirm the new test passes**

```bash
bin/test/commands.bash
```

Expected: the new `--show-skips is not a recognized flag` test passes. The seven old `--show-*` tests fail (they invoke flags that no longer exist).

---

### Task 4: Delete the seven `--show-*` bats tests

- [ ] **Delete these seven complete test blocks from `tests/bats/commands/plcc-scan.bats`:**

```bash
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
```

- [ ] **Run commands tests to confirm all green**

```bash
bin/test/commands.bash
```

Expected: all tests pass.

---

### Task 5: Commit 1

- [ ] **Commit**

```bash
git add src/plcc/cmd/scan.py tests/bats/commands/plcc-scan.bats
git commit -m "$(cat <<'EOF'
fix(scan)!: remove --show-skips, --show-line, --show-regex, --show-attempts flags

BREAKING CHANGE: the four --show-* flags are removed. Use --trace, which
already implied all four, to enable detailed output.
EOF
)"
```

---

## Commit 2 — Improve `--trace` output format (issue 006)

### Task 6: Write failing bats tests for the new `--trace` format

All seven tests below will fail because the current format does not match.

- [ ] **Add these seven tests to `tests/bats/commands/plcc-scan.bats`** — insert after the existing `plcc-scan --trace produces source line, cursor, attempts, and token line` test:

```bash
@test "plcc-scan --trace shows Candidates: heading" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Candidates:"* ]]
}

@test "plcc-scan --trace marks winner with ->" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"-> NUM"* ]]
}

@test "plcc-scan --trace excludes zero-match candidates" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" != *"   WS"* ]]
}

@test "plcc-scan --trace token line uses token: disposition" {
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" =~ -:1:1:\ token:\ NUM\ \'42\' ]]
}

@test "plcc-scan --trace skip line uses skip: disposition" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42 99' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" =~ -:1:3:\ skip:\ WS ]]
}

@test "plcc-scan --trace token line has no regex" {
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    token_line=$(echo "$output" | grep "token: NUM")
    [[ "$token_line" != *"\\d+"* ]]
}

@test "plcc-scan --trace adds blank line after each block" {
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" =~ $'\n\n' ]]
}
```

- [ ] **Run to confirm all seven fail**

```bash
bin/test/commands.bash
```

Expected: the seven new tests report FAIL because the old format is still in place.

---

### Task 7: Rewrite `_render_record` in `scan.py`

- [ ] **Replace the `_render_record` function body in `src/plcc/cmd/scan.py`**

The full new function (`show_regex` removed from signature):

```python
def _render_record(record, show_skips, show_line, show_attempts):
    kind = record.get("kind")

    if kind == "error":
        loc = _location_str(record.get("pos", {}))
        lexeme = record.get("lexeme", "?")
        message = record.get("message", "unrecognized character")
        print(f"{loc}: error: {message} '{lexeme}'", flush=True)
        return

    if kind == "skip" and not show_skips:
        return

    if kind not in ("token", "skip"):
        return

    source = record.get("source", {})
    loc = _location_str(source)
    name = record.get("name", "?")
    lexeme = record.get("lexeme", "?")
    source_line = record.get("source_line", "")
    attempts = record.get("attempts", [])
    col = source.get("column", 1)

    if show_line and source_line:
        print(source_line, flush=True)
        print(" " * (col - 1) + "^", flush=True)

    if show_attempts:
        print("Candidates:", flush=True)
        for attempt in attempts:
            if attempt.get("char_count", 0) == 0:
                continue
            prefix = "-> " if attempt.get("winner") else "   "
            a_name = attempt.get("name", "?")
            a_regex = attempt.get("regex", "?")
            a_count = attempt.get("char_count", 0)
            a_lexeme = attempt.get("lexeme", "?")
            print(f"{prefix}{a_name} '{a_regex}' {a_count} chars '{a_lexeme}'", flush=True)

    if show_attempts:
        if kind == "skip":
            print(f"{loc}: skip: {name} '{lexeme}'", flush=True)
        else:
            print(f"{loc}: token: {name} '{lexeme}'", flush=True)
        print(flush=True)
    elif kind == "skip":
        print(f"{loc} {name} '{lexeme}' SKIPPED", flush=True)
    else:
        print(f"{loc} {name} '{lexeme}'", flush=True)
```

- [ ] **Run commands tests to confirm the seven new tests pass**

```bash
bin/test/commands.bash
```

Expected: the seven new tests pass. The existing `--trace` test may still pass or may fail — check next task.

---

### Task 8: Update the existing `--trace` test

- [ ] **Replace the existing `plcc-scan --trace produces source line, cursor, attempts, and token line` test in `tests/bats/commands/plcc-scan.bats`:**

Old:
```bash
@test "plcc-scan --trace produces source line, cursor, attempts, and token line" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"^"* ]]
    [[ "$output" == *"chars"* ]]
    [[ "$output" =~ \'\\\d\+ ]]
}
```

New:
```bash
@test "plcc-scan --trace produces source line, cursor, candidates, and token line" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"^"* ]]
    [[ "$output" == *"Candidates:"* ]]
    [[ "$output" =~ "token: NUM" ]]
}
```

- [ ] **Run all commands tests to confirm everything is green**

```bash
bin/test/commands.bash
```

Expected: all tests pass with no failures.

---

### Task 9: Commit 2

- [ ] **Commit**

```bash
git add src/plcc/cmd/scan.py tests/bats/commands/plcc-scan.bats
git commit -m "$(cat <<'EOF'
fix(scan): improve --trace output format

- Add Candidates: heading before match attempts
- Mark winning candidate with -> instead of *
- Exclude zero-match candidates from Candidates list
- Use location: disposition: details format for token and skip lines
- Remove regex from token/skip lines (still present in Candidates)
- Add blank line after each match block
EOF
)"
```

---

## Final check

- [ ] **Run the full functional test suite**

```bash
bin/test/functional.bash
```

Expected: all tiers (units, commands, integration, e2e) pass.
