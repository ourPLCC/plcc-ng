# What's New Page (Issue 141) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the user-facing `docs/whats-new.md` page with its v1.0.0 first entry, and move the changelog page from the user docs site to the dev-docs site.

**Architecture:** Docs-only change across two mkdocs sites. The user site (`mkdocs.yml`, `docs/`) gains What's New and loses Changelog; the dev site (`mkdocs-dev.yml`, `dev-docs/`) gains Changelog. Issue 112 gets a release-day checklist line; issue 141 closes as the final commit.

**Tech Stack:** mkdocs (material theme), include-markdown plugin, `bin/issues/` scripts.

**Spec:** `dev-docs/specs/2026-07-06-141-whats-new-page-design.md`

## Global Constraints

- Run everything from the worktree root (`git rev-parse --show-toplevel`); never `cd` elsewhere.
- Commit messages use the `docs(...)` conventional-commit type. Never add `[skip ci]` — CI already ignores docs paths via `paths-ignore`.
- Verification after every content task: `pdm run mkdocs build` (user site) and `pdm run mkdocs build --config-file mkdocs-dev.yml` (dev site) must exit 0 with no NEW warnings relative to a pre-change baseline build.
- The entry text in Task 1 is the human-review deliverable of this issue — implement it verbatim; wording changes belong to the human reviewer, not the implementer.
- The `2026-07-XX` date placeholder and the `v1.0.0` version stamps are intentional (finalized at release time by issue 112). Do not "fix" them.

---

### Task 1: Create `docs/whats-new.md` and add it to the user-site nav

**Files:**
- Create: `docs/whats-new.md`
- Modify: `mkdocs.yml` (nav section, directly after `- Home: index.md`)

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `docs/whats-new.md` present in nav; Task 2 edits the same `mkdocs.yml` nav list (different line) and Task 4's `close.bash` run assumes this file is committed.

- [ ] **Step 1: Record the baseline build output**

```bash
pdm run mkdocs build 2>&1 | tee /tmp/claude-1000/-workspaces-plcc-ng/d3c69c12-bebe-4f31-b6e0-5f29eeb00248/scratchpad/build-user-baseline.txt
```

Expected: exit 0. Note any pre-existing warnings; they are the baseline, not regressions.

- [ ] **Step 2: Create `docs/whats-new.md` with exactly this content**

```markdown
# What's New

Curated highlights of what's changed in PLCC-ng and why it matters
to you. For the full commit-level history, see
[GitHub Releases](https://github.com/ourPLCC/plcc-ng/releases).

<!-- last-covered: v1.0.0 -->

## 2026-07-XX — PLCC-ng v1.0.0

PLCC-ng reaches 1.0: the next generation of
[PLCC](https://github.com/ourPLCC/plcc) is ready for classroom use.
If you're coming from PLCC, here's a tour of what's changed and why
it matters. Migrating a course? Start with the
[migration guide](migration.md).

### Write semantics in four languages

PLCC generated Java, and only Java. PLCC-ng generates scanners,
parsers, and interpreters in Python, Java, Haskell, or JavaScript —
pick the language your course teaches and write your semantics in
it. Start with the [Language Guide](language-guide/index.md), then
see the per-language pages for
[Python](language-guide/languages/python.md),
[Java](language-guide/languages/java.md),
[Haskell](language-guide/languages/haskell.md), and
[JavaScript](language-guide/languages/javascript.md).

### Simpler native installation

Installing PLCC-ng natively is now a single `pip install plcc-ng` —
no shell-script installer to fetch and configure. See
[Installation](installation.md) for upgrade, pinning, and uninstall
instructions.

### Three commands to run your language

Day-to-day work needs just three commands, with no separate compile
step: [`plcc-scan`](cli/commands/plcc-scan.md) tokenizes input,
[`plcc-parse`](cli/commands/plcc-parse.md) shows the parse tree, and
[`plcc-rep`](cli/commands/plcc-rep.md) runs your full language in a
read-eval-print loop. Each one orchestrates smaller composable
commands underneath — emitting generated code, building it, feeding
it input — that you can run directly to explore each stage of the
pipeline and how the pieces fit together. See
[Author-facing commands](cli/guide/author-commands.md) and
[Under the hood](cli/guide/under-the-hood.md).

### Diagrams from your spec

The `plcc-diagram` add-on package draws diagrams straight from your
spec file: class diagrams of the object model your semantics program
against, and syntax (EBNF) diagrams of your grammar. See
[plcc-diagram](cli/commands/plcc-diagram.md) and
[plcc-diagram-syntax](cli/commands/plcc-diagram-syntax.md).

### Built to extend

The pipeline is open: language extensions add new target languages,
parser extensions add new parsing algorithms, and diagram extensions
add new visualizations — all discovered and dispatched through the
same CLI conventions. See the
[language](cli/guide/language-extensions.md),
[parser](cli/guide/parser-extensions.md), and
[diagram](cli/guide/diagram-extensions.md) extension guides.

### A real documentation site

You're reading it. The [Language Guide](language-guide/index.md)
covers every section of a spec file with worked examples, and the
[CLI reference](cli/index.md) documents every command and flag.

### Spec syntax has changed

PLCC-ng is not backwards compatible with PLCC: spec files need
updating. Regular expressions switch from Java to Python flavor,
nonterminals become PascalCase, subclass and captured-field syntax
change, and more. The [migration guide](migration.md) walks through
every change step by step, and its
[features not yet in PLCC-ng](migration.md#features-not-yet-in-plcc-ng)
section lists what hasn't made the jump, so you know both sides of
the trade before switching.
```

