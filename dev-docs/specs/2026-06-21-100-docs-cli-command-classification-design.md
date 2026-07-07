# CLI Documentation Restructure Design

**Issue:** 100 — Reconsider how CLI commands are classified and presented in the docs
**Date:** 2026-06-21

## Problem

The current CLI docs group commands as "Level 2 orchestrators" and "Level 0 primitives." These labels reflect internal pipeline architecture, not how a language author experiences the tool. The result is that students have no signal about which commands matter to them, and the docs mix architectural explanation with command reference in a way that serves neither purpose well.

Additionally, many commands shipped in `pyproject.toml` are entirely undocumented.

## Goals

1. Replace the internal classification with one grounded in the author's actual experience
2. Separate guide content (orientation, architecture, how things relate) from reference content (flags, arguments, examples)
3. Document all 33 commands, including those currently absent from the docs
4. Make the package structure (core vs. optional packages vs. extensions) visible to readers

## Command Inventory

All commands registered in `pyproject.toml`, grouped by package:

### core (always installed)

**Author-facing:**
- `plcc-scan` — tokenize source input, print tokens in human-readable format
- `plcc-parse` — parse source input, print parse tree in human-readable format
- `plcc-rep` — REPL: read, eval, print loop for a PLCC spec
- `plcc-version` — print the installed plcc-ng version
- `plcc-lang-list` — list installed language plugins
- `plcc-parser-list` — list installed parser plugins

**Pipeline internals:**
- `plcc-make` — build orchestrator; runs the full pipeline up to a specified stage
- `plcc-spec` — parse, validate, and emit a `.plcc` spec file as JSON
- `plcc-ll1` — perform LL(1) analysis on spec JSON; emit LL(1) analysis JSON
- `plcc-tokens` — tokenize source files given spec JSON; emit token JSONL
- `plcc-trees` — dispatch to a parser plugin; reads token JSONL, emits parse tree
- `plcc-model` — transform spec JSON into a language-neutral code model
- `plcc-lang-emit` — dispatch to the appropriate `plcc-<lang>-emit` plugin
- `plcc-lang-build` — dispatch to the appropriate `plcc-<lang>-build` plugin
- `plcc-lang-run` — dispatch to the appropriate `plcc-<lang>-run` plugin

### plcc-diagram (optional package)

**Author-facing:**
- `plcc-diagram` — generate and display a class diagram from a PLCC spec
- `plcc-diagram-list` — list installed diagram plugins

**Pipeline internals:**
- `plcc-diagram-emit` — dispatch to the appropriate `plcc-<fmt>-diagram-emit` plugin
- `plcc-diagram-build` — dispatch to the appropriate `plcc-<fmt>-diagram-build` plugin
- `plcc-diagram-run` — dispatch to the appropriate `plcc-<fmt>-diagram-run` plugin

### parser-extensions

- `plcc-parser-table` — LL(1) table-driven parser plugin (called by `plcc-trees`)

### language-extensions

**plcc-java:**
- `plcc-java-emit` — emit Java source from model JSON
- `plcc-java-build` — compile emitted Java source
- `plcc-java-run` — run the compiled Java interpreter

**plcc-python:**
- `plcc-python-emit` — emit Python source from model JSON
- `plcc-python-build` — build step for Python (no-op or minimal)
- `plcc-python-run` — run the Python interpreter

### diagram-extensions

**plcc-mermaid-diagram:**
- `plcc-mermaid-diagram-emit` — emit Mermaid class diagram source from model JSON
- `plcc-mermaid-diagram-build` — render Mermaid source to PNG
- `plcc-mermaid-diagram-run` — display the rendered PNG

**plcc-plantuml-diagram:**
- `plcc-plantuml-diagram-emit` — emit PlantUML class diagram source from model JSON
- `plcc-plantuml-diagram-build` — render PlantUML source to PNG via plantuml.com
- `plcc-plantuml-diagram-run` — display the rendered PNG

## Dependency Diagram

The call dependency diagram (A → B means A calls B) is saved at:
`dev-docs/diagrams/cli-command-dependencies.puml`

