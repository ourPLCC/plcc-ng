# Phase 1 Design: Walking Skeleton

**Date:** 2026-04-13
**Status:** Approved
**Phase:** 1 of 5
**Companion:** [2026-04-12-multi-lang-implementation-plan.md](2026-04-12-multi-lang-implementation-plan.md)
**Implementation plan:** `docs/plans/2026-04-13-phase-1-walking-skeleton.md` (to be written)

## 1. Goals and Scope

Phase 1 has two equal deliverables:

1. **A connected walking skeleton** — every Level 0 command exists, produces valid JSON/JSONL for the trivial grammar, and hands it to the next stage, end-to-end to a `.puml` file.
2. **Complete development infrastructure** — the repo is organized, the test pyramid is in place, developer scripts are established, and CI is running. By the end of Phase 1, a new contributor knows exactly how to build, test, and extend the project.

Each Level 0 command is implemented just enough to process the trivial grammar correctly and no more (strict TDD). The existing spec parser and scanner are wired in as real implementations. `plcc-model` gets a real initial implementation that produces valid model JSON for the trivial grammar. JSON schemas (contracts) are defined in Phase 1 and enforced by tests. Phase 1 also exists to surface architectural and design problems early, before they become expensive to fix.

**Explicitly out of scope:**
- Any grammar more complex than the trivial one
- Runnable interpreters
- Backwards compatibility with v8 grammars
- Error *production* (in-band error passthrough is tested; producing error records is Phase 2)
- PyPI publication

## 2. Package Rename

The rename from `plccng` to `plcc` is the first task of Phase 1. The full test suite must be green before any skeleton work begins.

**Sequence:**
1. Verify all existing tests pass on `main` — fix any failures before doing anything else
2. Create the `multi-lang` branch
3. `git mv src/plccng src/plcc` — preserves full git history and student attribution
4. Update all internal imports (`plccng.*` → `plcc.*`) and `pyproject.toml` (`name = "plcc"`)
5. Migrate ALL existing tests — update imports, rename test files where appropriate
6. Full test suite green before proceeding

Existing code becomes obsolete during a refactor only as a last resort. This is a refactor, not a rewrite.

## 3. The Trivial Grammar

```
%% lexical rules
NUM '\d+'

%% syntactic rules
<program> ::= <NUM>

%% semantic rules
% diagram PlantUML
```

- Produces a `Program` class with a `num` field of type `Token`
- PlantUML output is a class box with one field — visually verifiable
- Lives at `tests/fixtures/trivial.plcc`

The grammar is intentionally the smallest thing that exercises every JSON contract once and drives the pipeline end-to-end.

## 4. Module Layout

```
src/plcc/
├── spec/               → plcc-spec       (existing, renamed)
├── tokens/             → plcc-tokens     (existing scan/, renamed)
├── tree/               → plcc-tree       (new)
├── model/              → plcc-model      (new)
├── lang/
│   ├── emit.py         → plcc-lang-emit  (dispatcher)
│   ├── build.py        → plcc-lang-build (dispatcher)
│   ├── list.py         → plcc-lang-list
│   └── ext/
│       └── plantuml/   → plcc-plantuml-emit
│           └── runtime/
└── cmd/
    ├── make.py         → plcc-make       (Level 2, implemented)
    ├── scan.py         → plcc-scan       (Level 2 skeleton)
    ├── parse.py        → plcc-parse      (Level 2 skeleton)
    └── rep.py          → plcc-rep        (Level 2 skeleton)
```

Level 2 skeletons print `"not yet implemented"` and exit 1. They exist to make the full command surface visible and to verify that the packaging and entry-point wiring is complete.

**Namespace rationale:** `plcc.lang` contains the dispatcher machinery. `plcc.lang.ext` contains built-in language plugins — `ext` signals they extend the mechanism rather than being the mechanism itself, and avoids name collisions with future third-party plugins.

### `pyproject.toml` console scripts

```toml
[project.scripts]
plcc-spec          = "plcc.spec:main"
plcc-tokens        = "plcc.tokens:main"
plcc-tree          = "plcc.tree:main"
plcc-model         = "plcc.model:main"
plcc-lang-emit     = "plcc.lang.emit:main"
plcc-lang-build    = "plcc.lang.build:main"
plcc-lang-list     = "plcc.lang.list:main"
plcc-plantuml-emit = "plcc.lang.ext.plantuml:main"
plcc-make          = "plcc.cmd.make:main"
plcc-scan          = "plcc.cmd.scan:main"
plcc-parse         = "plcc.cmd.parse:main"
plcc-rep           = "plcc.cmd.rep:main"
```

## 5. JSON Schemas and Contracts

Each Level 0 command has a JSON Schema in `src/plcc/schemas/`:

| File | Validates |
|---|---|
| `spec.schema.json` | Output of `plcc-spec` |
| `token.schema.json` | One record in the `plcc-tokens` JSONL stream |
| `tree.schema.json` | One record in the `plcc-tree` JSONL stream |
| `model.schema.json` | Output of `plcc-model` |

