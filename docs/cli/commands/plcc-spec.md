# plcc-spec

Parse, validate, and print a PLCC grammar file as JSON.

## Usage

```text
plcc-spec [-v ...] [options] FILE
```

## Arguments and Options

| Argument/Option | Description |
|---|---|
| `FILE` | PLCC grammar file (`.plcc`). Use `-` to read from stdin. |
| `--no-json` | Validate only; do not print JSON to stdout. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Parse and print spec as JSON
plcc-spec spec.plcc

# Validate only (no output on success)
plcc-spec --no-json spec.plcc

# Pipe into another command
plcc-spec spec.plcc | plcc-ll1
```