- [ ] **Step 3: Add the nav entry in `mkdocs.yml`**

In the `nav:` section, change:

```yaml
nav:
  - Home: index.md
  - Quick Start: quick-start.md
```

to:

```yaml
nav:
  - Home: index.md
  - What's New: whats-new.md
  - Quick Start: quick-start.md
```

- [ ] **Step 4: Build the user site and compare against baseline**

```bash
pdm run mkdocs build 2>&1 | tee /tmp/claude-1000/-workspaces-plcc-ng/d3c69c12-bebe-4f31-b6e0-5f29eeb00248/scratchpad/build-user-task1.txt
diff /tmp/claude-1000/-workspaces-plcc-ng/d3c69c12-bebe-4f31-b6e0-5f29eeb00248/scratchpad/build-user-baseline.txt /tmp/claude-1000/-workspaces-plcc-ng/d3c69c12-bebe-4f31-b6e0-5f29eeb00248/scratchpad/build-user-task1.txt
```

Expected: exit 0; diff shows no new warnings (timing lines may differ). In particular, no "contains a link ... but the target is not found" warnings for `whats-new.md`'s links, and no "pages exist in the docs directory but are not included in the nav" warning naming `whats-new.md`.

- [ ] **Step 5: Verify the rendered page landed in the site output**

```bash
test -f site/whats-new/index.html && grep -c "last-covered" docs/whats-new.md
```

Expected: `1` (the marker is present exactly once; `site/whats-new/index.html` exists).

- [ ] **Step 6: Commit**

```bash
git add docs/whats-new.md mkdocs.yml
git commit -m "docs: add What's New page with v1.0.0 first entry

First entry is a highlights tour of PLCC-ng relative to PLCC, per the
issue-141 design spec. Date placeholder and version stamps are
finalized at release time (issue 112).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Move the changelog page to the dev-docs site

**Files:**
- Delete: `docs/changelog.md`
- Modify: `mkdocs.yml` (remove `  - Changelog: changelog.md` from nav)
- Create: `dev-docs/changelog.md`
- Modify: `mkdocs-dev.yml` (nav: add Changelog after Home)

**Interfaces:**
- Consumes: Task 1's committed `mkdocs.yml` (this task removes a different nav line).
- Produces: changelog on the dev site only; nothing later depends on details beyond the files existing.

- [ ] **Step 1: Record the dev-site baseline build**

```bash
pdm run mkdocs build --config-file mkdocs-dev.yml 2>&1 | tee /tmp/claude-1000/-workspaces-plcc-ng/d3c69c12-bebe-4f31-b6e0-5f29eeb00248/scratchpad/build-dev-baseline.txt
```

Expected: exit 0.

- [ ] **Step 2: Remove the user-site changelog page and nav entry**

```bash
git rm docs/changelog.md
```

Then in `mkdocs.yml`, delete the line (near the end of `nav:`):

```yaml
  - Changelog: changelog.md