Key structural observations:
- `plcc-scan`, `plcc-parse`, `plcc-rep` all call `plcc-make` internally, then call pipeline stages directly
- `plcc-make` is the central build orchestrator — it is not author-facing, but is called by every high-level command
- `plcc-trees` is the parser dispatcher (analogous to `plcc-lang-emit`); a dedicated `plcc-parser` dispatch command was not created but may be added in future
- All extension packages communicate through their dispatcher commands in core or plcc-diagram

## Document Structure

### File Layout

```
docs/cli/
  index.md                        ← landing page: brief intro + links to guide and reference
  guide/
    author-commands.md            ← daily drivers, diagram, metadata, extension intro
    under-the-hood.md             ← dependency diagram, core pipeline walkthrough
    language-extensions.md        ← plcc-java and plcc-python: what they provide
    parser-extensions.md          ← plcc-parser-table: what it provides
    diagram-extensions.md         ← plcc-mermaid-diagram, plcc-plantuml-diagram
  commands/                       ← flat alphabetical reference, one file per command
    plcc-diagram.md
    plcc-diagram-build.md
    plcc-diagram-emit.md
    plcc-diagram-list.md
    plcc-diagram-run.md
    plcc-java-build.md
    plcc-java-emit.md
    plcc-java-run.md
    plcc-lang-build.md
    plcc-lang-emit.md
    plcc-lang-list.md
    plcc-lang-run.md
    plcc-ll1.md
    plcc-make.md
    plcc-mermaid-diagram-build.md
    plcc-mermaid-diagram-emit.md
    plcc-mermaid-diagram-run.md
    plcc-model.md
    plcc-parse.md
    plcc-parser-list.md
    plcc-parser-table.md
    plcc-plantuml-diagram-build.md
    plcc-plantuml-diagram-emit.md
    plcc-plantuml-diagram-run.md
    plcc-python-build.md
    plcc-python-emit.md
    plcc-python-run.md
    plcc-rep.md
    plcc-scan.md
    plcc-spec.md
    plcc-tokens.md
    plcc-trees.md
    plcc-version.md
```

Delete: `docs/cli/primitives.md`, `docs/cli/orchestrators.md`

### mkdocs.yml Nav

```yaml
- CLI:
  - Overview: cli/index.md
  - Guide:
    - Author-facing commands: cli/guide/author-commands.md
    - Under the hood: cli/guide/under-the-hood.md
    - Language extensions: cli/guide/language-extensions.md
    - Parser extensions: cli/guide/parser-extensions.md
    - Diagram extensions: cli/guide/diagram-extensions.md
  - All Commands:
    - plcc-diagram: cli/commands/plcc-diagram.md
    - plcc-diagram-build: cli/commands/plcc-diagram-build.md
    - plcc-diagram-emit: cli/commands/plcc-diagram-emit.md
    - plcc-diagram-list: cli/commands/plcc-diagram-list.md
    - plcc-diagram-run: cli/commands/plcc-diagram-run.md
    - plcc-java-build: cli/commands/plcc-java-build.md
    - plcc-java-emit: cli/commands/plcc-java-emit.md
    - plcc-java-run: cli/commands/plcc-java-run.md
    - plcc-lang-build: cli/commands/plcc-lang-build.md
    - plcc-lang-emit: cli/commands/plcc-lang-emit.md
    - plcc-lang-list: cli/commands/plcc-lang-list.md
    - plcc-lang-run: cli/commands/plcc-lang-run.md
    - plcc-ll1: cli/commands/plcc-ll1.md
    - plcc-make: cli/commands/plcc-make.md
    - plcc-mermaid-diagram-build: cli/commands/plcc-mermaid-diagram-build.md
    - plcc-mermaid-diagram-emit: cli/commands/plcc-mermaid-diagram-emit.md
    - plcc-mermaid-diagram-run: cli/commands/plcc-mermaid-diagram-run.md
    - plcc-model: cli/commands/plcc-model.md
    - plcc-parse: cli/commands/plcc-parse.md
    - plcc-parser-list: cli/commands/plcc-parser-list.md
    - plcc-parser-table: cli/commands/plcc-parser-table.md
    - plcc-plantuml-diagram-build: cli/commands/plcc-plantuml-diagram-build.md
    - plcc-plantuml-diagram-emit: cli/commands/plcc-plantuml-diagram-emit.md
    - plcc-plantuml-diagram-run: cli/commands/plcc-plantuml-diagram-run.md
    - plcc-python-build: cli/commands/plcc-python-build.md
    - plcc-python-emit: cli/commands/plcc-python-emit.md
    - plcc-python-run: cli/commands/plcc-python-run.md
    - plcc-rep: cli/commands/plcc-rep.md
    - plcc-scan: cli/commands/plcc-scan.md
    - plcc-spec: cli/commands/plcc-spec.md
    - plcc-tokens: cli/commands/plcc-tokens.md
    - plcc-trees: cli/commands/plcc-trees.md
    - plcc-version: cli/commands/plcc-version.md
```

