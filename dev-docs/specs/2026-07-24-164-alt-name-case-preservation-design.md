# camelCase alt-name case preservation — design

**Issue:** [164](../issues/done/164-multi-capture-alt-name-case-mismatch.md)
**Date:** 2026-07-24

## Problem

When a grammar rule captures the same nonterminal more than once, each
capture needs an explicit alt-name to give it a distinct field (e.g.
`<Exp:testExp>`, `<Exp:trueExp>`, `<Exp:falseExp>` in an `if...then...else`
rule). Code generation (`build_model.py::_extract_fields`) uses the
alt-name's case exactly as written. The runtime parser
(`spec_json_decoder.py::_field`) lowercases it. A camelCase alt-name like
`testExp` therefore produces a generated field `testExp` but a runtime
parse-tree field `testexp`; `plcc-rep`/`plcc-parse` fail at runtime with
`KeyError: "No class for rule 'IfExp' with fields {'testexp', ...}"`
(`src/plcc/lang/ext/python/runtime/registry.py:21`, mirrored in the Java
and JavaScript runtimes).

The documented workaround is to spell alt-names entirely in lowercase.
This design removes the need for the workaround by making case preserved
end-to-end, so `<Exp:testExp>` and `self.testExp` actually agree.

## Root cause: four independent call sites, three different behaviors

Every capturing symbol's field name is derived by one of two branches: an
explicit `altName`, or (when absent) a fallback to the symbol's own
grammar `name`. Four call sites each implement this `alt if alt else
name` choice independently, and they don't all treat the `alt` branch the
same way:

| Site | `altName` branch | Feeds |
| --- | --- | --- |
| `spec_json_decoder.py::_field()` | lowercases | runtime parse-tree field names (singular capture) → registry lookup |
| `spec_json_decoder.py::_arbno_field()` | lowercases | runtime parse-tree field names (list/arbno capture) → registry lookup |
| `build_model.py::_extract_fields()` | **preserves case** | generated class field names (singular capture) |
| `build_model.py::_extract_arbno_fields()` | lowercases | generated class field names (list/arbno capture) |
| `CapturingSymbol.getAttributeName()` | lowercases | duplicate-capture validation only (`validate_rhs.py`) — doesn't feed codegen or the parser |

The singular-capture case is the one that crashes: codegen preserves
case, the parser doesn't. The arbno/list case doesn't crash today —
`_arbno_field()` and `_extract_arbno_fields()` both lowercase, so they
agree — but it has the same latent defect: a camelCase alt-name on a
repeated capture (`<Exp:testExp>*`) is silently flattened to
`testexpList` on both sides, which will surprise anyone who wrote
`self.testExpList` in semantic code just as much as the crash surprises
someone who wrote `self.testExp`.

Git history (`2d5a25a1`, `fe1a54bc`) shows the lowercasing was never a
deliberate decision about alt-names specifically — every site implements
it as a single `(alt if alt else name).lower()` expression, applying one
transform uniformly to whichever branch wins. The transform is genuinely
needed for the **bare-name fallback**: nonterminals are conventionally
PascalCase (`Exp`) and terminals SCREAMING_SNAKE (`NUM`), neither of
which is a valid field name un-lowered. Alt-names don't need it:
`validate_rhs.py::_validateNonTerminalAltName` already requires them to
match `^[a-z][a-zA-Z0-9_]*$` (start lowercase), so by the time an
alt-name reaches these sites it's already a valid field identifier —
`.lower()` on the rest of it is pure information loss, not a needed
normalization. `build_model.py::_extract_fields()` is the one site that
already gets this right (`altName or name.lower()`, lowering only the
fallback).

## Decision

Preserve alt-name case in all four sites; leave bare-name lowercasing
untouched everywhere. Concretely, replace each site's single
`(alt if alt else name).lower()`-shaped expression with a form that
lowercases only the `name` branch, passing `alt` through unchanged.

