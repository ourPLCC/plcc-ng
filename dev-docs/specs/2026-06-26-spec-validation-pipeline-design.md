# Spec Validation Pipeline Design

**Issue:** 118 — Spec parser silently accepts `%%{...%%}` instead of `%%%...%%%`, generates bad code
**Date:** 2026-06-26

## Problem

The spec parser silently accepts `%%{` and `%%}` (old or incorrect block delimiters) as if they were valid content, generating malformed output (e.g. a Java file literally named `%%{.java`) instead of reporting a clear error. The user has no indication their spec file contains invalid syntax.

The root cause is systemic: `validate_semantic_spec` (and `validate_syntactic_spec`) exist in the codebase but are never called from the production pipeline — they are dead code outside their own test files. The existing `InvalidClassNameError` check (`^[A-Z][A-Za-z0-9_]*$`) would already reject `%%{`, `%%}`, or any other invalid class name. It simply never runs.

The fix is not to patch `%%{` detection specifically, but to wire the existing validators into the pipeline at the correct levels.

## Design

### The Pipeline Hierarchy

`plcc-make` has four `--through` levels. The fix introduces three new validate commands and slots them into the hierarchy such that each level is a strict superset of the one above it:

| Level | Pipeline |
|---|---|
| `scan` | spec → **validate-lexical** |
| `parse` | spec → **validate-lexical** → **validate-syntactic** → ll1 |
| `model` | spec → **validate-lexical** → **validate-syntactic** → ll1 → **validate-semantic** → model |
| `all` / `rep` | spec → **validate-lexical** → **validate-syntactic** → ll1 → **validate-semantic** → model → emit → build |

The key insight from the existing architecture:

- `plcc-ll1` is a *semantic* validation of the syntactic spec (LL(1) conflict analysis, first/follow sets). It belongs after structural syntactic validation.
- `plcc-validate-syntactic` is a *syntactic* (structural) validation of the syntactic spec (naming, cross-section terminal references). It belongs before `plcc-ll1`.
- `plcc-validate-semantic` is a structural validation of the semantic spec. It belongs before `plcc-model`.
- The lexical section's validation already happens inline during `plcc-spec` parsing; `plcc-validate-lexical` starts thin but establishes the pattern and provides a hook for future checks.

Scanning does not depend on parsing. Parsing does not depend on semantic code. Each validator only runs when its section is needed.

### New Commands

#### `plcc-validate-lexical`

- Reads spec JSON from stdin or a file argument (same interface as `plcc-model`).
- Calls `validate_lexical_spec(lexical_spec)` — a new thin function in `src/plcc/spec/lexical/validate_lexical_spec.py`.
- Initially validates nothing beyond what `plcc-spec` already checked inline; exists to complete the pattern and provide a future hook.
- Exits 0 if valid, 1 with structured error output if not.

#### `plcc-validate-syntactic`

- Reads spec JSON.
- Deserializes `SyntacticSpec` + `LexicalSpec` from JSON (cross-section dependency: `validate_syntactic_spec` checks that terminals used in syntax rules are defined in the lexical spec).
- Calls the existing `validate_syntactic_spec(syntactic_spec, lexical_spec)`.
- Exits 0 if valid, 1 with structured errors.

#### `plcc-validate-semantic`

- Reads spec JSON.
- Deserializes `SemanticSpec` from JSON.
- Calls the existing `validate_semantic_spec(semantic_spec)`.
- Exits 0 if valid, 1 with structured errors.
- This is the primary fix for issue 118: `InvalidClassNameError` now fires for `%%{`, `%%}`, or any class name not matching `^[A-Z][A-Za-z0-9_]*$`. `UndefinedBlockError` fires when a class name line is not immediately followed by a `%%%` block.

### Error Reporting

All three commands follow the same pattern as `plcc-spec`:

