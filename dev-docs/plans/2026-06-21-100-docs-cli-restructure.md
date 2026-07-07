# CLI Documentation Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the "Level 0 / Level 2" CLI doc structure with a guide + flat reference architecture that documents all 32 commands (31 real + `plcc-python-build` does not yet exist — skip its reference page) and presents them from the language author's perspective.

**Architecture:** A `cli/guide/` directory holds five narrative pages (author-facing commands, under the hood, and three extension pages). A `cli/commands/` directory holds one flat reference page per command (32 files). `cli/index.md` is a minimal landing page linking to both. The old `primitives.md` and `orchestrators.md` are deleted.

**Tech Stack:** MkDocs Material, Kroki plugin (plantuml fence blocks), Markdown.

## Global Constraints

- All work in worktree `.worktrees/issue-100` on branch `issue-100-docs-cli-command-classification`
- `docs(...)` commit subjects must end with `[skip ci]`
- Verify with `mkdocs build` (run from repo root) after each task — it must exit 0
- Do NOT create `plcc-python-build.md` — this command does not exist yet in `pyproject.toml`
- Kroki plantuml fence format: ` ```plantuml ` (no prefix, produces SVG)
- Common options (`-h/--help`, `-v`, `--verbose-format=FMT`) appear in the options table of every reference page and are summarised once in `cli/guide/author-commands.md`

---

### Task 1: Infrastructure — directories, nav, stubs, delete old files

**Files:**
- Create: `docs/cli/guide/` (directory)
- Create: `docs/cli/commands/` (directory)
- Create: stub `.md` for every new page (heading only — see step 1)
- Modify: `mkdocs.yml`
- Delete: `docs/cli/primitives.md`, `docs/cli/orchestrators.md`

- [ ] **Step 1: Create all stub files**

```bash
mkdir -p docs/cli/guide docs/cli/commands

# Landing page (replace existing)
echo "# CLI" > docs/cli/index.md

# Guide stubs
for page in author-commands under-the-hood language-extensions parser-extensions diagram-extensions; do
  echo "# $page" > docs/cli/guide/$page.md
done

# Reference stubs — one per command (note: no plcc-python-build)
for cmd in \
  plcc-diagram plcc-diagram-build plcc-diagram-emit plcc-diagram-list plcc-diagram-run \
  plcc-java-build plcc-java-emit plcc-java-run \
  plcc-lang-build plcc-lang-emit plcc-lang-list plcc-lang-run \
  plcc-ll1 plcc-make \
  plcc-mermaid-diagram-build plcc-mermaid-diagram-emit plcc-mermaid-diagram-run \
  plcc-model plcc-parse plcc-parser-list plcc-parser-table \
  plcc-plantuml-diagram-build plcc-plantuml-diagram-emit plcc-plantuml-diagram-run \
  plcc-python-emit plcc-python-run \
  plcc-rep plcc-scan plcc-spec plcc-tokens plcc-trees plcc-version; do
  echo "# $cmd" > docs/cli/commands/$cmd.md
done
```

- [ ] **Step 2: Delete old files**

```bash
rm docs/cli/primitives.md docs/cli/orchestrators.md
```

- [ ] **Step 3: Update mkdocs.yml nav**

Replace the entire `- CLI Reference:` block in `mkdocs.yml` with:

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
      - plcc-python-emit: cli/commands/plcc-python-emit.md
      - plcc-python-run: cli/commands/plcc-python-run.md
      - plcc-rep: cli/commands/plcc-rep.md
      - plcc-scan: cli/commands/plcc-scan.md
      - plcc-spec: cli/commands/plcc-spec.md
      - plcc-tokens: cli/commands/plcc-tokens.md
      - plcc-trees: cli/commands/plcc-trees.md
      - plcc-version: cli/commands/plcc-version.md
```

- [ ] **Step 4: Verify build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

Expected: `INFO - Documentation built in ...` with exit 0. Fix any broken nav references before continuing.

- [ ] **Step 5: Commit**

```bash
git add docs/cli/ mkdocs.yml
git commit -m "docs(cli): restructure directories and nav for issue 100 [skip ci]"
```

---

### Task 2: Landing page (`docs/cli/index.md`)

**Files:**
- Modify: `docs/cli/index.md`

- [ ] **Step 1: Write the landing page**

```markdown
# CLI Reference

plcc-ng provides a set of command-line tools for defining, building, and
experimenting with programming languages. Most language authors interact with
only a handful of them day-to-day.

- [Guide](guide/author-commands.md) — start here to understand which commands
  to use and how they fit together.
- [All Commands](commands/plcc-scan.md) — jump straight to the reference for a
  specific command.
```

- [ ] **Step 2: Verify build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add docs/cli/index.md
git commit -m "docs(cli): write CLI landing page [skip ci]"
```

---

### Task 3: Guide — author-facing commands (`docs/cli/guide/author-commands.md`)

**Files:**
- Modify: `docs/cli/guide/author-commands.md`

- [ ] **Step 1: Write the page**

```markdown
# Author-Facing Commands

These are the commands you interact with directly when working with plcc-ng.
Everything else runs behind the scenes.

## Daily drivers

Use these to experiment with your language spec at each stage of the pipeline.
They all remember the spec file path between invocations — pass `-s <path>`
once and subsequent commands in the same directory pick it up automatically.

### plcc-scan

Tokenize source input and print each token in human-readable format. Useful
for checking that your lexical rules match what you expect.

```bash
echo "42 36 2" | plcc-scan
plcc-scan -s subtract.plcc samples/
```

### plcc-parse

Parse source input and print the parse tree. Useful for verifying that your
grammar accepts the input you intend and rejects what it shouldn't.

```bash
echo "42 36 2" | plcc-parse
plcc-parse -s subtract.plcc samples/
```

`plcc-parse` also has an interactive mode: when no source files are given and
stdin is a terminal, it reads input at a `>>>` prompt and parses each line as
you type.

### plcc-rep

Read-eval-print loop. Runs your full language spec — scanning, parsing, and
executing semantics — and prints the result of each input.

```bash
plcc-rep -s subtract.plcc samples/   # evaluate files and exit
plcc-rep -s subtract.plcc            # enter interactive mode
```

