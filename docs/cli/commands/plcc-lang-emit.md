# plcc-lang-emit

Dispatch to the appropriate language emitter. Reads model JSON from stdin
and calls `plcc-<lang>-emit` for the specified target language.

## Usage

```text
plcc-lang-emit [-v ...] --target=LANG --output=DIR
```

## Arguments and Options

| Option | Description |
|---|---|
| `--target=LANG` | Target language (e.g. `Python`, `Java`). Required. |
| `--output=DIR` | Directory to write emitted source files into. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-lang-emit --target=Python --output=build/Python
```

## Language plugins

`plcc-lang-emit` calls `plcc-<lang>-emit` for the target language.
Use [`plcc-lang-list`](plcc-lang-list.md) to see available plugins.
See [Language extensions](../guide/language-extensions.md) for details.
