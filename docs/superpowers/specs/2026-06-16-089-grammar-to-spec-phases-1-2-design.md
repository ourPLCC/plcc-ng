# Design: Grammar-to-Spec Rename — Phases 1 & 2 (089)

**Date:** 2026-06-16
**Issue:** [089 - Rename "grammar file" to "specification file"](../../../dev-docs/issues/089-grammar-to-spec-rename.md)

## Goal

Rename all user-facing references from "grammar" to "spec" covering:

- CLI flag names (`--grammar`/`-g` → `--spec`/`-s`)
- Default filename (`grammar.plcc` → `spec.plcc`)
- Error messages and help text

This is a hard rename with no backward compatibility — the old flag names and default filename are dropped entirely.

## What the preparatory refactor (PR #205) gives us

The centralization work already merged into `cmd/grammar.py` and `build/grammar.py` means phases 1 and 2 require targeted edits in 5 files rather than scattered changes across all command files.

## Scope

### Files changed

| File | What changes |
| ---- | ------------ |
| `src/plcc/build/grammar.py` | `DEFAULT_GRAMMAR_FILE` value |
| `src/plcc/cmd/grammar.py` | flag name, args key, error text, child flag string |
| `src/plcc/cmd/make.py` | args key, 3 error messages, verbose emit, docstring |
| `src/plcc/cmd/output.py` | banner label |
| `src/plcc/cmd/rep.py` | one error message |

### Not touched

- `src/plcc/cmd/scan.py`, `parse.py`, `diagram.py` — use only the helper functions; cascade automatically from `cmd/grammar.py` changes with no direct edits needed
- `_GRAMMAR_FILE = ".grammar"` — hidden build-dir storage file (internal identifier, phase 4)
- `ll1/Grammar.py` — LL(1) grammar data structure, unrelated to the spec file concept
- `"grammar is not LL(1)"` in `make.py` — refers to grammatical structure, not the file
- Function names `validate_grammar_flag`, `grammar_flag_for_child` in `cmd/grammar.py` — internal identifiers, phase 4

## Specific changes

### `build/grammar.py`

```python
DEFAULT_GRAMMAR_FILE = "spec.plcc"   # was "grammar.plcc"
```

### `cmd/grammar.py`

```python
GRAMMAR_OPTION = f"""\
    -s <path> --spec=<path>
                            Spec to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to {DEFAULT_GRAMMAR_FILE} on first use.
"""

def validate_grammar_flag(cmd_name, args):
    path = args['--spec']                                        # was '--grammar'
    if path is not None and not os.path.exists(path):
        print(f"{cmd_name}: spec file not found: {path}", ...)  # was "grammar file"
        ...

def grammar_flag_for_child(args):
    path = args['--spec']                                        # was '--grammar'
    return [f'--spec={path}'] if path is not None else []       # was '--grammar='
```

### `cmd/make.py`

```python
explicit_grammar = args['--spec']                                # was '--grammar'
# error messages (×2):
print(f"plcc-make: spec file not found: {grammar}", ...)        # was "grammar file"
"use --spec to specify a different one"                          # was '--grammar'
verbose.emit(Events.STARTED, message=f"spec: {grammar}")        # was "grammar:"
# docstring: "Build a PLCC project from a spec file"            # was "grammar file"
```

### `cmd/output.py`

```python
print(f"spec: {grammar_path}", ...)   # was "grammar:"
```

### `cmd/rep.py`

```python
print("plcc-rep: no semantic sections found in spec.", ...)   # was "grammar"
```

## Approach

Single TDD pass: update all test files first to assert new behavior, confirm failures, then implement all changes. One commit per logical module.

## Testing

### Test files to update

- `src/plcc/build/grammar_test.py` — `DEFAULT_GRAMMAR_FILE` assertion expects `"spec.plcc"`
- `src/plcc/cmd/grammar_test.py` — `--spec` flag in `GRAMMAR_OPTION`, args key references, error message text
- `src/plcc/cmd/make_test.py` — any `--grammar` invocations updated to `--spec`

### Verification

Run `bin/test/functional.bash` after implementation to catch any bats tests that match on flag names or error text in the command/integration layers.