## Common options

All commands accept these options:

| Option | Effect |
|---|---|
| `-h`, `--help` | Show usage and exit |
| `-v` | Increase verbosity (repeat for more detail: `-v`, `-vv`, `-vvv`) |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json` |

## Visualization

### plcc-diagram

Generate and display a class diagram from your spec file. Shows the classes
and inheritance relationships that plcc-ng derives from your syntactic
grammar — useful for understanding the object model you'll program against
when writing semantics.

```bash
plcc-diagram -s subtract.plcc
```

> **Requires the `plcc-diagram` package.** If `plcc-diagram` is not
> installed, this command will not be available.

## Metadata and extension discovery

### plcc-version

Print the installed plcc-ng version.

```bash
plcc-version
```

### plcc-lang-list

List the language plugins installed on your system. plcc-ng ships with
`python` and `java` support; this command shows what is available.

```bash
plcc-lang-list
```

### plcc-parser-list

List the parser plugins installed on your system. plcc-ng ships with the
`table` parser (LL(1) table-driven); this command shows what is available.

```bash
plcc-parser-list
```

### plcc-diagram-list

List the diagram format plugins installed on your system. plcc-ng ships with
`mermaid` and `plantuml` support.

```bash
plcc-diagram-list
```

> **Requires the `plcc-diagram` package.**

## Extension points

plcc-ng is built around extension points. The language, parser, and diagram
plugins you see above are the built-in implementations, but the system is
designed so that new plugins can be installed alongside plcc-ng and discovered
automatically. See the [Language extensions](language-extensions.md),
[Parser extensions](parser-extensions.md), and
[Diagram extensions](diagram-extensions.md) guides for details.
```

- [ ] **Step 2: Verify build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add docs/cli/guide/author-commands.md
git commit -m "docs(cli): write author-facing commands guide page [skip ci]"
```

---

### Task 4: Guide — under the hood (`docs/cli/guide/under-the-hood.md`)

**Files:**
- Modify: `docs/cli/guide/under-the-hood.md`

- [ ] **Step 1: Write the page**

The dependency diagram to embed is at `dev-docs/diagrams/cli-command-dependencies.puml`. Copy its full PlantUML content (the `@startuml ... @enduml` block) into the fenced block below.

````markdown
# Under the Hood

The commands you use every day — `plcc-scan`, `plcc-parse`, `plcc-rep`, and
`plcc-diagram` — each orchestrate a pipeline of lower-level commands. This
page shows how the pieces fit together.

## Dependency diagram

The diagram below shows which commands call which. An arrow from A to B means
A calls B.

```plantuml
@startuml
allowmixing

left to right direction

package language-extensions {
  package plcc-java {
    class plcc-java-emit
    class plcc-java-build
    class plcc-java-run
  }

  package plcc-python {
    class plcc-python-emit
    class plcc-python-build
    class plcc-python-run
  }
}

package parser-extensions {
  package plcc-parser-table {
    class plcc-parser-table
  }
}

package diagram-extensions {
  package plcc-mermaid-diagram {
    class plcc-mermaid-diagram-emit
    class plcc-mermaid-diagram-build
    class plcc-mermaid-diagram-run
  }

  package plcc-plantuml-diagram {
    class plcc-plantuml-diagram-emit
    class plcc-plantuml-diagram-build
    class plcc-plantuml-diagram-run
  }
}

package core {

  class plcc-version
  class plcc-lang-list
  class plcc-parser-list

  plcc-scan --> plcc-make
  plcc-scan --> plcc-tokens

  plcc-parse --> plcc-make
  plcc-parse --> plcc-tokens
  plcc-parse --> plcc-trees

  plcc-rep --> plcc-make
  plcc-rep --> plcc-tokens
  plcc-rep --> plcc-trees
  plcc-rep --> plcc-lang-run

  plcc-make --> plcc-spec
  plcc-make --> plcc-ll1
  plcc-make --> plcc-model
  plcc-make --> plcc-lang-emit
  plcc-make --> plcc-lang-build

  plcc-trees --> parser-extensions.plcc-parser-table.plcc-parser-table

  plcc-lang-emit --> plcc-python-emit
  plcc-lang-emit --> plcc-java-emit
  plcc-lang-build --> plcc-java-build
  plcc-lang-build --> plcc-python-build
  plcc-lang-run --> plcc-python-run
  plcc-lang-run --> plcc-java-run

}

package plcc-diagram {

  class plcc-diagram-list

  plcc-diagram --> plcc-make
  plcc-diagram --> plcc-diagram-emit
  plcc-diagram --> plcc-diagram-build
  plcc-diagram --> plcc-diagram-run

  plcc-diagram-emit --> plcc-mermaid-diagram-emit
  plcc-diagram-emit --> plcc-plantuml-diagram-emit
  plcc-diagram-build --> plcc-mermaid-diagram-build
  plcc-diagram-build --> plcc-plantuml-diagram-build
  plcc-diagram-run --> plcc-mermaid-diagram-run
  plcc-diagram-run --> plcc-plantuml-diagram-run

}

actor "Language Author" as author

author --> plcc-scan
author --> plcc-parse
author --> plcc-rep
author --> plcc-version
author --> plcc-lang-list
author --> plcc-parser-list
author --> plcc-diagram
author --> plcc-diagram-list

