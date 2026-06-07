# Parse Trace Design

**Issue:** 069 — Improve output of `plcc-parse --trace`
**Date:** 2026-06-06

## Problem

The current `--trace` output uses LL(1) algorithm vocabulary (`predict`, `shift`, `complete`) that exposes parsing mechanics students don't need to understand. It is also redundant on success: the trace and the final parse tree convey the same structure.

## Decision

Remove the `--trace`/`-t` flag. Instead, always show a partial trace automatically before any parse error. On success, show only the parse tree as before.

## Output Format

The trace uses **Style B**: indented rule names and tokens, no entry/exit markers.

This format uses the same visual conventions as the successful parse tree printed by `_print_tree`, but shows more: every rule application and every token, regardless of whether the grammar assigns field names to them. The parse tree on success only shows captured (named) children.

- **Rule node:** `{indent}{ruleName}` — or `{indent}{ruleName} (empty)` if the rule matched nothing
- **Token node:** `{indent}{TOKEN_NAME} '{lexeme}' [{file:line:col}]`
- Indentation is two spaces per depth level

### Example

Grammar:

```text
<program>          ::= <expr>
<expr>             ::= <term> <exprRest>
<exprRest:AddRest> ::= PLUS <term> <exprRest>
<exprRest:NilRest> ::=
<term>             ::= NUM
```

Successful parse of `1 + 2` — shows only the parse tree (unchanged):

```text
program
  expr
    term
      NUM '1' [-:1:1]
    AddRest
      PLUS '+' [-:1:3]
      term
        NUM '2' [-:1:5]
      NilRest (empty)
```

Failed parse of `1 +` — shows partial trace then error:

```text
program
  expr
    term
      NUM '1' [-:1:1]
    AddRest
      PLUS '+' [-:1:3]
      term
plcc-parse: error: expected NUM, got eof
```

The partial trace stops where the parser stopped. Open rules (not yet completed) appear without `(empty)` — they were in progress when the error occurred.

## What Changes

### Removed

- `-t`/`--trace` CLI option from `plcc-parse`
- `_print_parse_step` rendering function
- The `trees_flags` logic that conditionally passed `--trace` to child processes

### Changed

- `ParseHandler.feed()` buffers `parse-step` records during parsing
  - On `error`: render buffered steps in Style B, then print the error
  - On `tree`: discard buffered steps (tree is already printed by `_print_tree`)

### Added

- Style B renderer: a function that takes the buffered list of parse-step event dicts and prints them in Style B format

## Rendering Algorithm

The renderer uses a stack to detect empty rules:

- **predict event** at depth D: push `(ruleName, D)` onto a pending stack (do not print yet)
- **shift event** at depth D: flush all pending rules (print each at its depth), then print the token at depth D using `[file:line:col]` format
- **complete event** at depth D: if the top pending entry is still unprinted (no children were flushed for it), print `{indent}{ruleName} (empty)` and pop; otherwise just pop

At error time, flush any remaining unprinted pending rules as plain rule headers (they were in progress, not empty).

## Tracer

`Tracer` in `predictive_parser.py` is unchanged. It is always active during parsing (not conditional on a flag). The `parse-step` records it produces already contain all information needed for Style B rendering: `event`, `depth`, `sym`/`production`/`name`/`lexeme`/`source`/`rule`.