For JSONL outputs, each line is validated independently against its schema. `check-jsonschema` (added to `[dependency-groups].dev`) is used in both Python tests and BATS tests.

Schemas are minimum viable in Phase 1 — they describe the shape required for the trivial grammar and no more. They are the authoritative contracts that Phase 2+ extends.

## 6. Test Pyramid

| Layer | Tool | Location | Feedback loop |
|---|---|---|---|
| Unit | pytest | `src/plcc/**/*_test.py` | TDD inner loop |
| Commands (black-box CLI) | BATS | `tests/bats/commands/` | Pre-commit |
| Integration (adjacent pairs) | BATS | `tests/bats/integration/` | Pre-commit |
| E2E (full pipeline) | BATS | `tests/bats/e2e/` | Pre-commit |

**Unit tests** live alongside their modules in `src/`. Existing plcc-ng tests migrate here. New tests written TDD-first for `plcc.tree`, `plcc.model`, and `plcc.lang.ext.plantuml`.

**Command tests** (`tests/bats/commands/`) — one `.bats` file per command. Covers: entry point is on PATH, `--help` works, required parameters enforced, valid input produces schema-valid output, bad input produces the correct error behavior.

**Integration tests** (`tests/bats/integration/`) — adjacent pipeline pairs. Each pipes one command's output into the next and asserts schema validity plus spot checks on content. Pairs: `plcc-spec | plcc-model`, `plcc-spec | plcc-tokens`, `plcc-tokens | plcc-tree`, `plcc-model | plcc-lang-emit`.

**E2E tests** (`tests/bats/e2e/`) — full pipeline via `plcc-make`. Covers:
- Happy path: `build/spec.json`, `build/model.json`, and `build/diagram/*.puml` all exist and are schema-valid
- In-band error propagation: a malformed input at one stage produces an error record that passes through downstream stages without breaking the pipeline

`tests/fixtures/` holds the trivial grammar and expected outputs.

## 7. Developer Tooling

`bin/` is the single source of truth for all developer actions. Developers, CI, and Claude use the same scripts.

```
bin/
├── install/
│   └── bats.bash            # installs BATS; called by BATS test scripts and devcontainer
├── build/
│   └── package.bash         # pdm build → wheel
└── test/
    ├── units.bash            # pdm install + pytest          ← TDD inner loop
    ├── commands.bash         # bats tests/bats/commands/
    ├── integration.bash      # bats tests/bats/integration/
    ├── e2e.bash              # bats tests/bats/e2e/
    ├── functional.bash       # units + commands + integration + e2e  ← pre-commit
    ├── packaging.bash        # install wheel into fresh venv, check entry points
    └── all.bash              # functional + packaging        ← CI / pre-release
```

- `check-jsonschema` lives in `[dependency-groups].dev`; installed by `pdm install` (already called by `units.bash`)
- BATS is not a Python package; `bin/install/bats.bash` manages its version; each BATS test script calls it at the top
- The devcontainer calls `bin/install/bats.bash` on startup
- Each test script self-installs its own dependencies before running — scripts are usable cold

## 8. CI Pipeline

GitHub Actions on every push to `multi-lang`:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: bin/test/functional.bash

  package:
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: bin/build/package.bash
      - run: bin/test/packaging.bash
```

`test` catches code correctness. `package` catches distribution regressions (entry points not wired up, console scripts missing). If `functional.bash` becomes slow, it splits into parallel jobs — each calls the corresponding `bin/test/*.bash` script directly.

## 9. `plcc-make` Behavior

- Takes an explicit grammar file path as a required positional argument. No default filename, no stdin piping of the grammar file.
- Locates `build/` relative to the current working directory
- Always cleans `build/` before rebuilding — the only behavior in v9
- Validates that `<tool>` from each `% <tool> <language>` semantic section matches `[a-zA-Z0-9_-]+`. No path separators, no `..`, no absolute paths. Errors and stops on violation. Output always goes to `build/<tool>/`.
- Phase 1 uses PlantUML's default `--semantics` behavior (`note`). The `--semantics` flag is wired up in a later phase.

## 10. Phase 1 Acceptance Criteria

These are the acceptance criteria from the implementation plan (§4.4), interpreted against this design:

- `plcc-make tests/fixtures/trivial.plcc` produces `build/spec.json`, `build/model.json`, and `build/diagram/program.puml` (or equivalent)
- The generated `.puml` renders a valid class diagram showing `Program` with a `num` field
- `plcc-plantuml-emit` is discovered via PATH; `plcc-lang-list` finds it
- `plcc-make --help` describes the tool correctly
- CI runs `bin/test/functional.bash` and `bin/test/packaging.bash` on every push to `multi-lang`
- All Level 0 command outputs validate against their JSON schemas
- `bin/test/units.bash` is the TDD inner loop and runs in seconds
