# plcc-lang-build

Dispatch to the appropriate language build step. Calls `plcc-<lang>-build`
for the target language. If no build command is found, exits silently with
success — not all languages require a build step (Python does not).

## Usage

```text
plcc-lang-build [-v ...] --target=LANG --output=DIR
```

## Arguments and options

| Option | Description |
|---|---|
| `--target=LANG` | Target language (e.g. `Python`, `Java`). Required. |
| `--output=DIR` | Output directory (already populated by `plcc-lang-emit`). Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-lang-build --target=Java --output=plcc-ng/Java
```