```

- [ ] **Step 3: Create `dev-docs/changelog.md` with exactly this content**

The dev config's include-markdown plugin uses `{!`/`!}` tags (see the `plugins:` block of `mkdocs-dev.yml`), not the user site's `{% %}` tags:

```markdown
<!-- markdownlint-disable-file MD041 -->
{!
  include-markdown "../CHANGELOG.md"
!}
```

- [ ] **Step 4: Add the dev-site nav entry**

In `mkdocs-dev.yml`, change:

```yaml
nav:
  - Home: index.md
  - Contributing: contributing.md
```

to:

```yaml
nav:
  - Home: index.md
  - Changelog: changelog.md
  - Contributing: contributing.md
```

- [ ] **Step 5: Build both sites and verify the move**

```bash
pdm run mkdocs build 2>&1 | tail -5
pdm run mkdocs build --config-file mkdocs-dev.yml 2>&1 | tee /tmp/claude-1000/-workspaces-plcc-ng/d3c69c12-bebe-4f31-b6e0-5f29eeb00248/scratchpad/build-dev-task2.txt
diff /tmp/claude-1000/-workspaces-plcc-ng/d3c69c12-bebe-4f31-b6e0-5f29eeb00248/scratchpad/build-dev-baseline.txt /tmp/claude-1000/-workspaces-plcc-ng/d3c69c12-bebe-4f31-b6e0-5f29eeb00248/scratchpad/build-dev-task2.txt
```

Expected: both builds exit 0, no new warnings. Then confirm content actually moved — the dev page renders real changelog text (not a literal `include-markdown` tag), and the user site no longer has the page:

```bash
grep -q "changelog" site-dev/changelog/index.html && ! grep -q "include-markdown" site-dev/changelog/index.html && echo DEV-OK
test ! -e site/changelog && echo USER-REMOVED
```

Expected: `DEV-OK` and `USER-REMOVED`.

- [ ] **Step 6: Commit**

```bash
git add mkdocs.yml mkdocs-dev.yml dev-docs/changelog.md
git commit -m "docs: move changelog page from user site to dev-docs site

What's New replaces it as the user-facing release narrative
(issue-141 design; agreed in the issue-136 spec, Part 2).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

(`git rm` already staged the deletion.)

---

### Task 3: Add the release-day checklist line to issue 112

**Files:**
- Modify: `dev-docs/issues/112-first-major-release.md` (Notes section)

**Interfaces:**
- Consumes: nothing.
- Produces: the hand-off contract that lets issue 112 finalize the entry's date/version at release time.

- [ ] **Step 1: Append this bullet to the `## Notes` list in `dev-docs/issues/112-first-major-release.md`**

```markdown
- Release-day step (from issue 141): in `docs/whats-new.md`, replace the first entry's `2026-07-XX` date placeholder with the release date, and confirm the entry heading and the `<!-- last-covered: ... -->` marker match the actual v1.0.0 version.
```

- [ ] **Step 2: Commit**

```bash
git add dev-docs/issues/112-first-major-release.md
git commit -m "docs(issues): add What's New release-day step to issue 112

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Close issue 141

**Files:**
- Moves: `dev-docs/issues/141-whats-new-user-release-notes.md` → `dev-docs/issues/done/` (via script)
- Modify: `dev-docs/roadmap.md` (via script)

**Interfaces:**
- Consumes: all prior tasks committed (this must be the branch's final commit).
- Produces: closed issue, clean roadmap.

- [ ] **Step 1: Run the close script**

```bash
bin/issues/close.bash 141
```

Expected: moves the issue file to `done/`, removes its Open Issues roadmap entry, and stages the changes (the script stages; you review and commit).

- [ ] **Step 2: Verify consistency and review what was staged**

```bash
bin/issues/check.bash
git diff --cached
```

Expected: check passes; staged diff shows only the file move and the roadmap entry removal (issue 141's entry gone from Open Issues; nothing else touched).

- [ ] **Step 3: Commit**

```bash
git commit -m "docs(issues): close issue 141 (What's New page)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
