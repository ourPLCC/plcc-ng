# plcc-diagram-list

List installed diagram format plugins. Scans `PATH` for
`plcc-diagram-*-*-emit` commands and prints each `type/format` pair, one per line.

Requires the `plcc-diagram` package.

## Usage

```text
plcc-diagram-list [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-diagram-list
# class/mermaid
# class/plantuml
```
