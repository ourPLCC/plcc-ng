# Issue 126: plcc-diagram-syntax Command Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add user-facing command reference pages for `plcc-diagram-syntax` and `plcc-diagram-syntax-plantuml-emit`, fix the missing nav entries for `plcc-diagram-class` and `plcc-diagram-class-plantuml-emit`, and document the syntax diagram type in the Diagram extensions guide.

**Architecture:** Pure documentation — no code changes. Three files are modified (`mkdocs.yml`, `diagram-extensions.md`) and two new Markdown pages are created, all following the patterns established by the `plcc-diagram-class` family.

**Tech Stack:** MkDocs (YAML nav), Markdown.

## Global Constraints

- All command pages live under `docs/cli/commands/`.
- Nav entries in `mkdocs.yml` are in alphabetical order within the "All Commands" section.
- Command page structure must follow the existing `plcc-diagram-class.md` pattern exactly (description, "Requires" note, Usage, Arguments and Options table, Examples, Diagram formats section).
- Emitter page structure must follow `plcc-diagram-class-plantuml-emit.md` exactly.
- No code changes. No new tests. No changes to `pyproject.toml`.
- Commit subject lines must include `[skip ci]` (docs-only changes).

---

### Task 1: Create command reference pages for `plcc-diagram-syntax` and `plcc-diagram-syntax-plantuml-emit`

**Files:**
- Create: `docs/cli/commands/plcc-diagram-syntax.md`
- Create: `docs/cli/commands/plcc-diagram-syntax-plantuml-emit.md`
- Reference (read, do not modify): `docs/cli/commands/plcc-diagram-class.md`
- Reference (read, do not modify): `docs/cli/commands/plcc-diagram-class-plantuml-emit.md`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: two Markdown files that Tasks 2 and 3 can reference by path

- [ ] **Step 1: Create `docs/cli/commands/plcc-diagram-syntax.md`**

Write this exact content:

