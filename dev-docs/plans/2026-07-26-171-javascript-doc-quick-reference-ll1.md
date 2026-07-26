# JavaScript Quick-Reference LL(1) Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `docs/language-guide/languages/javascript.md`'s "Quick reference example" an LL(1) grammar that actually emits and evaluates, so its documented `echo "1 + 2" | plcc-rep` → `3` claim is true, and re-ground every downstream reference to the old class names.

**Architecture:** Docs-only edit. Replace the left-recursive `<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>` grammar with the operator-alternation left-factoring proven in issue #166 (Java): `<Expr> ::= <NUM:left> <Op:op> <NUM:right>` with `<Op:AddOp> ::= PLUS` / `<Op:SubOp> ::= MINUS` (new `MINUS` token). Then update the BNF table, the default-naming paragraph, the Fragment-kinds `MathHelper` example, the `_run` example, the Generated-output file list, and two Tips lines to match the new names. Verification is manual end-to-end runs (no automated suite covers doc prose).

**Tech Stack:** PLCC-ng CLI (`plcc-rep`, on PATH via `.venv`), Node.js 18+ (JavaScript emitter target), Markdown.

**Design doc:** [dev-docs/specs/2026-07-25-171-javascript-doc-quick-reference-ll1-design.md](../specs/2026-07-25-171-javascript-doc-quick-reference-ll1-design.md)

## Global Constraints

- **Single file of substance:** only `docs/language-guide/languages/javascript.md` changes (plus this plan/design under `dev-docs/`). No source or generated code changes.
- **Workspace:** work in the existing `worktree-run-contract-impl` worktree (per direction), on its current branch. Do NOT create a new branch/worktree.
- **Abstract base `Op` gets no fragment.** JavaScript has no `abstract` keyword; the page conveys abstractness only via the grammar, the table's "alternative rule" row, and a Tips line — mirroring how the page treats `Exp` today. Do not add an `Op` fragment.
- **Method name is `apply`** (matches the Java doc; `this.op` is a class instance, so no `Function.prototype.apply` clash).
- **Arbno field name is `exprList`** (`<lowerCasedSymbol>List` for `<Prog> **= <Expr>`).
- **Verification commands** use the real, installed CLI: `echo "<input>" | plcc-rep --spec=spec.plcc`. A spec's language is selected from its semantic-section language line (`javascript`); no extra flag needed.
- Do NOT write ad-hoc shell scripts (per CLAUDE.md). Use `plcc-rep` directly and `bin/issues/close.bash` to close.

---

### Task 1: Reproduce the bug and prove the replacement grammar works

Establishes the "failing test → passing test" gate before touching the doc. No doc edits in this task.

**Files:**
- Create (scratch, not committed): `<scratchdir>/broken.plcc`, `<scratchdir>/fixed.plcc`

**Interfaces:**
- Produces: a verified `fixed.plcc` spec whose grammar + fragments are byte-identical to what Task 2 will paste into the doc. Later tasks re-run this same spec content.

- [ ] **Step 1: Write the currently-documented (broken) spec to reproduce the failure**

Create `<scratchdir>/broken.plcc` with the doc's *current* quick-reference contents:

```text
token NUM   '\d+'
token PLUS  '\+'
skip  SPACE '\s+'
%
<Prog>       **= <Exp>
<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>
<Exp:NumExp> ::= <NUM>
%
javascript

Prog
%%%
_run() {
    return this.expList.map(exp => String(exp.eval())).join('\n');
}
%%%

AddExp
%%%
eval() {
    return this.left.eval() + this.right.eval();
}
%%%

NumExp
%%%
eval() {
    return parseInt(this.num.lexeme);
}
%%%
```

