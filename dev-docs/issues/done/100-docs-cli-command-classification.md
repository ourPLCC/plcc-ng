# 100 - Reconsider how CLI commands are classified and presented in the docs

**Type:** docs
**Date:** 2026-06-18

## Description

The CLI reference currently groups commands as "Level 0" (primitives) and
"Level 2" (orchestrators). These labels are architectural/internal and not
meaningful to users. Issue 083 flagged that `plcc-diagram` is misclassified
under this scheme. The deeper question is whether this classification is the
right one for the docs at all.

## Context and Discussion

The current "Level 0 / Level 2" framing reflects the internal pipeline
architecture, not how students actually experience the tool. When you look at
actual usage patterns, the commands fall into three distinct groups:

**Primary student tools (`plcc-scan`, `plcc-parse`, `plcc-rep`):** These are
what students use day-in and day-out. Their primary purpose is to allow
students to experiment with and test their language specification at different
stages of the pipeline. These deserve the most prominent placement.

**Visualization (`plcc-diagram`):** Helps students understand the mapping from
the syntactic spec to the classes and objects they program with when defining
semantics. Useful but not a daily driver — its place in the workflow is less
clear and students may reach for it infrequently.

**Everything else (`plcc-make` and the lower-level pipeline commands):** Students
will rarely interact with these directly unless an instructor demonstrates them
or explicitly asks students to use them. These are closer to plumbing.

## Options Considered

- **"Workflow commands / Stage commands"** — maps to the pipeline architecture
  but still doesn't reflect the student experience.
- **"Testing / Visualization / Plumbing"** — more honest about purpose, but
  "plumbing" may be off-putting.
- **"Interactive / Visualization / Advanced"** — emphasizes that scan/parse/rep
  are the hands-on tools; "advanced" signals students can ignore the rest.
- **Drop grouping entirely** — lead with prose that says "you'll mostly use
  `plcc-scan`, `plcc-parse`, and `plcc-rep`" and let emphasis come from the
  narrative rather than category labels. The argument here is that category
  labels imply equal weight across groups, whereas what we really want is for
  students to immediately understand these three commands are their world.

## Decision

Use the following classification, presented in this order in the docs:

### Student-facing (daily drivers)

| Command | Summary |
| --- | --- |
| `plcc-scan` | Tokenize source input and print tokens in human-readable format. |
| `plcc-parse` | Parse source input and print the parse tree in human-readable format. |
| `plcc-rep` | REPL — read, eval, print loop for a PLCC spec. |

### Visualization

| Command | Summary |
| --- | --- |
| `plcc-diagram` | Generate and display a class diagram from a PLCC spec file. |

### Build orchestrator

| Command | Summary |
| --- | --- |
| `plcc-make` | Build a PLCC project from a spec file (full pipeline). |

### Pipeline stages (plumbing)

| Command | Summary |
| --- | --- |
| `plcc-spec` | Parse, validate, and print a PLCC grammar file as JSON. |
| `plcc-tokens` | Tokenize source files given a spec JSON, output token JSONL. |
| `plcc-trees` | Dispatch to a parser plugin; reads token JSONL, emits a parse tree. |
| `plcc-model` | Transform spec JSON into a language-neutral code model. |
| `plcc-lang-emit` | Dispatch to the appropriate language emitter plugin. |
| `plcc-lang-build` | Dispatch to the appropriate language builder plugin. |
| `plcc-lang-run` | Dispatch to the appropriate language runner plugin. |

### Plugin discovery

| Command | Summary |
| --- | --- |
| `plcc-lang-list` | List installed language emitter plugins. |
| `plcc-diagram-list` | List installed diagram plugins. |
| `plcc-parser-list` | List installed parser plugins. |

### Diagram sub-pipeline (plumbing)

| Command | Summary |
| --- | --- |
| `plcc-diagram-emit` | Dispatch model JSON to the appropriate diagram emitter. |
| `plcc-diagram-build` | Dispatch to the appropriate diagram builder (source → image). |
| `plcc-diagram-run` | Dispatch to the appropriate diagram runner (display image). |
| `plcc-mermaid-diagram-emit` | Emit a Mermaid class diagram from model JSON. |
| `plcc-mermaid-diagram-build` | Render a Mermaid source file to a PNG image. |
| `plcc-mermaid-diagram-run` | Print the path to the rendered Mermaid diagram image. |
| `plcc-plantuml-diagram-emit` | Emit a PlantUML class diagram from model JSON. |
| `plcc-plantuml-diagram-build` | Render a PlantUML source file to a PNG via plantuml.com. |
| `plcc-plantuml-diagram-run` | Print the path to the rendered PlantUML diagram image. |

### Parser sub-pipeline (plumbing)

| Command | Summary |
| --- | --- |
| `plcc-parser-table` | Table-driven LL(1) parser; reads token JSONL, emits a parse tree. |

## Doc Structure

Each group gets its own page. The overview page (`docs/cli/index.md`) serves
as a table of contents and explains the relationships between command groups
and the user — who uses what and why — so readers can orient quickly without
wading through individual command pages.

## Notes

This issue also supersedes the reclassification in [[083-fix-plcc-diagram-misclassified]]
— once the classification scheme itself is resolved, 083 either gets folded in
or becomes moot.

Likely touches `docs/cli/index.md` and the overall CLI reference structure.
