# plcc-plantuml-diagram-build

Render a PlantUML diagram source file to a PNG image. Sends the source to the
public `plantuml.com` API and writes the returned PNG to disk. No local
PlantUML installation required.

Called by [`plcc-diagram-build --format=plantuml`](plcc-diagram-build.md).

## Usage

```text
plcc-plantuml-diagram-build --input=FILE --output=FILE [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--input=FILE` | Path to `.puml` PlantUML source file. Required. |
| `--output=FILE` | Path to write PNG image. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-plantuml-diagram-build --input=diagram.puml --output=diagram.png
```
