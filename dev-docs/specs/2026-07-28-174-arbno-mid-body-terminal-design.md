# Arbno drops mid-body non-capturing terminal — design

**Issue:** [174](../issues/done/174-arbno-drops-mid-body-terminal.md)
**Date:** 2026-07-28

## Problem

An arbno (`**=`) body silently loses every non-capturing terminal it
contains. The grammar still analyzes as LL(1), so nothing complains at build
time; the failure surfaces at parse time as a bogus syntax error on a token
the grammar plainly declares.

```
<LetDecls> **= <SYMBOL> EQUALS <Exp>
```

```
plcc-parser-table: -:1:11: error: unexpected 'EQUALS', no production for 'Exp'
```

The LL(1) *analysis* is correct — `_handle_arbno` desugars the rule to
`LetDecls -> SYMBOL EQUALS Exp LetDecls# | ε` with `EQUALS` present. The bug
is in the parallel *runtime* metadata the same function builds, which filters
the body down to capturing symbols only:

```python
arbno_rhs = [
    {
        "field": _arbno_field(s),
        "symbol": s["name"],
        "is_terminal": bool(s.get("isTerminal", False)),
    }
    for s in rhs
    if s.get("isCapturing", False)   # drops non-capturing EQUALS
]
```

`_parse_arbno` walks exactly that list once per iteration, so after
consuming `SYMBOL` it tries to parse `Exp` and chokes on the unshifted
`EQUALS`.

## Decision: `field: None` means shift-and-discard

Keep every rhs symbol in `arbno_rhs`; give non-capturing symbols a `None`
field, and teach `_parse_arbno` to consume such an item without appending it
to any list.

This is the convention the rest of the pipeline already uses, not a new
mechanism. `_prod_entry` in `ll1_result_builder.py` already emits
`{"symbol": s, "field": None}` for elided symbols of regular `::=` rules;
`ll1.schema.json` already types production `field` as `["string", "null"]`;
and `_parse_regular` already shifts a token and skips the append when
`f is None`. After this change an arbno body is consumed the same way a
`::=` body is — the only difference stays what it should be, that captures
accumulate into lists instead of single children.

### Changes

**`src/plcc/ll1/spec_json_decoder.py::_handle_arbno`** — drop the
`isCapturing` filter, branch the field instead:

```python
arbno_rhs = [
    {
        "field": _arbno_field(s) if s.get("isCapturing", False) else None,
        "symbol": s["name"],
        "is_terminal": bool(s.get("isTerminal", False)),
    }
    for s in rhs
]
```

**`src/plcc/parser/predictive_parser.py::_parse_arbno`** — build the
accumulators from fielded items only, and guard the two appends:

```python
list_fields = {item["field"]: [] for item in rhs if item["field"] is not None}

def parse_iteration():
    ...
    for item in rhs:
        if item["is_terminal"]:
            tok = expect(item["symbol"])
            builder.note_token(tok)
            if item["field"] is not None:
                list_fields[item["field"]].append(tok)
        else:
            child_builder = parse_nt(item["symbol"])
            builder.note_span_from(child_builder)
            if item["field"] is not None:
                list_fields[item["field"]].append(child_builder.to_node())
```

Discarded tokens are still `expect`ed (so they are required, and a missing
one is a real error), still passed to `builder.note_token` (so the node's
source span covers them), and still traced — `expect` emits the shift event
itself. The trailing loop that appends `list_fields` to `builder.children` is
unchanged: it now iterates a dict that never contained a `None` key, so no
`None`-named child can appear in a tree.

In practice only terminals take the `None` branch — a nonterminal on an rhs
is a `CapturingSymbol`, whose `isCapturing` is `True` — but neither function
special-cases that, so nothing breaks if that ever changes.

### Two adjacent bugs fixed by the same change

`ll1_result_builder.py` derives an arbno's runtime `lookahead` from
`entry["rhs"][0]`. Today that is the first *capturing* symbol, so:

- **Leading non-capturing terminal.** `<Xs> **= BANG <Exp>` predicts on
  FIRST(`Exp`) and never shifts `BANG` — the same failure as the mid-body
  case, one position earlier. After the fix `rhs[0]` is `BANG`, so the
  lookahead is `["BANG"]`.
- **Fully non-capturing body.** `<Xs> **= BANG` produces an empty
  `arbno_rhs`, hence `lookahead: []`, hence an arbno that silently matches
  zero iterations against any input. After the fix it repeats correctly and
  contributes no list fields.

`ll1_result_builder.py` needs no edit for either; both follow from
`rhs[0]` becoming the body's true first symbol. They get regression tests
because they are separate user-visible behaviors, not because they need
separate code.

## What deliberately does not change

- **`build_model.py::_extract_arbno_fields` keeps its `isCapturing`
  filter.** Non-capturing symbols must not become fields of the generated
  class. That filter is correct where it is; only the parser-metadata copy
  of it was wrong.
- **The separator path.** Separators are consumed outside
  `parse_iteration`, so a separator arbno with a mid-body terminal
  (`<Ds> **= <SYMBOL> EQUALS <Exp> +COMMA`) is fixed by the same change with
  no separator-specific work.
- **`ll1.schema.json`.** It does not describe the `arbno` key at all, so
  there is nothing to widen. Documenting `arbno` in the schema is a real
  gap, but it is not this fix's job.
- **The tree format.** Trees gain no new children and lose none; a
  previously-failing parse now succeeds, and a previously-succeeding parse
  produces byte-identical output.

## Testing

Unit tests, following CONTRIBUTING's TDD loop (failing first), plus one
end-to-end case because the bug was reported end-to-end.

**`src/plcc/ll1/spec_json_decoder_test.py`**
- A mid-body non-capturing terminal survives into `arbno_rhs` with
  `field: None`, in body order.
- Capturing entries keep the field names they have today (no regression in
  `_arbno_field`).

**`src/plcc/ll1/ll1_result_builder_test.py`**
- An arbno whose body begins with a non-capturing terminal gets that
  terminal as its `lookahead`.
- An all-non-capturing body gets a non-empty `lookahead`.

**`src/plcc/parser/predictive_parser_test.py`** — against a hand-built ll1
dict for `letDecls **= SYMBOL EQUALS exp` (mirroring the existing
`_RANDS_LL1`/`_CMDS_LL1` fixtures):
- Two iterations parse; `EQUALS` is shifted, not reported as an error.
- The capture lists hold the right values in the right order.
- No child named `None` appears in the resulting tree.
- Zero iterations on empty input still yields empty lists.
- An all-non-capturing body repeats and produces a tree with no list
  children.

**`tests/bats/e2e/plcc-rep.bats`** with a new
`tests/fixtures/arbno-mid-body-terminal.plcc` — a let-decls grammar in the
issue's shape with a Python target, evaluated through `plcc-rep` alongside
the existing `trivial-arbno` cases. This is the tier that would have caught
the bug as filed.

## Bookkeeping

Branch `arbno-mid-body-terminal`. Commits: `test(...)` for the failing
tests, `fix(ll1,parser): ...` for the change, and a final
`bin/issues/close.bash 174` commit closing the issue with the work.
