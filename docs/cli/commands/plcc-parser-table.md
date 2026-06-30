# plcc-parser-table

Table-driven LL(1) parser. Reads token JSONL from stdin and emits parse tree
JSON to stdout. Called by [`plcc-trees --parser=table`](plcc-trees.md)
(this is the default parser).

## Usage

```text
plcc-parser-table [-v ...] [options] --ll1=LL1_JSON
```

## Arguments and Options

| Option | Description |
|---|---|
| `--ll1=LL1_JSON` | Path to LL(1) analysis JSON (output of `plcc-ll1`). Required. |
| `-t`, `--trace` | Emit `parse-step` records tracing predict, shift, and complete events. |
| `--hold-markers` | Emit a hold marker after a trailing extensible parse (used by interactive mode). |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-ll1 > plcc-ng/ll1.json
plcc-tokens plcc-ng/spec.json samples/ | plcc-parser-table --ll1=plcc-ng/ll1.json
```
