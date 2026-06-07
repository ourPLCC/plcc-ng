# Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up two MkDocs sites (user docs + developer docs) deployed to GitHub Pages from this repo, with all stub pages in place, CI wired, CHANGELOG.md auto-generated, and README updated — ready for content to be written in follow-on plans.

**Architecture:** Three phases. Phase 1 (this plan) is infrastructure: restructure the repo, configure MkDocs, wire CI, update CHANGELOG generation, slim the README. Phases 2 and 3 are content-writing phases (each gets its own detailed plan when the time comes). Infrastructure is the prerequisite; content phases can overlap once infrastructure is done.

**Tech Stack:** MkDocs, mkdocs-material, mike (versioning), mkdocs-include-markdown-plugin, python-semantic-release, GitHub Actions, GitHub Pages.

---

## Phase 1: Infrastructure

This phase produces a deployable skeleton: both sites build and deploy, all nav pages exist as stubs, CHANGELOG.md is auto-generated, and the README points to the live site.

### File map

**Create:**

- `mkdocs.yml` — user docs site config
- `mkdocs-dev.yml` — developer docs site config
- `docs/index.md` — Home stub
- `docs/getting-started.md` — Getting Started stub
- `docs/language-guide/index.md` — Language Guide overview stub
- `docs/language-guide/tokens.md` — Token rules stub
- `docs/language-guide/grammar.md` — Grammar rules stub
- `docs/language-guide/code-generation.md` — Code generation stub
- `docs/language-guide/examples.md` — Examples stub
- `docs/cli/index.md` — CLI Reference overview stub
- `docs/cli/primitives.md` — Level 0 primitives stub
- `docs/cli/orchestrators.md` — Level 2 orchestrators stub
- `docs/instructor-guide/index.md` — Instructor Guide overview stub
- `docs/instructor-guide/evaluating.md` — Evaluating plcc-ng stub
- `docs/instructor-guide/adopting.md` — Adopting plcc-ng stub
- `docs/changelog.md` — Changelog page (includes CHANGELOG.md via plugin)
- `dev-docs/index.md` — Developer docs home stub
- `dev-docs/contributing.md` — includes CONTRIBUTING.md via plugin
- `dev-docs/code-of-conduct.md` — includes CODE_OF_CONDUCT.md via plugin
- `dev-docs/release-sop.md` — Release SOP stub
- `dev-docs/architecture.md` — Architecture overview stub
- `dev-docs/issue-conventions.md` — Issue conventions stub
- `.github/workflows/docs.yml` — CI for user docs deployment

**Modify:**

- `pyproject.toml` — add MkDocs deps to `[dependency-groups].dev`; add `project.urls.Documentation`; enable `changelog = "true"` in `[tool.semantic_release]`
- `.github/workflows/release.yml` — set `changelog: "true"` in the python-semantic-release step
- `bin/issues/new.bash` — update `ISSUES_DIR` from `docs/issues` to `dev-docs/issues`
- `CLAUDE.md` — update references from `docs/issues/` to `dev-docs/issues/`
- `README.md` — slim to one paragraph + install + docs link

**Move (git mv):**

- `docs/superpowers/specs/` → `dev-docs/specs/`
- `docs/superpowers/plans/` → `dev-docs/plans/`
- `docs/issues/` → `dev-docs/issues/`

---

### Task 1: Restructure the repo

Move internal docs out of `docs/` (which becomes user docs) into `dev-docs/`.

**Files:**

- Move: `docs/superpowers/specs/` → `dev-docs/specs/`
- Move: `docs/superpowers/plans/` → `dev-docs/plans/`
- Move: `docs/issues/` → `dev-docs/issues/`
- Modify: `bin/issues/new.bash`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Move the directories with git mv**

```bash
mkdir -p dev-docs
git mv docs/superpowers/specs dev-docs/specs
git mv docs/superpowers/plans dev-docs/plans
git mv docs/issues dev-docs/issues
rmdir docs/superpowers 2>/dev/null || true
```

- [ ] **Step 2: Update bin/issues/new.bash**

In `bin/issues/new.bash`, change line:

```bash
ISSUES_DIR="docs/issues"
```

to:

```bash
ISSUES_DIR="dev-docs/issues"
```

- [ ] **Step 3: Update CLAUDE.md**

