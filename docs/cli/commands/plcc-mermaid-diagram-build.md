# plcc-mermaid-diagram-build

Render a Mermaid diagram source file to a PNG image using `mmdc`.

Called by [`plcc-diagram-build --format=mermaid`](plcc-diagram-build.md).

Requires `mmdc` on `PATH`: `npm install -g @mermaid-js/mermaid-cli`.

## Usage

```text
plcc-mermaid-diagram-build --input=FILE --output=FILE [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--input=FILE` | Path to `.mmd` Mermaid source file. Required. |
| `--output=FILE` | Path to write PNG image. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-mermaid-diagram-build --input=diagram.mmd --output=diagram.png
```
