# Issue 127: plcc-rep Protocol, `specification_error`, and `LanguageError` Docs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add user-facing documentation for `plcc-rep`'s startup/error behavior, the `LanguageError` mechanism, and how `plcc-rep` distinguishes language behavior from specification errors.

**Architecture:** Pure documentation edits across six existing Markdown files. No code changes. All six tasks are fully independent and can be done in any order. The design spec is at `docs/superpowers/specs/2026-06-30-127-rep-protocol-language-error-design.md`.

**Tech Stack:** Markdown, MkDocs (`bin/docs/serve.bash` to preview).

## Global Constraints

- All six files are existing docs — edit only, do not create new files.
- `LanguageError` sections on the three working languages (Python, Java, JavaScript) document the *intended* behavior: in scope by default without an explicit import. This is correct once issue 132 lands; the project has not released yet so docs-ahead-of-implementation is acceptable.
- The Haskell section documents the *current limitation* (not yet accessible from user code) and references issues 131 and 132.
- Commit style: `docs(rep): …` matching the existing git log.
- CI skips automatically for doc-only changes — no `[skip ci]` annotation needed.

---

### Task 1: Add "Startup and errors" section to `plcc-rep.md`

**Files:**

- Modify: `docs/cli/commands/plcc-rep.md`

**Interfaces:**

- Produces: a "Startup and errors" section readers can be directed to from `semantic.md` and the per-language pages.

- [ ] **Step 1: Confirm the insertion point**

  The new section goes at the end of the file, after "Interactive mode".

  ```bash
  tail -10 docs/cli/commands/plcc-rep.md
  ```

  Expected: the last lines are the Interactive mode content (the `^D` bullet points).

- [ ] **Step 2: Append the "Startup and errors" section**

  Add the following to the end of `docs/cli/commands/plcc-rep.md`. The outer fence uses four backticks because the content contains three-backtick fences — copy the inner content exactly as shown.

  ````markdown

  ## Startup and errors

  When `plcc-rep` starts, it builds your spec and launches an interpreter subprocess. If the interpreter fails to start — for example, because your semantics code has a syntax error that prevents it from loading — you will see:

  ```text
  Specification error: interpreter failed to start.
  Fix the errors in your specification and re-run.
  ```

  During a session, `plcc-rep` distinguishes between two categories:

  **Language behavior** — the defined language working as designed. `plcc-rep` reports the outcome and gives you a fresh prompt:

  - The scanner did not recognize the input (lexical error).
  - The parser found input that does not match any rule (syntax error).
  - Your semantics code raised a `LanguageError` (semantic rejection — e.g., a type error or division by zero your language author chose to handle explicitly).

  **Specification errors** — a flaw in the language specification itself. Your semantics code threw an unexpected exception (not a `LanguageError`). `plcc-rep` prints the error type and message, then exits. Fix the problem in your spec and re-run.

  See your language's page for how to raise a `LanguageError` from semantics code.
  ````

- [ ] **Step 3: Verify the section was added**

  ```bash
  grep -n "Startup and errors\|Language behavior\|Specification errors" docs/cli/commands/plcc-rep.md
  ```

  Expected: three matching lines in the new section.

- [ ] **Step 4: Commit**

  ```bash
  git add docs/cli/commands/plcc-rep.md
  git commit -m "docs(rep): document startup handshake and error taxonomy"
  ```

---

### Task 2: Add "Signaling errors from semantics" section to `semantic.md`

**Files:**

- Modify: `docs/language-guide/semantic.md`

**Interfaces:**

- Produces: a cross-language explanation of `LanguageError` that links readers to the per-language pages.

- [ ] **Step 1: Find the insertion point**

  The new section goes after the `## Entry point: '_run'` section and before `## Hooks`. Confirm:

  ```bash
  grep -n "## Entry point\|## Hooks\|## Adding" docs/language-guide/semantic.md
  ```

  Expected: `## Entry point` line number < `## Hooks` line number.

