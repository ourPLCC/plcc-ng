# plcc-mermaid-diagram-emit

Emit a Mermaid class diagram from model JSON. Reads model JSON from stdin
and writes a Mermaid `classDiagram` source to stdout.

Called by [`plcc-diagram-emit --format=mermaid`](plcc-diagram-emit.md).

## Usage

```text
plcc-mermaid-diagram-emit [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-mermaid-diagram-emit > diagram.mmd
```
