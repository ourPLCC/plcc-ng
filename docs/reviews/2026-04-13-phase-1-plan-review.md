# Phase 1 Plan Review

**Date:** 2026-04-13
**Reviewer:** Independent agent review
**Documents reviewed:**
- `docs/design/2026-04-13-phase-1-walking-skeleton.md`
- `docs/plans/2026-04-13-phase-1-walking-skeleton.md`
**Reference documents:**
- `docs/design/2026-04-12-multi-lang-pipeline.md` (architectural spec)
- `docs/design/2026-04-12-multi-lang-implementation-plan.md` (roadmap)

**Verdict:** Not ready to execute as written. Blockers require targeted fixes to the plan before implementation begins. The overall architecture, test pyramid design, and phasing strategy are sound.

---

## BLOCKERS — must be resolved before execution

### B1: `build_model.py` uses a fictional `"kind"` key (Task 10)

`build_model.py`'s `_extract_fields` function inspects `rhs` symbols using `symbol.get('kind', '')` and checks `'capturing' in kind`. When `plcc-spec` serializes the spec via `dataclasses.asdict()`, a `CapturingTerminal` object serializes to:

```json
{"name": "NUM", "altName": null, "isTerminal": true, "isCapturing": true}
```

There is no `kind` field. The plan's unit tests pass because they use hand-crafted dicts with a `"kind"` key — but `plcc-spec tests/fixtures/trivial.plcc | plcc-model -` will silently produce zero fields because no real symbol matches `'capturing' in kind`.

**Consequence:** Unit tests pass, integration and E2E tests fail. The acceptance criterion (`Program` class with `num` field) will not be met.

**Fix:** Before writing `build_model.py`, run `plcc-spec tests/fixtures/trivial.plcc` and record the actual serialized shape of `rhs` symbols. Then implement `_extract_fields` using the actual flags:

```python
def _extract_fields(rhs):
    fields = []
    for symbol in rhs:
        if symbol.get('isCapturing') and symbol.get('isTerminal'):
            field_name = symbol.get('altName') or symbol.get('name', '').lower()
            fields.append({'name': field_name, 'type': 'Token'})
        elif symbol.get('isCapturing') and not symbol.get('isTerminal'):
            field_name = symbol.get('altName') or symbol.get('name', '').lower()
            field_type = symbol.get('name', 'Object')[:1].upper() + symbol.get('name', 'Object')[1:]
            fields.append({'name': field_name, 'type': field_type})
    return fields
```

A discovery step should be added to Task 10 before writing the implementation: run `plcc-spec` on the trivial grammar, inspect the actual JSON output, and confirm the symbol structure before writing any model code against it.

---

### B2: `plcc-tree --spec` contract is unresolved (Task 9)

The `tree_cli_test.py` test passes a **raw grammar file** to `--spec`:

```python
run_main(['--spec=tests/fixtures/trivial.plcc'])
```

The docstring in `tree_cli.py` says:

```
--spec=SPEC_JSON   Path to spec JSON file (output of plcc-spec).
```

The architectural spec §5 also states `plcc-tree` takes `spec JSON path`. These three things disagree. The BATS integration test `tokens-tree.bats` correctly passes spec JSON, creating an internal contradiction within the plan.

**Fix:** Decide and document the contract. The architectural spec is clear: `--spec` takes the spec JSON path (output of `plcc-spec`). Update the unit test to match, and ensure `tree_cli.py` actually loads spec JSON at the path if it needs the grammar structure. For the Phase 1 minimal implementation (which ignores spec content), the `--spec` argument can be accepted but unused — but the test must pass spec JSON, not a grammar file.

---

### B3: Dead `with open` block in `plcc-make` (Task 15)

In the `plcc-make` implementation, the following block is present:

```python
with open(model_json) as model_f:
    _run_or_die(
        ['plcc-lang-emit', f'--target={lang}', f'--output={output_dir}'],
        stdin_file=model_json,
    )
```

`model_f` is never used. `_run_or_die` opens `model_json` independently via `stdin_file=`. The `with open` block creates a confusing double-open and should be removed.

**Fix:**

```python
_run_or_die(
    ['plcc-lang-emit', f'--target={lang}', f'--output={output_dir}'],
    stdin_file=model_json,
)
```

---

### B4: `--cov=plccng` not updated in Task 3

`pyproject.toml` contains:

