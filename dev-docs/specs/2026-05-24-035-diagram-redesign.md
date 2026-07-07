---
title: 035 - plcc-diagram interface redesign
date: 2026-05-24
issue: docs/issues/035-plcc-diagram-output-build-hangs.md
superseded_by: dev-docs/specs/2026-05-25-diagram-decouple-from-make-design.md
---

> **Superseded.** The `--through=diagram` / `--diagram-format` interface described here was replaced by the design in [2026-05-25-diagram-decouple-from-make-design.md](2026-05-25-diagram-decouple-from-make-design.md). `plcc-make` no longer has any diagram stages; `plcc-diagram` now owns the full emit → build → run pipeline. The historical record below is preserved for context.

## Problem

`plcc-diagram --output=build` hangs indefinitely. Root cause: the current
`plcc-diagram` is a Level 0 dispatcher that passes `stdin=sys.stdin` to a
subprocess, which blocks on `json.load(sys.stdin)` when no input is piped.
The hang is not specific to `build` — any `--output=DIR` value triggers it
when stdin is not piped — but users encounter it specifically with `--output=build`
because `plcc-make` produces `build/model.json` and they expect
`plcc-diagram --output=build` to use it.

The deeper issue is that `plcc-diagram` was designed as a Level 0 command but
needs to be a Level 2 user-facing command, consistent with `plcc-scan`,
`plcc-parse`, and `plcc-rep`.

## Design

### Architecture

```text
Level 2 (user-facing)
  plcc-diagram          --grammar-file + --format → calls plcc-make → calls plcc-diagram-run

Level 1 (build orchestration)
  plcc-make             gains --through=diagram and --diagram-format=FMT
                        calls plcc-diagram-emit then plcc-diagram-build
                        output: build/diagram/diagram.mmd + build/diagram/diagram.png

Level 0 dispatchers
  plcc-diagram-emit     model JSON (stdin) → diagram source (stdout)
  plcc-diagram-build    --input=FILE --output=FILE → image file
  plcc-diagram-run      --input=FILE → opens system viewer

Level 0 plugins (Mermaid, default)
  plcc-mermaid-diagram-emit    model JSON → Mermaid class diagram source
  plcc-mermaid-diagram-build   .mmd → .png via mmdc Python library
  plcc-mermaid-diagram-run     .png → system viewer (open/xdg-open/start)

Level 0 plugins (PlantUML, renamed)
  plcc-plantuml-diagram-emit   renames current plcc-plantuml-diagram
  (build and run deferred)

Discovery
  plcc-diagram-list     scans PATH for plcc-*-diagram-emit
```

The pattern is identical to the lang plugin system:

| lang           | diagram             | meaning                        |
|----------------|---------------------|--------------------------------|
| plcc-lang-emit | plcc-diagram-emit   | generate source                |
| plcc-lang-build| plcc-diagram-build  | compile/render to output image |
| plcc-lang-run  | plcc-diagram-run    | execute/view                   |

`plcc-make --through=all` runs emit + build for both tools and diagram.
`plcc-diagram` (Level 2) adds the run/view step on top, same as `plcc-scan`
adds interactive presentation on top of `plcc-make --through=scan`.

### Level 2: `plcc-diagram`

```text
Usage:
    plcc-diagram [-v ...] [options]

Options:
    --grammar-file=<path>   Path to PLCC grammar file [default: grammar.plcc].
    --format=FMT            Diagram format [default: mermaid].
    -h --help               Show this message.
```

Behaviour:

1. Calls `plcc-make --through=diagram --grammar-file=... --diagram-format=...`
2. Calls `plcc-diagram-run --format=FMT --input=build/diagram/diagram.png`

The hang is structurally impossible: `plcc-diagram` takes a grammar file
argument and calls `plcc-make`. There is no stdin-blocking dispatcher
exposed to users.

### `plcc-make` changes

**New `--through` stage: `diagram`**

`--through=diagram` builds: spec.json → model.json →
diagram.mmd + diagram.png. Output goes to `build/diagram/`.
`plcc-model` reads spec.json directly and does not need ll1.json,
so the ll1 step is skipped on this path.

`--through=all` now includes the diagram step after all tool steps.

```python
_run_or_die(['plcc-diagram-emit', f'--format={diagram_fmt}'] + child_flags,
            stdin_file=model_json,
            stdout_file=str(build_dir / 'diagram' / 'diagram.mmd'))

_run_or_die(['plcc-diagram-build', f'--format={diagram_fmt}',
             f'--input={build_dir / "diagram" / "diagram.mmd"}',
             f'--output={build_dir / "diagram" / "diagram.png"}'] + child_flags)
```

**New flag: `--diagram-format=FMT`** (default: `mermaid`)

Passed through to `plcc-diagram-emit` and `plcc-diagram-build`.

**`--through` stage ordering for `plcc-scan` and `plcc-parse`**