@enduml
```

## The core pipeline

`plcc-make` is the build orchestrator at the centre of the core package. Every
author-facing command calls it before doing its own work.

| Command | Input → Output |
|---|---|
| [`plcc-make`](../../docs/cli/commands/plcc-make.md) | `.plcc` spec file → build artifacts in `build/` |
| [`plcc-spec`](../../docs/cli/commands/plcc-spec.md) | `.plcc` file → spec JSON |
| [`plcc-ll1`](../../docs/cli/commands/plcc-ll1.md) | spec JSON → LL(1) analysis JSON |
| [`plcc-tokens`](../../docs/cli/commands/plcc-tokens.md) | spec JSON + source files → token JSONL |
| [`plcc-trees`](../../docs/cli/commands/plcc-trees.md) | token JSONL + LL(1) JSON → parse tree JSON (dispatches to parser plugin) |
| [`plcc-model`](../../docs/cli/commands/plcc-model.md) | spec JSON → language-neutral model JSON |
| [`plcc-lang-emit`](../../docs/cli/commands/plcc-lang-emit.md) | model JSON → language source files (dispatches to language plugin) |
| [`plcc-lang-build`](../../docs/cli/commands/plcc-lang-build.md) | language source files → compiled output (dispatches to language plugin) |
| [`plcc-lang-run`](../../docs/cli/commands/plcc-lang-run.md) | compiled output + parse tree JSON → evaluation result (dispatches to language plugin) |

## The diagram pipeline

`plcc-diagram` (in the `plcc-diagram` package) calls `plcc-make` to build the
model, then runs its own sub-pipeline:

| Command | Input → Output |
|---|---|
| [`plcc-diagram-emit`](../../docs/cli/commands/plcc-diagram-emit.md) | model JSON → diagram source (dispatches to diagram plugin) |
| [`plcc-diagram-build`](../../docs/cli/commands/plcc-diagram-build.md) | diagram source → PNG image (dispatches to diagram plugin) |
| [`plcc-diagram-run`](../../docs/cli/commands/plcc-diagram-run.md) | PNG path → prints path to stdout (dispatches to diagram plugin) |
````

- [ ] **Step 2: Verify build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add docs/cli/guide/under-the-hood.md
git commit -m "docs(cli): write under-the-hood guide page [skip ci]"
```

---

### Task 5: Guide — extension pages (3 pages)

**Files:**
- Modify: `docs/cli/guide/language-extensions.md`
- Modify: `docs/cli/guide/parser-extensions.md`
- Modify: `docs/cli/guide/diagram-extensions.md`

- [ ] **Step 1: Write `language-extensions.md`**

```markdown
# Language Extensions

Language extensions provide the emit, build, and run steps for a specific
target language. plcc-ng ships with Python and Java support.

## How language extensions plug in

When `plcc-make` (or any command that calls it) builds a spec with a semantic
section, it runs three dispatch commands in sequence:

1. [`plcc-lang-emit --target=LANG`](../../docs/cli/commands/plcc-lang-emit.md) — calls `plcc-<lang>-emit`
2. [`plcc-lang-build --target=LANG`](../../docs/cli/commands/plcc-lang-build.md) — calls `plcc-<lang>-build` (no-op if not found)
3. [`plcc-lang-run --target=LANG`](../../docs/cli/commands/plcc-lang-run.md) — calls `plcc-<lang>-run`

The `LANG` value comes from the `language` declaration in the spec's semantic
section. Use [`plcc-lang-list`](../../docs/cli/commands/plcc-lang-list.md) to see what is
installed.

## plcc-python

Emits a Python interpreter from model JSON, then runs it with the system
Python.

| Command | What it does |
|---|---|
| [`plcc-python-emit`](../../docs/cli/commands/plcc-python-emit.md) | Writes `.py` class files and a `main.py` entry point to the output directory |
| [`plcc-python-run`](../../docs/cli/commands/plcc-python-run.md) | Runs `main.py` with the system Python interpreter |

No build step is required for Python — `plcc-lang-build` exits silently if
`plcc-python-build` is not found.

## plcc-java

Emits a Java interpreter from model JSON, compiles it with `javac`, then
runs it with `java`.

| Command | What it does |
|---|---|
| [`plcc-java-emit`](../../docs/cli/commands/plcc-java-emit.md) | Writes `.java` class files and a `Main.java` entry point to the output directory |
| [`plcc-java-build`](../../docs/cli/commands/plcc-java-build.md) | Compiles all `.java` files with `javac`; requires Java JDK 21+ on `PATH` |
| [`plcc-java-run`](../../docs/cli/commands/plcc-java-run.md) | Runs `Main` with `java`; requires Java JDK 21+ on `PATH` |
```

- [ ] **Step 2: Write `parser-extensions.md`**

```markdown
# Parser Extensions

Parser extensions implement the parsing step. plcc-ng ships with a single
built-in parser: `plcc-parser-table`, an LL(1) table-driven parser.

## How parser extensions plug in

[`plcc-trees`](../../docs/cli/commands/plcc-trees.md) dispatches to a parser plugin via
the `--parser=KIND` flag (default: `table`). It calls `plcc-parser-<kind>`,
passing the LL(1) analysis JSON and token JSONL on stdin.

Use [`plcc-parser-list`](../../docs/cli/commands/plcc-parser-list.md) to see what is
installed.

> **Note:** there is no dedicated `plcc-parser` dispatch command — `plcc-trees`
> handles dispatch directly.

## plcc-parser-table

The default LL(1) table-driven parser. Reads token JSONL from stdin and the
LL(1) analysis JSON from `--ll1`, emits parse tree JSON to stdout.

| Command | What it does |
|---|---|
| [`plcc-parser-table`](../../docs/cli/commands/plcc-parser-table.md) | Table-driven LL(1) parse; emits parse tree JSON or error records |

`plcc-parser-table` also supports `--trace`, which emits `parse-step` records
interleaved with the parse tree for debugging.
```

- [ ] **Step 3: Write `diagram-extensions.md`**

