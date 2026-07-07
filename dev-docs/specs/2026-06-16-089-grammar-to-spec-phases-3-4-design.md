# Design: Grammar-to-Spec Rename — Phases 3 & 4 (089)

**Date:** 2026-06-16
**Issue:** [089 - Rename "grammar file" to "specification file"](../issues/done/089-grammar-to-spec-rename.md)
**Prior work:** Phases 1 & 2 shipped in PRs #205 and #206 (CLI flags, default filename, error messages, help text).

## Goal

Complete the rename by updating documentation (Phase 3) and internal Python identifiers (Phase 4).

## Delivery

Two PRs shipped in order:

1. **PR A — Phase 3 (docs):** text-only, trivially reviewable
2. **PR B — Phase 4 (internals):** module renames + symbol renames across the Python source

---

## Phase 3 — Documentation

### Rule

If "grammar" refers to *the `.plcc` spec file or a CLI flag*, update it.
If "grammar" refers to *grammar as a language concept* (LL(1), context-free, syntactic structure), leave it alone.

### Files changed

| File | What changes |
|------|-------------|
| `docs/cli/index.md` | "grammar file" → "spec file"; "grammar path" → "spec path" |
| `docs/cli/orchestrators.md` | "grammar file" → "spec file"; "grammar banner" → "spec banner"; `grammar.plcc` → `spec.plcc` in examples; `--grammar` → `--spec` in examples |
| `docs/cli/primitives.md` | "grammar file" → "spec file"; `grammar.plcc` → `spec.plcc` in example commands |
| `CONTRIBUTING.md` | One instance: "grammar file" → "spec file" in the test tier table |

### Files left alone

- `docs/getting-started.md` — "PLCC-ng automatically generates fields from the grammar" refers to grammar-as-language-concept.
- Any reference to "LL(1) grammar", "context-free grammar", "grammar rule", "grammar syntax", etc.

### Commit

```
docs(089): update docs grammar-file references to spec-file [skip ci]
```

---

## Phase 4 — Internal Identifiers

### Module renames

| Old path | New path |
|----------|----------|
| `src/plcc/build/grammar.py` | `src/plcc/build/spec.py` |
| `src/plcc/build/grammar_test.py` | `src/plcc/build/spec_test.py` |
| `src/plcc/cmd/grammar.py` | `src/plcc/cmd/spec.py` |
| `src/plcc/cmd/grammar_test.py` | `src/plcc/cmd/spec_test.py` |

`src/plcc/spec/syntax/validations/ll1/build_spec_grammar.py` is about the LL(1) grammar data structure — unchanged.

### Symbol renames

Applied in the renamed modules and all import sites (`make.py`, `scan.py`, `parse.py`, `rep.py`, `diagram.py`, and their test files):

| Old | New |
|-----|-----|
| `_GRAMMAR_FILE = ".grammar"` | `_SPEC_FILE = ".spec"` |
| `DEFAULT_GRAMMAR_FILE` | `DEFAULT_SPEC_FILE` |
| `read_grammar` | `read_spec` |
| `write_grammar` | `write_spec` |
| `resolve_grammar_path` | `resolve_spec_path` |
| `GRAMMAR_OPTION` | `SPEC_OPTION` |
| `validate_grammar_flag` | `validate_spec_flag` |
| `grammar_flag_for_child` | `spec_flag_for_child` |
| `explicit_grammar`, `stored_grammar`, `grammar` (locals in `make.py`) | `explicit_spec`, `stored_spec`, `spec` |

### Test function renames

Test function names in the renamed test files are updated to match new symbol names (e.g. `test_grammar_option_contains_flag` → `test_spec_option_contains_flag`). Test behavior is unchanged.

### Backward compatibility

None required. The project is experimental. Existing build directories with a `.grammar` file will lose their remembered spec path — acceptable.

### Approach

TDD pass per module:
1. Rename file, update test names and assertions to use new symbols — confirm red
2. Implement renames in the module — confirm green
3. Update all import sites

### Commits (one per logical group)

```
refactor(089): rename build/grammar → build/spec, .grammar → .spec
refactor(089): rename cmd/grammar → cmd/spec and update all import sites
```

### Verification

Run `bin/test/functional.bash` after all changes to catch any bats tests that reference old symbol names or the `.grammar` filename.
