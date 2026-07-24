# Java Doc Quick Reference LL(1) Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `docs/language-guide/languages/java.md`'s "Quick reference example" so its grammar is actually LL(1) and the doc's claimed output (`echo "1 + 2" | plcc-rep` prints `3`) is true, by left-factoring the left-recursive `Exp` rule and updating every place in the file that references the old rule/class names.

**Architecture:** Pure documentation change, one file. Reuse the previously-drafted, previously-verified left-factored grammar (`Exp`→`Expr`, `AddExp`→`Add`, `NumExp`→`End`, accumulator-style `eval`) that was reverted in commit `426c0075` as out of scope for a different task. Three independent edits to the same file: (1) the grammar + Java code fragments themselves, (2) the "BNF to Java constructs" table and its explanatory paragraph, (3) two stale `Exp`-family references elsewhere in the file that a naive find-and-replace on the example alone would miss. A fourth task files sibling issues for the three other language pages (`javascript.md`, `python.md`, `haskell.md`), which share the identical bug but are out of scope for this fix.

**Tech Stack:** Markdown docs; PLCC-ng grammar/Java syntax inside fenced code blocks; verification via `plcc-rep` CLI (Java JDK 21+ required, per this doc's own Prerequisites section).

## Global Constraints

- Design of record: `dev-docs/specs/2026-07-24-166-java-doc-quick-reference-ll1-design.md`. If anything here seems to contradict it, the spec wins — stop and reconcile before continuing.
- Docs-only change; there is no automated test suite covering doc prose. The gate for Task 1 is running the example for real (`plcc-rep`), matching the process that surfaced this bug in the first place.
- Only `docs/language-guide/languages/java.md` changes in Tasks 1–3. Do not touch `javascript.md`, `python.md`, or `haskell.md` — they get sibling issues in Task 4, not fixes.
- Follow `dev-docs/issue-conventions.md` for Task 4: always file via `bin/issues/new.bash`, never hand-assign IDs; add the roadmap entry in the same commit.
- Final commit on the branch closes #166 via `bin/issues/close.bash 166`.

---

### Task 1: Left-factor the quick reference grammar and Java fragments

**Files:**
- Modify: `docs/language-guide/languages/java.md:27-67` (the fenced grammar + semantic-section code block)

**Interfaces:** None — documentation only. This task's "interface" is the doc's own prose claim two lines below the block (line 69, unchanged): "Running this with `echo "1 + 2" | plcc-rep` prints `3`." Task 1 must make that claim true.

- [ ] **Step 1: Replace the grammar and code fragments**

Current content (`docs/language-guide/languages/java.md:27-67`):

````text
```text
token NUM   '\d+'
token PLUS  '\+'
skip  SPACE '\s+'
%
<Prog>       **= <Exp>
<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>
<Exp:NumExp> ::= <NUM>
%
Java

Exp
%%%
public abstract int eval();
%%%

Prog
%%%
public String _run() {
    java.util.List<String> lines = new java.util.ArrayList<>();
    for (Exp exp : expList) {
        lines.add(String.valueOf(exp.eval()));
    }
    return String.join("\n", lines);
}
%%%

AddExp
%%%
public int eval() {
    return left.eval() + right.eval();
}
%%%

NumExp
%%%
public int eval() {
    return Integer.parseInt(num.lexeme);
}
%%%
```
````

Replace with:

````text
```text
token NUM   '\d+'
token PLUS  '\+'
skip  SPACE '\s+'
%
<Prog>         **= <Expr>
<Expr>         ::= <NUM:left> <ExprTail:tail>
<ExprTail:Add> ::= PLUS <NUM:right>
<ExprTail:End> ::=
%
Java

Expr
%%%
public int eval() {
    return tail.eval(Integer.parseInt(left.lexeme));
}
%%%

ExprTail
%%%
public abstract int eval(int left);
%%%

Prog
%%%
public String _run() {
    java.util.List<String> lines = new java.util.ArrayList<>();
    for (Expr expr : exprList) {
        lines.add(String.valueOf(expr.eval()));
    }
    return String.join("\n", lines);
}
%%%

Add
%%%
public int eval(int left) {
    return left + Integer.parseInt(right.lexeme);
}
%%%

End
%%%
public int eval(int left) {
    return left;
}
%%%
```
````

- [ ] **Step 2: Verify it actually runs — copy the example into a scratch spec**

```bash
VERIFY_DIR="$(mktemp -d)"
cd "${VERIFY_DIR}"
cat > spec.plcc <<'EOF'
token NUM   '\d+'
token PLUS  '\+'
skip  SPACE '\s+'
%
<Prog>         **= <Expr>
<Expr>         ::= <NUM:left> <ExprTail:tail>
<ExprTail:Add> ::= PLUS <NUM:right>
<ExprTail:End> ::=
%
Java

Expr
%%%
public int eval() {
    return tail.eval(Integer.parseInt(left.lexeme));
}
%%%

ExprTail
%%%
public abstract int eval(int left);
%%%

Prog
%%%
public String _run() {
    java.util.List<String> lines = new java.util.ArrayList<>();
    for (Expr expr : exprList) {
        lines.add(String.valueOf(expr.eval()));
    }
    return String.join("\n", lines);
}
%%%

Add
%%%
public int eval(int left) {
    return left + Integer.parseInt(right.lexeme);
}
%%%

End
%%%
public int eval(int left) {
    return left;
}
%%%
EOF
```

- [ ] **Step 3: Run the two cases**

```bash
echo "1 + 2" | plcc-rep --spec=spec.plcc
echo "1" | plcc-rep --spec=spec.plcc
```

Expected: first command prints `3` (exercises the `Add` alternative), second prints `1` (exercises the `End` alternative — proves the grammar isn't just accidentally right for the one case the doc already claims).

If either fails, stop — do not proceed to Step 4 with a grammar that doesn't actually run; re-check the block against Step 1's replacement text for a transcription error.

- [ ] **Step 4: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/run-contract-impl
git add docs/language-guide/languages/java.md
git commit -m "$(cat <<'EOF'
docs(java): left-factor quick reference example grammar (issue 166)

<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right> was left-recursive, which
PLCC-ng's LL(1) parser rejects outright - the doc's claim that the
example runs and prints 3 was false. Left-factor into Expr/ExprTail
(NUM followed by an optional PLUS NUM), moving the alternative choice
off Expr itself so there's no FIRST/FIRST conflict. Verified end-to-end:
`echo "1 + 2" | plcc-rep` now prints 3, `echo "1" | plcc-rep` prints 1.

Renames Exp->Expr, AddExp->Add, NumExp->End, field expList->exprList.
Reuses the rewrite drafted (and verified) while working on #162/#165,
then reverted in 426c0075 as out of scope for that task.

Design: dev-docs/specs/2026-07-24-166-java-doc-quick-reference-ll1-design.md
EOF
)"
```

---

### Task 2: Update the "BNF to Java constructs" table and its explanatory paragraph

**Files:**
- Modify: `docs/language-guide/languages/java.md:71-82`

**Interfaces:** None — documentation only. Depends on Task 1's renames (`Expr`/`ExprTail`/`Add`/`End`/`exprList`) being in place first, since this table's whole job is to cite those exact names.

- [ ] **Step 1: Replace the table and paragraph**

Current content (`docs/language-guide/languages/java.md:71-82`):

```markdown
## BNF to Java constructs

| Grammar Construct | Example from spec | Java Construct | Example based on spec |
| --- | --- | --- | --- |
| Concrete rule (LHS, no alt name) — generates one class | `<Prog>` in `<Prog> **= <Exp>` | Java class with public fields and constructor | `class Prog extends _Start { public ArrayList<Exp> expList; ... }` |
| Alternative rule (LHS, with alt name) — base nonterminal becomes abstract | `<Exp:AddExp>` in `<Exp:AddExp> ::= ...` | Java class extending the base nonterminal | `class AddExp extends Exp { public Exp left, right; ... }` |
| Named non-terminal (RHS) | `<Exp:left>` | `left` — an `Exp` instance | `left.eval()` |
| Captured terminal (RHS) | `<NUM>` | `num` — a `Token`; `.lexeme` for the string value | `Integer.parseInt(num.lexeme)` |
| Uncaptured terminal (RHS) | `PLUS` | No field generated | — |
| Arbno rule (`**=`) | `<Prog> **= <Exp>` | `expList` — `ArrayList<Exp>` | `for (Exp exp : expList)` |

Without explicit `:name` on a RHS symbol, the field name is the symbol name lowercased (e.g., `<Exp>` → `exp`, `<NUM>` → `num`). Use explicit names when two RHS symbols would produce the same field name.
```

Replace with:

```markdown
## BNF to Java constructs

| Grammar Construct | Example from spec | Java Construct | Example based on spec |
| --- | --- | --- | --- |
| Concrete rule (LHS, no alt name) — generates one class | `<Prog>` in `<Prog> **= <Expr>` | Java class with public fields and constructor | `class Prog extends _Start { public ArrayList<Expr> exprList; ... }` |
| Alternative rule (LHS, with alt name) — base nonterminal becomes abstract | `<ExprTail:Add>` in `<ExprTail:Add> ::= PLUS <NUM:right>` | Java class extending the base nonterminal | `class Add extends ExprTail { public Token right; ... }` |
| Named non-terminal (RHS) | `<ExprTail:tail>` | `tail` — an `ExprTail` instance | `tail.eval(left)` |
| Captured terminal (RHS) | `<NUM:left>` | `left` — a `Token`; `.lexeme` for the string value | `Integer.parseInt(left.lexeme)` |
| Uncaptured terminal (RHS) | `PLUS` | No field generated | — |
| Arbno rule (`**=`) | `<Prog> **= <Expr>` | `exprList` — `ArrayList<Expr>` | `for (Expr expr : exprList)` |

Without explicit `:name` on a RHS symbol, the field name is the symbol name lowercased (e.g., `<Expr>` → `expr`, `<NUM>` → `num`). Use explicit names when two RHS symbols would produce the same field name.
```

- [ ] **Step 2: Verify no old names remain in the table**

```bash
sed -n '71,82p' docs/language-guide/languages/java.md | grep -E "\bExp\b|AddExp|NumExp|expList"
```

Expected: no output (empty match — confirms the table no longer references any pre-fix names).

- [ ] **Step 3: Commit**

```bash
git add docs/language-guide/languages/java.md
git commit -m "docs(java): update BNF-to-Java-constructs table for left-factored example (issue 166)"
```

---

### Task 3: Fix the two stale `Exp`-family references outside the example and table

**Files:**
- Modify: `docs/language-guide/languages/java.md:136` (abstract-class note in "`_run` entry point" section)
- Modify: `docs/language-guide/languages/java.md:174-182` ("Generated output" file tree)

**Interfaces:** None — documentation only. These two spots don't live inside the example or the table Tasks 1–2 already fixed, so they're easy to miss with a narrower find-and-replace; that's exactly what happened in the reverted draft (`426c0075`'s commit message calls out the table specifically, not these).

- [ ] **Step 1: Fix the abstract-class note**

Current content (`docs/language-guide/languages/java.md:136`):

```markdown
Abstract classes cannot be instantiated. Declare abstract methods on them so the Java compiler enforces that all concrete subclasses implement them (see `Exp` in the quick reference example).
```

Replace with:

```markdown
Abstract classes cannot be instantiated. Declare abstract methods on them so the Java compiler enforces that all concrete subclasses implement them (see `ExprTail` in the quick reference example).
```

(`ExprTail` is the abstract base after Task 1's rewrite — `Expr` itself is a concrete, non-abstract class.)

- [ ] **Step 2: Fix the "Generated output" file tree**

Current content (`docs/language-guide/languages/java.md:174-182`):

````text
```
DIR/
  Main.java         — entry point
  _Start.java       — default base for the start class
  Prog.java         — one .java file per class from the grammar
  AddExp.java
  NumExp.java
  *.class           — compiled after plcc-java-build
```
````

Replace with:

````text
```
DIR/
  Main.java         — entry point
  _Start.java       — default base for the start class
  Prog.java         — one .java file per class from the grammar
  Expr.java
  Add.java
  End.java
  *.class           — compiled after plcc-java-build
```
````

- [ ] **Step 3: Verify no stale names remain anywhere in the file**

```bash
grep -n "\bExp\b\|AddExp\|NumExp\|expList" docs/language-guide/languages/java.md
```

Expected: no output. (This is the same grep that found these two spots during design — running it again here proves the sweep is complete.)

- [ ] **Step 4: Commit**

```bash
git add docs/language-guide/languages/java.md
git commit -m "docs(java): fix remaining stale Exp-family references (issue 166)"
```

---

### Task 4: File sibling issues for javascript.md, python.md, haskell.md

**Files:**
- Create: `dev-docs/issues/170-javascript-doc-quick-reference-not-ll1.md`
- Create: `dev-docs/issues/171-python-doc-quick-reference-not-ll1.md`
- Create: `dev-docs/issues/172-haskell-doc-quick-reference-not-ll1.md`
- Modify: `dev-docs/issues/.next-id.txt`
- Modify: `dev-docs/roadmap.md`

**Interfaces:** None — documentation/bookkeeping only. These three files each have the exact same `<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>` left-recursion in their own "Quick reference example" (confirmed by grep during design), but are explicitly out of scope for this branch's fix per the design doc's Scope section.

- [ ] **Step 1: File the three issues**

```bash
bin/issues/new.bash javascript-doc-quick-reference-not-ll1 docs
bin/issues/new.bash python-doc-quick-reference-not-ll1 docs
bin/issues/new.bash haskell-doc-quick-reference-not-ll1 docs
```

Expected: each prints its created path; `dev-docs/issues/.next-id.txt` goes from `170` to `173`. If the printed paths don't start with `170-`, `171-`, `172-` respectively, stop — something else consumed an ID between Step 1's three invocations and this plan's hard-coded filenames above no longer match; re-run this task with the actual assigned numbers instead of forcing 170/171/172.

- [ ] **Step 2: Fill in `dev-docs/issues/170-javascript-doc-quick-reference-not-ll1.md`**

Replace the template's `## Description` / `## Steps to Reproduce` / `## Notes` sections with:

```markdown
## Description

`docs/language-guide/languages/javascript.md`'s "Quick reference example" has
the same left-recursive grammar as issue #166's Java version:
`<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>` makes `Exp` left-recursive,
which PLCC-ng's LL(1) parser rejects outright. The doc's claimed output for
`echo "1 + 2" | plcc-rep` is false as written, same as #166.

## Steps to Reproduce

1. Copy the "Quick reference example" grammar from
   `docs/language-guide/languages/javascript.md` verbatim into a `spec.plcc`.
2. `echo "1 + 2" | plcc-rep --spec=spec.plcc`
3. Actual: `plcc-make: error: grammar is not LL(1)` (same FIRST/FIRST
   conflict as #166). Expected per the doc: prints `3`.

## Notes

Same root cause and left-factoring shape as #166 — see
`dev-docs/specs/2026-07-24-166-java-doc-quick-reference-ll1-design.md` and
its implementation plan for the grammar to reuse: `<Prog> **= <Expr>`,
`<Expr> ::= <NUM:left> <ExprTail:tail>`, `<ExprTail:Add> ::= PLUS
<NUM:right>`, `<ExprTail:End> ::=`.

JavaScript has no `abstract` keyword, so `ExprTail`'s base-class fragment
can't copy Java's `public abstract int eval(int left);` verbatim — check
how this page's existing `Exp` fragment expresses the same "abstract
base" idea today and follow that pattern instead.

Also update this page's own "BNF to JavaScript constructs" table
(§`BNF to JavaScript constructs`), its "Generated output" file list
(`AddExp.js`/`NumExp.js` → new names), and any other stale
`Exp`/`AddExp`/`NumExp`/`expList` references — grep the whole file first,
the way #166's design doc did, since #166 found two such references
that lived outside the example and its table and would have been missed
by a narrower fix.
```

- [ ] **Step 3: Fill in `dev-docs/issues/171-python-doc-quick-reference-not-ll1.md`**

Replace the template's sections with:

```markdown
## Description

`docs/language-guide/languages/python.md`'s "Quick reference example" has
the same left-recursive grammar as issue #166's Java version:
`<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>` makes `Exp` left-recursive,
which PLCC-ng's LL(1) parser rejects outright. The doc's claimed output for
`echo "1 + 2" | plcc-rep` is false as written, same as #166.

## Steps to Reproduce

1. Copy the "Quick reference example" grammar from
   `docs/language-guide/languages/python.md` verbatim into a `spec.plcc`.
2. `echo "1 + 2" | plcc-rep --spec=spec.plcc`
3. Actual: `plcc-make: error: grammar is not LL(1)` (same FIRST/FIRST
   conflict as #166). Expected per the doc: prints `3`.

## Notes

Same root cause and left-factoring shape as #166 — see
`dev-docs/specs/2026-07-24-166-java-doc-quick-reference-ll1-design.md` and
its implementation plan for the grammar to reuse: `<Prog> **= <Expr>`,
`<Expr> ::= <NUM:left> <ExprTail:tail>`, `<ExprTail:Add> ::= PLUS
<NUM:right>`, `<ExprTail:End> ::=`.

Python has no `abstract` keyword either — check how this page's existing
`Exp` fragment currently expresses the "abstract base" idea (if at all;
Python doesn't enforce method presence at class-definition time the way
Java does) and follow that pattern for `ExprTail`.

Also update this page's own "BNF to Python constructs" table, its
"Generated output" file list (`AddExp.py`/`NumExp.py` → new names), and
any other stale `Exp`/`AddExp`/`NumExp`/`expList` references — grep the
whole file first, the way #166's design doc did, since #166 found two
such references that lived outside the example and its table and would
have been missed by a narrower fix.
```

- [ ] **Step 4: Fill in `dev-docs/issues/172-haskell-doc-quick-reference-not-ll1.md`**

Replace the template's sections with:

```markdown
## Description

`docs/language-guide/languages/haskell.md`'s "Quick reference example" has
the same left-recursive grammar as issue #166's Java version:
`<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>` makes `Exp` left-recursive,
which PLCC-ng's LL(1) parser rejects outright. The doc's claimed output for
`echo "1 + 2" | plcc-rep` is false as written, same as #166.

## Steps to Reproduce

1. Copy the "Quick reference example" grammar from
   `docs/language-guide/languages/haskell.md` verbatim into a `spec.plcc`.
2. `echo "1 + 2" | plcc-rep --spec=spec.plcc`
3. Actual: `plcc-make: error: grammar is not LL(1)` (same FIRST/FIRST
   conflict as #166). Expected per the doc: prints `3`.

## Notes

Same root cause as #166, but the fix's *shape* differs more here than in
the JS/Python siblings: this page's own "Fragment kinds" section documents
that Haskell fragment class names must be module names — the abstract
rule name (`Exp`) or a lone concrete name (`Prog`), never a concrete
alternative name (`AddExp`, `NumExp`). That means Haskell's `eval`
implementations for `Add`/`End` live as pattern-matched clauses inside a
single `ExprTail` fragment (`eval (Add ...) = ...` / `eval (End ...) =
...`), not as separate per-class fragments the way Java/JS/Python do it.
Whoever picks this up should design the left-factored grammar's Haskell
fragment(s) around that constraint from the start, rather than porting
#166's per-class fragment structure and hitting the "fragment tagged
'Add': Add is a concrete alternative of ExprTail" error.

Also update this page's own "BNF to Haskell constructs" table, its
"Generated output" file list (`AddExp.hs`/`NumExp.hs` → new names), and
any other stale `Exp`/`AddExp`/`NumExp`/`expList` references — grep the
whole file first, the way #166's design doc did, since #166 found two
such references that lived outside the example and its table and would
have been missed by a narrower fix.
```

- [ ] **Step 5: Add roadmap entries**

In `dev-docs/roadmap.md`, under the existing `### Docs` heading in the
Open Issues section, insert these three entries directly after the
existing `#169` entry (so the Docs group reads #166, #167, #169, #170, #171,
#172 in order):

```markdown
- **[#170](issues/170-javascript-doc-quick-reference-not-ll1.md) — JavaScript language guide's "Quick reference example" grammar is not LL(1)**
  Same left-recursive `Exp` rule as #166's Java version; `plcc-rep` rejects it with the same LL(1) conflict.
- **[#171](issues/171-python-doc-quick-reference-not-ll1.md) — Python language guide's "Quick reference example" grammar is not LL(1)**
  Same left-recursive `Exp` rule as #166's Java version; `plcc-rep` rejects it with the same LL(1) conflict.
- **[#172](issues/172-haskell-doc-quick-reference-not-ll1.md) — Haskell language guide's "Quick reference example" grammar is not LL(1)**
  Same left-recursive `Exp` rule as #166's Java version, but the fix must respect Haskell's fragment-naming constraint (pattern-matched clauses in one `ExprTail` fragment, not per-alternative fragments).
```

- [ ] **Step 6: Verify consistency**

```bash
bin/issues/check.bash
```

Expected: exits `0`, no drift reported.

- [ ] **Step 7: Commit**

```bash
git add dev-docs/issues/.next-id.txt \
        dev-docs/issues/170-javascript-doc-quick-reference-not-ll1.md \
        dev-docs/issues/171-python-doc-quick-reference-not-ll1.md \
        dev-docs/issues/172-haskell-doc-quick-reference-not-ll1.md \
        dev-docs/roadmap.md
git commit -m "$(cat <<'EOF'
docs(issues): file 170 - javascript doc quick reference not LL(1)
docs(issues): file 171 - python doc quick reference not LL(1)
docs(issues): file 172 - haskell doc quick reference not LL(1)

Same left-recursive Exp rule as #166's Java version, confirmed present
byte-for-byte in all three of these pages' own quick reference examples
while fixing #166. Filed as siblings rather than folded into #166's fix,
per this repo's convention of narrow, single-concern issues.
EOF
)"
```

---

## After this plan

Issue 166 closes as the final commit of this branch, per CLAUDE.md's issue-closing convention:

```bash
bin/issues/close.bash 166
```

This moves `dev-docs/issues/166-java-doc-quick-reference-not-ll1.md` to
`dev-docs/issues/done/` and updates `dev-docs/roadmap.md`. Verify with
`bin/issues/check.bash` afterward.

Issues #170, #171, #172 (filed in Task 4) stay open — they're follow-up
work, not part of this fix.
