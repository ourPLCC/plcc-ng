# plcc-trees

Dispatch to a parser plugin. Reads token JSONL from stdin and emits parse
tree JSON to stdout. The parser plugin is selected with `--parser`.

## Usage

```text
plcc-trees [-v ...] [options] --ll1=LL1_JSON
```

## Arguments and Options

| Option | Description |
|---|---|
| `--ll1=LL1_JSON` | Path to LL(1) analysis JSON (output of `plcc-ll1`). Required. |
| `--parser=KIND` | Parser plugin to use. Default: `table` (calls `plcc-parser-table`). |
| `-t`, `--trace` | Forward trace flag to the parser plugin. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc > build/spec.json
plcc-spec spec.plcc | plcc-ll1 > build/ll1.json
plcc-tokens build/spec.json samples/ | plcc-trees --ll1=build/ll1.json
```

## Parser plugins

`plcc-trees` calls `plcc-parser-<kind>` for the given `--parser` value.
Use [`plcc-parser-list`](plcc-parser-list.md) to see available plugins.
See [Parser extensions](../guide/parser-extensions.md) for details.