```markdown
# Diagram Extensions

Diagram extensions implement the emit, build, and run steps for a specific
diagram format. plcc-ng ships with Mermaid and PlantUML support.

## How diagram extensions plug in

[`plcc-diagram`](../../docs/cli/commands/plcc-diagram.md) runs three dispatch commands:

1. [`plcc-diagram-emit --format=FMT`](../../docs/cli/commands/plcc-diagram-emit.md) — calls `plcc-<fmt>-diagram-emit`
2. [`plcc-diagram-build --format=FMT`](../../docs/cli/commands/plcc-diagram-build.md) — calls `plcc-<fmt>-diagram-build`
3. [`plcc-diagram-run --format=FMT`](../../docs/cli/commands/plcc-diagram-run.md) — calls `plcc-<fmt>-diagram-run`

The default format is `plantuml`. Use [`plcc-diagram-list`](../../docs/cli/commands/plcc-diagram-list.md)
to see what is installed.

## plcc-mermaid-diagram

Generates a Mermaid class diagram. Requires the `mmdc` CLI
(`npm install -g @mermaid-js/mermaid-cli`).

| Command | What it does |
|---|---|
| [`plcc-mermaid-diagram-emit`](../../docs/cli/commands/plcc-mermaid-diagram-emit.md) | Reads model JSON from stdin; writes a `.mmd` Mermaid source file |
| [`plcc-mermaid-diagram-build`](../../docs/cli/commands/plcc-mermaid-diagram-build.md) | Renders `.mmd` to PNG using `mmdc` |
| [`plcc-mermaid-diagram-run`](../../docs/cli/commands/plcc-mermaid-diagram-run.md) | Prints the path to the rendered PNG |

## plcc-plantuml-diagram

Generates a PlantUML class diagram. Rendering is done via the public
`plantuml.com` API — no local PlantUML installation required.

| Command | What it does |
|---|---|
| [`plcc-plantuml-diagram-emit`](../../docs/cli/commands/plcc-plantuml-diagram-emit.md) | Reads model JSON from stdin; writes a `.puml` PlantUML source file |
| [`plcc-plantuml-diagram-build`](../../docs/cli/commands/plcc-plantuml-diagram-build.md) | Sends `.puml` to plantuml.com and writes the returned PNG |
| [`plcc-plantuml-diagram-run`](../../docs/cli/commands/plcc-plantuml-diagram-run.md) | Prints the path to the rendered PNG |
```

- [ ] **Step 4: Verify build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

- [ ] **Step 5: Commit**

```bash
git add docs/cli/guide/language-extensions.md docs/cli/guide/parser-extensions.md docs/cli/guide/diagram-extensions.md
git commit -m "docs(cli): write extension guide pages [skip ci]"
```

---

### Task 6: Reference pages — daily drivers (plcc-scan, plcc-parse, plcc-rep)

**Files:**
- Modify: `docs/cli/commands/plcc-scan.md`
- Modify: `docs/cli/commands/plcc-parse.md`
- Modify: `docs/cli/commands/plcc-rep.md`

Source for migration: `docs/cli/orchestrators.md` (existing content). Also read `src/plcc/cmd/scan.py`, `src/plcc/cmd/parse.py`, `src/plcc/cmd/rep.py` for the full docstrings.

- [ ] **Step 1: Write `plcc-scan.md`**

```markdown
# plcc-scan

Tokenize source input and print tokens in human-readable format.

## Usage

```text
plcc-scan [-v ...] [options] [SOURCE ...]
```

## Arguments and Options

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to tokenize. Reads stdin if none given. |
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc`. |
| `-t`, `--trace` | Show detailed scanning output including regex candidates and source lines. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Tokenize stdin
echo "42 36 2" | plcc-scan

# Tokenize files
plcc-scan -s subtract.plcc samples/

# After setting spec once, subsequent calls remember it
plcc-scan -s subtract.plcc
plcc-scan samples/
```
```

- [ ] **Step 2: Write `plcc-parse.md`**

```markdown
# plcc-parse

Parse source input and print the parse tree in human-readable format.

## Usage

```text
plcc-parse [-v ...] [options] [SOURCE ...]
```

## Arguments and Options

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to parse. Reads stdin if none given. |
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc`. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Parse stdin
echo "42 36 2" | plcc-parse

# Parse files
plcc-parse -s subtract.plcc samples/
```

## Interactive mode

When no source files are given and stdin is a terminal, `plcc-parse` reads
input at a `>>>` prompt. After each line, complete sentences are parsed and
printed immediately. If the input so far is a valid prefix that could be
extended (e.g., `3` in a grammar that also accepts `3 + 4`), parsing is
deferred and a `...` continuation prompt appears.

- Press `^D` at the `>>>` prompt (empty buffer) to exit.
- Press `^D` at the `...` prompt to force-submit the buffered input and return to `>>>`.
```

- [ ] **Step 3: Write `plcc-rep.md`**

```markdown
# plcc-rep

REPL — read, eval, print loop for a PLCC spec. Scans and parses source input,
then evaluates it using the generated semantics.

## Usage

```text
plcc-rep [-v ...] [options] [SOURCE ...]
```

## Arguments and Options

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to evaluate. Omit (or pass `-`) to enter interactive mode. |
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc`. |
| `-b`, `--banner` | Print the plcc-ng version, spec path, and target language to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Evaluate files and exit
plcc-rep -s subtract.plcc samples/

# Enter interactive mode
plcc-rep -s subtract.plcc
```

## Interactive mode

When no source files are given and stdin is a terminal, `plcc-rep` reads
input at a `>>>` prompt. After each line, complete sentences are evaluated
and their results printed. Continuation prompts (`...`) appear when the input
so far is a valid prefix.

- Press `^D` at the `>>>` prompt (empty buffer) to exit.
- Press `^D` at the `...` prompt to force-submit the buffered input and return to `>>>`.
```

- [ ] **Step 4: Verify build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

- [ ] **Step 5: Commit**

```bash
git add docs/cli/commands/plcc-scan.md docs/cli/commands/plcc-parse.md docs/cli/commands/plcc-rep.md
git commit -m "docs(cli): write plcc-scan, plcc-parse, plcc-rep reference pages [skip ci]"
```

---

### Task 7: Reference page — build orchestrator (plcc-make)

**Files:**
- Modify: `docs/cli/commands/plcc-make.md`

Source for migration: `docs/cli/orchestrators.md` (existing content) and `src/plcc/cmd/make.py`.

- [ ] **Step 1: Write `plcc-make.md`**

