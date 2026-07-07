# plcc-tokens

Tokenize source files given a spec JSON file; emit token JSONL (one JSON
record per line, each record representing a token, skip, or error).

## Usage

```text
plcc-tokens [-v ...] [options] SPEC_JSON [SOURCE ...]
```

## Arguments and options

| Argument/Option | Description |
|---|---|
| `SPEC_JSON` | Path to spec JSON (output of `plcc-spec`). |
| `SOURCE` | Source files to tokenize. Use `-` for stdin. Defaults to stdin. |
| `-t`, `--trace` | Include regex candidates, source lines, and skip records in output. |
| `--source-name=LABEL` | Override the source label used for stdin. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Tokenize stdin using a spec JSON piped from plcc-spec
plcc-spec spec.plcc | plcc-tokens - samples/

# Save spec JSON first, then tokenize
plcc-spec spec.plcc > plcc-ng/spec.json
plcc-tokens plcc-ng/spec.json samples/
```