- [ ] **Step 2: Insert the "Signaling errors from semantics" section**

  In `docs/language-guide/semantic.md`, add the following block after the paragraph that ends "Override `_run` in your start class to implement your language's semantics." and before the `## Hooks` heading:

  ```markdown

  ## Signaling errors from semantics

  When your semantics code needs to report a deliberate error — a type mismatch, a precondition violation, or any condition your language treats as an error — raise a `LanguageError`. `plcc-rep` prints the message and gives a fresh prompt; the session continues.

  Raising any other exception is treated as a bug in your specification. `plcc-rep` prints a Specification Error and exits.

  Each language provides `LanguageError` as part of its generated runtime. See your language's page for the exact syntax.
  ```

- [ ] **Step 3: Verify the section is in the right place**

  ```bash
  grep -n "Signaling errors\|## Hooks\|## Entry point" docs/language-guide/semantic.md
  ```

  Expected: `## Entry point` line < `Signaling errors` line < `## Hooks` line.

- [ ] **Step 4: Commit**

  ```bash
  git add docs/language-guide/semantic.md
  git commit -m "docs(rep): add LanguageError overview to semantic section guide"
  ```

---

### Task 3: Add `LanguageError` section to `python.md`

**Files:**

- Modify: `docs/language-guide/languages/python.md`

- [ ] **Step 1: Find the insertion point**

  The section goes after the `_run` entry point section and before "## Referencing other generated classes".

  ```bash
  grep -n "_run entry point\|## Referencing\|## Generated" docs/language-guide/languages/python.md
  ```

  Expected: `_run entry point` line number < `## Referencing` line number.

- [ ] **Step 2: Insert the `LanguageError` section**

  In `docs/language-guide/languages/python.md`, add the following after the paragraph "The default `_Start._run()` prints `str(self)`. Override it to replace the default behavior." and before `## Referencing other generated classes`. The outer fence uses four backticks because the content contains three-backtick fences — copy the inner content exactly as shown.

  ````markdown

  ## `LanguageError`

  Raise `LanguageError` to signal a deliberate error in the defined language — a type mismatch, division by zero, or any condition your language treats as an error. `plcc-rep` prints the message and gives a fresh prompt; the session continues.

  `LanguageError` is available in all generated classes without any import:

  ```python
  def eval(self):
      raise LanguageError("type mismatch: expected int")
  ```

  Subclass it to create named error types:

  ```python
  class TypeError(LanguageError): pass
  raise TypeError("expected int")
  ```

  Any other exception (not `LanguageError` or a subclass) is treated as a specification error — `plcc-rep` prints the error and exits.
  ````

- [ ] **Step 3: Verify**

  ```bash
  grep -n "LanguageError\|## Referencing" docs/language-guide/languages/python.md
  ```

  Expected: `LanguageError` lines appear before `## Referencing`.

- [ ] **Step 4: Commit**

  ```bash
  git add docs/language-guide/languages/python.md
  git commit -m "docs(rep): document LanguageError for Python"
  ```

---

### Task 4: Add `LanguageError` section to `java.md`

**Files:**

- Modify: `docs/language-guide/languages/java.md`

- [ ] **Step 1: Find the insertion point**

  The section goes after the `_run` entry point section and before "## Referencing other generated classes".

  ```bash
  grep -n "_run entry point\|## Referencing\|## Generated" docs/language-guide/languages/java.md
  ```

  Expected: `_run entry point` line number < `## Referencing` line number.

- [ ] **Step 2: Insert the `LanguageError` section**

  In `docs/language-guide/languages/java.md`, add the following after the paragraph "Abstract classes cannot be instantiated. Declare abstract methods on them so the Java compiler enforces that all concrete subclasses implement them (see `Exp` in the quick reference example)." and before `## Referencing other generated classes`. The outer fence uses four backticks because the content contains three-backtick fences — copy the inner content exactly as shown.

  ````markdown

  ## `LanguageError`

  Throw `LanguageError` to signal a deliberate error in the defined language — a type mismatch, division by zero, or any condition your language treats as an error. `plcc-rep` prints the message and gives a fresh prompt; the session continues.

  `LanguageError` is available in all generated classes without any import:

  ```java
  public int eval() {
      throw new LanguageError("type mismatch: expected int");
  }
  ```

  Subclass it to create named error types:

  ```java
  public class TypeError extends LanguageError {
      public TypeError(String msg) { super(msg); }
  }
  throw new TypeError("expected int");
  ```

  Any other exception (not `LanguageError` or a subclass) is treated as a specification error — `plcc-rep` prints the error and exits.
  ````

