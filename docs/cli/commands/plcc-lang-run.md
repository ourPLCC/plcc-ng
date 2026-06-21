# plcc-lang-run

Dispatch to the appropriate language runner. Reads parse tree JSON from stdin
and calls `plcc-<lang>-run` for the target language.

## Usage

```text
plcc-lang-run --target=LANG --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--target=LANG` | Target language (e.g. `Python`, `Java`). Required. |
| `--output=DIR` | Directory containing built artifacts. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-lang-run --target=Python --output=build/Python
```
