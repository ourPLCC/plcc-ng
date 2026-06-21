# plcc-scan

Tokenize source input and print tokens in human-readable format.

## Usage

```text
plcc-scan [-v ...] [options] [SOURCE ...]
```

## Arguments and Options

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to tokenize. Reads stdin if none given. |
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc`. |
| `-t`, `--trace` | Show detailed scanning output including regex candidates and source lines. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Tokenize stdin
echo "42 36 2" | plcc-scan

# Tokenize files
plcc-scan -s subtract.plcc samples/

# After setting spec once, subsequent calls remember it
plcc-scan -s subtract.plcc
plcc-scan samples/
```
