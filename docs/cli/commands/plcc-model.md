# plcc-model

Transform spec JSON into a language-neutral code model. The model describes
the classes, fields, and inheritance relationships that the language emitter
uses to generate source code.

## Usage

```text
plcc-model [-v ...] [options] [SPEC_JSON]
```

## Arguments and options

| Argument/Option | Description |
|---|---|
| `SPEC_JSON` | Path to spec JSON (output of `plcc-spec`). Use `-` or omit to read from stdin. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Pipe from plcc-spec
plcc-spec spec.plcc | plcc-model

# From a saved spec JSON
plcc-model plcc-ng/spec.json
```
