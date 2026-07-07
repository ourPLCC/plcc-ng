# Installation Page and Migration Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `installation.md` (pip install, upgrade, pin, uninstall) and `migration.md` (checklist for PLCC → PLCC-ng), rename `getting-started.md` → `quick-start.md`, and update the nav.

**Architecture:** Pure docs changes — markdown files and `mkdocs.yml`. No code changes. Each task ends with a `mkdocs build --strict` verification and a commit. Tasks are ordered so the build stays green at every step.

**Tech Stack:** MkDocs Material, Markdown, `mkdocs build --strict` for verification. Run mkdocs via `.venv/bin/mkdocs` from the repo root.

## Global Constraints

- All commits are docs commits; subject line must end with `[skip ci]`
- Commit message format: `docs(<scope>): <description> [skip ci]`
- Work in the worktree at `.worktrees/issue-071-072-102-docs-upgrade-migration/`
- Run `mkdocs build --strict` from inside the worktree (where `mkdocs.yml` lives)
- `%include` directive syntax in PLCC-ng: `%include FILENAME` (with `%` prefix)
- Do not create or modify any files outside `docs/` and `mkdocs.yml`

---

### Task 1: Rename Quick Start and update all references

**Files:**
- Rename: `docs/getting-started.md` → `docs/quick-start.md`
- Modify: `mkdocs.yml` (update filename and nav label)
- Modify: `docs/index.md` (update link text and target)

**Interfaces:**
- Produces: `docs/quick-start.md` — same content as `getting-started.md`, ready for a link addition in Task 2

- [ ] **Step 1: Rename the file**

```bash
git mv docs/getting-started.md docs/quick-start.md
```

- [ ] **Step 2: Update `mkdocs.yml`**

Find this line:
```yaml
  - Getting Started: getting-started.md
```
Replace with:
```yaml
  - Quick Start: quick-start.md
```

- [ ] **Step 3: Update the H1 title in `docs/quick-start.md`**

Find:
```markdown
# Getting Started
```
Replace with:
```markdown
# Quick Start
```

- [ ] **Step 4: Update `docs/index.md`**

Find this line:
```markdown
- [Getting Started](getting-started.md) — Install plcc-ng and run your first specification in under 10 minutes.
```
Replace with:
```markdown
- [Quick Start](quick-start.md) — Install plcc-ng and run your first specification in under 10 minutes.
```

- [ ] **Step 5: Verify the build**

```bash
.venv/bin/mkdocs build --strict
```
Expected: build succeeds with no warnings or errors. The `site/` directory is created or updated.

- [ ] **Step 6: Commit**

```bash
git add docs/quick-start.md docs/index.md mkdocs.yml
git commit -m "docs(quick-start): rename getting-started to quick-start [skip ci]"
```

Note: `git mv` already staged the rename; `git add` picks up the modified files.

---

### Task 2: Create `installation.md` and wire it into the nav

**Files:**
- Create: `docs/installation.md`
- Modify: `mkdocs.yml` (add nav entry)
- Modify: `docs/quick-start.md` (add link to installation.md)

**Interfaces:**
- Consumes: `docs/quick-start.md` from Task 1
- Produces: `docs/installation.md` — covers pip install, upgrade, pinning, uninstall

- [ ] **Step 1: Create `docs/installation.md`**

Create the file with this exact content:

```markdown
# Installation

This page covers installing plcc-ng via pip.
Additional installation methods will be documented here as they become available.

## Requirements

- Python 3.12 or later
- Java JDK 21 or later (only needed if implementing semantics in Java)

## Install

```bash
pip install plcc-ng
```

Verify the installation:

```bash
plcc-version
```

## Upgrade

```bash
pip install --upgrade plcc-ng
```

Verify the new version:

```bash
plcc-version
```

Check the [Changelog](changelog.md) for breaking changes between versions before upgrading.

## Pin a Specific Version

To install a specific version:

```bash
pip install plcc-ng==X.Y.Z
```

To pin in `requirements.txt`:

```
plcc-ng==X.Y.Z
```

To pin in `pyproject.toml`:

```toml
[project]
dependencies = [
    "plcc-ng==X.Y.Z",
]
```

Check which version is currently installed:

```bash
plcc-version
```

## Uninstall

```bash
pip uninstall plcc-ng
```
```

