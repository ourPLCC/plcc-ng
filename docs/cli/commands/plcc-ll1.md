# plcc-ll1

Perform LL(1) analysis on a grammar spec. Reads spec JSON from stdin and
emits LL(1) analysis JSON to stdout, including FIRST sets, FOLLOW sets,
PREDICT sets, any conflicts, and any left-recursion cycles.

## Usage

```text
plcc-ll1 [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). Higher verbosity emits FIRST/FOLLOW/PREDICT sets and conflict details. |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Analyse a spec and print LL(1) JSON
plcc-spec spec.plcc | plcc-ll1

# Save to file for use with plcc-trees
plcc-spec spec.plcc | plcc-ll1 > build/ll1.json
```