```toml
[tool.pdm.scripts]
test = "pytest -qq -rfEsxXP --cov=plccng --cov-branch --cov-report term-missing:skip-covered"
```

Task 3 does not include a step to update `--cov=plccng` to `--cov=plcc`. After the rename, running `bin/test/units.bash` (which calls `pdm test`) will either fail or report 0% coverage against a non-existent module.

**Fix:** Add a step to Task 3:

```bash
sed -i '' 's/--cov=plccng/--cov=plcc/g' pyproject.toml
```

---

### B5: No tasks retire `scan/scan_cli.py`, `scan/json_formatter.py`, and their tests

The roadmap §9.2 explicitly states: "Tests that are temporarily broken by Phase 1 work are either migrated or deleted in that same phase. Tests should not be skipped indefinitely."

After Phase 1, the following files from the old `plccng.scan` package remain active with passing tests, but they test an interface that no longer aligns with the pipeline:

- `src/plcc/scan/scan_cli.py` — old CLI that reads raw grammar file, outputs formatted tokens
- `src/plcc/scan/scan_cli_test.py` — tests the old interface
- `src/plcc/scan/json_formatter.py` — produces multi-line JSON with uppercase keys (incompatible with `token.schema.json`)
- `src/plcc/scan/json_formatter_test.py` — tests the old format
- `src/plcc/scan/text_formatter.py` — text formatter, superseded
- `src/plcc/scan/text_formatter_test.py`

**Fix:** Add a task (before Task 8) that inventories these files, migrates any test coverage worth keeping into the new `plcc.tokens` tests, and deletes the rest. The new `plcc-tokens` JSONL output is tested in `tokens_cli_test.py` and `jsonl_formatter_test.py` — the old formatters are not needed.

---

### B6: No tasks retire `spec/spec_cli.py` and `spec/spec_cli_test.py`

The plan adds `plcc_spec_cli.py` alongside the existing `spec_cli.py` without retiring the old one. After Phase 1, both exist and both have passing tests. The old `spec_cli.py` tests the subcommand interface (`run(['spec', FILE])`); the new `plcc_spec_cli.py` tests the standalone interface.

**Fix:** Add a task (after Task 7) to either:
- Delete `spec_cli.py` and `spec_cli_test.py` if the `plcc_cli.py` dispatcher is also being removed, or
- Update `spec_cli.py` to delegate to `plcc_spec_cli.main()` (making it a thin wrapper) if the `plcc spec` subcommand is being kept.

Also clarify what happens to `plcc_cli.py` (the renamed `plccng_cli.py`): it currently dispatches `plcc spec` and `plcc scan`. As standalone commands are added, the subcommand CLI becomes redundant. The plan should state explicitly whether it is kept or removed in Phase 1.

---

## CONCERNS — should be addressed but won't stop work

### C1: Trivial grammar mismatch between design doc §3 and plan Task 5

Design doc §3 shows `% plantuml PlantUML` as the semantic divider. Task 5 uses `% diagram PlantUML`. The plan's choice is correct (tool name `diagram` produces `build/diagram/` matching the acceptance criterion). The design doc §3 should be corrected.

### C2: `capitalize()` corrupts camelCase rule names

`_build_classes` uses `lhs_name.capitalize()` which lowercases everything after the first character. `addExpr` → `Addexpr` (wrong); `program` → `Program` (correct for the trivial grammar only). Fix: `lhs_name[:1].upper() + lhs_name[1:]`.

### C3: `spec_loader.py` duplicates `LexicalRule`

`spec_loader.py` defines a private `_LexicalRule` dataclass with `name`, `pattern`, `isSkip` fields — the same fields as `plcc.spec.lexical.LexicalRule`. Consider whether `spec_loader` can import and instantiate `LexicalRule` directly from the spec package, or document why a copy is preferable (e.g. avoiding circular imports).

### C4: `plcc-tree` silently ignores `--spec` in Phase 1 implementation

The minimal `tree_cli.py` accepts `--spec=SPEC_JSON` but never reads it. This is intentional for Phase 1 but should be documented with a comment:

```python
# Phase 1: --spec is accepted for interface compatibility but not yet used.
# The minimal implementation wraps each token in a tree record unconditionally.
# Phase 2 will implement a real LL(1) parser using the spec.
```

### C5: `plcc-plantuml-emit` emits one file per class

For the trivial grammar (one class), this produces one file. For any grammar with multiple classes, it produces N separate one-class `.puml` files rather than one class hierarchy diagram. The design choice (one file per class vs. one combined diagram) should be made explicitly and documented in `emit.py`.

