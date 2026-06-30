# plcc-java-build

Compile generated Java source files. Runs `javac` on all `.java` files in the
output directory.

Called by [`plcc-lang-build --target=Java`](plcc-lang-build.md).

Requires Java JDK 21 or later on `PATH`.

## Usage

```text
plcc-java-build --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Directory containing generated Java files (from `plcc-java-emit`). Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-java-build --output=plcc-ng/Java
```