## Page Content Specifications

### `cli/index.md` — Landing page

Two to three sentences introducing plcc-ng's CLI. Then two links:
- "Guide — start here if you're new"
- "All Commands — jump straight to a command reference"

Nothing else.

### `cli/guide/author-commands.md` — Author-facing commands

**Intro:** one sentence framing these as the commands authors use directly.

**Daily drivers (`plcc-scan`, `plcc-parse`, `plcc-rep`):**
A short paragraph on each: what it does, when you reach for it, one minimal example. No flag tables (those live in the reference pages).

**Visualization (`plcc-diagram`):**
Same treatment as daily drivers. Note that it requires the `plcc-diagram` package.

**Metadata and extensions (`plcc-version`, `plcc-lang-list`, `plcc-parser-list`, `plcc-diagram-list`):**
Brief description of each. Then a short paragraph introducing the extension point concept: plcc-ng ships with built-in support for Python and Java, but the system is designed to be extended. `plcc-lang-list` and `plcc-parser-list` show what language and parser plugins are installed; `plcc-diagram-list` (requires `plcc-diagram`) shows what diagram plugins are installed.

### `cli/guide/under-the-hood.md` — Internal architecture

Opens with the detailed dependency diagram from `dev-docs/diagrams/cli-command-dependencies.puml` (embedded via Kroki).

An orientation paragraph: how the author-facing commands from the previous page fit into the full picture.

A pipeline walkthrough — one sentence per stage explaining what it consumes and produces:
- `plcc-make` — the build orchestrator; called internally by every author-facing command
- `plcc-spec` — `.plcc` file → spec JSON
- `plcc-ll1` — spec JSON → LL(1) analysis JSON
- `plcc-tokens` — spec JSON + source → token JSONL
- `plcc-trees` — token JSONL + LL(1) JSON → parse tree (dispatches to parser plugin)
- `plcc-model` — spec JSON → language-neutral model JSON
- `plcc-lang-emit` / `plcc-lang-build` / `plcc-lang-run` — model JSON → language source → built → evaluated (dispatches to language plugin)

### `cli/guide/language-extensions.md`

- What language extensions provide
- How they plug into `plcc-lang-emit`, `plcc-lang-build`, `plcc-lang-run` via the `--target` flag
- The built-in extensions: `plcc-java` and `plcc-python` — what each provides
- How `plcc-lang-list` shows what is installed

### `cli/guide/parser-extensions.md`

- What parser extensions provide
- How they plug into `plcc-trees` via the `--parser` flag
- The built-in extension: `plcc-parser-table` — the LL(1) table-driven parser
- How `plcc-parser-list` shows what is installed
- Note: a dedicated `plcc-parser` dispatch command does not currently exist; `plcc-trees` handles dispatch directly

### `cli/guide/diagram-extensions.md`

- What diagram extensions provide
- How they plug into `plcc-diagram-emit`, `plcc-diagram-build`, `plcc-diagram-run` via the `--format` flag
- The built-in extensions: `plcc-mermaid-diagram` and `plcc-plantuml-diagram` — what each provides
- How `plcc-diagram-list` shows what is installed

### `cli/commands/*.md` — Per-command reference template

```markdown
# plcc-<name>

One-sentence description.

## Usage

​```text
synopsis
​```

## Arguments and Options

| Argument/Option | Description |
|---|---|
| ... | ... |

## Examples

​```bash
example
​```
```

Content migrated from existing `primitives.md` and `orchestrators.md` where it exists; written fresh from source for undocumented commands.

## Common Options

All commands accept `-h`/`--help`, `-v` (repeatable for verbosity), and `--verbose-format=FMT`. These are noted in the options table on each reference page and summarised once in `cli/guide/author-commands.md` after the daily drivers section.
