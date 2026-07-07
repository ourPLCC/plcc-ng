# Parser extensions

Parser extensions implement the parsing step. plcc-ng ships with a single
built-in parser: `plcc-parser-table`, an LL(1) table-driven parser.

## How parser extensions plug in

[`plcc-trees`](../commands/plcc-trees.md) dispatches to a parser plugin via
the `--parser=KIND` flag (default: `table`). It calls `plcc-parser-<kind>`,
passing the LL(1) analysis JSON and token JSONL on stdin.

Use [`plcc-parser-list`](../commands/plcc-parser-list.md) to see what is
installed.

> **Note:** there is no dedicated `plcc-parser` dispatch command — `plcc-trees`
> handles dispatch directly.

## plcc-parser-table

The default LL(1) table-driven parser. Reads token JSONL from stdin and the
LL(1) analysis JSON from `--ll1`, emits parse tree JSON to stdout.

| Command | What it does |
| --- | --- |
| [`plcc-parser-table`](../commands/plcc-parser-table.md) | Table-driven LL(1) parse; emits parse tree JSON or error records |

`plcc-parser-table` also supports `--trace`, which emits `parse-step` records
interleaved with the parse tree for debugging.
