# plcc-diagram-class

Generate and display a class diagram from a PLCC spec file. Shows the classes
and inheritance relationships derived from the syntactic grammar.

Requires the `plcc-diagram` package.

## Usage

```text
plcc-diagram-class [-v ...] [options]
```

## Arguments and options

| Option | Description |
|---|---|
| `-s PATH`, `--spec=PATH` | Spec file. Remembered across invocations. Defaults to `spec.plcc`. |
| `--format=FMT` | Diagram format plugin to use. Default: `plantuml`. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-diagram-class -s subtract.plcc
```

## Diagram formats

`plcc-diagram-class` dispatches to diagram extension plugins via `--format`.
Use [`plcc-diagram-list`](plcc-diagram-list.md) to see installed formats.
See [Diagram extensions](../guide/diagram-extensions.md) for details.
