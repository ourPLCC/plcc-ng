# plcc-lang-list

List installed language emitter plugins. Scans `PATH` for `plcc-*-emit`
commands and prints each discovered language name, one per line.

## Usage

```text
plcc-lang-list [-v ...] [options]
```

## Arguments and options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-lang-list
# java
# python
```