In `CLAUDE.md`, change both occurrences of `docs/issues/` to `dev-docs/issues/`:

```markdown
To add a new issue to [dev-docs/issues/](dev-docs/issues/), always use [bin/issues/new.bash](bin/issues/new.bash):
```

and:

```markdown
This reads [dev-docs/issues/.next-id.txt](dev-docs/issues/.next-id.txt) for the next ID...
```

- [ ] **Step 4: Verify bin/issues/new.bash still works**

```bash
bin/issues/new.bash test-restructure-works docs
```

Expected: creates `dev-docs/issues/NNN-test-restructure-works.md` and prints the path.

Then delete the test issue:

```bash
rm dev-docs/issues/*-test-restructure-works.md
# Decrement .next-id.txt back by 1
echo $(($(cat dev-docs/issues/.next-id.txt) - 1)) > dev-docs/issues/.next-id.txt
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(docs): move internal docs to dev-docs/ [skip ci]"
```

---

### Task 2: Add MkDocs dependencies

**Files:**

- Modify: `pyproject.toml`

- [ ] **Step 1: Add dependencies to pyproject.toml**

In `pyproject.toml`, add to the `[dependency-groups] dev` array:

```toml
"mkdocs>=1.6",
"mkdocs-material>=9.5",
"mike>=2.1",
"mkdocs-include-markdown-plugin>=6.0",
```

- [ ] **Step 2: Install and verify**

```bash
pdm install
pdm run mkdocs --version
pdm run mike --version
```

Expected: version strings printed for both, no errors.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml pdm.lock
git commit -m "build(docs): add mkdocs, material, mike, include-markdown-plugin [skip ci]"
```

---

### Task 3: Configure and build the user docs site

**Files:**

- Create: `mkdocs.yml`
- Create: all `docs/` stub pages listed in the file map

- [ ] **Step 1: Create mkdocs.yml**

```yaml
site_name: plcc-ng
site_url: https://ourplcc.github.io/plcc-ng/
repo_url: https://github.com/ourPLCC/plcc-ng
repo_name: ourPLCC/plcc-ng

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - toc.integrate
    - search.suggest

plugins:
  - search
  - include-markdown

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Language Guide:
    - Overview: language-guide/index.md
    - Token Rules: language-guide/tokens.md
    - Grammar Rules: language-guide/grammar.md
    - Code Generation: language-guide/code-generation.md
    - Examples: language-guide/examples.md
  - CLI Reference:
    - Overview: cli/index.md
    - Primitives: cli/primitives.md
    - Orchestrators: cli/orchestrators.md
  - Instructor Guide:
    - Overview: instructor-guide/index.md
    - Evaluating plcc-ng: instructor-guide/evaluating.md
    - Adopting plcc-ng: instructor-guide/adopting.md
  - Changelog: changelog.md

extra:
  version:
    provider: mike
```

- [ ] **Step 2: Create stub pages**

Create each of the following files with the content shown. Replace `TITLE` with the heading matching the nav label.

`docs/index.md`:
```markdown
# plcc-ng

plcc-ng is a tool for teaching and learning programming language concepts.

- [Getting Started](getting-started.md)
- [Language Guide](language-guide/index.md)
- [CLI Reference](cli/index.md)
- [Instructor Guide](instructor-guide/index.md)
```

`docs/getting-started.md`:
```markdown
# Getting Started

*Content coming soon.*
```

`docs/language-guide/index.md`:
```markdown
# Language Guide

*Content coming soon.*
```

`docs/language-guide/tokens.md`:
```markdown
# Token Rules

*Content coming soon.*
```

`docs/language-guide/grammar.md`:
```markdown
# Grammar Rules

*Content coming soon.*
```

`docs/language-guide/code-generation.md`:
```markdown
# Code Generation

*Content coming soon.*
```

`docs/language-guide/examples.md`:
```markdown
# Examples

*Content coming soon.*
```

`docs/cli/index.md`:
```markdown
# CLI Reference

*Content coming soon.*
```

`docs/cli/primitives.md`:
```markdown
# Level 0 Primitives

*Content coming soon.*
```

`docs/cli/orchestrators.md`:
```markdown
# Level 2 Orchestrators

*Content coming soon.*
```

`docs/instructor-guide/index.md`:
```markdown
# Instructor Guide

