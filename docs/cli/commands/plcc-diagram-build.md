# plcc-diagram-build

Dispatch to the appropriate diagram build step. Calls
`plcc-diagram-<fmt>-build` for the specified format, converting a diagram
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
