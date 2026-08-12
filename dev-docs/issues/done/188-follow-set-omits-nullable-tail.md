# 188 - FOLLOW set omits the nullable tail, breaking empty alternatives

**Type:** fix
**Date:** 2026-08-11

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

The FOLLOW set of a nonterminal that is followed by a *nullable* symbol is
under-approximated. The predict set of an **empty alternative** is exactly
FOLLOW of its nonterminal, so the generated parse table silently loses
entries and valid programs fail to parse — while `plcc-ll1` still reports
`is_ll1: true` and no conflicts.

The defect is in
[`FollowSetBuilder._updateWithSingleOccuranceOfNonterminalInProduction`](../../../src/plcc/spec/syntax/validations/ll1/build_follow_sets.py):

```python
else:
    self._addFirstOfNextSymbol(rules[index + 1], nonterminal)
    if self._canDeriveEmpty(rules[index + 1:]):
        self._addFollowOfLHS(lhs, nonterminal)
```

It adds FIRST of the **single** next symbol, then jumps straight to the
"whole remainder is nullable" case. The standard algorithm walks forward
from `index + 1`, adding `FIRST(X_j) \ {ε}` and stopping at the first `X_j`
that is not nullable. When `X_{i+1}` is nullable but the remainder is not,
every symbol between them is skipped.

A repeating (`**=`) nonterminal makes this easy to hit, because it is
nullable by construction and is a natural thing to place in a sequence.

Distinct from issue
[#170](170-arbno-follow-set-missing-eof.md), which was about
nullability being tested against only a nonterminal's first-registered
production. That fix landed (`_canDeriveEmpty` now consults the FIRST sets);
this is the separate forward-walk defect in the same function.

## Steps to Reproduce

1. A grammar in which a nonterminal with an empty alternative is followed by
   a nullable symbol — here `<Ext>` (which has an empty alternative) is
   followed by `<Statics>` (nullable, because `**=`):

   ```
   <ClassDecl>     ::= CLASS <Ext> <Statics> <Fields> <Methods> END
   <Ext:Ext1>      ::= EXTENDS <Exp>
   <Ext:Ext0>      ::=
   <Statics>       **= STATIC <SYMBOL> EQUALS <Exp>
   <Fields>        **= FIELD <SYMBOL>
   <Methods>       **= METHOD <SYMBOL> EQUALS <Proc>
   ```

2. `plcc-ll1` reports `is_ll1: true`, no conflicts, and
   `FOLLOW(Ext) = ['STATIC']`. The correct set is
   `{STATIC, FIELD, METHOD, END}`.

3. `printf 'class static x = 3 end\n' | plcc-parse` — parses. This is the
   one class shape whose next token happens to be in the truncated FOLLOW
   set.

4. `printf 'class field x end\n' | plcc-parse` — fails:

   ```
   plcc-parser-table: -:1:7: error: unexpected 'FIELD', no production for 'Ext'
   ```

   Same for `class method m = proc() 1 end` and for the empty `class end`.

## Notes

Two things make this worse than an ordinary parse bug.

**It is silent.** `plcc-ll1` reports the grammar LL(1)-clean, so nothing
warns the spec author. The failure appears later, on one particular input
shape.

**The diagnosis is inverted.** The message names the token that *is* there
(`unexpected 'FIELD'`) and the nonterminal that has no entry for it, which
reads like a grammar-ambiguity problem. The actual cause is several rules
away, in a symbol the author never looked at.

Suggested fix, replacing the `else` branch above:

```python
else:
    for j in range(index + 1, len(rules)):
        self._addFirstOfNextSymbol(rules[j], nonterminal)
        if not self._canDeriveEmpty([rules[j]]):
            break
    else:
        self._addFollowOfLHS(lhs, nonterminal)
```

Whoever picks this up should add a unit test at the `build_follow_sets`
level directly, not only an end-to-end regression: a minimal grammar
`S -> A B C`, `A -> a | ε`, `B -> b | ε`, `C -> c`, asserting
`FOLLOW(A) = {b, c}` rather than `{b}`. The grammar above is the
end-to-end case.

Found while migrating a course language whose class-declaration rule has
exactly this shape. That port works around it by splitting the class body
into a non-nullable nonterminal, so the symbol immediately following the
empty-alternative nonterminal has a correctly computed FIRST set; the
accepted language is unchanged, and the workaround can be reverted once
this is fixed.
