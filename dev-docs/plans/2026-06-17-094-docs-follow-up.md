# Issue 094 Docs Follow-Up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update docs and the 093 issue file to reflect landed changes from issues 084, 089, and 095, and verify all output examples against the real tool.

**Architecture:** Four independent file edits. No new code. Each task modifies one file and commits. Order: 093 note → primitives.md → orchestrators.md → examples.md.

**Tech Stack:** Markdown docs, PLCC CLI tools (`plcc-make`, `plcc-scan`, `plcc-parse`, `plcc-rep`, `plcc-ll1`).

## Global Constraints

- All work happens in the `.worktrees/094-docs-status-after-initial-branch` worktree on branch `094-docs-status-after-initial-branch`.
- Commit subjects must include `[skip ci]` for docs-only commits.
- Do not modify any files outside the four listed below.

---

### Task 1: Add docs responsibility note to 093 issue

**Files:**
- Modify: `dev-docs/issues/093-incremental-parsing-repl.md`

**Interfaces:**
- Consumes: nothing
- Produces: nothing (standalone docs edit)

- [ ] **Step 1: Open the file and read it**

  Read `dev-docs/issues/093-incremental-parsing-repl.md` in full.

- [ ] **Step 2: Append the docs responsibility section**

  Add the following at the end of the file (after the last existing section):

  ```markdown

  ## Docs responsibility

  When this issue lands, update `docs/cli/orchestrators.md`:

  - Resolve the `<!-- TODO: verify how to suppress interactive mode (< /dev/null or EOF behavior) -->` comment in the `plcc-rep` section.
  - Update the "Evaluate a file only (no interactive mode)" example to reflect the new behavior.
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add dev-docs/issues/093-incremental-parsing-repl.md
  git commit -m "docs(093): note docs responsibility for orchestrators.md [skip ci]"
  ```

---

### Task 2: Document `plcc-ll1` in `primitives.md` and fix `plcc-trees`

**Files:**
- Modify: `docs/cli/primitives.md`

**Interfaces:**
- Consumes: nothing
- Produces: nothing (standalone docs edit)

`plcc-ll1` reads spec JSON from stdin (output of `plcc-spec`) and emits LL(1) analysis JSON to stdout. It belongs between `plcc-tokens` and `plcc-trees` in the doc.

