# 174 - arbno drops mid-body non-capturing terminal

**Type:** fix
**Date:** 2026-07-28

<!--
Classify by user-facing impact, not by whether something was "broken".
`fix` and `feat` bump the release version (see [tool.semantic_release]
in pyproject.toml); reserve them for changes to the shipped package
(src/). A bug in a test, script, or CI workflow (bin/, tests/,
.github/) is still a bug, but it's not user-facing — classify it
`test` or `chore` instead so it doesn't spin the version. `docs` is for
documentation content, and never bumps the version either way.
-->

## Description

An arbno (`**=`) repeated-rule body **silently loses any non-capturing
terminal that appears between two capturing symbols** when no separator is
declared. The grammar analyzes as LL(1) (`is_ll1: True`, `conflicts: []`),
but the generated runtime parse table omits the terminal, so parsing fails
at runtime.

A minimal shape that triggers it:

```
<LetDecls> **= <SYMBOL> EQUALS <Exp>
```

Here `EQUALS` is a non-capturing terminal sitting between the capturing
`<SYMBOL>` and `<Exp>`, with no declared separator. Parsing
`let three = 2 four = 5 in +(three, four)` dies immediately after the first
`SYMBOL`:

```
Program
  LetExp
    LET 'let' [-:1:1]
    LetDecls
      SYMBOL 'three' [-:1:5]
plcc-parser-table: -:1:11: error: unexpected 'EQUALS', no production for 'Exp'
```

The working, separator-based arbno form (`<Rands> **= <Exp> +COMMA`, where
`COMMA` is a **separator**) does not hit this — separators go through a
different, correct code path. The bug is specific to a **mid-body terminal**
with no separator.

## Steps to Reproduce

1. Write a grammar containing an arbno rule with a mid-body non-capturing
   terminal and no separator, e.g.:
   ```
   token SYMBOL '[A-Za-z]\w*'
   token EQUALS '='
   token LIT '\d+'
   ...
   <LetDecls> **= <SYMBOL> EQUALS <Exp>
   ```
2. `plcc-parse -s grammar.plcc` (or `plcc-rep`) on input that exercises the
   rule (`x = 1 y = 2`).
3. Observe `unexpected 'EQUALS', no production for '<next capture>'` — the
   `EQUALS` is never shifted.

## Notes

**Root cause** (confirmed against current `src/`, not just the installed
2.0.0 CLI):

- LL(1) table *analysis* is correct.
  [`_handle_arbno`](../../src/plcc/ll1/spec_json_decoder.py) expands
  `LetDecls -> SYMBOL EQUALS Exp LetDecls# | ε` with `EQUALS` included, so
  the grammar is (correctly) accepted as LL(1).
- The bug is in the *runtime* arbno metadata that the same function builds.
  It filters the repeated body down to **capturing symbols only** when
  constructing `arbno_rhs`:
  ```python
  arbno_rhs = [
      {
          "field": _arbno_field(s),
          "symbol": s["name"],
          "is_terminal": bool(s.get("isTerminal", False)),
      }
      for s in rhs
      if s.get("isCapturing", False)   # <-- drops non-capturing EQUALS
  ]
  ```
  The resulting arbno entry for `LetDecls` lists only `symbolList` (SYMBOL)
  and `expList` (Exp); `EQUALS` is gone.
- At runtime,
  [`_parse_arbno`](../../src/plcc/parser/predictive_parser.py) walks exactly
  that `rhs` list once per iteration, so after consuming `SYMBOL` it tries
  to parse `Exp` and chokes on the unshifted `EQUALS`.

**Suggested fix:** stop filtering the arbno body by `isCapturing`. Include
every rhs symbol in `arbno_rhs`, marking non-capturing terminals so
`_parse_arbno` **shifts them without appending to a field list** (much as a
non-arbno `::=` rule consumes its full RHS). Note that `_parse_arbno`
currently appends every shifted token to `item["field"]`, so the fix needs a
way to represent "shift-and-discard" (e.g. a `None` field) rather than
reusing the existing per-item append path. Add a regression test with a
separator-less arbno whose body has a mid-body terminal.

**Downstream context:** found while migrating a `let` grammar whose faithful
shape is `<LetDecls> **= <SYMBOL> EQUALS <Exp>`. That work chose to keep the
grammar in its natural form and wait on this upstream fix rather than
restructure around the bug.
