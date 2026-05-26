# Design: Issues 043 and 044 — Spec Error Improvements

**Date:** 2026-05-26

## Summary

Two related fixes to spec error handling:

- **043**: `parseSpec` silently drops rough-parse errors by shadowing the `errors` variable.
- **044**: Spec errors appear as unstructured multi-line text that gets corrupted when piped through the verbose event layer (`parse_child_events` strips leading whitespace, destroying the caret alignment). The deeper fix aligns `plcc-spec` with the rest of the build-time command architecture by routing its errors through `verbose.emit_error`.

---

## Background: stdout/stderr architecture

The system has two distinct error contexts:

- **Build-time commands** (`plcc-spec`, `plcc-ll1`, `plcc-emit`): run sequentially before any interactive session. No concurrent data stream on stdout. Errors go to stderr via `verbose.emit_error`, which emits JSONL in JSON mode and human-readable text in text mode.
- **Runtime/interactive commands** (`plcc-tokens`, `plcc-tree`): run concurrently during the REPL session. Errors are embedded in the JSONL stream on stdout to preserve ordering with data output.

`plcc-spec` is a build-time command but currently bypasses `verbose.emit_error`, printing multi-line human text directly to stderr. This is the anomaly that causes issue 044.

---

## Fix 1: Issue 043 — Variable shadowing in `parseSpec`

**File:** `src/plcc/spec/parseSpec.py`

Use distinct variable names for each phase so rough errors are not overwritten:

```python
def parseSpec(string, file=None, startLineNumber=1):
    rough_, rough_errors = rough.parseRough(string, file, startLineNumber)
    rough_ = iter(rough_)
    rough_lex, rough_syn, rough_sems = split_rough(rough_)
    lex_, lex_errors = lexical.parseLexicalSpec(rough_lex)
    syn_, syn_errors = syntax.parse_syntactic_spec(rough_syn)
    sems_ = [semantics.parse_semantic_spec(rs) for rs in rough_sems]
    return Spec(lexical=lex_, syntax=syn_, semantics=sems_), rough_errors + lex_errors + syn_errors
```

---

## Fix 2: Issue 044 — Structured spec errors via `verbose.emit_error`

### 2a. Extend `verbose.emit_error` with `source_line` and `hint`

**File:** `src/plcc/verbose.py`

`emit_error` already accepts `**fields` that flow into the JSON record. Two optional fields are given meaning in text mode:

- `source_line`: the text of the offending grammar line
- `hint`: multi-line guidance (e.g. the examples block)

**JSON mode** — no change. Both fields land in the record as top-level fields automatically via `**fields`.

**Text mode** — render the full block when fields are present:

```
plcc-spec: grammar.plcc:23:7: error: syntax error
<stmt>Assign     ::= <IDENT> ASSGN <expr>
      ^
Examples:
  <nonTerminal> ::=
  <nonTerminal> ::= TOKEN <TOKEN> <rhs>
  ...
```

If `source_line` is absent, the existing single-line format is preserved (no regression for other commands).

`reformat_child_events` is extended with the same rendering logic for `event == "error"` records that carry `source_line` and `hint`.

### 2b. Error protocol: `kind` and `hint` properties

All spec errors share a common shape — `.line` (with `.file`, `.number`, `.string`) and `.column`. Two properties are added to make `plcc_spec_cli.py` generic across all error types:

**`SpecError`** (base class for lexical and rough errors):
- `kind` — returns `self.message` if set, otherwise `type(self).__name__`
- `hint` — returns `None`

**`MalformedBNFError`** (syntactic errors):
- `kind` — returns `"syntax error"`
- `hint` — returns `_EXAMPLES`

`__str__` on both classes is unchanged — still used in tests and wherever errors are raised directly.

### 2c. `plcc_spec_cli.py` uses `emit_error`

**File:** `src/plcc/spec/plcc_spec_cli.py`

Replace direct `print(e, file=sys.stderr)` with structured `emit_error` calls:

```python
if errors:
    for e in errors:
        pos = {"file": e.line.file, "line": e.line.number, "column": e.column}
        kwargs = {"source_line": e.line.string}
        if e.hint:
            kwargs["hint"] = e.hint
        verbose.emit_error(pos, e.kind, **kwargs)
    sys.exit(1)
```

No `isinstance` checks. Each error class owns its presentation via `kind` and `hint`.

---

## Testing

### 043
- **`parseSpec_test.py`**: new test — grammar with a circular include (rough error) plus a syntactic error — assert both appear in the returned error list.

### 044 — `verbose`
- **`verbose_test.py`**: `emit_error` text mode with `source_line` and `hint` renders source line, caret, and hint.
- **`verbose_test.py`**: `emit_error` text mode without those fields renders existing single-line format (no regression).
- **`verbose_test.py`**: `reformat_child_events` renders the same full block for an event dict carrying `source_line` and `hint`.

### 044 — error classes
- Unit tests for `kind` and `hint` on `SpecError` and `MalformedBNFError`.

### 044 — `plcc_spec_cli.py`
- Existing `test_malformed_syntactic_rule_prints_error_and_exits_nonzero` stays green.
- New test: malformed syntactic rule → stderr includes source line and caret at correct column.
- New test: lexical error (malformed token rule) → stderr includes source line and caret.

### Integration (bats commands tier)
- Existing `plcc-spec` bats tests stay green.
- New bats test: `plcc-spec` with a malformed syntactic rule → stderr contains source line and caret (guards full end-to-end rendering path).

---

## Files touched

| File | Change |
|------|--------|
| `src/plcc/spec/parseSpec.py` | Rename shadowed variables (043) |
| `src/plcc/spec/parseSpec_test.py` | New test for combined rough + syntactic errors |
| `src/plcc/verbose.py` | Render `source_line`/`hint` in `emit_error` and `reformat_child_events` text mode |
| `src/plcc/verbose_test.py` | New tests for rich error rendering |
| `src/plcc/spec/SpecError.py` | Add `kind` and `hint` properties |
| `src/plcc/spec/syntax/MalformedBNFError.py` | Add `kind` and `hint` properties |
| `src/plcc/spec/syntax/MalformedBNFError_test.py` | New tests for `kind` and `hint` |
| `src/plcc/spec/plcc_spec_cli.py` | Use `verbose.emit_error` instead of `print` |
| `src/plcc/spec/plcc_spec_cli_test.py` | New tests for structured error output |
| `tests/bats/commands/` | New bats test for end-to-end caret rendering |
