# plcc-mermaid-diagram-run

Print the path to the rendered Mermaid diagram image.

Called by [`plcc-diagram-run --format=mermaid`](plcc-diagram-run.md).

## Usage

```text
plcc-mermaid-diagram-run --input=FILE [-v ...] [options]
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
plcc-mermaid-diagram-run --input=diagram.png
# /path/to/diagram.png
```
