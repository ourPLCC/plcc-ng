# Acknowledgments Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a standalone acknowledgments page to the plcc-ng MkDocs site crediting contributors, institutions/funding, and open-source dependencies.

**Architecture:** Create one new markdown file (`docs/acknowledgments.md`) with three placeholder sections, then register it in the site nav (`mkdocs.yml`). No code, no tests — this is a pure docs change.

**Tech Stack:** MkDocs Material, Markdown

## Global Constraints

- Docs commits must end with `[skip ci]` in the subject line.
- Work in the `.worktrees/issue-101` worktree; all commits go to the `issue-101` branch.
- Follow the existing flat-prose style of the docs (no Material-specific HTML or admonition blocks).

---

### Task 1: Create the acknowledgments page

**Files:**
- Create: `docs/acknowledgments.md`
- Modify: `mkdocs.yml`

**Interfaces:**
- Produces: `docs/acknowledgments.md` — a page with three `##` sections: Contributors, Institutions & Funding, Open-Source Dependencies.

- [ ] **Step 1: Create `docs/acknowledgments.md`**

Full file content:

```markdown
# Acknowledgments

## Contributors

<!-- TODO: List named maintainers here before merging. -->

For a full list of contributors, see the
[GitHub contributors page](https://github.com/ourPLCC/plcc-ng/graphs/contributors).

## Institutions & Funding

<!-- TODO: Fill in institutions and funding sources before merging. -->

## Open-Source Dependencies

<!-- TODO: List notable open-source dependencies before merging. -->
```

- [ ] **Step 2: Add nav entry to `mkdocs.yml`**

Find the existing `Changelog` nav entry:

```yaml
  - Changelog: changelog.md
```

Add the acknowledgments entry immediately after it:

```yaml
  - Changelog: changelog.md
  - Acknowledgments: acknowledgments.md
```

- [ ] **Step 3: Verify the site builds without errors**

```bash
cd .worktrees/issue-101
.venv/bin/mkdocs build --strict 2>&1 | tail -20
```

Expected: build completes with no warnings or errors. The `site/` directory will contain `acknowledgments/index.html`.

- [ ] **Step 4: Commit**

```bash
cd .worktrees/issue-101
git add docs/acknowledgments.md mkdocs.yml
git commit -m "docs(acknowledgments): add acknowledgments page placeholder [skip ci]"
```
