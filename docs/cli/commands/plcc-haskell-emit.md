# plcc-haskell-emit

Emit a Haskell interpreter from model JSON. Reads model JSON from stdin and
writes `.hs` source files and an `interpreter.cabal` project file to the
output directory.

Called by [`plcc-lang-emit --target=Haskell`](plcc-lang-emit.md).

Requires GHC 9.4 or later and cabal 3.0 or later on `PATH` to build and run
the emitted interpreter.

## Usage

```text
plcc-haskell-emit --output=DIR [-v ...] [options]
```

## Arguments and options

| Option | Description |
|---|---|
| `--output=DIR` | Directory to write generated Haskell files into. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-haskell-emit --output=plcc-ng/Haskell
```

See the [Haskell language guide](../../language-guide/languages/haskell.md) for
how to write Haskell semantic sections.
