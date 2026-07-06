# Design: Issue 067 — Version Header Prints First

**Date:** 2026-06-05
**Issue:** [067-version-header-prints-first](../issues/done/067-version-header-prints-first.md)

## Problem

The version line introduced in issue 049 is printed after `plcc-make` succeeds. If make
fails (grammar not found, syntax error, etc.) the user sees only an error message with no
version information, making bug reports hard to diagnose.

```
$ plcc-scan
plcc-make: grammar file not found: grammar.plcc
$
```

## Decisions

- **Split the banner into two outputs.** The version line prints unconditionally at
  startup. The grammar path prints only after make succeeds. Together they produce the
  same information as before, but version is never suppressed by an early failure.

- **Version line is first output.** It prints before argument validation, grammar-file
  checks, and the `plcc-make` subprocess — before anything that can fail.

- **stdout for all five orchestrators.** Consistent with issue 039 / issue 049: all
  user-facing output from `plcc-scan`, `plcc-parse`, `plcc-rep`, `plcc-diagram`, and
  `plcc-make` goes to stdout.

- **`--no-banner` flag on all five orchestrators.** When present, both the version line
  and the grammar line are suppressed. Orchestrators pass `--no-banner` to every
  `plcc-make` subprocess they spawn, so the user never sees a double banner. The flag
  is also available to users who want to suppress output when scripting.

- **Lower-level commands are out of scope.** `plcc-spec`, `plcc-tokens`, `plcc-ll1`,
  `plcc-model`, and language-plugin commands do not print a banner and are not changed.

## Output Format

On success the two lines appear in sequence (unchanged from issue 049):

```
plcc-ng 1.2.3
grammar: /abs/path/to/grammar.plcc
```

On early failure only the version line appears:

```
plcc-ng 1.2.3
plcc-make: grammar file not found: grammar.plcc
```

`plcc-rep` adds a third line after the grammar line (unchanged):

```
plcc-ng 1.2.3
grammar: /abs/path/to/grammar.plcc
Running calc with python.
```

## Implementation

### `src/plcc/cmd/output.py`

Replace `print_startup_banner` with two focused functions:

```python
def print_version_line(version):
    print(f"plcc-ng {version}", flush=True)

def print_grammar_line(grammar_path, tool=None, language=None):
    print(f"grammar: {grammar_path}", flush=True)
    if tool is not None and language is not None:
        print(f"Running {tool} with {language}.", flush=True)
```

`print_startup_banner` is removed. All callers are updated.

### All five orchestrators (`scan.py`, `parse.py`, `rep.py`, `diagram.py`, `make.py`)

1. Add `--no-banner` to the docopt options string.
2. Parse it: `no_banner = args['--no-banner']`.
3. As the very first output in `main()` (before any validation or subprocess):
   ```python
   if not no_banner:
       print_version_line(get_version())
   ```
4. After `plcc-make` succeeds:
   ```python
   if not no_banner:
       print_grammar_line(os.path.abspath(read_grammar('build')))
   ```
5. Every `subprocess.run(['plcc-make', ...])` call gains `--no-banner` in its argument
   list.

### `plcc-make` specifics

`plcc-make` resolves the grammar path before spawning any subprocess, so both banner
calls happen early in `main()`:

1. `print_version_line(get_version())` — before arg validation output.
2. `print_grammar_line(grammar)` — immediately after the grammar path is resolved and
   validated (before `plcc-spec` runs).

### `plcc-diagram` specifics

`plcc-diagram` currently prints no banner. It gains the same two-call pattern. After
make succeeds it calls `read_grammar('build')` (already available via
`plcc.build.grammar`) to obtain the grammar path for `print_grammar_line`.

## Testing

All five command test files are updated:

- Assert `print_version_line` output appears in stdout before any error output.
- Assert `print_grammar_line` output appears in stdout on success.
- Assert neither line appears when `--no-banner` is passed.
- Assert the `plcc-make` subprocess call includes `--no-banner`.
- For `rep_test.py`: assert `Running <tool> with <language>.` still appears on success.

Existing banner tests that check for the combined `plcc-ng X.Y.Z  grammar: ...` line are
updated to match the new two-line format.