*Content coming soon.*
```

`docs/instructor-guide/evaluating.md`:
```markdown
# Evaluating plcc-ng

*Content coming soon.*
```

`docs/instructor-guide/adopting.md`:
```markdown
# Adopting plcc-ng

*Content coming soon.*
```

`docs/changelog.md`:
```markdown
# Changelog

{%
  include-markdown "../CHANGELOG.md"
  start="<!--next-version-placeholder-->"
%}
```

Note: If `CHANGELOG.md` does not yet exist, create a minimal placeholder:

```markdown
# Changelog

No releases yet.
```

- [ ] **Step 3: Build the user docs site**

```bash
pdm run mkdocs build --strict
```

Expected: `site/` directory created, no errors, no warnings.

- [ ] **Step 4: Preview locally**

```bash
pdm run mkdocs serve
```

Open `http://127.0.0.1:8000` in a browser. Verify:

- All nav items are present and clickable
- No broken links in the sidebar
- Search box is visible

Press `Ctrl-C` to stop.

- [ ] **Step 5: Commit**

```bash
git add mkdocs.yml docs/
git commit -m "docs: add mkdocs config and user docs stub pages [skip ci]"
```

---

### Task 4: Configure and build the developer docs site

**Files:**

- Create: `mkdocs-dev.yml`
- Create: all `dev-docs/` stub pages listed in the file map

- [ ] **Step 1: Create mkdocs-dev.yml**

```yaml
site_name: plcc-ng Developer Docs
site_url: https://ourplcc.github.io/plcc-ng/dev-docs/
repo_url: https://github.com/ourPLCC/plcc-ng
repo_name: ourPLCC/plcc-ng
docs_dir: dev-docs
site_dir: site-dev

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - toc.integrate
    - search.suggest

plugins:
  - search
  - include-markdown

nav:
  - Home: index.md
  - Contributing: contributing.md
  - Code of Conduct: code-of-conduct.md
  - Release SOP: release-sop.md
  - Architecture: architecture.md
  - Issue Conventions: issue-conventions.md
  - Design Specs: specs/
  - Implementation Plans: plans/
```

- [ ] **Step 2: Create stub pages**

`dev-docs/index.md`:
```markdown
# plcc-ng Developer Docs

Documentation for contributors and maintainers.

- [Contributing](contributing.md)
- [Release SOP](release-sop.md)
- [Architecture](architecture.md)
- [Issue Conventions](issue-conventions.md)
```

`dev-docs/contributing.md`:
```markdown
# Contributing

{%
  include-markdown "../CONTRIBUTING.md"
%}
```

`dev-docs/code-of-conduct.md`:
```markdown
# Code of Conduct

{%
  include-markdown "../CODE_OF_CONDUCT.md"
%}
```

`dev-docs/release-sop.md`:
```markdown
# Release SOP

*Content coming soon.*
```

`dev-docs/architecture.md`:
```markdown
# Architecture

*Content coming soon.*
```

`dev-docs/issue-conventions.md`:
```markdown
# Issue Conventions

*Content coming soon.*
```

- [ ] **Step 3: Add .pages files so MkDocs-material lists specs/ and plans/ directories**

MkDocs needs an index page to navigate into subdirectories. Create minimal index files:

`dev-docs/specs/index.md`:
```markdown
# Design Specs
```

`dev-docs/plans/index.md`:
```markdown
# Implementation Plans
```

`dev-docs/issues/index.md`:
```markdown
# Issues
```

- [ ] **Step 4: Build the developer docs site**

```bash
pdm run mkdocs build --config-file mkdocs-dev.yml --strict
```

Expected: `site-dev/` directory created, no errors.

- [ ] **Step 5: Preview locally**

```bash
pdm run mkdocs serve -f mkdocs-dev.yml -a 127.0.0.1:8001
```

Open `http://127.0.0.1:8001` in a browser. Verify:

- All nav items are present
- Contributing and Code of Conduct pages render the included file content

Press `Ctrl-C` to stop.

- [ ] **Step 6: Add site-dev/ to .gitignore**

The user docs `site/` directory may already be in `.gitignore`. Add `site-dev/` as well:

```bash
echo "site-dev/" >> .gitignore
```

Verify `site/` is also present in `.gitignore`. If not, add it too.

