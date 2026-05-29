# 048 - LL(1) conflict detection misses identical predict sets

**Type:** fix
**Date:** 2026-05-29

## Description

When two alternatives for the same non-terminal have identical predict sets, the
LL(1) conflict detector reports no conflict and `is_ll1: true`. It silently overwrites
the parse table entry with the last alternative, dropping the earlier one entirely.

## Steps to Reproduce

Grammar with two `<expr>` alternatives that both derive `<IDENT>`:

```
<expr>:Var   ::= <IDENT>
<expr>:Const ::= <IDENT>
```

Running `plcc-ll1` on this grammar produces:

```json
"is_ll1": true,
"conflicts": [],
"predict_sets": { "expr": [["IDENT"], ["IDENT"]] },
"parse_table": {
  "expr": {
    "IDENT": { "alt": "Const", ... }
  }
}
```

`Var` is silently discarded. No conflict is reported.

## Notes

The predict sets `[["IDENT"], ["IDENT"]]` make the conflict obvious — the detector
should flag any non-terminal where two predict sets share a token. The parse table
construction appears to overwrite earlier entries without checking for collisions,
and the conflict-detection pass does not catch the case where both sets are identical.

A correct implementation should detect this as a FIRST/FIRST conflict and report it
the same way other FIRST/FIRST conflicts are reported (see issue 036).
