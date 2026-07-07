# plcc-python-emit

Emit a Python interpreter from model JSON. Reads model JSON from stdin and
writes `.py` class files and a `main.py` entry point to the output directory.

Called by [`plcc-lang-emit --target=Python`](plcc-lang-emit.md).

## Usage

```text
plcc-python-emit --output=DIR [-v ...] [options]
```

## Arguments and options

| Option | Description |
|---|---|
| `--output=DIR` | Directory to write generated Python files into. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-python-emit --output=plcc-ng/Python
```
