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