- [ ] **Step 7: Commit**

```bash
git add mkdocs-dev.yml dev-docs/ .gitignore
git commit -m "docs: add mkdocs-dev config and developer docs stub pages [skip ci]"
```

---

### Task 5: Wire CI for both docs sites

**Files:**

- Create: `.github/workflows/docs.yml`

The user docs are deployed by `mike` (versioned). The dev docs are deployed by `mkdocs gh-deploy` to the `dev-docs/` subdirectory of the `gh-pages` branch.

**Manual prerequisite (do this before pushing the workflow):**

Enable GitHub Pages on this repository:

1. Go to the repo on GitHub → Settings → Pages
2. Set Source to "Deploy from a branch", branch `gh-pages`, folder `/` (root)
3. Save. GitHub will create the `gh-pages` branch on first deploy.

- [ ] **Step 1: Create .github/workflows/docs.yml**

```yaml
name: Docs

on:
  push:
    branches: [main]
  release:
    types: [published]

permissions:
  contents: write

jobs:
  deploy-user-docs:
    name: Deploy user docs
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install PDM
        run: pip install pdm
      - name: Install dependencies
        run: pdm install
      - name: Configure git for mike
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
      - name: Deploy dev docs preview (on push to main)
        if: github.event_name == 'push'
        run: pdm run mike deploy --push dev
      - name: Deploy versioned docs (on release)
        if: github.event_name == 'release'
        run: |
          VERSION="${{ github.ref_name }}"
          # Strip leading 'v' (v1.2.3 → 1.2.3), then take major.minor (1.2)
          MAJOR_MINOR=$(echo "${VERSION#v}" | cut -d. -f1,2)
          pdm run mike deploy --push --update-aliases "${MAJOR_MINOR}" latest

  deploy-dev-docs:
    name: Deploy developer docs
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install PDM
        run: pip install pdm
      - name: Install dependencies
        run: pdm install
      - name: Configure git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
      - name: Deploy developer docs
        run: pdm run mkdocs gh-deploy --config-file mkdocs-dev.yml --dest-dir dev-docs --force
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/docs.yml
git commit -m "ci(docs): add GitHub Actions workflow for user and developer docs [skip ci]"
```

- [ ] **Step 3: Push to main and verify CI runs**

```bash
git push origin 065-design-end-user-documentation
```

Create a PR and merge it to `main`. Watch the Actions tab. Both `deploy-user-docs` and `deploy-dev-docs` jobs should pass. After the first successful run, visit:

- `https://ourplcc.github.io/plcc-ng/dev/` — user docs dev preview
- `https://ourplcc.github.io/plcc-ng/dev-docs/` — developer docs

---

### Task 6: Enable CHANGELOG.md auto-generation

**Files:**

- Modify: `pyproject.toml`
- Modify: `.github/workflows/release.yml`

The release workflow currently runs python-semantic-release with `changelog: "false"`. We need to enable changelog generation and configure its output file.

- [ ] **Step 1: Add semantic_release config to pyproject.toml**

Add a `[tool.semantic_release]` section (or extend it if it exists):

```toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
changelog_file = "CHANGELOG.md"
```

- [ ] **Step 2: Update release.yml to enable changelog**

In `.github/workflows/release.yml`, change the `python-semantic-release` step:

```yaml
      - name: Python Semantic Release
        id: release
        uses: python-semantic-release/python-semantic-release@v9
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          push: "true"
          changelog: "true"
          vcs_release: "false"
```

- [ ] **Step 3: Create an initial CHANGELOG.md**

If `CHANGELOG.md` does not exist at the repo root, create a minimal one:

```markdown
# Changelog

<!--next-version-placeholder-->
```

python-semantic-release will insert release entries above the placeholder marker on each release.

- [ ] **Step 4: Verify the changelog page builds**

```bash
pdm run mkdocs build --strict
```

Expected: no errors. The Changelog page should render (even if it only shows the placeholder text for now).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .github/workflows/release.yml CHANGELOG.md
git commit -m "build(release): enable CHANGELOG.md auto-generation [skip ci]"
```

---

### Task 7: Update README and PyPI metadata

**Files:**

- Modify: `README.md`
- Modify: `pyproject.toml`

- [ ] **Step 1: Slim down README.md**

Replace the body of `README.md` with:

```markdown
# plcc-ng

