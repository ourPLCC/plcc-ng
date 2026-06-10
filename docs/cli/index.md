# CLI Reference

plcc-ng provides two groups of commands: **Level 2 orchestrators** and
**Level 0 primitives**.

## Level 2 orchestrators

High-level commands for common workflows. These are the commands most users
run day-to-day.

| Command | Purpose |
|---|---|
| [`plcc-make`](orchestrators.md#plcc-make) | Build a PLCC project from a grammar file |
| [`plcc-scan`](orchestrators.md#plcc-scan) | Tokenize source input and print tokens |
| [`plcc-parse`](orchestrators.md#plcc-parse) | Parse source input and print the parse tree |
| [`plcc-rep`](orchestrators.md#plcc-rep) | Read-eval-print loop using generated semantics |

## Level 0 primitives

Low-level commands that each perform one step of the pipeline. They read and
write JSON, making them composable with other tools.

| Command | Purpose |
|---|---|
| [`plcc-spec`](primitives.md#plcc-spec) | Parse and validate a `.plcc` grammar file; emit spec JSON |
| [`plcc-tokens`](primitives.md#plcc-tokens) | Tokenize source files given a spec JSON; emit token JSONL |
| [`plcc-trees`](primitives.md#plcc-trees) | Parse token JSONL using an LL(1) table; emit parse trees |
| [`plcc-model`](primitives.md#plcc-model) | Transform spec JSON into a language-neutral code model |
| [`plcc-lang-emit`](primitives.md#plcc-lang-emit) | Dispatch to the appropriate language emitter |
| [`plcc-diagram`](primitives.md#plcc-diagram) | Generate a class diagram from a grammar file |

## Common options

All commands accept:

| Option | Effect |
|---|---|
| `-h`, `--help` | Show usage and exit |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`) |
| `--verbose-format=FMT` | Verbosity output format: `text` or `json` |

## Grammar memory

The Level 2 orchestrators remember the grammar path between invocations.
Pass `-g <path>` once; subsequent commands in the same directory use the same
grammar automatically.

<!-- TODO: verify grammar memory behavior (sticky grammar) and where it is stored -->
