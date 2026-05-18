# 024 - plcc-parser-table emits no diagnostic on premature end of input

**Type:** fix
**Date:** 2026-05-15

## Description

When the parser receives input that ends before the parse is complete (e.g., `12 +` with no following operand), `plcc-parser-table` catches `IncompleteInputError` and silently exits with code 1, emitting nothing to stdout. The caller (`ParseHandler.feed()`) interprets empty stdout as "need more input" and returns `False`, but no error message is shown to the user.

In an interactive REPL session this means the user gets no feedback — the prompt just resets, or (with recent `eof=True` changes to `SourceRunner`) the session exits with a confusing "PLCC internal error" message.

## Steps to Reproduce

1. Define a grammar with at least one binary operation (e.g., `<exp> ::= <NUM> <exp2>`).
2. Start an interactive session (`plcc-parse`).
3. Type `12 +` and press Enter, then press a blank line to force-submit.
4. Observe: no diagnostic is printed; the error is silent.

## Notes

- `plcc-parser-table` already emits a `{"kind": "error", ...}` record for `ParseError`. The `IncompleteInputError` path should do the same.
- At the point `IncompleteInputError` is raised in `_parse_regular`, the parse table entry for the current nonterminal is available — its keys are exactly the tokens that would have been valid next. These should be included in the error record as an `expected` field and in the human-readable message.
- There are two raise sites in `predictive_parser.py`: one in `expect()` (single expected terminal) and one in `_parse_regular()` (set of expected terminals from the parse table).
- A partial parse tree is not available at the point of failure — `NodeBuilder` objects live only on the call stack and are abandoned when the exception unwinds. Partial-tree diagnostics would require significant parser restructuring and are out of scope here.
- `ParseHandler` requires no changes — it already handles `{"kind": "error", ...}` records by printing the message and returning `True`, which allows the interactive session to continue normally.
- See plan at `docs/superpowers/plans/` (created during the 2026-05-15 session) for a detailed implementation sketch.
