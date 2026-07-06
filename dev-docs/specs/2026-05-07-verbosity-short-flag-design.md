# Design: Replace `--verbose=LEVEL` with `-v` counting flag

**Date:** 2026-05-07
**Issue:** [docs/issues/004-verbosity-short-flag.md](../issues/done/004-verbosity-short-flag.md)

## Summary

Replace `--verbose=LEVEL` with the conventional `-v` / `-vv` / `-vvv` counting style across all PLCC commands. `--verbose-format=FMT` is unchanged.

| User types | Verbosity level |
|------------|-----------------|
| (nothing)  | 0 |
| `-v`       | 1 |
| `-vv`      | 2 |
| `-v -v`    | 2 |
| `-vvv`     | 3 |
| `-v -v -v` | 3 |

`--verbose=LEVEL` is removed entirely — no alias, no deprecation shim.

## Architecture

All changes flow from a single shared module. No command needs bespoke logic.

### `src/plcc/verbose.py`

**`VERBOSE_OPTIONS`** — replace the `--verbose=LEVEL` line:

```
    -v                      Increase verbosity (may repeat: -v, -vv, -vvv for levels 1–3).
    --verbose-format=FMT    Output format: text or json [default: text].
```

**`VerboseContext.from_args()`** — read `-v` count (docopt-ng returns an int for counted options):

```python
level = int(args.get("-v") or 0)
```

**`child_flags()`** — emit repeated `-v` instead of `--verbose=N`:

```python
return ['-v'] * self.level + [f'--verbose-format={self.fmt}']
```

**`child_flags_for_orchestrator()`** — same pattern:

```python
level = max(self.level, min_level or 0)
return ['-v'] * level + ['--verbose-format=json']
```

### 22 CLI usage lines

Every CLI that uses `VERBOSE_OPTIONS` must add `[-v ...]` to its `Usage:` line. The `...` is the docopt-ng syntax for a repeatable option; without it docopt treats `-v` as a boolean toggle, not a counter. Example:

```
    plcc-scan [-v ...] [options] GRAMMAR [SOURCE ...]
```

Full list of files requiring this change:

- `src/plcc/cmd/make.py`
- `src/plcc/cmd/parse.py`
- `src/plcc/cmd/rep.py`
- `src/plcc/cmd/scan.py`
- `src/plcc/diagram/dispatch.py`
- `src/plcc/diagram/list.py`
- `src/plcc/diagram/plantuml/emit.py`
- `src/plcc/lang/build.py`
- `src/plcc/lang/emit.py`
- `src/plcc/lang/ext/java/build.py`
- `src/plcc/lang/ext/java/emit.py`
- `src/plcc/lang/ext/java/run.py`
- `src/plcc/lang/ext/python/emit.py`
- `src/plcc/lang/ext/python/run.py`
- `src/plcc/lang/list.py`
- `src/plcc/lang/run.py`
- `src/plcc/ll1/ll1_cli.py`
- `src/plcc/model/model_cli.py`
- `src/plcc/parser/list_cli.py`
- `src/plcc/parser/table_cli.py`
- `src/plcc/spec/plcc_spec_cli.py`
- `src/plcc/tokens/tokens_cli.py`
- `src/plcc/tree/tree_cli.py`

## Tests

### Unit tests (`src/plcc/verbose_test.py`)

- Args dicts change from `{"--verbose": "2"}` to `{"-v": 2}` (docopt-ng returns int for counted options, not string).
- Assertions on `child_flags()` / `child_flags_for_orchestrator()` output change from checking `"--verbose=N"` to checking `"-v"` repeated N times.

### CLI unit tests

- `src/plcc/ll1/ll1_cli_test.py`: argv entries `--verbose=1`, `--verbose=2` → `-v`, `-vv`.
- `src/plcc/lang/ext/java/emit_test.py`: `--verbose=1` → `-v`.

### Bats integration/command tests

Every `--verbose=N` in bats files changes to the equivalent `-v` repetition:

- `tests/bats/commands/plcc-parser-table.bats`
- `tests/bats/commands/plcc-java-emit.bats`
- `tests/bats/commands/plcc-parser-list.bats`
- `tests/bats/commands/plcc-scan.bats`
- `tests/bats/commands/plcc-tree.bats`
- `tests/bats/commands/plcc-ll1.bats`
- `tests/bats/commands/plcc-make.bats`
- `tests/bats/commands/plcc-parse.bats`
- `tests/bats/commands/plcc-python-emit.bats`
- `tests/bats/commands/plcc-rep.bats`

Bats tests that verify `--verbose` is accepted become tests that verify `-v` is accepted.

## Error handling

Mixing `-v` with a no-longer-existing `--verbose=N` is a non-issue: `--verbose` is removed from the docopt schema, so docopt rejects it as an unknown option with a usage error. No special handling needed.

## Constraints

- `--verbose-format=FMT` is unchanged.
- No deprecation shim for `--verbose=LEVEL` — it disappears cleanly.
- The change must be applied to all 22 CLIs at once; a partial rollout would create inconsistency (per the issue's own requirement).