Bare-name full-lowercasing (`<OneMore>` → `onemore` instead of the
arguably-more-correct `oneMore`) is a separate, non-crashing defect in
the same fallback branch these sites all share, filed as
[#168](../issues/168-bare-name-decapitalization-not-camelcase.md) rather
than fixed here — the two sides already agree on it, so it isn't broken
in the way #164 is, and fixing it would change generated field names for
every multi-word bare capture across all existing grammars, a much
larger blast radius than this fix.

## Changes

### 1. `spec_json_decoder.py::_field()` — singular runtime field name

Before:

```python
def _field(sym: dict) -> str | None:
    if not sym.get("isCapturing", False):
        return None
    alt = sym.get("altName")
    name = sym["name"]
    return (alt if alt else name).lower()
```

After: `return alt if alt else name.lower()`.

### 2. `spec_json_decoder.py::_arbno_field()` — list/arbno runtime field name

Before:

```python
def _arbno_field(sym: dict) -> str:
    alt = sym.get("altName")
    name = sym["name"]
    return (alt if alt else name).lower() + "List"
```

After: `return (alt if alt else name.lower()) + "List"`.

### 3. `build_model.py::_extract_arbno_fields()` — list/arbno generated field name

Currently:

```python
field_name = (alt if alt else name).lower() + 'List'
```

Change to: `field_name = (alt if alt else name.lower()) + 'List'`.

### 4. `CapturingSymbol.getAttributeName()` — duplicate-capture validation identity

Before:

```python
def getAttributeName(self):
    if self.altName is None:
        return self.name.lower()
    else:
        return self.altName.lower()
```

After: return `self.altName` unchanged when present, `self.name.lower()`
otherwise. Effect: `testExp` and `testexp` become distinguishable
captures for duplicate-detection purposes — correct, since after this
fix they really are two different field names, not the same field
spelled two ways.

`build_model.py::_extract_fields()` (singular generated field name) is
already correct — no change.

## Testing

Per CONTRIBUTING.md's TDD loop: a failing unit test first at each site,
then the minimal change to pass it.

- `spec_json_decoder_test.py`: extend `test_capturing_terminal_uses_alt_name`
  fashion with a camelCase case, e.g. assert `alt_name="testExp"` decodes
  to field `"testExp"` (not `"testexp"`), for both the plain-rule path and
  the arbno path (new case mirroring the existing arbno tests, alt-name
  `"testExp"` → field `"testExpList"`). Keep the existing
  `test_capturing_terminal_uses_name_lower` /
  `test_capturing_nonterminal_uses_name_lower` bare-name cases passing
  unchanged — they lock in the fallback behavior this design doesn't
  touch.
- `build_model_test.py`: add a camelCase-alt-name arbno case asserting
  the generated field is `testExpList`, not `testexpList`.
- `CapturingSymbol` / `validate_rhs_test.py`: add a case where two
  captures use alt-names differing only in case (`testExp` vs `testexp`)
  and assert no duplicate-capture error is raised (they're distinct
  fields); keep existing same-case duplicate detection passing.
- Regression/integration proof: reproduce the issue's exact repro (the
  `IfExp` grammar with `<Exp:testExp>`, `<Exp:trueExp>`, `<Exp:falseExp>`
  and a Python semantic section referencing `self.testExp` etc.) through
  `plcc-rep` end-to-end, confirming `2` is printed instead of the
  `KeyError`. New fixture `tests/fixtures/multi-capture-camelcase.plcc`
  (grammar + Python semantics in one file, following `arith.plcc`'s
  shape), exercised by a new case in `tests/bats/e2e/plcc-rep.bats`
  (this tier already builds a fixture spec into a real Python emit and
  evaluates through `plcc-rep`, e.g. "plcc-rep evaluates 1+2 to 3 in
  batch mode" — the right home for a semantics-correctness regression,
  as opposed to `tests/bats/commands/plcc-rep.bats`, which only covers
  the CLI contract: flags, exit codes, error messages).

## Files changed

| File | Change |
| --- | --- |
| `src/plcc/ll1/spec_json_decoder.py` | `_field()`, `_arbno_field()`: stop lowercasing the `alt` branch |
| `src/plcc/model/build_model.py` | `_extract_arbno_fields()`: stop lowercasing the `alt` branch |
| `src/plcc/spec/syntax/CapturingSymbol.py` | `getAttributeName()`: stop lowercasing the `altName` branch |
| `src/plcc/ll1/spec_json_decoder_test.py` | camelCase alt-name cases (singular + arbno) |
| `src/plcc/model/build_model_test.py` | camelCase alt-name arbno case |
| `src/plcc/spec/syntax/validations/validate_rhs_test.py` | case-differing alt-names are not duplicates |
| `tests/fixtures/multi-capture-camelcase.plcc` (new) | Grammar + Python semantics reproducing issue 164's `IfExp` example |
| `tests/bats/e2e/plcc-rep.bats` | New case: end-to-end repro from issue 164 evaluates correctly instead of raising `KeyError` |
