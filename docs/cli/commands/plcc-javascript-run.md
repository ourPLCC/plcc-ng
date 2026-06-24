# plcc-javascript-run

Run a generated JavaScript interpreter. Reads parse tree JSON from stdin and
passes it to `main.js` in the output directory using `node`.

Called by [`plcc-lang-run --target=javascript`](plcc-lang-run.md).

Requires Node.js 18 or later on `PATH`.

## Usage

```text
plcc-javascript-run --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Directory containing generated JavaScript files (from `plcc-javascript-emit`). Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-javascript-run --output=build/javascript
```
