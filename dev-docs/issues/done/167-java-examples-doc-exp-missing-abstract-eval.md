# 167 - Java "subtraction language" example in examples.md doesn't compile — `Exp` never declares `eval()`

**Type:** docs
**Date:** 2026-07-23

## Description

`docs/language-guide/examples.md`'s "Example: subtraction language" Java
tab has `<Exp:WholeExp>` and `<Exp:SubExp>` alternatives, so PLCC-ng
generates `Exp` as an abstract base class (per the rule documented in
`java.md`'s "BNF to Java constructs" table: alternative rules make the
base nonterminal abstract). But no semantic-section fragment is attached
to `Exp` declaring `public abstract int eval();`, so the generated
`Exp.java` has no `eval()` method at all. Every reference to
`exp.eval()`/`exp1.eval()`/`exp2.eval()` (in `Prog`'s `_run()` and in
`SubExp.eval()`) fails to compile with `cannot find symbol: method
eval()`.

Found via extra end-to-end verification while fixing issues #162/#165
(a docs sweep for `_run()`'s new String-returning contract touched the
`Prog%%%` block in this same example). Confirmed pre-existing and
unrelated to that change: the identical `cannot find symbol` error
reproduces with the original `void`+`System.out.println` form of
`_run()`, before any of that series' changes.

The Python tab of the same example (lines 39-57) doesn't have this
problem — Python has no compile-time method-existence check, so
`self.exp.eval()` works via dynamic dispatch even without a declared
`eval` on the base class.

## Steps to Reproduce

1. Copy the "Java" tab's grammar from `docs/language-guide/examples.md`'s
   "Example: subtraction language" section verbatim into a `spec.plcc`.
2. `echo "-(3,2)" | plcc-rep --spec=spec.plcc`
3. Actual: `javac` fails — `cannot find symbol: method eval() location:
   variable exp of type Exp` (and the same for `exp1`/`exp2` inside
   `SubExp.eval()`). Expected per the doc's walkthrough: evaluates to `1`.

## Notes

Fix: add an `Exp` semantic-section fragment to the Java tab declaring
`public abstract int eval();`, matching the pattern already used
correctly in `java.md`'s own "Quick reference example" (before issue
#166's revert) and in the "BNF to Java constructs" table's guidance.
