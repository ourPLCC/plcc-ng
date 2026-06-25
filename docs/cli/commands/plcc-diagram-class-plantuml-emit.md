# plcc-diagram-class-plantuml-emit

Emit a PlantUML class diagram from model JSON. Reads model JSON from stdin
and writes PlantUML source to stdout (or to a file if `--output` is given).

Called by [`plcc-diagram-emit --type=class --format=plantuml`](plcc-diagram-emit.md).

## Usage

```text
plcc-diagram-class-plantuml-emit [--output=DIR] [-v ...] [options]
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
plcc-spec spec.plcc | plcc-model | plcc-diagram-class-plantuml-emit > diagram.puml
```
