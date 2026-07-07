# Design: Grammar CLI Refactor (089 preparatory)

**Date:** 2026-06-16
**Issue:** Preparatory refactor for [089 - Rename "grammar file" to "specification file"](../../../dev-docs/issues/089-grammar-to-spec-rename.md)

## Goal

Centralize the scattered `--grammar`/`-g` CLI option text, validation logic, default file name, and path resolution before the user-facing rename in issue 089. No functional or behavioral changes for the user — same flags, same defaults, same error messages. The `--help` formatting for `plcc-scan` and `plcc-parse` changes cosmetically: those two commands previously had the grammar option description inline on the same line; after the refactor they use the same two-line format as the other three commands.

## Motivation

Five command files (`make.py`, `scan.py`, `parse.py`, `rep.py`, `diagram.py`) each independently inline:
- The `--grammar/-g` docopt option text
- A file-exists validation block (4 of the 5)
- A `[f'--grammar={path}'] if path else []` expression (4 of the 5)

And `make.py` inlines the `explicit → stored → 'grammar.plcc'` resolution chain with the default file name as a bare string literal.

Without this refactor, the follow-on rename would require scattered edits across all five files. With it, the rename becomes targeted changes in two modules.

## Approach

Split by concern (mirrors the existing `VERBOSE_OPTIONS` / `VerboseContext` pattern):
- `build/grammar.py` — storage and path resolution (build-level concerns)
- New `cmd/grammar.py` — CLI option text and arg validation (cmd-level concerns)

## Design

### `build/grammar.py` additions

```python
DEFAULT_GRAMMAR_FILE = "grammar.plcc"

def resolve_grammar_path(explicit, stored):
    if explicit is not None:
        return explicit
    elif stored is not None:
        return stored
    else:
        return DEFAULT_GRAMMAR_FILE
```

`resolve_grammar_path` takes the already-read `stored` value rather than `build_dir` to avoid double-reading the stored file. `make.py` already reads it and needs it separately for the "stored file missing" hint error and the "grammar changed, wipe build" logic — the function owns only the 3-way selection.

### New `cmd/grammar.py`

```python
import os
import sys

from plcc.build.grammar import DEFAULT_GRAMMAR_FILE

GRAMMAR_OPTION = f"""\
    -g <path> --grammar=<path>
                            Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to {DEFAULT_GRAMMAR_FILE} on first use."""

def validate_grammar_flag(cmd_name, args):
    path = args['--grammar']
    if path is not None and not os.path.exists(path):
        print(f"{cmd_name}: grammar file not found: {path}", file=sys.stderr)
        sys.exit(1)

def grammar_flag_for_child(args):
    path = args['--grammar']
    return [f'--grammar={path}'] if path is not None else []
```

`GRAMMAR_OPTION` references `DEFAULT_GRAMMAR_FILE` so the help text always matches the actual default. `validate_grammar_flag` takes `cmd_name` so each command's error prefix stays accurate.

### `scan.py`, `parse.py`, `rep.py`, `diagram.py`

Each file:
- Imports `GRAMMAR_OPTION`, `validate_grammar_flag`, `grammar_flag_for_child` from `plcc.cmd.grammar`
- Replaces the inline `--grammar/-g` option text in its docstring with `+ GRAMMAR_OPTION`
- Replaces the inline file-exists block with `validate_grammar_flag('plcc-xxx', args)`
- Replaces the inline flag expression with `grammar_flag_for_child(args)`

### `make.py`

- Imports `resolve_grammar_path`, `DEFAULT_GRAMMAR_FILE` from `plcc.build.grammar`
- Imports `GRAMMAR_OPTION` from `plcc.cmd.grammar`
- Replaces the inline `--grammar/-g` option text in its docstring with `+ GRAMMAR_OPTION`
- Replaces the 3-way `if/elif/else` selection with `resolve_grammar_path(explicit_grammar, stored_grammar)`
- Does **not** use `validate_grammar_flag` or `grammar_flag_for_child` — its validation is more complex (two distinct error messages) and it does not forward `--grammar` to a single child in the same pattern

## What this does NOT touch

- Flag names (`--grammar`, `-g`)
- Default file name in user-visible text
- Error message strings
- Banner output
- Docs
- `ll1/Grammar.py` (LL(1) grammar data structure — unrelated to the spec file concept)

Those are all reserved for issue 089.

## Testing

New unit tests are added for the two new modules:

- `src/plcc/build/grammar_test.py` — 3 tests covering each branch of `resolve_grammar_path`
- `src/plcc/cmd/grammar_test.py` — tests covering `GRAMMAR_OPTION`, `validate_grammar_flag`, and `grammar_flag_for_child`

The existing bats command and integration tests cover the end-to-end behavior without modification, confirming no behavioral regression.
