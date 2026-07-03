# plcc-diagram

Generate all installed diagram types from a PLCC spec file. Discovers and
runs each installed `plcc-diagram-{type}` command in alphabetical order.

## Usage

```text
plcc-diagram [-v ...] [options]
```

## Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-s PATH`, `--spec=PATH` | Spec file. Remembered across invocations. Defaults to `spec.plcc`. |

## Output

| Option | Description |
|---|---|
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |

## Diagnostics

| Option | Description |
|---|---|
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-diagram -s subtract.plcc
```

## Diagram types

`plcc-diagram` discovers installed diagram types by scanning PATH for
`plcc-diagram-{type}` executables. Use [`plcc-diagram-list`](plcc-diagram-list.md)
to see installed formats per type.
See [Diagram extensions](../guide/diagram-extensions.md) for details.
