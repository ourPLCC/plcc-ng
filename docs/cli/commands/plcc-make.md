# plcc-make

Build a PLCC project from a spec file. Runs the full pipeline — spec parsing,
LL(1) analysis, code model generation, language emit, and language build —
stopping at the stage specified by `--through`.

Called internally by `plcc-scan`, `plcc-parse`, `plcc-rep`, and `plcc-diagram`.
You can also call it directly to pre-build before running other commands.

## Usage

```text
plcc-make [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc` on first use. |
| `--through=LEVEL` | Build up to this level: `scan`, `parse`, `model`, or `all`. Default: `all`. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Build everything
plcc-make -s subtract.plcc

# Rebuild after editing the spec (spec remembered from previous run)
plcc-make

# Build only through the scan stage
plcc-make --through=scan
```

## Build levels

| `--through` value | Stages run |
|---|---|
| `scan` | `plcc-spec` |
| `parse` | `plcc-spec`, `plcc-ll1` |
| `model` | `plcc-spec`, `plcc-model` |
| `all` (default) | `plcc-spec`, `plcc-ll1`, `plcc-model`, `plcc-lang-emit`, `plcc-lang-build` |

`plcc-make` caches its output in `plcc-ng/` and skips stages whose inputs
haven't changed since the last successful run.
