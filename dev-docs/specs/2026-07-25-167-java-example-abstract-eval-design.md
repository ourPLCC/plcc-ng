# Java subtraction-language example: `Exp` never declares abstract `eval()` — design

**Issue:** [167](../issues/167-java-examples-doc-exp-missing-abstract-eval.md)
**Date:** 2026-07-25

## Problem

`docs/language-guide/examples.md`'s "Example: subtraction language" Java tab
has alternative rules `<Exp:WholeExp>` and `<Exp:SubExp>`, so PLCC-ng
generates `Exp` as an **abstract base class** (per `java.md`'s "BNF to Java
constructs" table: an alternative rule makes the base nonterminal abstract).
But the Java tab attaches semantic fragments only to `Prog`, `WholeExp`, and
`SubExp` — never to `Exp` itself. The generated `Exp.java` therefore has no
`eval()` method, and every call through the static type `Exp` —
`exp.eval()` in `Prog._run()`, `exp1.eval()`/`exp2.eval()` in
`SubExp.eval()` — fails to compile:

```text
cannot find symbol: method eval() location: variable exp of type Exp
```

The doc's own walkthrough claims this example evaluates `-(3,2)` to `1`, but
as written it never compiles.

The Python tab of the same example is unaffected: Python has no compile-time
method-existence check, so `self.exp.eval()` dispatches dynamically even with
no `eval` declared on the base class. No Python change is needed.

This is purely a docs defect. It is not a code/generator bug — PLCC-ng's
"alternative rule ⇒ abstract base" behavior is correct and documented; the
example simply omits the abstract-method fragment that behavior requires.

## Decision

Add one semantic fragment to the **Java tab only**, on the base nonterminal
`Exp`, declaring the `eval()` contract that `WholeExp`/`SubExp` implement:

```text
Exp
%%%
public abstract int eval();
%%%
```

- **Kind:** plain (body) fragment — no colon — matching every other fragment
  in this example and the `Op` abstract-method fragment in `java.md`'s Quick
  reference example.
- **Return type:** `int`, matching the concrete `WholeExp.eval()` /
  `SubExp.eval()` implementations (`return Integer.parseInt(...)` /
  `return exp1.eval() - exp2.eval()`).
- **Placement:** immediately after the `Prog` fragment and before
  `WholeExp`. The start class `Prog` stays first as the entry point; the
  `Exp` hierarchy then reads top-down — abstract base, then its concrete
  subclasses.

This mirrors the pattern already correct in `java.md` (`Op` →
`public abstract int apply(int, int);` declared ahead of its `AddOp`/`SubOp`
subclasses), so the two docs stay consistent.

### Explicitly out of scope

- **The Python tab** — works as-is (dynamic dispatch); no change.
- **The `plcc-rep` → `plcc-eval` rename** (open issue 161) — leave command
  names in this example unchanged.
- **Prose / narration** — this example has no per-fragment explanatory text
  today; keep it that way. The fix is the fragment alone.

## Change

Single file: `docs/language-guide/examples.md`, Java tab (`=== "Java"` block,
currently lines 60–96). Insert the new `Exp` fragment between the `Prog`
fragment (ends ~line 81) and the `WholeExp` fragment (begins ~line 83).

Resulting fragment order in the Java tab: `Prog`, **`Exp`**, `WholeExp`,
`SubExp`.

## Verification

This bug was found only by running the example end-to-end, so the fix must
clear the same bar (per CONTRIBUTING.md — do not claim the fix works without
running it):

1. Copy the corrected Java-tab grammar verbatim into a temporary `spec.plcc`
   and the doc's three sample programs into `samples`.
2. Run the example end-to-end through the pipeline the doc documents
   (`plcc-rep -s spec.plcc samples`).
3. Confirm `javac` no longer reports `cannot find symbol: method eval()` and
   the output matches the doc's stated interpreter result:

   ```text
   3
   1
   2
   ```

If a `bin/` script already drives "extract a doc's fenced spec and run it",
prefer it over an ad-hoc script (per CLAUDE.md); otherwise verify by hand in
the scratchpad directory. No new automated test is added — this is a
documentation example, and the fix is verified manually against the doc's own
expected output.

## Commit shape

`docs`-type change; no `BREAKING CHANGE` footer (docs-only, no behavior
change). Suggested subject:

```text
docs(examples): declare abstract eval() on Exp in java subtraction example
```

Final commit on the branch closes the issue via
`bin/issues/close.bash 167` (moves the file to `done/`, updates
`dev-docs/roadmap.md`), per CLAUDE.md. Work stays on the
`worktree-run-contract-impl` worktree and is **not** merged for now.

## Files changed

| File | Change |
| --- | --- |
| `docs/language-guide/examples.md` | Add `Exp` abstract-`eval()` fragment to the Java tab, after `Prog`, before `WholeExp` |
| `dev-docs/issues/167-...md` → `done/` | Closed via `bin/issues/close.bash 167` |
| `dev-docs/roadmap.md` | Updated by `close.bash` |