- [ ] **Step 3: Verify**

  ```bash
  grep -n "LanguageError\|## Referencing" docs/language-guide/languages/java.md
  ```

  Expected: `LanguageError` lines appear before `## Referencing`.

- [ ] **Step 4: Commit**

  ```bash
  git add docs/language-guide/languages/java.md
  git commit -m "docs(rep): document LanguageError for Java"
  ```

---

### Task 5: Add `LanguageError` section to `javascript.md`

**Files:**

- Modify: `docs/language-guide/languages/javascript.md`

- [ ] **Step 1: Find the insertion point**

  The section goes after the `_run` entry point section and before "## Referencing other generated classes".

  ```bash
  grep -n "_run entry point\|## Referencing\|## Generated" docs/language-guide/languages/javascript.md
  ```

  Expected: `_run entry point` line number < `## Referencing` line number.

- [ ] **Step 2: Insert the `LanguageError` section**

  In `docs/language-guide/languages/javascript.md`, add the following after the paragraph "The default `_Start._run()` prints `String(this)` to stdout. Override it to replace the default behavior entirely." and before `## Referencing other generated classes`. The outer fence uses four backticks because the content contains three-backtick fences — copy the inner content exactly as shown.

  ````markdown

  ## `LanguageError`

  Throw `LanguageError` to signal a deliberate error in the defined language — a type mismatch, division by zero, or any condition your language treats as an error. `plcc-rep` prints the message and gives a fresh prompt; the session continues.

  `LanguageError` is available in all generated classes without any import:

  ```javascript
  eval() {
      throw new LanguageError("type mismatch: expected int");
  }
  ```

  Subclass it to create named error types:

  ```javascript
  class TypeError extends LanguageError {}
  throw new TypeError("expected int");
  ```

  Any other exception (not `LanguageError` or a subclass) is treated as a specification error — `plcc-rep` prints the error and exits.
  ````

- [ ] **Step 3: Verify**

  ```bash
  grep -n "LanguageError\|## Referencing" docs/language-guide/languages/javascript.md
  ```

  Expected: `LanguageError` lines appear before `## Referencing`.

- [ ] **Step 4: Commit**

  ```bash
  git add docs/language-guide/languages/javascript.md
  git commit -m "docs(rep): document LanguageError for JavaScript"
  ```

---

### Task 6: Add `LanguageError` section to `haskell.md`

**Files:**

- Modify: `docs/language-guide/languages/haskell.md`

- [ ] **Step 1: Find the insertion point**

  The section goes after the `_run` entry point section and before "## Referencing other generated modules".

  ```bash
  grep -n "_run entry point\|## Referencing\|## Generated" docs/language-guide/languages/haskell.md
  ```

  Expected: `_run entry point` line number < `## Referencing` line number.

- [ ] **Step 2: Insert the `LanguageError` section**

  In `docs/language-guide/languages/haskell.md`, add the following after the paragraph "If you do not define `_run`, the default `_run = show` is injected, which prints the `Show` instance of the root node." and before `## Referencing other generated modules`:

  ```markdown

  ## `LanguageError`

  `LanguageError` is the intended mechanism for signaling a deliberate error in the defined language from Haskell semantics code. When thrown, `plcc-rep` prints the message and gives a fresh prompt; the session continues.

  `LanguageError` is currently not accessible from user-authored module files — it is defined in the generated `Main.hs`, which user modules cannot import. Support for throwing `LanguageError` from semantics code is tracked in issues 131 and 132.

  In the meantime, note that Haskell's built-in `error "message"` throws `ErrorCall`, which is treated as a **specification error** (not a language error) — `plcc-rep` will exit.
  ```

- [ ] **Step 3: Verify**

  ```bash
  grep -n "LanguageError\|## Referencing" docs/language-guide/languages/haskell.md
  ```

  Expected: `LanguageError` lines appear before `## Referencing`.

- [ ] **Step 4: Commit**

  ```bash
  git add docs/language-guide/languages/haskell.md
  git commit -m "docs(rep): document LanguageError limitation for Haskell"
  ```
