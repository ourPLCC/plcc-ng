# plcc-parser-list

List installed parser plugins. Scans `PATH` for `plcc-parser-*` commands
and prints each discovered parser kind, one per line.

## Usage

```text
plcc-parser-list [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-parser-list
# table
```
