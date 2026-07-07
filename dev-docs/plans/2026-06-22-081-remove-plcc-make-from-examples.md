# Remove plcc-make from Examples Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the explicit `plcc-make` Build step from `docs/language-guide/examples.md` so the example reflects the correct user workflow.

**Architecture:** Delete lines 59–65 of `docs/language-guide/examples.md` (the `### Build` heading, the `plcc-make -s subtract.plcc` code block, and the "Exits silently on success." line). No other files change.

**Tech Stack:** Markdown only.

## Global Constraints

- Docs commits must include `[skip ci]` in the commit subject.
- Do not touch `docs/cli/guide/under-the-hood.md`, `docs/cli/guide/language-extensions.md`, or `docs/cli/commands/plcc-make.md`.

---

### Task 1: Remove the Build section from examples.md

**Files:**
- Modify: `docs/language-guide/examples.md:59-65`

**Interfaces:**
- Produces: `examples.md` with no `### Build` section; the `### Scanner` heading follows directly after the grammar file code block.

- [ ] **Step 1: Delete the Build section**

In `docs/language-guide/examples.md`, remove these exact lines (59–65):

```
### Build

```bash
plcc-make -s subtract.plcc
```

Exits silently on success.

```

After the edit, line 58 (```` ``` ````) is followed immediately by a blank line and then `### Scanner`.

- [ ] **Step 2: Verify the file looks correct**

Run:

```bash
grep -n "plcc-make\|### Build\|### Scanner\|### Parser\|### Interpreter" docs/language-guide/examples.md
```

Expected output (no `plcc-make` or `### Build` lines):

```
67:### Scanner
90:### Parser
117:### Interpreter
```

(Line numbers may shift slightly — the key is no `plcc-make` or `### Build` entries.)

- [ ] **Step 3: Commit**

```bash
git add docs/language-guide/examples.md
git commit -m "docs(examples): remove explicit plcc-make build step [skip ci]"
```
