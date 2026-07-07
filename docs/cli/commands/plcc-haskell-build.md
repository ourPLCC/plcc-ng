# plcc-haskell-build

Build a generated Haskell interpreter with cabal. Runs `cabal build` in the
output directory.

Called by [`plcc-lang-build --target=Haskell`](plcc-lang-build.md).

Requires GHC 9.4 or later and cabal 3.0 or later on `PATH`.

## Usage

```text
plcc-haskell-build --output=DIR [-v ...] [options]
```

## Arguments and options

| Option | Description |
|---|---|
| `--output=DIR` | Directory containing generated Haskell files (from `plcc-haskell-emit`). Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-haskell-build --output=plcc-ng/Haskell
```
