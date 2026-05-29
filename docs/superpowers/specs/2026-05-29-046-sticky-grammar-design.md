# Sticky Grammar Design

**Issue:** 046
**Date:** 2026-05-29

## Problem

When working with a non-default grammar file, specifying `--grammar-file=X` on one
command has no effect on subsequent commands. Each command independently defaults to
`grammar.plcc` when `--grammar-file` is omitted. There is no way to declare "I am
working on `a.plcc`" and have all subsequent commands use `a.plcc` automatically.

## Solution

Treat `build/` as tied to a specific grammar file. Store the active grammar path in
`build/.grammar`. `plcc-make` resolves, records, and enforces the active grammar.
Individual commands stop defaulting to `grammar.plcc` and delegate resolution entirely
to `plcc-make`.

## Grammar Resolution Rules (in `plcc-make`)

1. `--grammar-file` given explicitly → use it
2. `--grammar-file` not given, `build/.grammar` exists → use stored path
3. `--grammar-file` not given, no `build/.grammar` → fall back to `grammar.plcc`

If rule 2 applies and the stored path does not exist on disk → error to stderr, exit 1:

```
plcc-make: grammar file not found: a.plcc
(the active grammar was set by a previous run; use --grammar-file to specify a different one)
```

If rule 1 applies and the explicit path differs from the stored grammar → wipe `build/`
entirely, then rebuild from scratch with the new grammar.

`build/.grammar` is written (or overwritten) after every successful build.

## New Module: `plcc/build/grammar.py`

```python
def read_grammar(build_dir) -> str | None: ...
def write_grammar(build_dir, path: str) -> None: ...
```

Grammar tracking is a distinct concern from staleness; it lives in its own module.

## Changes to `plcc-make`

At the top of `main()`, before the staleness check:

1. Call `read_grammar(build_dir)` → `stored_grammar`
2. Resolve `grammar` using the three rules above
3. If resolved from stored path and file missing → print error to stderr, exit 1
4. If explicit `--grammar-file` given, `stored_grammar` exists, and they differ →
   `shutil.rmtree(build_dir)`, recreate it
5. Proceed with existing staleness check and build pipeline
6. On success: call `write_grammar(build_dir, grammar)` after `write_sentinel`

`plcc-make` emits the resolved grammar via its `STARTED` event:

```python
verbose.emit(Events.STARTED, message=f"grammar: {grammar}")
```

This is a natural future candidate for a verbose(0) informational message (always
displayed), but that change is out of scope here.

## Changes to Commands (`plcc-scan`, `plcc-parse`, `plcc-rep`, `plcc-diagram`)

Four commands need the same treatment:

- Remove `[default: grammar.plcc]` from `--grammar-file` docstring entry; replace with
  a short description of how the flag works (see Docstring below)
- When `args['--grammar-file']` is `None` (user did not give the flag): skip the local
  existence check; do not pass `--grammar-file` to `plcc-make`
- When `args['--grammar-file']` is given: validate locally (file exists), then pass
  `--grammar-file=<path>` to `plcc-make` as before
- Drop the grammar filename from each command's own `STARTED` verbose message;
  `plcc-make` is now the authoritative reporter of which grammar is active

## Docstring Wording for `--grammar-file`

```
--grammar-file=<path>   Grammar to build from. Once set, remembered for subsequent
                        commands until changed. Defaults to grammar.plcc on first use.
```

## Testing

**Unit tests (pytest)**

- `plcc/build/grammar_test.py` (new):
  - `read_grammar` returns `None` when `build/.grammar` is absent
  - `read_grammar` returns the stored path when present
  - `write_grammar` creates/overwrites `build/.grammar` with the correct content

- `make_test.py`:
  - No `--grammar-file`, no `build/.grammar` → resolves to `grammar.plcc`
  - No `--grammar-file`, `build/.grammar` = `a.plcc`, file exists → resolves to `a.plcc`
  - No `--grammar-file`, `build/.grammar` = `a.plcc`, file missing → error to stderr, exit 1
  - Explicit `--grammar-file`, no `build/.grammar` → uses given path, writes `build/.grammar`
  - Explicit `--grammar-file` matches stored → no wipe
  - Explicit `--grammar-file` differs from stored → wipes `build/`, rebuilds

**Bats tests**

- Sticky grammar: run with `--grammar-file=a.plcc`, then run without flag → `a.plcc` used
- Grammar switch: run with `--grammar-file=a.plcc`, then `--grammar-file=b.plcc` →
  `build/` wiped, rebuilt from `b.plcc`
- Missing stored grammar: `build/.grammar` points to nonexistent file → error on stderr
  with `--grammar-file` hint
- No `build/.grammar`, no `--grammar-file` → falls back to `grammar.plcc`
