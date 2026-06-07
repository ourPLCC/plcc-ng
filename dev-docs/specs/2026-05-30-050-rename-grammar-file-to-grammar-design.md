# Design: Rename --grammar-file to --grammar (issue 050)

**Date:** 2026-05-30
**Issue:** 050
**Type:** refactor

## Summary

Rename the `--grammar-file` flag to `--grammar` across all commands that accept it, and add `-g` as a short form. Clean break — no deprecated alias.

## Scope

Five commands are affected:

- `plcc-make` ([src/plcc/cmd/make.py](src/plcc/cmd/make.py))
- `plcc-scan` ([src/plcc/cmd/scan.py](src/plcc/cmd/scan.py))
- `plcc-parse` ([src/plcc/cmd/parse.py](src/plcc/cmd/parse.py))
- `plcc-rep` ([src/plcc/cmd/rep.py](src/plcc/cmd/rep.py))
- `plcc-diagram` ([src/plcc/cmd/diagram.py](src/plcc/cmd/diagram.py))

## Changes per command

In each command source file:

1. Docopt usage string: `--grammar-file=<path>` → `-g <path>` / `--grammar=<path>`
2. Key lookup: `args['--grammar-file']` → `args['--grammar']`
3. Error messages mentioning `--grammar-file` → `--grammar` (long form only)
4. Forwarded flag strings: `f'--grammar-file={grammar_file}'` → `f'--grammar={grammar_file}'`

## What is NOT changed

Prose strings that describe the concept ("grammar file not found", `UndefinedTerminalError` message) are left alone — they describe a file, not the flag.

## Tests

All test references to `--grammar-file` are updated to `--grammar` or `-g`, maintaining the existing style of each file:

- Unit tests: `src/plcc/cmd/make_test.py`, `rep_test.py`, `diagram_test.py`
- Bats command tests: `tests/bats/commands/plcc-make.bats`, `plcc-scan.bats`, `plcc-parse.bats`, `plcc-rep.bats`, `plcc-diagram.bats`
- Bats integration tests: `tests/bats/integration/plcc-parse-errors.bats`
- Bats e2e tests: `tests/bats/e2e/happy-path.bats`, `tests/bats/e2e/plcc-rep.bats`

## Approach

All five commands and all their tests are updated in a single commit. This is a mechanical rename with no behavioral change — no red-green cycle per command is needed.

## Backward compatibility

None. `--grammar-file` stops working immediately. The project is experimental; no deprecation alias is introduced.
