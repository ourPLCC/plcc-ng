# Documentation Design for plcc-ng

**Date:** 2026-06-07
**Issue:** [065](../../issues/065-design-end-user-documentation.md)

## Overview

plcc-ng needs two separate documentation sites, both built with MkDocs Material
and deployed to GitHub Pages from the same repository:

- **User docs** — for students, language implementors, and instructors
- **Developer docs** — for contributors and maintainers

They are separate sites with separate search indexes so that users never see
internal design documents when searching user-facing documentation, and vice versa.

## Audiences

### User docs audiences

**Students** are the primary readers of the Language Guide and CLI Reference.
They are writing `.plcc` grammar files and using plcc tools to test their language.
They come to the docs to fix bugs, understand spec syntax, and learn how the spec
translates to generated classes. They need accurate reference material and worked examples.

**Instructors (evaluating)** want to know whether plcc-ng is suitable for their course
and their students. They need to understand the installation story, the learning curve,
what prior knowledge students require (programming languages, tools, data structures,
algorithms), and what the tool actually teaches.

**Instructors (adopting)** have decided to use plcc-ng and want to know what they can
teach with it, what materials exist, how hard it will be for students, and how to
structure assignments.

**Language implementors** (students, researchers, or hobbyists building a language)
use the same core user docs as students — Language Guide, CLI Reference, Getting Started.

### Developer docs audiences

**Contributors** need to understand the codebase, the test tiers, the TDD workflow,
issue and PR conventions, and how to write code that fits the project's standards.

**Maintainers** need SOPs for cutting releases, managing the GitHub Pages deployment,
handling issues, and understanding the architectural decisions behind the codebase.

## Repository Layout

```text
docs/                    ← user docs MkDocs source
  index.md
  getting-started.md
  language-guide/
  cli/
  instructor-guide/
dev-docs/                ← developer docs MkDocs source
  index.md
  specs/                 ← moved from docs/superpowers/specs/
  plans/                 ← moved from docs/superpowers/plans/
  issues/                ← moved from docs/issues/
CHANGELOG.md             ← repo root; auto-updated by python-semantic-release
CONTRIBUTING.md          ← repo root; GitHub special file; included into dev-docs site
CODE_OF_CONDUCT.md       ← repo root; GitHub special file; included into dev-docs site
mkdocs.yml               ← user docs site config
mkdocs-dev.yml           ← developer docs site config
```

`CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` stay at the repo root because GitHub
renders them automatically in PR and issue flows. The dev docs site includes them
directly using `mkdocs-include-markdown-plugin` — one source of truth, no duplication.

## User Docs Site Structure

Hosted at `ourplcc.github.io/plcc-ng/` (versioned, `mike`-managed).

### Home (`index.md`)

What plcc-ng is, who it is for, and quick navigation paths for each audience:

- "I'm an instructor evaluating this tool" → Instructor Guide
- "I'm ready to install" → Getting Started
- "I want spec syntax" → Language Guide
- "I need a CLI command reference" → CLI Reference

Includes version badge, license badge, and link to Changelog.

### Getting Started

Prerequisites (Python version; Java if targeting Java output), installation
(`pip install plcc-ng`), a minimal end-to-end quickstart (write a trivial `.plcc`
file, run `plcc-make`, see what gets generated). Goal: a new user is productive in
under 10 minutes.

### Language Guide

The main user documentation. Organized as multiple pages:

- **Overview** — the three sections of a `.plcc` file (tokens, grammar, code generation)
- **Token rules** — `token` and `skip` syntax, regular expression patterns
- **Grammar rules** — BNF syntax, how rules map to generated classes, rule naming conventions
- **Code generation** — target language selection, embedding target-language code, class lifecycle
- **Examples** — worked examples of increasing complexity (lexical-only, simple expression grammar, full language with evaluation)

This is the section students return to most often when debugging.

### CLI Reference

One page per command (or logically grouped). Each page covers:

- Purpose and position in the pipeline
- Stdin/stdout contract
- All flags with descriptions
- Exit codes
- A usage example

Commands are organized into two groups matching the architectural spec:

- **Level 0 primitives** — `plcc-spec`, `plcc-tokens`, `plcc-trees`, `plcc-model`, `plcc-lang-emit`, `plcc-diagram`, etc.
- **Level 2 orchestrators** — `plcc-make`, `plcc-scan`, `plcc-parse`, `plcc-rep`

### Instructor Guide

Two sub-pages:

#### Evaluating plcc-ng

- What concepts the tool teaches (scanning, parsing, tree construction, code generation)
- What prior knowledge students need (programming languages supported, tools, data structures and algorithms assumed)
- How it fits different course levels
- What the student learning curve looks like

#### Adopting plcc-ng

- How to structure assignments around the tool
- What exercises work well at each stage of a course
- Index of existing teaching materials (slides, sample grammars, problem sets) if any exist

### Changelog

