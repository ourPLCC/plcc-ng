# Require Colon in RHS `<...>:name` Syntax Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject the no-colon form `<word>hello` on the RHS of syntactic rules and require `<word>:hello`, matching the LHS parser's existing behavior.

**Architecture:** Two surgical edits in `_parseSymbol` and `_parseCapturing` in `parse_syntactic_spec.py` — swap `re.match` for `re.fullmatch` with a colon-required regex and add a `<` guard that raises `MalformedBNFError`, then delete the now-redundant `strip(":")` call. One test is converted from a success case to an error case.

**Tech Stack:** Python, pytest, `re` stdlib module.

---

### Task 1: Convert the existing no-colon test to an error case

**Files:**
- Modify: `src/plcc/spec/syntax/parse_syntactic_spec_test.py:303-318`

- [ ] **Step 1: Replace the test**

Find `test_named_rhs_non_terminal` (around line 303) and replace it entirely:

```python
def test_named_rhs_non_terminal_without_colon_is_an_error():
    line = makeLine("<noun> ::= WORD WORD <word>hello")
    spec, errors = parse_syntactic_spec([makeDivider(), line])
    assert len(errors) == 1
    assert isinstance(errors[0], MalformedBNFError)
```

`MalformedBNFError` is already imported at the top of the test file.

- [ ] **Step 2: Run the new test to verify it fails**

```bash
pytest src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_named_rhs_non_terminal_without_colon_is_an_error -v
```

Expected: **FAIL** — the current implementation accepts `<word>hello`, so `errors` will be empty and the assertion will fail.

---

### Task 2: Fix `_parseSymbol` and `_parseCapturing`

**Files:**
- Modify: `src/plcc/spec/syntax/parse_syntactic_spec.py:87-102`

- [ ] **Step 1: Update `_parseSymbol`**

Replace the current implementation (lines 87–93):

```python
def _parseSymbol(self, symbol: str) -> Symbol:
    capturing = re.match(r"<(?P<name>\S*)>(?P<altName>\S+)?", symbol)
    return (
        self._parseCapturing(capturing["name"], capturing["altName"])
        if capturing
        else Terminal(symbol)
    )
```

With:

```python
def _parseSymbol(self, symbol: str) -> Symbol:
    capturing = re.fullmatch(r"<(?P<name>\S*)>(?::(?P<altName>\S+))?", symbol)
    if capturing:
        return self._parseCapturing(capturing["name"], capturing["altName"])
    if symbol.startswith("<"):
        raise MalformedBNFError(self.line)
    return Terminal(symbol)
```

- `re.fullmatch` requires the entire symbol string to be consumed.
- The regex now requires `:` before the alt name; `altName` captures only what follows the colon.
- If fullmatch fails and the symbol starts with `<`, it is an invalid non-terminal form — raise `MalformedBNFError(self.line)`.
- Plain terminals (e.g. `WORD`) don't start with `<` and fall through to `Terminal(symbol)` as before.

- [ ] **Step 2: Remove `strip(":")` from `_parseCapturing`**

The colon is now consumed by the regex in `_parseSymbol`, so `altName` never includes it. Remove the strip line (line 97):

```python
def _parseCapturing(self, name: str, altName: str) -> CapturingSymbol:
    terminal = re.fullmatch(r"[A-Z_][A-Z0-9_]*", name)
    return (
        CapturingTerminal(name=name, altName=altName)
        if terminal
        else RhsNonTerminal(name, altName)
    )
```

- [ ] **Step 3: Run the converted test to verify it passes**

```bash
pytest src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_named_rhs_non_terminal_without_colon_is_an_error -v
```

Expected: **PASS**

- [ ] **Step 4: Run the full unit suite to verify no regressions**

```bash
bin/test/units.bash
```

Expected: all 905 tests pass (or more, counting the new test name).

- [ ] **Step 5: Commit**

```bash
git add src/plcc/spec/syntax/parse_syntactic_spec.py \
        src/plcc/spec/syntax/parse_syntactic_spec_test.py
git commit -m "$(cat <<'EOF'
refactor(syntax): require colon in RHS <...>:name syntax (issue 052)

`<word>hello` now raises MalformedBNFError; only `<word>:hello` is accepted,
consistent with the LHS parser. Removes the silent strip(":") workaround.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```
