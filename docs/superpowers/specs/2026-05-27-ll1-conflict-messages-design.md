# Design: Improve LL(1) Conflict Error Messages

**Date:** 2026-05-27
**Issue:** [036 - Improve LL(1) conflict error messages](../../issues/036-ll1-conflict-error-messages.md)

## Overview

Replace the raw-data conflict output in `plcc-make` with human-readable messages that explain the type of LL(1) conflict and give concrete remediation tips. The conflict type is computed once in `ll1_result_builder.py` and stored in `ll1.json`; a new formatter module turns the enriched data into readable text.

## Section 1: JSON schema change

**File:** `src/plcc/ll1/ll1_result_builder.py`

Each conflict entry in the `conflicts` list gains a `"conflict_type"` field, derived from the conflict's own production data:

- If any production in `productions` has an empty symbol list (`[]`) → `"conflict_type": "first_follow"`
- If all productions are non-empty → `"conflict_type": "first_first"`

Before:
```json
{"nonterminal": "elsePart", "lookahead": "ELSE", "productions": [...]}
```

After:
```json
{"nonterminal": "elsePart", "lookahead": "ELSE", "conflict_type": "first_follow", "productions": [...]}
```

No other data fields change. The field is computed inline where the `conflicts` list is assembled.

## Section 2: Formatter module

**File:** `src/plcc/ll1/format_conflict_message.py`
**Test file:** `src/plcc/ll1/format_conflict_message_test.py`

### Public API

```python
def format_conflict_message(conflict: dict) -> str:
    ...
```

Takes a single conflict dict (as stored in `ll1.json`) and returns a multi-line string ready to print to stderr. Called once per conflict.

### Production rendering

A helper `_render_production(nonterminal, production_entry)` converts a production entry to a readable grammar rule:

- `{"alt": ..., "production": [{"symbol": "ELSE", "field": "..."}, {"symbol": "stmt", "field": "..."}]}` → `<elsePart> ::= ELSE <stmt>`
- `{"alt": ..., "production": []}` → `<elsePart> ::=    (empty)`

The `alt` and `field` values are ignored; only `symbol` is used.

### FIRST/FIRST message

```
LL(1) conflict: <expr> on lookahead ID

  All of these productions apply:
    <expr> ::= ID PLUS <expr>
    <expr> ::= ID MINUS <expr>

  This is a FIRST/FIRST conflict: all productions start with ID, so
  the parser cannot choose between them.

  Tip: left-factor the common prefix:
    <expr>     ::= ID <exprTail>
    <exprTail> ::= PLUS <expr>
    <exprTail> ::= MINUS <expr>
```

The left-factoring suggestion:
1. Find the longest common prefix (LCP) across all non-empty conflicting productions' symbol lists.
2. Name the tail nonterminal by stripping angle brackets from the nonterminal name and appending `Tail`, wrapped in angle brackets: `<expr>` → `<exprTail>`.
3. Show the factored rules as an example. This is a suggestion, not code generation; name collisions with existing nonterminals are not checked.

### FIRST/FOLLOW message

```
LL(1) conflict: <elsePart> on lookahead ELSE

  All of these productions apply:
    <elsePart> ::= ELSE <stmt>
    <elsePart> ::=    (empty)

  This is a FIRST/FOLLOW conflict: ELSE can start the first production,
  but also appears in the FOLLOW set of <elsePart>, making the empty
  production ambiguous here.

  Tip: look at the rule(s) that use <elsePart> — one of them places
  ELSE in a position that follows <elsePart>, creating the ambiguity.
  This often means the grammar is genuinely ambiguous (e.g., the
  dangling-else problem) and must be restructured.
```

The empty production(s) and the non-empty production(s) may each number more than one; all are listed.

## Section 3: `make.py` update

**File:** `src/plcc/cmd/make.py`

`_report_ll1_failure` imports and calls the formatter:

```python
from plcc.ll1.format_conflict_message import format_conflict_message

def _report_ll1_failure(ll1, path):
    print(f"plcc-make: error: grammar is not LL(1); see {path}", file=sys.stderr)
    for conflict in ll1.get("conflicts", []):
        print(format_conflict_message(conflict), file=sys.stderr)
    for entry in ll1.get("left_recursion", []):
        cycle = entry.get("cycle", [])
        print(f"plcc-make: error: left-recursion cycle: {' -> '.join(cycle)}", file=sys.stderr)
```

The existing unit test `test_report_ll1_failure_prints_error_and_conflicts` passes a dict with a `"competing"` key that does not exist in real conflict data. It should be updated to use a realistic conflict dict (with `nonterminal`, `lookahead`, `conflict_type`, and `productions`) and assert on meaningful output such as the nonterminal name, lookahead, and conflict type label.

## Testing

- **Unit tests in `format_conflict_message_test.py`** — cover production rendering, FIRST/FIRST with 2+ productions, FIRST/FOLLOW with 2+ productions, LCP extraction for left-factoring (including single-production edge case, full-production match).
- **Unit tests in `ll1_result_builder_test.py`** — assert that `conflict_type` is present and correct in the output for both conflict types.
- **Unit tests in `make_test.py`** — update the existing conflict test; assert on readable output content.

## What is not in scope

- Tracking FOLLOW provenance (which rules put a token into a nonterminal's FOLLOW set). A generic tip to search the grammar is sufficient for now.
- A standalone `plcc-ll1-explain` command. This is noted as a possible future escape valve if inline messages become unwieldy.
- Checking the left-factoring tail name against existing nonterminals for collisions.
