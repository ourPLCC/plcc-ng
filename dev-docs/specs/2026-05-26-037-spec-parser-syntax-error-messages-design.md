# Design: Issue 037 — Spec Parser Syntax Error Messages

**Date:** 2026-05-26
**Issue:** [037-spec-parser-syntax-error-messages](../issues/done/037-spec-parser-syntax-error-messages.md)

## Problem

When `plcc-spec` encounters a malformed syntactic rule, it crashes with a Python stack trace. The `MalformedBNFError` exception propagates uncaught to Python's default handler. The error object already carries the file, line number, and offending text — none of it is formatted for a human.

## Error Message Format

Given a malformed line at `grammar.plcc:25`, the output on stderr:

```
grammar.plcc:25:7: syntax error
<stmt>IfStmt     ::= IF <expr> THEN <stmt> <elsePart>
      ^
Examples:
  <nonTerminal> ::=
  <nonTerminal> ::= TOKEN <TOKEN> <rhs>
  <nonTerminal>:ClassName ::= TOKEN <TOKEN>:field1 <rhs>:field2
  <nonTerminal> **= <rhs>
  <nonTerminal> **= <rhs> +SEPARATOR
```

The first line matches the `file:line:col: message` format used by `LexError` in plcc-scan, enabling IDE click-through. The caret points to the first unexpected character. The examples section is static — the same five lines regardless of how the rule is malformed.

### Column Computation

The column is determined by inspecting the offending line:

1. Try to match the LHS pattern `<\S+>(?::\S+)?` against the stripped line.
2. If matched: `column = leading_whitespace_length + lhs_match.end() + 1` (1-based, points to first char after LHS).
3. If not matched: `column = index of first non-whitespace character + 1` (column 1 if no leading whitespace).

## Architecture

Three changes, following the pattern established by the lexical parser.

### 1. `MalformedBNFError.__str__`

Add a `__str__` method that produces the format above. The class already holds the full `Line` object (with `file`, `number`, `string`); it computes the column internally.

### 2. `SyntacticParser` — collect errors, continue parsing

In `SyntacticParser._parseLine`, catch `MalformedBNFError`, append to an internal `self.errors` list, and continue to the next line. `parseSpec` returns `(SyntacticSpec, errors)` instead of just `SyntacticSpec`. `parse_syntactic_spec` is updated to match.

### 3. `parseSpec.py` — merge syntactic errors

`parseSpec.py` unpacks the `(spec, errors)` tuple from `syntax.parse_syntactic_spec` and merges the syntactic errors into the combined `errors` list alongside lexical errors.

`plcc_spec_cli.py` requires no changes — it already prints every item in the errors list to stderr and exits 1.

## Tests

### `parse_syntactic_spec_test.py`

- **`test_malformed_bnf_raises`** — rename to `test_malformed_bnf_returned_as_error`: assert the returned errors list contains a `MalformedBNFError` and parsing continues (spec is returned).
- **`test_malformed_bnf_column_after_lhs`** — line `<stmt>IfStmt ::= ...`: assert `error.column == 7`.
- **`test_malformed_bnf_column_no_lhs`** — line `stmt ::= ...`: assert `error.column == 1`.

### `plcc_spec_cli_test.py` (or `parseSpec_test.py`)

- End-to-end: a malformed syntactic rule in a grammar file produces the human-readable message on stderr and exits 1 (no stack trace).

## Implementation Notes

- `parse_syntactic_spec` is also called directly in tests. All call sites must be updated to unpack `(spec, errors)`.

## Out of Scope

- Lexical parser errors with the same stack-trace problem (noted in issue 037 as a follow-up).
- Verbose/debug mode stack trace suppression — the stack trace is already gone once the exception is caught; re-raising in verbose mode is a separate concern.
