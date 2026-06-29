# plcc-diagram-emit

Dispatch model JSON to the appropriate diagram emitter. Reads model JSON from
stdin and calls `plcc-diagram-<type>-<fmt>-emit` for the specified type and format.

Requires the `plcc-diagram` package.

## Usage

```text
plcc-diagram-emit --type=TYPE [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--type=TYPE` | Diagram type (e.g., `class`). Required. |
| `--format=FMT` | Diagram format plugin to use. Default: `plantuml`. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-diagram-emit --type=class --format=plantuml
```
