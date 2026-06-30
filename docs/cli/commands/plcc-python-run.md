# plcc-python-run

Run a generated Python interpreter. Reads parse tree JSON from stdin and runs
`main.py` in the output directory using the system Python.

Called by [`plcc-lang-run --target=Python`](plcc-lang-run.md).

## Usage

```text
plcc-python-run --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Directory containing generated Python files (from `plcc-python-emit`). Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-python-run --output=plcc-ng/Python
```
