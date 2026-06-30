# plcc-java-run

Run a compiled Java interpreter. Reads parse tree JSON from stdin and passes
it to the `Main` class in the output directory.

Called by [`plcc-lang-run --target=Java`](plcc-lang-run.md).

Requires Java JDK 21 or later on `PATH`.

## Usage

```text
plcc-java-run --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Directory containing compiled Java class files. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-java-run --output=plcc-ng/Java
```