`CHANGELOG.md` from the repo root, included directly as a page. Organized by version,
showing what changed in each release. This is the compact, searchable format preferred
over individual GitHub Release entries for browsing history.

## Developer Docs Site Structure

Hosted at `ourplcc.github.io/plcc-ng/dev-docs/` (latest only, no versioning).

Content includes:

- **Contributing guide** — `CONTRIBUTING.md` included directly; covers the PR process, DCO sign-off, and test tiers
- **Code of conduct** — `CODE_OF_CONDUCT.md` included directly
- **Release SOP** — how to cut a release, what `python-semantic-release` handles automatically, what requires manual steps
- **Architecture and design specs** — the `specs/` directory (moved from `docs/superpowers/specs/`)
- **Implementation plans** — the `plans/` directory (moved from `docs/superpowers/plans/`)
- **Issue conventions** — how issues are numbered, the template, `bin/issues/new.bash`
- **Test tier reference** — detailed explanation of test tiers (drawn from `CONTRIBUTING.md`)

### Boundary between CONTRIBUTING.md and dev-docs pages

`CONTRIBUTING.md` should remain focused on what GitHub needs it to be: the minimal
entry point that appears in the PR/issue flow. Deep reference material (architecture,
full SOP detail, historical design context) belongs in dedicated dev-docs pages.
This boundary must be resolved carefully when writing the content — it is not defined
here. The principle is: if a contributor needs it before opening their first PR,
it belongs in `CONTRIBUTING.md`; if they need it while doing deeper work, it belongs
in `dev-docs/`.

## Versioning Strategy

User docs are versioned at the **major.minor** level using `mike`:

- Patch releases (`1.2.1`, `1.2.2`) update the `/1.2/` docs in place. Patch releases
  contain only bug fixes — no new features, no spec syntax changes — so in-place
  updates are accurate.
- Minor releases (`1.3.0`) deploy a new `/1.3/` version and update the `latest` alias.
- Major releases (`2.0.0`) deploy a new `/2.0/` version and update the `latest` alias.
  Subsequent minor releases within that major (e.g., `2.1.0`) deploy `/2.1/`.

Old versions remain accessible indefinitely. The policy for backporting doc fixes to
old versions is **frozen at release** — once a version is deployed, its docs are not
retroactively patched. Instructors pinning to a version get docs that accurately
reflect what shipped, even if a later correction was made.

Developer docs are **latest only** — no versioning, no `mike`, just a plain
`mkdocs gh-deploy` to `gh-pages/dev-docs/` on every push to `main`.

## Build and Release Pipeline

Two CI jobs for the user docs site:

- **On push to `main`:** `mike deploy --push dev` — deploys a `dev` preview at `/dev/`
- **On release tag (e.g., `v1.2.0`):** `mike deploy --push --update-aliases 1.2 latest`

One CI job for the developer docs site:

- **On push to `main`:** `mkdocs gh-deploy --config-file mkdocs-dev.yml --remote-name origin`
  targeting the `gh-pages` branch under the `dev-docs/` prefix

`python-semantic-release` updates `CHANGELOG.md` automatically as part of the release
process, so the Changelog page in the user docs site stays current without manual effort.

Contributors preview locally:

- User docs: `mkdocs serve`
- Developer docs: `mkdocs serve -f mkdocs-dev.yml`

## Relationship to Existing Documents

| Document | After this change |
| --- | --- |
| `README.md` | Slimmed to one paragraph + install snippet + prominent link to the docs site. Duplicate content removed. |
| `CONTRIBUTING.md` | Stays at repo root. Included into dev-docs site. Content boundary with dev-docs pages to be resolved when writing. |
| `CODE_OF_CONDUCT.md` | Stays at repo root. Included into dev-docs site. |
| `docs/superpowers/specs/` | Moved to `dev-docs/specs/` |
| `docs/superpowers/plans/` | Moved to `dev-docs/plans/` |
| `docs/issues/` | Moved to `dev-docs/issues/` |

## Discovery

Users find the user docs through three channels:

1. **README** — prominent link in the opening paragraph and a dedicated "Documentation" section
2. **PyPI** — `project.urls` in `pyproject.toml` gets a `Documentation` key pointing to the site; PyPI renders this as a sidebar link on the package page
3. **GitHub repo About** — the repo's "About" description includes the docs URL

Contributors find the developer docs through the README (a secondary link) and through
`CONTRIBUTING.md` (which links to the dev docs site for deeper reference).

## Tooling Summary

| Tool | Purpose |
| --- | --- |
| `mkdocs` | Static site generator for both sites |
| `mkdocs-material` | Theme (both sites) |
| `mike` | Version management for user docs site |
| `mkdocs-include-markdown-plugin` | Include `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` into dev-docs |
| `python-semantic-release` | Auto-update `CHANGELOG.md` on release |

All added to the `dev` dependency group in `pyproject.toml`.