### C6: `plcc-make` lets `ValueError` propagate as a raw traceback

`validate_tool_name` raises `ValueError` but `main()` does not catch it. A grammar with an invalid tool name produces a Python traceback rather than a clean error message. Add:

```python
try:
    validate_tool_name(tool)
except ValueError as e:
    print(f"plcc-make: {e}", file=sys.stderr)
    sys.exit(1)
```

### C7: `plcc_cli.py` retains old subcommand dispatch

After the rename, `plcc_cli.py` still dispatches `plcc spec` and `plcc scan`. As standalone commands are added, this becomes dead code. The plan should state explicitly what happens to it.

### C8: No inventory of existing tests

The roadmap §9.2 requires an inventory of existing tests: valid as-is, needs migration, or delete. Task 4 assumes a global rename is sufficient. It is not — `scan_cli_test.py` tests an interface that will no longer exist.

### C9: `--semantics` deferral not documented

The architectural spec §10.1 defines `--semantics` as a required part of the plugin contract. `plcc-lang-emit` (Task 12) omits it entirely with no comment. A note should be added to the `plcc-lang-emit` dispatcher and `plcc-make` acknowledging this gap and which phase addresses it.

### C10: `packaging.bash` entry-point check logic is fragile

The double-negative `&&` chain in `packaging.bash` is hard to follow and can incorrectly pass for broken commands. Simplify to:

```bash
"${VENV}/bin/${cmd}" --help > /dev/null 2>&1 || \
"${VENV}/bin/${cmd}" 2>&1 | grep -qi 'not yet implemented' || {
    echo "FAIL: ${cmd} not working"; exit 1
}
```

Or more simply, just verify the binary exists on the venv PATH:

```bash
test -x "${VENV}/bin/${cmd}" || { echo "FAIL: ${cmd} not installed"; exit 1; }
```

---

## Scope judgment

No area requires a separate design/plan cycle. The overall scope of Phase 1 is appropriate: restrict to the trivial grammar, establish all contracts, defer real parsing to Phase 2. The test pyramid is well-structured.

One area needs a brief discovery step rather than a separate cycle: the `spec → model` mapping (Blocker B1). Before writing `build_model.py`, a developer must run `plcc-spec` on the trivial grammar and record the actual serialized shape of `rhs` symbols. The plan should include this as an explicit step.

---

## Summary table

| ID | Severity | Area | Short description |
|---|---|---|---|
| B1 | BLOCKER | Task 10 | `build_model.py` uses fictional `"kind"` key; real output uses `isCapturing`/`isTerminal` |
| B2 | BLOCKER | Task 9 | `--spec` contract unresolved: test passes grammar file, docstring says spec JSON |
| B3 | BLOCKER | Task 15 | Dead `with open(model_json) as model_f:` block in `plcc-make` |
| B4 | BLOCKER | Task 3 | `--cov=plccng` not updated to `--cov=plcc` in `pyproject.toml` |
| B5 | BLOCKER | Missing task | No task retires `scan_cli.py`, `json_formatter.py`, and their tests |
| B6 | BLOCKER | Missing task | No task retires `spec_cli.py` and `spec_cli_test.py` |
| C1 | CONCERN | Design doc §3 | Trivial grammar shows `% plantuml PlantUML`; fixture uses `% diagram PlantUML` |
| C2 | CONCERN | Task 10 | `capitalize()` corrupts camelCase names; use `[:1].upper() + [1:]` |
| C3 | CONCERN | Task 8 | `spec_loader.py` duplicates `LexicalRule` |
| C4 | CONCERN | Task 9 | `plcc-tree` silently ignores `--spec`; should be documented with a comment |
| C5 | CONCERN | Task 11 | `plcc-plantuml-emit` emits one file per class; design choice undocumented |
| C6 | CONCERN | Task 15 | `ValueError` from `validate_tool_name` propagates as raw traceback |
| C7 | CONCERN | Task 3 | `plcc_cli.py` retains old subcommand dispatch; fate not stated |
| C8 | CONCERN | Task 4 | No inventory of existing tests for migration vs. deletion |
| C9 | CONCERN | Task 12 | `--semantics` flag deferred with no comment in dispatcher or `plcc-make` |
| C10 | CONCERN | Task 17 | `packaging.bash` entry-point check logic is fragile |
