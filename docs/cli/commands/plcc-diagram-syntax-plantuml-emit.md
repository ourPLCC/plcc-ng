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
