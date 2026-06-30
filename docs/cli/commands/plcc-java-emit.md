# plcc-java-emit

Emit a Java interpreter from model JSON. Reads model JSON from stdin and
writes `.java` source files and a `Main.java` entry point to the output
directory.

Called by [`plcc-lang-emit --target=Java`](plcc-lang-emit.md).

## Usage

```text
plcc-java-emit --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Directory to write generated Java files into. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-java-emit --output=plcc-ng/Java
```
