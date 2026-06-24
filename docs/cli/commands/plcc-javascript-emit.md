# plcc-javascript-emit

Emit a JavaScript interpreter from model JSON. Reads model JSON from stdin and
writes `.js` class files and a `main.js` entry point to the output directory.

Called by [`plcc-lang-emit --target=javascript`](plcc-lang-emit.md).

Requires Node.js 18 or later on `PATH` to run the emitted interpreter.

## Usage

```text
plcc-javascript-emit --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Directory to write generated JavaScript files into. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-javascript-emit --output=build/javascript
```
