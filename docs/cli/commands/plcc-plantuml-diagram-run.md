# plcc-plantuml-diagram-run

Print the path to the rendered PlantUML diagram image.

Called by [`plcc-diagram-run --format=plantuml`](plcc-diagram-run.md).

## Usage

```text
plcc-plantuml-diagram-run --input=FILE [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--input=FILE` | Path to PNG image file. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-plantuml-diagram-run --input=diagram.png
# /path/to/diagram.png
```