- [ ] **Step 1: Add `plcc-ll1` section after `plcc-tokens`**

  Insert the following block between the `plcc-tokens` section and the `plcc-trees` section (after the `---` that follows `plcc-tokens`'s example):

  ````markdown
  ## plcc-ll1

  Perform LL(1) analysis on a grammar spec.

  ```text
  plcc-ll1 [-v ...]
  ```

  Reads spec JSON from stdin (output of `plcc-spec`); emits LL(1) analysis JSON to stdout.

  **Example:**

  ```bash
  plcc-spec spec.plcc | plcc-ll1 > ll1.json
  ```

  ---
  ````

- [ ] **Step 2: Remove the TODO comment from `plcc-trees` and add a pipeline example**

  In the `plcc-trees` section, replace:

  ```markdown
  <!-- TODO: document how to obtain LL1_JSON (output of plcc-ll1) -->
  ```

  with:

  ````markdown
  **Example:**

  ```bash
  plcc-spec spec.plcc | plcc-ll1 > ll1.json
  plcc-spec spec.plcc | plcc-tokens - samples | plcc-trees --ll1=ll1.json
  ```
  ````

- [ ] **Step 3: Commit**

  ```bash
  git add docs/cli/primitives.md
  git commit -m "docs(094): document plcc-ll1 and fix plcc-trees example [skip ci]"
  ```

---

### Task 3: Remove `--tool` from `plcc-rep` in `orchestrators.md`

**Files:**
- Modify: `docs/cli/orchestrators.md`

**Interfaces:**
- Consumes: nothing
- Produces: nothing (standalone docs edit)

Issue 095 removed named tools and the `--tool` flag entirely.

- [ ] **Step 1: Remove the `--tool=NAME` row from the plcc-rep options table**

  In the `plcc-rep` section, the options table currently contains:

  ```markdown
  | `--tool=NAME` | Semantic section to run. Inferred automatically when only one exists. |
  ```

  Delete that entire row.

- [ ] **Step 2: Update the plcc-rep examples**

  Replace the current example block:

  ```markdown
  **Example:**

  ```bash
  # Run the 'subtract' semantic section against samples, then enter interactive mode
  plcc-rep -s subtract.plcc --tool=subtract samples

  # Evaluate a file only (no interactive mode)
  plcc-rep -s subtract.plcc samples < /dev/null
  ```
  ```

  with:

  ````markdown
  **Example:**

  ```bash
  # Run against samples, then enter interactive mode
  plcc-rep -s subtract.plcc samples

  # Evaluate a file only (no interactive mode)
  plcc-rep -s subtract.plcc samples < /dev/null
  ```
  ````

  Leave the `<!-- TODO: verify how to suppress interactive mode (< /dev/null or EOF behavior) -->` comment in place — 093 owns that.

- [ ] **Step 3: Commit**

  ```bash
  git add docs/cli/orchestrators.md
  git commit -m "docs(094): remove --tool from plcc-rep (095) [skip ci]"
  ```

---

### Task 4: Full pass on `language-guide/examples.md`

**Files:**
- Modify: `docs/language-guide/examples.md`

**Interfaces:**
- Consumes: nothing
- Produces: nothing (standalone docs edit)

Three categories of change: (a) spec file syntax, (b) CLI flags, (c) verified output.

- [ ] **Step 1: Update the spec file block**

  Find the `Create \`subtract.plcc\`:` fenced code block. Replace its entire contents with:

  ```text
  # Subtraction language
  skip WHITESPACE '\s+'
  token WHOLE     '\d+'
  token MINUS     '\-'
  token LP        '\('
  token RP        '\)'
  token COMMA     ','
  %
  <Prog>         ::= <Exp:exp>
  <Exp:WholeExp> ::= <WHOLE:whole>
  <Exp:SubExp>   ::= MINUS LP <Exp:exp1> COMMA <Exp:exp2> RP
  %
  Python

  Prog
  %%%
  def _run(self):
      print(self.exp.eval())
  %%%

  WholeExp
  %%%
  def eval(self):
      return int(self.whole.lexeme)
  %%%

  SubExp
  %%%
  def eval(self):
      return self.exp1.eval() - self.exp2.eval()
  %%%
  ```

  Key changes from current file:
  - Remove the stray `%` line that appeared directly before `Python` (leftover from old `% subtract Python` divider syntax).
  - Result: exactly one `%` divider between the syntactic and semantic sections, followed by `Python` as the first line of the semantic section.

- [ ] **Step 2: Update the Build section**

  Replace the entire Build section (heading through closing fence) with:

  ````markdown
  ### Build

  ```bash
  plcc-make -s subtract.plcc
  ```

  Exits silently on success.
  ````

  (`plcc-make` produces no stdout output; the banner moved to stderr via `-b` in issue 084.)

- [ ] **Step 3: Update the Scanner section command and output**

  Replace:

  ````markdown
  ```bash
  plcc-scan -g subtract.plcc samples
  ```

  <!-- TODO: verify plcc-scan output format -->
  Expected output:

  ```text
     1: WHOLE '3'
     3: MINUS '-'
  ...
  ```
  ````

  with:

  ````markdown
  ```bash
  plcc-scan -s subtract.plcc samples
  ```

  Expected output:

  ```text
  samples:1:1 WHOLE '3'
  samples:3:1 MINUS '-'
  samples:3:2 LP '('
  samples:3:3 WHOLE '3'
  samples:3:4 COMMA ','
  samples:3:5 WHOLE '2'
  samples:3:6 RP ')'
  samples:5:1 MINUS '-'
  samples:5:2 LP '('
  samples:5:3 MINUS '-'
  samples:5:4 LP '('
  samples:5:5 WHOLE '4'
  samples:5:6 COMMA ','
  samples:5:7 WHOLE '1'
  samples:5:8 RP ')'
  samples:5:9 COMMA ','
  samples:5:11 MINUS '-'
  samples:5:12 LP '('
  samples:5:13 WHOLE '3'
  samples:5:14 COMMA ','
  samples:5:15 WHOLE '2'
  samples:5:16 RP ')'
  samples:5:17 RP ')'
  ```
  ````

- [ ] **Step 4: Update the Parser section command and output**

  Replace:

  ````markdown
  ```bash
  plcc-parse -g subtract.plcc samples
  ```

  <!-- TODO: verify plcc-parse output format and flags -->
  Expected output:

  ```text
  <Prog>
  | <Exp:WholeExp>
  ...
  ```
  ````

  with:

  ````markdown
  ```bash
  plcc-parse -s subtract.plcc samples
  ```

  Expected output:

  ```text
  Prog
    WholeExp
      WHOLE '3' [-:1:1]
  Prog
    SubExp
      WholeExp
        WHOLE '3' [-:3:3]
      WholeExp
        WHOLE '2' [-:3:5]
  Prog
    SubExp
      SubExp
        WholeExp
          WHOLE '4' [-:5:5]
        WholeExp
          WHOLE '1' [-:5:7]
      SubExp
        WholeExp
          WHOLE '3' [-:5:13]
        WholeExp
          WHOLE '2' [-:5:15]
  ```
  ````

- [ ] **Step 5: Update the Interpreter section command and output**

  Replace:

  ````markdown
  ```bash
  plcc-rep -g subtract.plcc --tool=subtract samples
  ```

  <!-- TODO: verify plcc-rep output format -->
  Expected output:

  ```text
  3
  1
  2
  ```
  ````

  with:

  ````markdown
  ```bash
  plcc-rep -s subtract.plcc samples < /dev/null
  ```

  Expected output:

  ```text
  3
  1
  2
  ```
  ````

  Note: `< /dev/null` suppresses interactive mode. This will be updated once issue 093 lands and the interactive mode behavior is finalized.

- [ ] **Step 6: Commit**

  ```bash
  git add docs/language-guide/examples.md
  git commit -m "docs(094): update examples for 089+095, verify all output [skip ci]"
  ```
