# File-Based Issue Tracker — Design

**Date:** 2026-05-06
**Status:** Approved

---

## 1. Goal

Provide a lightweight, file-based mechanism for capturing bugs, improvements, and feature ideas discovered during manual testing of plcc-ng. The tracker must be usable collaboratively between the developer and Claude Code without any external tooling.

---

## 2. Location

Issues live in `docs/issues/`. This directory sits alongside other project documentation, is visible to anyone browsing the repo, and is independent of the superpowers workflow artifacts.

---

## 3. File Naming

```
NNN-short-slug.md
```

- `NNN` — three-digit zero-padded sequential integer (001, 002, …)
- `short-slug` — kebab-case summary of the issue

Example: `001-scan-error-message.md`

Sequential numbers make issues easy to reference in conversation and in links from design docs.

---

## 4. Template

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

**Type** aligns with conventional commit prefixes so there is no translation step when the issue is picked up for implementation.

**Steps to Reproduce** is optional — include it for bugs, omit it for features and refactors.

**Notes** is a freeform scratchpad for early ideas and context.

---

## 5. Lifecycle

- **Open:** file exists in `docs/issues/`
- **Done:** file is deleted

Git history is the record of closed issues. No status field is needed.

---

## 6. Workflow

During a manual testing session:

1. Developer identifies a bug, improvement, or feature idea.
2. Developer describes it to Claude Code.
3. Claude Code drafts the issue file.
4. Developer reviews and approves.
5. Both commit the file.

No external tooling required.
