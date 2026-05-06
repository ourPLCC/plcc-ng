# Issue Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the `docs/issues/` directory with a template file so the file-based issue tracker is ready to use.

**Architecture:** A single `docs/issues/TEMPLATE.md` file serves as the canonical reference for the issue format. New issues are created by copying the template, numbering it, and filling it in. No code changes — this is purely documentation scaffolding.

**Tech Stack:** Markdown, git

---

### Task 1: Create the issues directory and template

**Files:**
- Create: `docs/issues/TEMPLATE.md`

- [ ] **Step 1: Create the template file**

Create `docs/issues/TEMPLATE.md` with this exact content:

```markdown
# NNN - Short descriptive title

**Type:** (conventional commit type: fix, feat, refactor, perf, docs, test, …)
**Date:** YYYY-MM-DD

## Description

What you observed, or what you want changed.

## Steps to Reproduce

(For bugs — omit if not applicable)

1. ...

## Notes

Any ideas, hunches, or related context.
```

- [ ] **Step 2: Verify the file exists**

```bash
ls docs/issues/
```

Expected output:
```
TEMPLATE.md
```

- [ ] **Step 3: Commit**

```bash
git add docs/issues/TEMPLATE.md
git commit -m "docs: scaffold file-based issue tracker"
```