- [ ] **Step 2: Confirm the current grammar fails (reproduces issue #171)**

Run: `echo "1 + 2" | plcc-rep --spec=<scratchdir>/broken.plcc`
Expected: FAILS — a "grammar is not LL(1)" / FIRST-FIRST conflict error on `<Exp>` at lookahead `NUM`. It must NOT print `3`. This is the bug the doc currently misrepresents.

- [ ] **Step 3: Write the replacement (fixed) spec**

Create `<scratchdir>/fixed.plcc` with exactly:

```text
token NUM   '\d+'
token PLUS  '\+'
token MINUS '-'
skip  SPACE '\s+'
%
<Prog>     **= <Expr>
<Expr>     ::= <NUM:left> <Op:op> <NUM:right>
<Op:AddOp> ::= PLUS
<Op:SubOp> ::= MINUS
%
javascript

Expr
%%%
eval() {
    return this.op.apply(parseInt(this.left.lexeme), parseInt(this.right.lexeme));
}
%%%

Prog
%%%
_run() {
    return this.exprList.map(expr => String(expr.eval())).join('\n');
}
%%%

AddOp
%%%
apply(left, right) {
    return left + right;
}
%%%

SubOp
%%%
apply(left, right) {
    return left - right;
}
%%%
```

- [ ] **Step 4: Confirm the replacement grammar emits and evaluates correctly**

Run these three and check each:
- `echo "1 + 2" | plcc-rep --spec=<scratchdir>/fixed.plcc` → last line `3`
- `echo "5 - 3" | plcc-rep --spec=<scratchdir>/fixed.plcc` → last line `2` (exercises `SubOp`, not just `AddOp`)
- `echo "1 + 2 5 - 3" | plcc-rep --spec=<scratchdir>/fixed.plcc` → lines `3` then `2` (exercises the arbno list with >1 element)

Expected: all three as stated. (No commit — these are scratch files outside the repo.)

---

### Task 2: Rewrite the Quick reference example (grammar + fragments)

**Files:**
- Modify: `docs/language-guide/languages/javascript.md` (the ```text block under "## Quick reference example", currently lines ~26–57)

**Interfaces:**
- Consumes: the verified `fixed.plcc` content from Task 1.
- Produces: the canonical grammar names (`Prog`, `Expr`, `Op`/`AddOp`/`SubOp`, `NUM`/`PLUS`/`MINUS`, field `exprList`) that Tasks 3–5 reference.

- [ ] **Step 1: Replace the example block**

In the ```text fenced block under "## Quick reference example", replace this exact content:

```text
token NUM   '\d+'
token PLUS  '\+'
skip  SPACE '\s+'
%
<Prog>       **= <Exp>
<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>
<Exp:NumExp> ::= <NUM>
%
javascript

Prog
%%%
_run() {
    return this.expList.map(exp => String(exp.eval())).join('\n');
}
%%%

AddExp
%%%
eval() {
    return this.left.eval() + this.right.eval();
}
%%%

NumExp
%%%
eval() {
    return parseInt(this.num.lexeme);
}
%%%
```

with (identical to Task 1's `fixed.plcc`):

```text
token NUM   '\d+'
token PLUS  '\+'
token MINUS '-'
skip  SPACE '\s+'
%
<Prog>     **= <Expr>
<Expr>     ::= <NUM:left> <Op:op> <NUM:right>
<Op:AddOp> ::= PLUS
<Op:SubOp> ::= MINUS
%
javascript

Expr
%%%
eval() {
    return this.op.apply(parseInt(this.left.lexeme), parseInt(this.right.lexeme));
}
%%%

Prog
%%%
_run() {
    return this.exprList.map(expr => String(expr.eval())).join('\n');
}
%%%

AddOp
%%%
apply(left, right) {
    return left + right;
}
%%%

SubOp
%%%
apply(left, right) {
    return left - right;
}
%%%
```

Leave the sentence below the block ("Running this with `echo "1 + 2" | plcc-rep` prints `3`.") unchanged — it is now true. Do NOT add an `Op` fragment.

- [ ] **Step 2: Verify the doc's block runs end-to-end**

Copy the *new* block verbatim from the doc into a fresh `spec.plcc` and run:
- `echo "1 + 2" | plcc-rep --spec=spec.plcc` → `3`
- `echo "5 - 3" | plcc-rep --spec=spec.plcc` → `2`

Expected: both pass. (This confirms the pasted-from-doc block matches Task 1's verified spec.)

- [ ] **Step 3: Commit**

```bash
git add docs/language-guide/languages/javascript.md
git commit -m "docs(javascript): fix quick-reference grammar to be LL(1) (#171)"
```

---

### Task 3: Re-ground the BNF constructs table and default-naming paragraph

**Files:**
- Modify: `docs/language-guide/languages/javascript.md` ("## BNF to JavaScript constructs" table, ~lines 63–70, and the paragraph immediately below it, ~line 72)

**Interfaces:**
- Consumes: the new grammar names from Task 2.

- [ ] **Step 1: Replace the table body rows**

Replace these exact six rows:

```text
| Concrete rule (LHS, no alt name) — generates one class | `<Prog>` in `<Prog> **= <Exp>` | ES6 class with constructor and fields | `class Prog extends _Start { constructor(expList) { ... } }` |
| Alternative rule (LHS, with alt name) — base nonterminal becomes abstract | `<Exp:AddExp>` in `<Exp:AddExp> ::= ...` | ES6 class extending the base nonterminal | `class AddExp extends Exp { constructor(left, right) { ... } }` |
| Named non-terminal (RHS) | `<Exp:left>` | `this.left` — an `Exp` instance | `this.left.eval()` |
| Captured terminal (RHS) | `<NUM>` | `this.num` — a `Token`; `.lexeme` for the string value | `parseInt(this.num.lexeme)` |
| Uncaptured terminal (RHS) | `PLUS` | No field generated | — |
| Arbno rule (`**=`) | `<Prog> **= <Exp>` | `this.expList` — `Array` of `Exp` | `this.expList.map(e => e.eval())` |
```

with:

```text
| Concrete rule (LHS, no alt name) — generates one class | `<Prog>` in `<Prog> **= <Expr>` | ES6 class with constructor and fields | `class Prog extends _Start { constructor(exprList) { ... } }` |
| Alternative rule (LHS, with alt name) — base nonterminal becomes abstract | `<Op:AddOp>` in `<Op:AddOp> ::= PLUS` | ES6 class extending the base nonterminal | `class AddOp extends Op { ... }` |
| Named non-terminal (RHS) | `<Op:op>` in `<Expr> ::= <NUM:left> <Op:op> <NUM:right>` | `this.op` — an `Op` instance | `this.op.apply(left, right)` |
| Captured terminal (RHS) | `<NUM:left>` | `this.left` — a `Token`; `.lexeme` for the string value | `parseInt(this.left.lexeme)` |
| Uncaptured terminal (RHS) | `PLUS` in `<Op:AddOp> ::= PLUS` | No field generated | — |
| Arbno rule (`**=`) | `<Prog> **= <Expr>` | `this.exprList` — `Array` of `Expr` | `this.exprList.map(e => e.eval())` |
```

- [ ] **Step 2: Fix the default-naming paragraph below the table**

Replace this exact sentence:

```text
Without explicit `:name` on a RHS symbol, the field name is the symbol name lowercased (e.g., `<Exp>` → `this.exp`, `<NUM>` → `this.num`). Use explicit names when two RHS symbols would produce the same field name.
```

with:

```text
Without explicit `:name` on a RHS symbol, the field name is the symbol name lowercased (e.g., `<Expr>` → `this.expr`, `<NUM>` → `this.num`). Use explicit names when two RHS symbols would produce the same field name.
```

- [ ] **Step 3: Verify no old table names remain in this section**

Run: `grep -nE '<Exp|AddExp|expList|this\.exp\b' docs/language-guide/languages/javascript.md`
Expected: no matches within the table or the paragraph (lines ~61–73). (Other sections are fixed in Tasks 4–5; if this grep still shows lines outside this range, that's expected until then.)

- [ ] **Step 4: Commit**

```bash
git add docs/language-guide/languages/javascript.md
git commit -m "docs(javascript): re-ground BNF table + naming paragraph on new grammar (#171)"
```

---

### Task 4: Re-ground the Fragment-kinds `MathHelper` example

The illustrative import/file-fragment example references `NumExp` and `this.num`, both removed by the new grammar.

**Files:**
- Modify: `docs/language-guide/languages/javascript.md` (the ```text block under "### Example" in "## Fragment kinds", ~lines 92–112)

- [ ] **Step 1: Replace the example block**

Replace this exact content:

```text
NumExp:import
%%%
const { MathHelper } = require('./MathHelper');
%%%

NumExp
%%%
eval() {
    return MathHelper.parse(this.num.lexeme);
}
%%%

MathHelper:file
%%%
class MathHelper {
    static parse(s) { return parseInt(s, 10); }
}
module.exports = { MathHelper };
%%%
```

with:

```text
Expr:import
%%%
const { MathHelper } = require('./MathHelper');
%%%

Expr
%%%
eval() {
    return this.op.apply(MathHelper.parse(this.left.lexeme), MathHelper.parse(this.right.lexeme));
}
%%%

MathHelper:file
%%%
class MathHelper {
    static parse(s) { return parseInt(s, 10); }
}
module.exports = { MathHelper };
%%%
```

- [ ] **Step 2: Verify no `NumExp` remains anywhere in the file**

Run: `grep -n 'NumExp' docs/language-guide/languages/javascript.md`
Expected: no matches (this was the last non-generated-output `NumExp`; the Generated-output list is handled in Task 5, so if a match remains it should only be at ~line 177 — note it for Task 5).

- [ ] **Step 3: Commit**

```bash
git add docs/language-guide/languages/javascript.md
git commit -m "docs(javascript): re-ground MathHelper fragment example on Expr (#171)"
```

---

### Task 5: Fix remaining stale references (`_run` example, Generated output, Tips)

**Files:**
- Modify: `docs/language-guide/languages/javascript.md` (the `_run` example ~line 122; the Generated-output tree ~lines 176–177; two Tips lines ~223–224)

- [ ] **Step 1: Fix the `_run` entry-point example**

In the ```javascript block under "## `_run` entry point", replace:

```text
    return this.expList.map(exp => String(exp.eval())).join('\n');
```

with:

```text
    return this.exprList.map(expr => String(expr.eval())).join('\n');
```

(The surrounding prose "`Prog` in the quick reference example" is correct — `Prog` is still the start class — leave it.)

- [ ] **Step 2: Fix the Generated-output file list**

In the ```text tree under "## Generated output", replace these two lines:

```text
  AddExp.js
  NumExp.js
```

with:

```text
  Expr.js
  AddOp.js
  SubOp.js
```

(The abstract `Op.js` stays unlisted, matching the list's existing practice of omitting the abstract base — it already omitted `Exp.js`. `Prog.js` above stays.)

- [ ] **Step 3: Fix the two Tips lines**

Replace:

```text
- Abstract classes (`Exp` in the quick reference example) are never instantiated. You cannot add a constructor to them via fragments.
```

with:

```text
- Abstract classes (`Op` in the quick reference example) are never instantiated. You cannot add a constructor to them via fragments.
```

Replace:

```text
- The arbno field name is always `<lowerCasedSymbol>List`. For `<Prog> **= <Exp>`, the field is `this.expList`.
```

with:

```text
- The arbno field name is always `<lowerCasedSymbol>List`. For `<Prog> **= <Expr>`, the field is `this.exprList`.
```

- [ ] **Step 4: Commit**

```bash
git add docs/language-guide/languages/javascript.md
git commit -m "docs(javascript): fix remaining stale Exp/AddExp/NumExp refs (#171)"
```

---

### Task 6: Full-file sweep and close the issue

**Files:**
- Modify (via script): issue moves to `dev-docs/issues/done/`, `dev-docs/roadmap.md` updated by `bin/issues/close.bash`

- [ ] **Step 1: Confirm no stale grammar names remain anywhere in the file**

Run: `grep -nE '\bExp\b|AddExp|NumExp|expList|<Exp' docs/language-guide/languages/javascript.md`
Expected: NO matches. (Every `Exp`/`AddExp`/`NumExp`/`expList` should now be `Expr`/`AddOp`/`SubOp`/`exprList` or removed.) If any line matches, fix it in the section it belongs to and re-run before continuing.

- [ ] **Step 2: Final end-to-end sanity check from the doc**

Rebuild `spec.plcc` from the doc's (now-updated) Quick reference example block and run once more:
- `echo "1 + 2" | plcc-rep --spec=spec.plcc` → `3`
- `echo "5 - 3" | plcc-rep --spec=spec.plcc` → `2`

Expected: both pass.

- [ ] **Step 3: Close the issue**

Run: `bin/issues/close.bash 171`
This moves `dev-docs/issues/done/171-javascript-doc-quick-reference-not-ll1.md` to `done/` and updates `dev-docs/roadmap.md`.

- [ ] **Step 4: Verify issue-tracker consistency**

Run: `bin/issues/check.bash`
Expected: no inconsistencies reported.

- [ ] **Step 5: Commit the close**

```bash
git add -A
git commit -m "docs(issues): close #171 (javascript quick-reference LL(1))"
```

---

## Self-Review

**Spec coverage** (design doc → task):
- Change §1 Quick-reference grammar + fragments → Task 2. ✓
- Change §2 BNF table + default-naming paragraph → Task 3. ✓
- Change §3 Fragment-kinds `MathHelper` example → Task 4. ✓
- Change §4 `_run` example / Generated-output list / two Tips lines → Task 5. ✓
- JS-specific decision "no `Op` fragment" → Global Constraints + Task 2 Step 1 note. ✓
- JS-specific decision "keep `apply`" → Global Constraints + reflected in fragment code. ✓
- Testing (`1 + 2`→3, `5 - 3`→2) → Task 1 Step 4, Task 2 Step 2, Task 6 Step 2. ✓
- Commit shape / close via `bin/issues/close.bash 171` → Task 6. ✓

**Placeholder scan:** No TBD/TODO; every edit gives exact old→new text and every verification gives an exact command and expected result. `<scratchdir>` is an intentional path placeholder for the executor's scratch directory (files there are never committed). ✓

**Type/name consistency:** `Expr`, `Op`/`AddOp`/`SubOp`, field `exprList`, method `apply`, `MINUS` token, and `this.left`/`this.right`/`this.op` are used identically across Tasks 1–6 and match the design doc. The arbno field is `exprList` everywhere (never `expList`). ✓
