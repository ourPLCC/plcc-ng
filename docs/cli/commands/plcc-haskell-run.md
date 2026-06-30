# plcc-haskell-run

Run a generated Haskell interpreter. Reads parse tree JSON from stdin and
passes it to the interpreter via `cabal run interpreter` in the output
directory.

Called by [`plcc-lang-run --target=Haskell`](plcc-lang-run.md).

Requires cabal 3.0 or later on `PATH`. Run
[`plcc-haskell-build`](plcc-haskell-build.md) before running.

## Usage

```text
plcc-haskell-run --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Directory containing built Haskell files (from `plcc-haskell-build`). Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-haskell-run --output=plcc-ng/Haskell
```