```python
errors = validate(spec_json)
if errors:
    for e in errors:
        pos = {"file": e.line.file, "line": e.line.number, "column": e.column}
        kwargs = {"source_line": e.line.string}
        if e.hint:
            kwargs["hint"] = e.hint
        verbose.emit_error(pos, e.kind, **kwargs)
    sys.exit(1)
```

### Deserialization

`plcc-spec` serializes via `dataclasses.asdict()`, which recursively includes all fields — including `Line.string`, `Line.number`, and `Line.file`. Deserialization reconstructs only the fields each validator needs:

- **`plcc-validate-semantic`** — reconstructs `SemanticSpec`: language string, list of `CodeFragment`s each containing a `TargetLocator` (with `Line`) and optional `Block`.
- **`plcc-validate-syntactic`** — reconstructs `SyntacticSpec` (rules) and `LexicalSpec` (rules), enough for cross-section terminal validation.
- **`plcc-validate-lexical`** — no deserialization needed initially; the thin validator works directly with the spec JSON dict.

Each deserializer lives alongside its CLI entry point.

### File Layout

New files:

```
src/plcc/spec/lexical/
  validate_lexical_spec.py          # new thin validator function
  validate_lexical_spec_test.py
  plcc_validate_lexical_cli.py      # plcc-validate-lexical

src/plcc/spec/syntax/
  deserialize.py                    # SyntacticSpec + LexicalSpec from JSON
  deserialize_test.py
  plcc_validate_syntactic_cli.py    # plcc-validate-syntactic

src/plcc/spec/semantics/
  deserialize.py                    # SemanticSpec from JSON
  deserialize_test.py
  plcc_validate_semantic_cli.py     # plcc-validate-semantic

tests/bats/commands/
  plcc-validate-lexical.bats
  plcc-validate-syntactic.bats
  plcc-validate-semantic.bats

tests/bats/e2e/
  bad_block_delimiters.bats         # acceptance test for issue 118
```

### Changes to Existing Files

**`pyproject.toml`** — three new entry points under `[project.scripts]`:

```toml
plcc-validate-lexical   = "plcc.spec.lexical.plcc_validate_lexical_cli:main"
plcc-validate-syntactic = "plcc.spec.syntax.plcc_validate_syntactic_cli:main"
plcc-validate-semantic  = "plcc.spec.semantics.plcc_validate_semantic_cli:main"
```

**`src/plcc/cmd/make.py`** — two changes:

1. Update `_REQUIRED` so `model` subsumes `parse`:

```python
_REQUIRED = {
    'scan':  {'scan'},
    'parse': {'scan', 'parse'},
    'model': {'scan', 'parse', 'model'},   # was {'scan', 'model'}
    'all':   {'scan', 'parse', 'model'} | lang_stage,
}
```

2. Add the three validate commands to the pipeline using `_run_or_die`, at the correct levels:
   - `plcc-validate-lexical` — immediately after `plcc-spec`, for all levels
   - `plcc-validate-syntactic` — before `plcc-ll1`, for `parse`, `model`, `all`
   - `plcc-validate-semantic` — before `plcc-model`, for `model`, `all`

## Testing

**Unit tests for validators** — `validate_lexical_spec_test.py`, and the existing `validate_syntactic_spec_test.py` and `validation_test.py` for semantic. No changes needed to existing validator tests; the fix is wiring, not logic.

**Unit tests for deserializers** — `deserialize_test.py` in each section directory. Verify that spec JSON round-trips correctly into the domain objects, including `None` blocks, missing sections, and `Line` field preservation.

**Bats command tests** — one file per validate command:
- Valid spec → exits 0
- Invalid spec (e.g. `%%{` for semantic, undefined terminal for syntactic) → exits 1 with a message citing file, line, and a readable description

**E2e acceptance test** — `bad_block_delimiters.bats` runs `plcc-make` against a spec containing `%%{...%%}` delimiters and asserts: exits non-zero, error output references the offending line, no `FileNotFoundError` or garbled file names.

**Regression** — all existing unit, command, integration, and e2e tests continue to pass.