plcc-ng is a tool for teaching and learning programming language concepts.
It is a reimagining of [PLCC](https://github.com/ourPLCC/plcc).

**[Documentation](https://ourplcc.github.io/plcc-ng/)**

## Install

```bash
pip install plcc-ng
```

> This package has a separate identity from the original `plcc` package.
> `plcc-ng` is experimental — no compatibility guarantees with `plcc` until a stable 1.0 release.

## Licensing

Developers license contributions under [AGPL-3.0-or-later](LICENSES/AGPL-3.0-or-later.txt) and sign off on the
[DCO-1.1](DCO-1.1.txt).

## Community

- [Code of conduct](CODE_OF_CONDUCT.md)
- [Discord server](https://discord.gg/EVtNSxS9E2)
- [Developer docs](https://ourplcc.github.io/plcc-ng/dev-docs/)

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow, test tiers, and TDD inner loop.
```

- [ ] **Step 2: Add Documentation URL to pyproject.toml**

In `pyproject.toml`, find or create the `[project.urls]` table and add:

```toml
[project.urls]
Documentation = "https://ourplcc.github.io/plcc-ng/"
Repository = "https://github.com/ourPLCC/plcc-ng"
```

- [ ] **Step 3: Set the GitHub repo About URL (manual)**

1. Go to the plcc-ng repo on GitHub
2. Click the gear icon next to "About" on the right sidebar
3. Set "Website" to `https://ourplcc.github.io/plcc-ng/`
4. Save

This makes the docs URL visible on the repo's main page without any code change.

- [ ] **Step 4: Commit**

```bash
git add README.md pyproject.toml
git commit -m "docs(readme): slim README and add docs site link [skip ci]"
```

---

## Phase 2: User Docs Content

*This phase gets its own detailed plan when Phase 1 is complete.*

High-level task list for the plan author:

1. **Home page** — Write the full `docs/index.md`: what plcc-ng is, audience navigation paths, badges
2. **Getting Started** — Install instructions, prerequisites, end-to-end quickstart with a trivial `.plcc` file through `plcc-make`
3. **Language Guide: Overview** — Explain the three-section `.plcc` file structure
4. **Language Guide: Token Rules** — `token` and `skip` syntax, regex patterns, examples
5. **Language Guide: Grammar Rules** — BNF syntax, rule-to-class mapping, naming conventions
6. **Language Guide: Code Generation** — Target selection, embedding code, class lifecycle
7. **Language Guide: Examples** — Three worked examples (lexical-only, expression grammar, full language with evaluation)
8. **CLI Reference: Overview** — Pipeline overview diagram/description, when to use primitives vs. orchestrators
9. **CLI Reference: Primitives** — One section per Level 0 command: purpose, stdin/stdout, flags, exit codes, example
10. **CLI Reference: Orchestrators** — One section per Level 2 command: `plcc-make`, `plcc-scan`, `plcc-parse`, `plcc-rep`
11. **Instructor Guide: Evaluating** — What plcc-ng teaches, prerequisites, learning curve
12. **Instructor Guide: Adopting** — Assignment ideas, course structure, teaching materials index

---

## Phase 3: Developer Docs Content

*This phase gets its own detailed plan when Phase 1 is complete. Phase 2 and Phase 3 can proceed in parallel.*

High-level task list for the plan author:

1. **Resolve the CONTRIBUTING.md boundary** — Decide what stays in `CONTRIBUTING.md` (GitHub entry point) vs. what moves to dedicated `dev-docs/` pages; update accordingly
2. **Release SOP** — Document the full release process: what `python-semantic-release` handles automatically, what requires manual steps (GitHub Pages setup, version aliases, backport policy)
3. **Architecture overview** — Summarize the pipeline architecture, Level 0 primitives vs. Level 2 orchestrators, the data model, the test tier structure
4. **Test tier reference** — Detailed explanation of the five test tiers (unit, commands, integration, e2e, packaging), when to use each, and how to run them; drawn from `CONTRIBUTING.md` content where appropriate
5. **Issue conventions** — How issues are numbered, the template fields, `bin/issues/new.bash` usage, the `done/` directory
6. **Dev docs index pages for specs/ and plans/** — Add brief descriptions of what design specs and implementation plans are, and how to navigate them