- [ ] **Step 2: Add nav entry to `mkdocs.yml`**

Find:
```yaml
  - Quick Start: quick-start.md
```
Replace with:
```yaml
  - Quick Start: quick-start.md
  - Installation: installation.md
```

- [ ] **Step 3: Add link in `docs/quick-start.md`**

In `docs/quick-start.md`, find the install block. It looks like:

```markdown
## Install

```bash
pip install plcc-ng
```
```

Add a line immediately after the closing code fence:

```markdown
For upgrade, version pinning, and uninstall instructions, see [Installation](installation.md).
```

- [ ] **Step 4: Verify the build**

```bash
.venv/bin/mkdocs build --strict
```
Expected: build succeeds with no warnings or errors.

- [ ] **Step 5: Commit**

```bash
git add docs/installation.md docs/quick-start.md mkdocs.yml
git commit -m "docs(installation): add installation page with upgrade, pinning, and uninstall [skip ci]"
```

---

### Task 3: Create `migration.md` and wire it into the nav

**Files:**
- Create: `docs/migration.md`
- Modify: `mkdocs.yml` (add nav entry)

**Interfaces:**
- Consumes: nothing from earlier tasks
- Produces: `docs/migration.md` — full migration checklist

**Scan algorithm behavior (verified from `src/plcc/scan/matcher_test.py`):**
- PLCC: skip rules take priority over *all* token rules when they match *any* input, regardless of match length
- PLCC-ng: pure first-longest-match — skip and token rules compete equally; ties broken by declaration order
- Example: with `skip ONE '1'` and `token NUMBER '\d+'`, input `123` → PLCC emits nothing (skip wins on any match), PLCC-ng emits `NUMBER '123'` (longer match wins)
- Example: with `skip ONETWOTHREE '123'` declared before `token NUMBER '\d+'`, input `123` → both match 3 chars, PLCC-ng emits skip (declaration order breaks tie)

- [ ] **Step 1: Create `docs/migration.md`**

Create the file with this exact content:

```markdown
# Migration from PLCC to PLCC-ng

PLCC-ng is a modern, pip-installable rewrite of [PLCC](https://github.com/ourPLCC/plcc).
It adds Python semantics support, a cleaner CLI, and a more extensible architecture.
It is not backward compatible — spec files and command invocations both require updates.

## Migration checklist

### 1. Install PLCC-ng

Replace the PLCC shell script, Docker, or DevContainer install with:

```bash
pip install plcc-ng
```

See [Installation](installation.md) for upgrade, pinning, and uninstall instructions.

### 2. Rename your grammar file

PLCC's default grammar file is named `grammar`. PLCC-ng's default is `spec.plcc`.

```
grammar  →  spec.plcc
```

### 3. Update regex patterns in the lexical section

PLCC uses Java regex ([`java.util.regex.Pattern`](https://docs.oracle.com/en/java/javase/11/docs/api/java.base/java/util/regex/Pattern.html)).
PLCC-ng uses Python regex ([`re`](https://docs.python.org/3/library/re.html)).

Most common patterns are identical. The following Java-specific syntax must be rewritten:

| Java pattern | Python equivalent |
|---|---|
| `\p{Alpha}` | `[a-zA-Z]` |
| `(?<name>...)` named group | `(?P<name>...)` |
| `\p{Digit}` | `\d` |

Test your patterns with a Python regex tool (e.g. [regex101.com](https://regex101.com/) set to Python flavor).

### 4. Check scan algorithm behavior

PLCC gives skip rules priority over all token rules whenever they match *any* input,
regardless of match length. PLCC-ng uses pure first-longest-match — skip and token rules
compete equally, with ties broken by declaration order.

If any of your skip rules are shorter than competing token rules, the behavior changes:

| Input | PLCC | PLCC-ng |
|---|---|---|
| `123` with `skip ONE '1'` before `token NUMBER '\d+'` | skip wins (nothing emitted) | `NUMBER '123'` (longer match wins) |

**Fix:** If you relied on skip-first behavior, rewrite the skip pattern to match as many characters as the token it was shadowing. For most grammars (whitespace skips vs. identifier/number tokens), the longest match already produces the same result and no change is needed.

### 5. Update nonterminal names to PascalCase

PLCC nonterminals are lowercase; PLCC-ng uses PascalCase.

| PLCC | PLCC-ng |
|---|---|
| `<prog>` | `<Program>` |
| `<exp>` | `<Expr>` |

Update every nonterminal on both the left-hand side and right-hand side of every rule.

### 6. Update alternative/subclass syntax

PLCC places the distinguishing name as a suffix after the closing bracket.
PLCC-ng places it after a colon inside the brackets.

| PLCC | PLCC-ng |
|---|---|
| `<exp>WholeExp ::= ...` | `<Expr:WholeExp> ::= ...` |
| `<exp>SubExp ::= ...` | `<Expr:SubExp> ::= ...` |

### 7. Update captured field syntax

PLCC places a field name as a suffix after the closing bracket.
PLCC-ng places it after a colon inside the brackets.

| PLCC | PLCC-ng |
|---|---|
| `<exp>exp1` (field named `exp1`) | `<Expr:exp1>` |
| `<exp>exp2` (field named `exp2`) | `<Expr:exp2>` |
| `<WHOLE>` (auto-named field `whole`) | `<WHOLE>` (same — auto-naming unchanged) |
| `<WHOLE>` with explicit name | `<WHOLE:whole>` |

### 8. Add semantic section language header

PLCC only supports Java semantics and has no language header.
PLCC-ng requires the first non-blank line of the semantic section to declare the language.

Before (PLCC):
```
%
Prog
%%%
  public void $run() { ... }
