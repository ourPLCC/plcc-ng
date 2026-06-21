# plcc-rep

REPL — read, eval, print loop for a PLCC spec. Scans and parses source input,
then evaluates it using the generated semantics.

## Usage

```text
plcc-rep [-v ...] [options] [SOURCE ...]
```

## Arguments and Options

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to evaluate. Omit (or pass `-`) to enter interactive mode. |
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc`. |
| `-b`, `--banner` | Print the plcc-ng version, spec path, and target language to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
# Evaluate files and exit
plcc-rep -s subtract.plcc samples/

# Enter interactive mode
plcc-rep -s subtract.plcc
```

## Interactive mode

When no source files are given and stdin is a terminal, `plcc-rep` reads
input at a `>>>` prompt. After each line, complete sentences are evaluated
and their results printed. Continuation prompts (`...`) appear when the input
so far is a valid prefix.

- Press `^D` at the `>>>` prompt (empty buffer) to exit.
- Press `^D` at the `...` prompt to force-submit the buffered input and return to `>>>`.