```markdown
# plcc-make

Build a PLCC project from a spec file. Runs the full pipeline — spec parsing,
LL(1) analysis, code model generation, language emit, and language build —
stopping at the stage specified by `--through`.

Called internally by `plcc-scan`, `plcc-parse`, `plcc-rep`, and `plcc-diagram`.
You can also call it directly to pre-build before running other commands.

## Usage

```text
plcc-make [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc` on first use. |
| `--through=LEVEL` | Build up to this level: `scan`, `parse`, `model`, or `all`. Default: `all`. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Build everything
plcc-make -s subtract.plcc

# Rebuild after editing the spec (spec remembered from previous run)
plcc-make

# Build only through the scan stage
plcc-make --through=scan
```

## Build levels

| `--through` value | Stages run |
|---|---|
| `scan` | `plcc-spec` |
| `parse` | `plcc-spec`, `plcc-ll1` |
| `model` | `plcc-spec`, `plcc-model` |
| `all` (default) | `plcc-spec`, `plcc-ll1`, `plcc-model`, `plcc-lang-emit`, `plcc-lang-build` |

`plcc-make` caches its output in `build/` and skips stages whose inputs
haven't changed since the last successful run.
```

- [ ] **Step 2: Verify build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add docs/cli/commands/plcc-make.md
git commit -m "docs(cli): write plcc-make reference page [skip ci]"
```

---

### Task 8: Reference pages — core pipeline (plcc-spec, plcc-ll1, plcc-tokens, plcc-trees, plcc-model)

**Files:**
- Modify: `docs/cli/commands/plcc-spec.md`
- Modify: `docs/cli/commands/plcc-ll1.md`
- Modify: `docs/cli/commands/plcc-tokens.md`
- Modify: `docs/cli/commands/plcc-trees.md`
- Modify: `docs/cli/commands/plcc-model.md`

Existing content for plcc-spec, plcc-tokens, plcc-trees, plcc-model: `docs/cli/primitives.md` (already deleted in Task 1 — use git show HEAD~:docs/cli/primitives.md to recover or read from source files).
Source files: `src/plcc/spec/plcc_spec_cli.py`, `src/plcc/ll1/ll1_cli.py`, `src/plcc/tokens/tokens_cli.py`, `src/plcc/tree/tree_cli.py`, `src/plcc/model/model_cli.py`.

- [ ] **Step 1: Write `plcc-spec.md`**

```markdown
# plcc-spec

Parse, validate, and print a PLCC grammar file as JSON.

## Usage

```text
plcc-spec [-v ...] [options] FILE
```

## Arguments and Options

| Argument/Option | Description |
|---|---|
| `FILE` | PLCC grammar file (`.plcc`). Use `-` to read from stdin. |
| `--no-json` | Validate only; do not print JSON to stdout. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Parse and print spec as JSON
plcc-spec spec.plcc

# Validate only (no output on success)
plcc-spec --no-json spec.plcc

# Pipe into another command
plcc-spec spec.plcc | plcc-ll1
```
```

- [ ] **Step 2: Write `plcc-ll1.md`**

```markdown
# plcc-ll1

Perform LL(1) analysis on a grammar spec. Reads spec JSON from stdin and
emits LL(1) analysis JSON to stdout, including FIRST sets, FOLLOW sets,
PREDICT sets, any conflicts, and any left-recursion cycles.

## Usage

```text
plcc-ll1 [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). Higher verbosity emits FIRST/FOLLOW/PREDICT sets and conflict details. |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Analyse a spec and print LL(1) JSON
plcc-spec spec.plcc | plcc-ll1

# Save to file for use with plcc-trees
plcc-spec spec.plcc | plcc-ll1 > build/ll1.json
```
```

- [ ] **Step 3: Write `plcc-tokens.md`**

Read `src/plcc/tokens/tokens_cli.py` for the exact `__doc__` string, then write:

```markdown
# plcc-tokens

Tokenize source files given a spec JSON file; emit token JSONL (one JSON
record per line, each record representing a token, skip, or error).

## Usage

```text
plcc-tokens [-v ...] [options] SPEC_JSON [SOURCE ...]
```

## Arguments and Options

| Argument/Option | Description |
|---|---|
| `SPEC_JSON` | Path to spec JSON (output of `plcc-spec`). |
| `SOURCE` | Source files to tokenize. Use `-` for stdin. Defaults to stdin. |
| `-t`, `--trace` | Include regex candidates, source lines, and skip records in output. |
| `--source-name=LABEL` | Override the source label used for stdin. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Tokenize stdin using a spec JSON piped from plcc-spec
plcc-spec spec.plcc | plcc-tokens - samples/

# Save spec JSON first, then tokenize
plcc-spec spec.plcc > build/spec.json
plcc-tokens build/spec.json samples/
```
```

- [ ] **Step 4: Write `plcc-trees.md`**

```markdown
# plcc-trees

Dispatch to a parser plugin. Reads token JSONL from stdin and emits parse
tree JSON to stdout. The parser plugin is selected with `--parser`.

## Usage

```text
plcc-trees [-v ...] [options] --ll1=LL1_JSON
```

## Arguments and Options

| Option | Description |
|---|---|
| `--ll1=LL1_JSON` | Path to LL(1) analysis JSON (output of `plcc-ll1`). Required. |
| `--parser=KIND` | Parser plugin to use. Default: `table` (calls `plcc-parser-table`). |
| `-t`, `--trace` | Forward trace flag to the parser plugin. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc > build/spec.json
plcc-spec spec.plcc | plcc-ll1 > build/ll1.json
plcc-tokens build/spec.json samples/ | plcc-trees --ll1=build/ll1.json
```

## Parser plugins

`plcc-trees` calls `plcc-parser-<kind>` for the given `--parser` value.
Use [`plcc-parser-list`](plcc-parser-list.md) to see available plugins.
See [Parser extensions](../../docs/cli/guide/parser-extensions.md) for details.
```

- [ ] **Step 5: Write `plcc-model.md`**

```markdown
# plcc-model

Transform spec JSON into a language-neutral code model. The model describes
the classes, fields, and inheritance relationships that the language emitter
uses to generate source code.

## Usage

```text
plcc-model [-v ...] [options] [SPEC_JSON]
```

## Arguments and Options

| Argument/Option | Description |
|---|---|
| `SPEC_JSON` | Path to spec JSON (output of `plcc-spec`). Use `-` or omit to read from stdin. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Pipe from plcc-spec
plcc-spec spec.plcc | plcc-model

# From a saved spec JSON
plcc-model build/spec.json
```
```

- [ ] **Step 6: Verify build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

- [ ] **Step 7: Commit**

```bash
git add docs/cli/commands/plcc-spec.md docs/cli/commands/plcc-ll1.md docs/cli/commands/plcc-tokens.md docs/cli/commands/plcc-trees.md docs/cli/commands/plcc-model.md
git commit -m "docs(cli): write core pipeline reference pages [skip ci]"
```

---

### Task 9: Reference pages — dispatch commands (plcc-lang-emit, plcc-lang-build, plcc-lang-run)

**Files:**
- Modify: `docs/cli/commands/plcc-lang-emit.md`
- Modify: `docs/cli/commands/plcc-lang-build.md`
- Modify: `docs/cli/commands/plcc-lang-run.md`

Source files: `src/plcc/lang/emit.py`, `src/plcc/lang/build.py`, `src/plcc/lang/run.py`.

- [ ] **Step 1: Write `plcc-lang-emit.md`**

```markdown
# plcc-lang-emit

Dispatch to the appropriate language emitter. Reads model JSON from stdin
and calls `plcc-<lang>-emit` for the specified target language.

## Usage

```text
plcc-lang-emit [-v ...] --target=LANG --output=DIR
```

## Arguments and Options

| Option | Description |
|---|---|
| `--target=LANG` | Target language (e.g. `Python`, `Java`). Required. |
| `--output=DIR` | Directory to write emitted source files into. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-lang-emit --target=Python --output=build/Python
```

## Language plugins

`plcc-lang-emit` calls `plcc-<lang>-emit` for the target language.
Use [`plcc-lang-list`](plcc-lang-list.md) to see available plugins.
See [Language extensions](../../docs/cli/guide/language-extensions.md) for details.
```

- [ ] **Step 2: Write `plcc-lang-build.md`**

```markdown
# plcc-lang-build

Dispatch to the appropriate language build step. Calls `plcc-<lang>-build`
for the target language. If no build command is found, exits silently with
success — not all languages require a build step (Python does not).

## Usage

```text
plcc-lang-build [-v ...] --target=LANG --output=DIR
```

## Arguments and Options

| Option | Description |
|---|---|
| `--target=LANG` | Target language (e.g. `Python`, `Java`). Required. |
| `--output=DIR` | Output directory (already populated by `plcc-lang-emit`). Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-lang-build --target=Java --output=build/Java
```
```

- [ ] **Step 3: Write `plcc-lang-run.md`**

```markdown
# plcc-lang-run

Dispatch to the appropriate language runner. Reads parse tree JSON from stdin
and calls `plcc-<lang>-run` for the target language.

## Usage

```text
plcc-lang-run --target=LANG --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--target=LANG` | Target language (e.g. `Python`, `Java`). Required. |
| `--output=DIR` | Directory containing built artifacts. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-lang-run --target=Python --output=build/Python
```
```

- [ ] **Step 4: Verify build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

- [ ] **Step 5: Commit**

```bash
git add docs/cli/commands/plcc-lang-emit.md docs/cli/commands/plcc-lang-build.md docs/cli/commands/plcc-lang-run.md
git commit -m "docs(cli): write lang dispatch reference pages [skip ci]"
```

---

### Task 10: Reference pages — discovery and utility (plcc-lang-list, plcc-parser-list, plcc-version)

**Files:**
- Modify: `docs/cli/commands/plcc-lang-list.md`
- Modify: `docs/cli/commands/plcc-parser-list.md`
- Modify: `docs/cli/commands/plcc-version.md`

Source files: `src/plcc/lang/list.py`, `src/plcc/parser/list_cli.py`, `src/plcc/version.py`.

- [ ] **Step 1: Write `plcc-lang-list.md`**

```markdown
# plcc-lang-list

List installed language emitter plugins. Scans `PATH` for `plcc-*-emit`
commands and prints each discovered language name, one per line.

## Usage

```text
plcc-lang-list [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-lang-list
# java
# python
```
```

- [ ] **Step 2: Write `plcc-parser-list.md`**

```markdown
# plcc-parser-list

List installed parser plugins. Scans `PATH` for `plcc-parser-*` commands
and prints each discovered parser kind, one per line.

## Usage

```text
plcc-parser-list [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-parser-list
# table
```
```

- [ ] **Step 3: Write `plcc-version.md`**

```markdown
# plcc-version

Print the installed plcc-ng version.

## Usage

```text
plcc-version
```

## Examples

```bash
plcc-version
# plcc-ng 1.2.3
```
```

- [ ] **Step 4: Verify build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

- [ ] **Step 5: Commit**

```bash
git add docs/cli/commands/plcc-lang-list.md docs/cli/commands/plcc-parser-list.md docs/cli/commands/plcc-version.md
git commit -m "docs(cli): write discovery and utility reference pages [skip ci]"
```

---

### Task 11: Reference pages — plcc-diagram package (5 pages)

**Files:**
- Modify: `docs/cli/commands/plcc-diagram.md`
- Modify: `docs/cli/commands/plcc-diagram-list.md`
- Modify: `docs/cli/commands/plcc-diagram-emit.md`
- Modify: `docs/cli/commands/plcc-diagram-build.md`
- Modify: `docs/cli/commands/plcc-diagram-run.md`

Source files: `src/plcc/cmd/diagram.py`, `src/plcc/diagram/list.py`, `src/plcc/diagram/emit.py`, `src/plcc/diagram/build.py`, `src/plcc/diagram/run.py`.

- [ ] **Step 1: Write `plcc-diagram.md`**

```markdown
# plcc-diagram

Generate and display a class diagram from a PLCC spec file. Shows the classes
and inheritance relationships derived from the syntactic grammar.

Requires the `plcc-diagram` package.

## Usage

```text
plcc-diagram [-v ...] [options]
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
plcc-diagram -s subtract.plcc
plcc-diagram --format=mermaid
```

## Diagram formats

`plcc-diagram` dispatches to diagram extension plugins via `--format`.
Use [`plcc-diagram-list`](plcc-diagram-list.md) to see installed formats.
See [Diagram extensions](../../docs/cli/guide/diagram-extensions.md) for details.
```

- [ ] **Step 2: Write `plcc-diagram-list.md`**

```markdown
# plcc-diagram-list

List installed diagram format plugins. Scans `PATH` for
`plcc-*-diagram-emit` commands and prints each format name, one per line.

Requires the `plcc-diagram` package.

## Usage

```text
plcc-diagram-list [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-diagram-list
# mermaid
# plantuml
```
```

- [ ] **Step 3: Write `plcc-diagram-emit.md`**

```markdown
# plcc-diagram-emit

Dispatch model JSON to the appropriate diagram emitter. Reads model JSON from
stdin and calls `plcc-<fmt>-diagram-emit` for the specified format.

Requires the `plcc-diagram` package.

## Usage

```text
plcc-diagram-emit [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--format=FMT` | Diagram format plugin to use. Default: `plantuml`. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-diagram-emit --format=mermaid
```
```

- [ ] **Step 4: Write `plcc-diagram-build.md`**

```markdown
# plcc-diagram-build

Dispatch to the appropriate diagram build step. Calls
`plcc-<fmt>-diagram-build` for the specified format, converting a diagram
source file into a PNG image.

Requires the `plcc-diagram` package.

## Usage

```text
plcc-diagram-build --input=FILE --output=FILE [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--format=FMT` | Diagram format plugin to use. Default: `plantuml`. |
| `--input=FILE` | Path to diagram source file. Required. |
| `--output=FILE` | Path to write PNG image. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-diagram-build --format=plantuml --input=build/diagram/diagram.puml --output=build/diagram/diagram.png
```
```

- [ ] **Step 5: Write `plcc-diagram-run.md`**

```markdown
# plcc-diagram-run

Dispatch to the appropriate diagram runner. Calls
`plcc-<fmt>-diagram-run` for the specified format. Currently, all built-in
runners print the path to the rendered image file to stdout.

Requires the `plcc-diagram` package.

## Usage

```text
plcc-diagram-run --input=FILE [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--format=FMT` | Diagram format plugin to use. Default: `plantuml`. |
| `--input=FILE` | Path to PNG image file. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-diagram-run --format=plantuml --input=build/diagram/diagram.png
```
```

- [ ] **Step 6: Verify build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

- [ ] **Step 7: Commit**

```bash
git add docs/cli/commands/plcc-diagram.md docs/cli/commands/plcc-diagram-list.md docs/cli/commands/plcc-diagram-emit.md docs/cli/commands/plcc-diagram-build.md docs/cli/commands/plcc-diagram-run.md
git commit -m "docs(cli): write plcc-diagram package reference pages [skip ci]"
```

---

### Task 12: Reference pages — language extensions (plcc-java-*, plcc-python-*)

**Files:**
- Modify: `docs/cli/commands/plcc-java-emit.md`
- Modify: `docs/cli/commands/plcc-java-build.md`
- Modify: `docs/cli/commands/plcc-java-run.md`
- Modify: `docs/cli/commands/plcc-python-emit.md`
- Modify: `docs/cli/commands/plcc-python-run.md`

Source files: `src/plcc/lang/ext/java/emit.py`, `src/plcc/lang/ext/java/build.py`, `src/plcc/lang/ext/java/run.py`, `src/plcc/lang/ext/python/emit.py`, `src/plcc/lang/ext/python/run.py`.

Note: `plcc-python-build` does not exist — do not create a reference page for it.

- [ ] **Step 1: Write `plcc-java-emit.md`**

```markdown
# plcc-java-emit

Emit a Java interpreter from model JSON. Reads model JSON from stdin and
writes `.java` source files and a `Main.java` entry point to the output
directory.

Called by [`plcc-lang-emit --target=Java`](plcc-lang-emit.md).

## Usage

```text
plcc-java-emit --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Directory to write generated Java files into. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-java-emit --output=build/Java
```
```

- [ ] **Step 2: Write `plcc-java-build.md`**

```markdown
# plcc-java-build

Compile generated Java source files. Runs `javac` on all `.java` files in the
output directory.

Called by [`plcc-lang-build --target=Java`](plcc-lang-build.md).

Requires Java JDK 21 or later on `PATH`.

## Usage

```text
plcc-java-build --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Directory containing generated Java files (from `plcc-java-emit`). Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-java-build --output=build/Java
```
```

- [ ] **Step 3: Write `plcc-java-run.md`**

```markdown
# plcc-java-run

Run a compiled Java interpreter. Reads parse tree JSON from stdin and passes
it to the `Main` class in the output directory.

Called by [`plcc-lang-run --target=Java`](plcc-lang-run.md).

Requires Java JDK 21 or later on `PATH`.

## Usage

```text
plcc-java-run --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Directory containing compiled Java class files. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-java-run --output=build/Java
```
```

- [ ] **Step 4: Write `plcc-python-emit.md`**

```markdown
# plcc-python-emit

Emit a Python interpreter from model JSON. Reads model JSON from stdin and
writes `.py` class files and a `main.py` entry point to the output directory.

Called by [`plcc-lang-emit --target=Python`](plcc-lang-emit.md).

## Usage

```text
plcc-python-emit --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Directory to write generated Python files into. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-python-emit --output=build/Python
```
```

- [ ] **Step 5: Write `plcc-python-run.md`**

```markdown
# plcc-python-run

Run a generated Python interpreter. Reads parse tree JSON from stdin and runs
`main.py` in the output directory using the system Python.

Called by [`plcc-lang-run --target=Python`](plcc-lang-run.md).

## Usage

```text
plcc-python-run --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Directory containing generated Python files (from `plcc-python-emit`). Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-python-run --output=build/Python
```
```

- [ ] **Step 6: Verify build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

- [ ] **Step 7: Commit**

```bash
git add docs/cli/commands/plcc-java-emit.md docs/cli/commands/plcc-java-build.md docs/cli/commands/plcc-java-run.md docs/cli/commands/plcc-python-emit.md docs/cli/commands/plcc-python-run.md
git commit -m "docs(cli): write language extension reference pages [skip ci]"
```

---

### Task 13: Reference page — parser extension (plcc-parser-table)

**Files:**
- Modify: `docs/cli/commands/plcc-parser-table.md`

Source file: `src/plcc/parser/table_cli.py`.

- [ ] **Step 1: Write `plcc-parser-table.md`**

```markdown
# plcc-parser-table

Table-driven LL(1) parser. Reads token JSONL from stdin and emits parse tree
JSON to stdout. Called by [`plcc-trees --parser=table`](plcc-trees.md)
(this is the default parser).

## Usage

```text
plcc-parser-table [-v ...] [options] --ll1=LL1_JSON
```

## Arguments and Options

| Option | Description |
|---|---|
| `--ll1=LL1_JSON` | Path to LL(1) analysis JSON (output of `plcc-ll1`). Required. |
| `-t`, `--trace` | Emit `parse-step` records tracing predict, shift, and complete events. |
| `--hold-markers` | Emit a hold marker after a trailing extensible parse (used by interactive mode). |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-ll1 > build/ll1.json
plcc-tokens build/spec.json samples/ | plcc-parser-table --ll1=build/ll1.json
```
```

- [ ] **Step 2: Verify build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add docs/cli/commands/plcc-parser-table.md
git commit -m "docs(cli): write plcc-parser-table reference page [skip ci]"
```

---

### Task 14: Reference pages — diagram extensions (mermaid and plantuml, 6 pages)

**Files:**
- Modify: `docs/cli/commands/plcc-mermaid-diagram-emit.md`
- Modify: `docs/cli/commands/plcc-mermaid-diagram-build.md`
- Modify: `docs/cli/commands/plcc-mermaid-diagram-run.md`
- Modify: `docs/cli/commands/plcc-plantuml-diagram-emit.md`
- Modify: `docs/cli/commands/plcc-plantuml-diagram-build.md`
- Modify: `docs/cli/commands/plcc-plantuml-diagram-run.md`

Source files: `src/plcc/diagram/mermaid/emit.py`, `src/plcc/diagram/mermaid/build.py`, `src/plcc/diagram/mermaid/run.py`, `src/plcc/diagram/plantuml/emit.py`, `src/plcc/diagram/plantuml/build.py`, `src/plcc/diagram/plantuml/run.py`.

- [ ] **Step 1: Write `plcc-mermaid-diagram-emit.md`**

```markdown
# plcc-mermaid-diagram-emit

Emit a Mermaid class diagram from model JSON. Reads model JSON from stdin
and writes a Mermaid `classDiagram` source to stdout.

Called by [`plcc-diagram-emit --format=mermaid`](plcc-diagram-emit.md).

## Usage

```text
plcc-mermaid-diagram-emit [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-mermaid-diagram-emit > diagram.mmd
```
```

- [ ] **Step 2: Write `plcc-mermaid-diagram-build.md`**

```markdown
# plcc-mermaid-diagram-build

Render a Mermaid diagram source file to a PNG image using `mmdc`.

Called by [`plcc-diagram-build --format=mermaid`](plcc-diagram-build.md).

Requires `mmdc` on `PATH`: `npm install -g @mermaid-js/mermaid-cli`.

## Usage

```text
plcc-mermaid-diagram-build --input=FILE --output=FILE [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--input=FILE` | Path to `.mmd` Mermaid source file. Required. |
| `--output=FILE` | Path to write PNG image. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-mermaid-diagram-build --input=diagram.mmd --output=diagram.png
```
```

- [ ] **Step 3: Write `plcc-mermaid-diagram-run.md`**

```markdown
# plcc-mermaid-diagram-run

Print the path to the rendered Mermaid diagram image.

Called by [`plcc-diagram-run --format=mermaid`](plcc-diagram-run.md).

## Usage

```text
plcc-mermaid-diagram-run --input=FILE [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--input=FILE` | Path to PNG image file. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-mermaid-diagram-run --input=diagram.png
# /path/to/diagram.png
```
```

- [ ] **Step 4: Write `plcc-plantuml-diagram-emit.md`**

```markdown
# plcc-plantuml-diagram-emit

Emit a PlantUML class diagram from model JSON. Reads model JSON from stdin
and writes PlantUML source to stdout (or to a file if `--output` is given).

Called by [`plcc-diagram-emit --format=plantuml`](plcc-diagram-emit.md).

## Usage

```text
plcc-plantuml-diagram-emit [--output=DIR] [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Write `diagram.puml` into this directory. Writes to stdout if omitted. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-plantuml-diagram-emit > diagram.puml
```
```

- [ ] **Step 5: Write `plcc-plantuml-diagram-build.md`**

```markdown
# plcc-plantuml-diagram-build

Render a PlantUML diagram source file to a PNG image. Sends the source to the
public `plantuml.com` API and writes the returned PNG to disk. No local
PlantUML installation required.

Called by [`plcc-diagram-build --format=plantuml`](plcc-diagram-build.md).

## Usage

```text
plcc-plantuml-diagram-build --input=FILE --output=FILE [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--input=FILE` | Path to `.puml` PlantUML source file. Required. |
| `--output=FILE` | Path to write PNG image. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-plantuml-diagram-build --input=diagram.puml --output=diagram.png
```
```

- [ ] **Step 6: Write `plcc-plantuml-diagram-run.md`**

```markdown
# plcc-plantuml-diagram-run

Print the path to the rendered PlantUML diagram image.

Called by [`plcc-diagram-run --format=plantuml`](plcc-diagram-run.md).

## Usage

```text
plcc-plantuml-diagram-run --input=FILE [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--input=FILE` | Path to PNG image file. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-plantuml-diagram-run --input=diagram.png
# /path/to/diagram.png
```
```

- [ ] **Step 7: Verify build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

- [ ] **Step 8: Final commit**

```bash
git add docs/cli/commands/plcc-mermaid-diagram-emit.md docs/cli/commands/plcc-mermaid-diagram-build.md docs/cli/commands/plcc-mermaid-diagram-run.md docs/cli/commands/plcc-plantuml-diagram-emit.md docs/cli/commands/plcc-plantuml-diagram-build.md docs/cli/commands/plcc-plantuml-diagram-run.md
git commit -m "docs(cli): write diagram extension reference pages [skip ci]"
```