```markdown
# plcc-diagram-syntax

Generate and display a syntax grammar (EBNF) diagram from a PLCC spec file. Shows the
grammar rules derived from the syntactic section of the spec.

Requires the `plcc-diagram` package.

## Usage

```text
plcc-diagram-syntax [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-s PATH`, `--spec=PATH` | Spec file. Remembered across invocations. Defaults to `spec.plcc`. |
| `--format=FMT` | Diagram format plugin to use. Default: `plantuml`. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-diagram-syntax -s subtract.plcc
```

## Diagram formats

`plcc-diagram-syntax` dispatches to diagram extension plugins via `--format`.
Use [`plcc-diagram-list`](plcc-diagram-list.md) to see installed formats.
See [Diagram extensions](../../docs/cli/guide/diagram-extensions.md) for details.
```

- [ ] **Step 2: Create `docs/cli/commands/plcc-diagram-syntax-plantuml-emit.md`**

Write this exact content:

```markdown
# plcc-diagram-syntax-plantuml-emit

Emit a PlantUML EBNF diagram from spec JSON. Reads spec JSON from stdin
and writes PlantUML source to stdout.

Called by [`plcc-diagram-emit --type=syntax --format=plantuml`](plcc-diagram-emit.md).

## Usage

```text
plcc-diagram-syntax-plantuml-emit [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-diagram-syntax-plantuml-emit > diagram.puml
```
```

- [ ] **Step 3: Verify both files look right**

Run:
```bash
cat docs/cli/commands/plcc-diagram-syntax.md
cat docs/cli/commands/plcc-diagram-syntax-plantuml-emit.md
```

Expected: content matches Step 1 and Step 2 exactly. No stray characters or missing sections.

- [ ] **Step 4: Commit**

```bash
git add docs/cli/commands/plcc-diagram-syntax.md \
        docs/cli/commands/plcc-diagram-syntax-plantuml-emit.md
git commit -m "docs(cli): add command pages for plcc-diagram-syntax and emitter (issue 126) [skip ci]"
```

---

### Task 2: Fix `mkdocs.yml` nav — add four missing entries

**Files:**
- Modify: `mkdocs.yml` (lines 60–64, "All Commands" section)

**Interfaces:**
- Consumes: `docs/cli/commands/plcc-diagram-syntax.md` and `plcc-diagram-syntax-plantuml-emit.md` from Task 1 (must exist before nav can reference them)
- Produces: working nav that includes all four `plcc-diagram-class*` and `plcc-diagram-syntax*` entries

- [ ] **Step 1: Locate the insertion points in `mkdocs.yml`**

Run:
```bash
grep -n 'plcc-diagram' mkdocs.yml
```

Expected output (current state — no class or syntax entries):
```
60:      - plcc-diagram: cli/commands/plcc-diagram.md
61:      - plcc-diagram-build: cli/commands/plcc-diagram-build.md
62:      - plcc-diagram-emit: cli/commands/plcc-diagram-emit.md
63:      - plcc-diagram-list: cli/commands/plcc-diagram-list.md
64:      - plcc-diagram-run: cli/commands/plcc-diagram-run.md
```

- [ ] **Step 2: Insert the four missing entries**

Replace the current five-line block:

```yaml
      - plcc-diagram: cli/commands/plcc-diagram.md
      - plcc-diagram-build: cli/commands/plcc-diagram-build.md
      - plcc-diagram-emit: cli/commands/plcc-diagram-emit.md
      - plcc-diagram-list: cli/commands/plcc-diagram-list.md
      - plcc-diagram-run: cli/commands/plcc-diagram-run.md
```

With this nine-line block (alphabetical order preserved):

```yaml
      - plcc-diagram: cli/commands/plcc-diagram.md
      - plcc-diagram-build: cli/commands/plcc-diagram-build.md
      - plcc-diagram-class: cli/commands/plcc-diagram-class.md
      - plcc-diagram-class-plantuml-emit: cli/commands/plcc-diagram-class-plantuml-emit.md
      - plcc-diagram-emit: cli/commands/plcc-diagram-emit.md
      - plcc-diagram-list: cli/commands/plcc-diagram-list.md
      - plcc-diagram-run: cli/commands/plcc-diagram-run.md
      - plcc-diagram-syntax: cli/commands/plcc-diagram-syntax.md
      - plcc-diagram-syntax-plantuml-emit: cli/commands/plcc-diagram-syntax-plantuml-emit.md
```

- [ ] **Step 3: Verify the nav change**

Run:
```bash
grep -n 'plcc-diagram' mkdocs.yml
```

Expected (nine lines, in alphabetical order, no duplicates):
```
60:      - plcc-diagram: cli/commands/plcc-diagram.md
61:      - plcc-diagram-build: cli/commands/plcc-diagram-build.md
62:      - plcc-diagram-class: cli/commands/plcc-diagram-class.md
63:      - plcc-diagram-class-plantuml-emit: cli/commands/plcc-diagram-class-plantuml-emit.md
64:      - plcc-diagram-emit: cli/commands/plcc-diagram-emit.md
65:      - plcc-diagram-list: cli/commands/plcc-diagram-list.md
66:      - plcc-diagram-run: cli/commands/plcc-diagram-run.md
67:      - plcc-diagram-syntax: cli/commands/plcc-diagram-syntax.md
68:      - plcc-diagram-syntax-plantuml-emit: cli/commands/plcc-diagram-syntax-plantuml-emit.md
```

- [ ] **Step 4: Commit**

```bash
git add mkdocs.yml
git commit -m "docs(nav): add plcc-diagram-class and plcc-diagram-syntax entries to mkdocs.yml (issue 126) [skip ci]"
```

---

### Task 3: Document the syntax diagram type in `diagram-extensions.md`

**Files:**
- Modify: `docs/cli/guide/diagram-extensions.md`

**Interfaces:**
- Consumes: `docs/cli/commands/plcc-diagram-syntax-plantuml-emit.md` from Task 1 (linked from the new section)
- Produces: guide page that documents both class and syntax diagram types

- [ ] **Step 1: Read the current end of `diagram-extensions.md`**

Run:
```bash
cat docs/cli/guide/diagram-extensions.md
```

Expected: file ends after the `plcc-diagram-plantuml-run` row in the `## plcc-plantuml-diagram` table.

- [ ] **Step 2: Append the syntax diagram section**

Add the following content at the end of `docs/cli/guide/diagram-extensions.md`:

```markdown

## plcc-syntax-diagram

Generates a PlantUML EBNF diagram showing the syntactic grammar rules from a
PLCC spec file. Rendering is done via the public `plantuml.com` API — no local
PlantUML installation required.

| Command | What it does |
| --- | --- |
| [`plcc-diagram-syntax-plantuml-emit`](../../docs/cli/commands/plcc-diagram-syntax-plantuml-emit.md) | Reads spec JSON from stdin; writes a `.puml` PlantUML EBNF source file |
| `plcc-diagram-plantuml-build` | Sends `.puml` to plantuml.com and writes the returned PNG |
| `plcc-diagram-plantuml-run` | Prints the path to the rendered PNG |
```

- [ ] **Step 3: Verify the appended section**

Run:
```bash
cat docs/cli/guide/diagram-extensions.md
```

Expected: file now has two `##` sections — `## plcc-plantuml-diagram` (unchanged) followed by `## plcc-syntax-diagram` (new). Each section has a description paragraph and a three-row table.

- [ ] **Step 4: Commit**

```bash
git add docs/cli/guide/diagram-extensions.md
git commit -m "docs(guide): document plcc-syntax-diagram type in diagram-extensions (issue 126) [skip ci]"
```