Unchanged. `plcc-scan` calls `--through=scan`, `plcc-parse` calls
`--through=parse`. Neither triggers diagram generation.

### Staleness: set-based sentinel

The current linear `_LEVELS` dict is replaced with a set-based sentinel that
correctly handles parallel stages (tools and diagram both depend on model.json
but are independent of each other).

**New sentinel format:**

```json
{"hash": "abc123", "stages": ["scan", "parse", "model", "diagram"]}
```

**`staleness.py` API changes:**

- `_LEVELS` removed
- `is_current(sentinel, hash_, required_stages)` — `required_stages` is a
  `set[str]`; returns True iff hash matches AND `required_stages ⊆ completed`
- `write_sentinel(build_dir, hash_, stages)` — `stages` is the set of stages
  just successfully built

**`plcc-make` maps each `--through` value to a required set:**

```python
tool_stages = {s['tool'] for s in spec.get('semantics', [])}

required = {
    'scan':    {'scan'},
    'parse':   {'scan', 'parse'},
    'diagram': {'scan', 'model', 'diagram'},
    'all':     {'scan', 'parse', 'model', 'diagram'} | tool_stages,
}[through]
```

`is_current` is called with that set after running `plcc-spec` (since tool
names are not known until the spec is read). Unknown stage names are simply
absent from the completed set, so `is_current` returns False — the safe default.

No backwards compatibility with old sentinels. Existing `build/` directories
will trigger a clean rebuild on first use after upgrade. This is acceptable
while the project is experimental.

### Level 0 dispatchers

**`plcc-diagram-emit`** (renames current `plcc-diagram`):

```text
Usage:
    plcc-diagram-emit [-v ...] [options]

Options:
    --format=FMT    Diagram format [default: mermaid].

stdin:  model JSON
stdout: diagram source text
```

Dispatches to `plcc-<fmt>-diagram-emit`.

**`plcc-diagram-build`** (new):

```text
Usage:
    plcc-diagram-build --format=FMT --input=FILE --output=FILE [-v ...] [options]
```

File paths (not stdin/stdout) because input is already on disk and output
is a binary image. Dispatches to `plcc-<fmt>-diagram-build`.

**`plcc-diagram-run`** (new):

```text
Usage:
    plcc-diagram-run --format=FMT --input=FILE [-v ...] [options]
```

Opens image in system viewer. Dispatches to `plcc-<fmt>-diagram-run`.
Called only by `plcc-diagram` (Level 2), never by `plcc-make`.

### Mermaid plugin (default)

Located in `src/plcc/diagram/mermaid/`.

**`plcc-mermaid-diagram-emit`**: reads model JSON from stdin, writes Mermaid
class diagram source to stdout. Pure Python, no extra dependencies. Ships
with base `plcc`.

Example output:

```text
classDiagram
    class Expr {
        <<abstract>>
    }
    class AddExpr {
        left: Expr
        right: Expr
    }
    Expr <|-- AddExpr
```

**`plcc-mermaid-diagram-build`**: renders `.mmd` to `.png` using the `mmdc`
Python library. Requires `pip install plcc[diagram]`.

If `mmdc` is not installed, exits with a clear error:
`plcc-mermaid-diagram-build: mmdc not installed — run: pip install plcc[diagram]`

**`plcc-mermaid-diagram-run`**: opens the image with the system viewer
(`open` on macOS, `xdg-open` on Linux, `start` on Windows). Ships with
base `plcc`, no extra dependencies.

**`pyproject.toml`:**

```toml
[project.optional-dependencies]
diagram = ["mmdc"]
```

### PlantUML plugin

`plcc-plantuml-diagram` is renamed to `plcc-plantuml-diagram-emit`. No other
changes. `plcc-plantuml-diagram-build` and `plcc-plantuml-diagram-run` are
deferred.

### Discovery: `plcc-diagram-list`

Updated to scan PATH for the pattern `plcc-*-diagram-emit` (replacing the
current `plcc-*-diagram` pattern). Reports installed emit plugins by format name.

### Renamed entry points summary

| Old                                | New                          |
|------------------------------------|------------------------------|
| `plcc-diagram` (Level 0 dispatcher)| `plcc-diagram-emit`          |
| `plcc-plantuml-diagram`            | `plcc-plantuml-diagram-emit` |

`plcc-diagram` is reclaimed as the Level 2 user-facing command.

## Testing

- Unit tests for `staleness.py` updated to cover set-based sentinel
- Unit tests for `plcc-mermaid-diagram-emit` (model JSON → Mermaid source)
- Bats command tests for `plcc-diagram-emit`, `plcc-diagram-build`, `plcc-diagram-run`
- Bats command test for `plcc-diagram` (Level 2)
- Bats command test for `plcc-diagram-list` (updated pattern)
- E2E test: `plcc-diagram grammar.plcc` produces `build/diagram/diagram.png`
- `plcc-make --through=diagram` produces `build/diagram/diagram.mmd` and `build/diagram/diagram.png`
