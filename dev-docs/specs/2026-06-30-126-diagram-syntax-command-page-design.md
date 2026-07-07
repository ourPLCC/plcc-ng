# Design: Add command reference pages for `plcc-diagram-syntax` (issue 126)

**Date:** 2026-06-30
**Issue:** 126

## Goal

Add missing user-facing documentation for `plcc-diagram-syntax` and
`plcc-diagram-syntax-plantuml-emit`, fix the nav gap for the `plcc-diagram-class`
family, and update the Diagram extensions guide to cover the syntax/EBNF type.

## Scope

### New files

| File | Description |
| --- | --- |
| `docs/cli/commands/plcc-diagram-syntax.md` | Command reference for the `plcc-diagram-syntax` orchestrator |
| `docs/cli/commands/plcc-diagram-syntax-plantuml-emit.md` | Command reference for the `plcc-diagram-syntax-plantuml-emit` emitter |

### Modified files

| File | Change |
| --- | --- |
| `mkdocs.yml` | Add 4 nav entries: `plcc-diagram-class`, `plcc-diagram-class-plantuml-emit`, `plcc-diagram-syntax`, `plcc-diagram-syntax-plantuml-emit` |
| `docs/cli/guide/diagram-extensions.md` | Add `## plcc-syntax-diagram` section documenting the syntax/EBNF diagram type |

### Out of scope

- `plcc-diagram-emit.md` — dispatch doc; types are discoverable via `plcc-diagram-list`, not enumerated there
- `plcc-diagram.md` — no change needed
- Internal `docs/superpowers/` planning docs that reference `plcc-diagram-syntactic` — historical, not user-facing

## New command pages

Both pages follow the structure established by `plcc-diagram-class.md` and
`plcc-diagram-class-plantuml-emit.md`.

### `plcc-diagram-syntax.md`

Structure:
1. One-line description: generates a syntax grammar (EBNF) diagram from a PLCC spec file
2. "Requires the `plcc-diagram` package."
3. `## Usage` — fenced `text` block from `--help` output
4. `## Arguments and Options` — table matching `plcc-diagram-class.md` (spec, format, banner, help, verbose)
5. `## Examples` — `plcc-diagram-syntax -s subtract.plcc`
6. `## Diagram formats` — paragraph linking to `plcc-diagram-list` and `diagram-extensions.md`

### `plcc-diagram-syntax-plantuml-emit.md`

Structure:
1. One-line description: emits a PlantUML EBNF diagram from spec JSON; reads from stdin, writes to stdout
2. Note: called by `plcc-diagram-emit --type=syntax --format=plantuml`
3. `## Usage` — fenced `text` block from `--help` output
4. `## Arguments and Options` — table (help, verbose only; no `--output` for this emitter)
5. `## Examples` — `plcc-spec spec.plcc | plcc-diagram-syntax-plantuml-emit > diagram.puml`

## `mkdocs.yml` nav changes

Insert four entries in the "All Commands" section in alphabetical order. Current sequence around the insertion points:

```
- plcc-diagram: ...
- plcc-diagram-build: ...
- plcc-diagram-emit: ...
- plcc-diagram-list: ...
- plcc-diagram-run: ...
```

After change:

```
- plcc-diagram: ...
- plcc-diagram-build: ...
- plcc-diagram-class: cli/commands/plcc-diagram-class.md          # was missing
- plcc-diagram-class-plantuml-emit: cli/commands/plcc-diagram-class-plantuml-emit.md  # was missing
- plcc-diagram-emit: ...
- plcc-diagram-list: ...
- plcc-diagram-run: ...
- plcc-diagram-syntax: cli/commands/plcc-diagram-syntax.md        # new
- plcc-diagram-syntax-plantuml-emit: cli/commands/plcc-diagram-syntax-plantuml-emit.md  # new
```

## `diagram-extensions.md` change

Append a new section after the existing `## plcc-plantuml-diagram` section:

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

Note: `plcc-diagram-plantuml-build` and `plcc-diagram-plantuml-run` are shared
between the class and syntax diagram types (same format plugin, different emitter).