%%%
```

After (PLCC-ng):
```
%
Java

Prog
%%%
  public void _run() { ... }
%%%
```

The supported values are `Java` and `Python`.

### 9. Rename the entry point method

The method the start symbol's class uses as its execution entry point was renamed.

| PLCC | PLCC-ng |
|---|---|
| `$run()` | `_run()` |

Update this in the semantic section of your spec file.

### 10. Check `%include` paths

Both PLCC and PLCC-ng support `%include FILENAME`. The syntax is unchanged.
If your include paths were relative to a file named `grammar`, they will work
unchanged — paths are resolved relative to the file that contains the `%include` directive.

### 11. Replace commands

| PLCC | PLCC-ng | Notes |
|---|---|---|
| `plcc.py --version` | `plcc-version` | |
| `plccmk [-c] [file]` | *(not needed)* | Top-level commands generate and compile automatically |
| `scan [file...]` | `plcc-scan [file...]` | Token output format changed (see below) |
| `parse [-t] [-n] [file...]` | `plcc-parse [file...]` | Always shows parse tree; no `-t` flag needed |
| `rep [-t] [-n] [file...]` | `plcc-rep [file...]` | |
| `parse --json_ast` | `plcc-tokens \| plcc-trees` | See below |

**Token output format change:**

PLCC format:
```
   1: WHOLE '3'
```

PLCC-ng format (`file:line:column`):
```
-:1:1 NUM '42'
```

**JSON parse trees:**

PLCC's `--json_ast` flag (passed to `plccmk` and `parse`) is not available in PLCC-ng.
To obtain a JSON parse tree, use the lower-level pipeline:

```bash
plcc-spec spec.plcc | plcc-ll1 > build/ll1.json
plcc-tokens build/spec.json samples/ | plcc-trees --ll1=build/ll1.json
```

See [`plcc-trees`](cli/commands/plcc-trees.md) for details.

## Features not yet in PLCC-ng

- **Docker installation** — PLCC supported Docker via `plcc-con`. PLCC-ng is currently pip-only. Docker support is planned.
- **DevContainer** — PLCC provided a ready-to-use devcontainer image. PLCC-ng does not yet provide one.
```

- [ ] **Step 2: Add nav entry to `mkdocs.yml`**

Find:
```yaml
  - Installation: installation.md
```
Replace with:
```yaml
  - Installation: installation.md
  - Migration from PLCC: migration.md
```

- [ ] **Step 3: Verify the build**

```bash
.venv/bin/mkdocs build --strict
```
Expected: build succeeds with no warnings or errors.

- [ ] **Step 4: Commit**

```bash
git add docs/migration.md mkdocs.yml
git commit -m "docs(migration): add migration guide from PLCC to PLCC-ng [skip ci]"
```
