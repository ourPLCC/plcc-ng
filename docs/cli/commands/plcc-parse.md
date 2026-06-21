# plcc-parse

Parse source input and print the parse tree in human-readable format.

## Usage

```text
plcc-parse [-v ...] [options] [SOURCE ...]
```

## Arguments and Options

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to parse. Reads stdin if none given. |
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc`. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Parse stdin
echo "42 36 2" | plcc-parse

# Parse files
plcc-parse -s subtract.plcc samples/
```

## Interactive mode

When no source files are given and stdin is a terminal, `plcc-parse` reads
input at a `>>>` prompt. After each line, complete sentences are parsed and
printed immediately. If the input so far is a valid prefix that could be
extended (e.g., `3` in a grammar that also accepts `3 + 4`), parsing is
deferred and a `...` continuation prompt appears.

- Press `^D` at the `>>>` prompt (empty buffer) to exit.
- Press `^D` at the `...` prompt to force-submit the buffered input and return to `>>>`.
