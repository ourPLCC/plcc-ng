# Bare-name field derivation decapitalizes instead of full-lowercasing — design

**Issue:** [168](../issues/168-bare-name-decapitalization-not-camelcase.md)
**Date:** 2026-07-24

## Problem

When a captured symbol has no explicit alt-name, its field name falls back
to the symbol's own grammar `name`. Every site implementing that fallback
does `name.lower()` — full-lowercasing the entire string, not decapitalizing
just the first letter. For a single-word symbol this is invisible (`Term` →
`term` either way), but for a multi-word PascalCase nonterminal it destroys
the word boundary:

```
<OneMore>  ->  onemore     (current)
           ->  oneMore     (expected: PascalCase -> camelCase)
```

This doesn't crash today — the runtime parser and code generation already
agree on full-lowercasing for the bare-name case — so it's a naming wart,
not a mismatch bug like #164. But it does produce field names that don't
match the standard PascalCase-to-camelCase convention plcc-ng otherwise
follows (`docs/language-guide/syntactic.md`'s own naming table).

## Root cause: five sites share one fallback, and one of them was deferred here

Issue #164 fixed a *different* branch of this same `alt if alt else name`
expression (the `alt` branch, when an alt-name is given) across four call
sites, and explicitly deferred the `name` (bare) branch to this issue.
Auditing all sites that implement the bare fallback:

| Site | Feeds | Fixed by #164? |
| --- | --- | --- |
| `spec_json_decoder.py::_field()` | runtime parse-tree field names (singular) | alt-branch only |
| `spec_json_decoder.py::_arbno_field()` | runtime parse-tree field names (arbno/list) | alt-branch only |
| `build_model.py::_extract_fields()` | generated class field names (singular) | already correct pre-#164 |
| `build_model.py::_extract_arbno_fields()` | generated class field names (arbno/list) | alt-branch only |
| `CapturingSymbol.getAttributeName()` | duplicate-capture validation (`validate_rhs.py`) only — not codegen/runtime | alt-branch only |

`CapturingSymbol.getAttributeName()` isn't mentioned in this issue's own
Notes section, but #164's design doc (`2026-07-24-164-alt-name-case-preservation-design.md`,
"Decision" section) explicitly names it as sharing this exact bare-name
fallback and defers it here. It must be fixed alongside the other four:
leaving it on full-lowercase while the codegen/runtime sites decapitalize
reopens a #164-shaped mismatch, just between validation and codegen instead
of between parser and codegen. Concretely: two *different* bare nonterminal
captures that collide under full-lowercase but not under decapitalize
(`<OneMore>` and `<Onemore>` both bare-lower to `onemore`) would be
false-positive-rejected as duplicates, even though post-fix they'd generate
distinct fields (`oneMore` vs `onemore`).

## Decision

At all five sites, branch on `isTerminal`:

- **Terminal** (conventionally `SCREAMING_SNAKE_CASE`, e.g. `NUM`,
  `MY_TOKEN`): keep today's full-lowercase (`num`, `my_token`).
  Decapitalizing a terminal would be wrong (`NUM` → `nUM`), and this is
  explicitly called out in the issue's Notes.
- **Nonterminal** (conventionally `PascalCase`, e.g. `OneMore`, `Term`):
  decapitalize only the first letter (`name[:1].lower() + name[1:]`) —
  `OneMore` → `oneMore`, `Term` → `term` (unchanged for single-word names).

Introduce one small private helper per file (not a new shared module across
`ll1`/`model`/`spec` — those packages don't currently share code, and the
function is a 3-line conditional; a cross-package util would be premature
for this):

```python
def _bare_field_name(sym: dict) -> str:  # spec_json_decoder.py
    name = sym["name"]
    if sym.get("isTerminal", False):
        return name.lower()
    return name[:1].lower() + name[1:]
```

```python
def _bare_field_name(symbol: dict) -> str:  # build_model.py
    name = symbol.get('name', '')
    if symbol.get('isTerminal'):
        return name.lower()
    return name[:1].lower() + name[1:]
```

`CapturingSymbol.getAttributeName()` inlines the same branch directly
(it operates on `self`, not a dict — `self.name` / `self.isTerminal` are
available via the `Terminal`/`NonTerminal` mixins already used by
`CapturingTerminal`/`RhsNonTerminal`):

```python
def getAttributeName(self):
    if self.altName is not None:
        return self.altName
    if self.isTerminal:
        return self.name.lower()
    return self.name[:1].lower() + self.name[1:]
```

## Changes

### 1. `spec_json_decoder.py`

Add `_bare_field_name(sym)`. Use it in both:
- `_field()`: `return alt if alt else _bare_field_name(sym)`
- `_arbno_field()`: `return (alt if alt else _bare_field_name(sym)) + "List"`

### 2. `build_model.py`

Add `_bare_field_name(symbol)`. Use it in both:
- `_extract_fields()`: `field_name = symbol.get('altName') or _bare_field_name(symbol)`
- `_extract_arbno_fields()`: `field_name = (alt if alt else _bare_field_name(symbol)) + 'List'`

### 3. `spec/syntax/CapturingSymbol.py`

`getAttributeName()`: inline `isTerminal`-gated decapitalization for the
bare branch, as shown above.

## Testing

Per CONTRIBUTING.md's TDD loop: a failing unit test first at each site,
then the minimal change to pass it.

- `spec_json_decoder_test.py`: add a multi-word bare nonterminal case for
  `_field()` (`OneMore` → `oneMore`) and for `_arbno_field()` (`OneMore` →
  `oneMoreList`). Keep existing single-word (`test_capturing_nonterminal_uses_name_lower`)
  and terminal (`test_capturing_terminal_uses_name_lower`) cases passing
  unchanged as regression locks — add a multi-word terminal case too
  (e.g. `MY_TOKEN` → `my_token`, unchanged) to prove terminals are
  unaffected.
- `build_model_test.py`: add analogous multi-word bare nonterminal cases
  for `_extract_fields()` and `_extract_arbno_fields()` — no such case
  exists today (current fixtures always set an explicit `altName`, even
  in the "bare" terminal test).
- `validate_rhs_test.py`: add a case with two different bare multi-word
  nonterminal captures that would collide under full-lowercase but not
  under decapitalize (e.g. `<OneMore>` and `<Onemore>` both captured in
  one rule) and assert no duplicate-capture error — they're distinct
  fields post-fix.
- E2E regression (`tests/bats/e2e/plcc-rep.bats` + new fixture), mirroring
  #164's `multi-capture-camelcase.plcc` pattern: a grammar using this
  issue's own repro (`<Program> ::= <OneMore>`, `<OneMore> ::= <LIT>`),
  Python semantics referencing `self.oneMore`, run through `plcc-rep`.

## Docs

- `docs/language-guide/syntactic.md` (~line 107-108): currently states
  "Their field names will be the nonterminal name lower-cased." Update to
  describe decapitalization (PascalCase → camelCase) with a multi-word
  example (`<OneMore>` → field `oneMore`).
- `docs/migration.md` §7 ("Update captured field syntax"): add a row and
  a short note explaining the decapitalize-vs-full-lowercase translation
  for bare nonterminal auto-naming. This is *not* a behavior difference
  from legacy PLCC — verified against `ourPLCC/plcc`'s actual source
  (`defangRHS` in `src/plcc/__main__.py`): legacy PLCC nonterminals were
  required to already be lowerCamelCase (`isNonterm` matches `[a-z]\w*`),
  so bare captures used the name verbatim (`field = tnt`), which was
  already the identity transform. Once you apply migration step 5's
  PascalCase rename, decapitalize-first-letter reproduces that exact
  result (`oneMore` → `OneMore` → decapitalize → `oneMore`). It's worth
  documenting anyway because the *mechanism* differs even though the
  *end result* matches: a migrating user renaming `<oneMore>` to
  `<OneMore>` per step 5 should know plcc-ng auto-derives the field name
  back down from the PascalCase spelling, not that it's coincidentally
  unaffected.

## Commit shape

Per `dev-docs/release-sop.md`: the source-fix commit is `fix!(...)` with
a `BREAKING CHANGE:` footer — this changes generated/validated field names
for any existing multi-word bare nonterminal capture (terminals are
unaffected — always full-lowercased, before and after) across plcc-ng
grammars written before this fix. The footer should also note that,
although this is a breaking change *for plcc-ng*, it brings plcc-ng's
bare-name auto-naming back in line with legacy PLCC's original behavior
(see the `docs/migration.md` reasoning above) — this was a plcc-ng-only
regression, not a deliberate divergence, so the break is a correction, not
a new design choice:

```
fix(model)!: decapitalize bare multi-word nonterminal capture field names

Bare (no alt-name) capture field names were derived by full-lowercasing
the symbol's grammar name instead of decapitalizing just the first
letter, e.g. `<OneMore>` produced field `onemore` instead of `oneMore`.
Terminals are unaffected (SCREAMING_SNAKE_CASE terminals are still
correctly full-lowercased); only bare nonterminal captures change.

Although this is a breaking change for plcc-ng, it brings bare-capture
auto-naming back in line with legacy PLCC's original behavior: PLCC
required nonterminals to already be lowerCamelCase and used the name
verbatim for a bare capture's field, which was already the identity
transform. plcc-ng's PascalCase nonterminal convention (see the
migration guide) means the equivalent identity transform is
decapitalize-first-letter, not full-lowercase — the full-lowercase
behavior was a plcc-ng-only regression from the intended
PLCC-equivalent naming, not a deliberate design choice.

BREAKING CHANGE: a bare (no `:fieldname`) multi-word nonterminal
capture now generates/validates a camelCase field name instead of an
all-lowercase one, e.g. `<OneMore>` now produces field `oneMore`
instead of `onemore`. Semantic-section code referencing the old
all-lowercase field name (`self.onemore`) must update to the new
camelCase name (`self.oneMore`), or add an explicit `<OneMore:onemore>`
alt-name to keep the old spelling. Single-word nonterminal captures and
all terminal captures are unaffected.
```

Final commit on the branch closes #168 via `bin/issues/close.bash 168`.

## Files changed

| File | Change |
| --- | --- |
| `src/plcc/ll1/spec_json_decoder.py` | New `_bare_field_name()`; `_field()`, `_arbno_field()` use it |
| `src/plcc/model/build_model.py` | New `_bare_field_name()`; `_extract_fields()`, `_extract_arbno_fields()` use it |
| `src/plcc/spec/syntax/CapturingSymbol.py` | `getAttributeName()`: decapitalize the bare-nonterminal branch |
| `src/plcc/ll1/spec_json_decoder_test.py` | Multi-word bare nonterminal cases (singular + arbno), multi-word terminal regression case |
| `src/plcc/model/build_model_test.py` | Multi-word bare nonterminal cases (singular + arbno) |
| `src/plcc/spec/syntax/validations/validate_rhs_test.py` | Case where full-lowercase-colliding bare names are not flagged as duplicates |
| `tests/fixtures/*.plcc` (new) | Grammar + Python semantics reproducing issue #168's `OneMore` example |
| `tests/bats/e2e/plcc-rep.bats` | New case: end-to-end repro evaluates correctly with `oneMore` field |
| `docs/language-guide/syntactic.md` | Correct the bare-nonterminal-naming description |
| `docs/migration.md` | New row + note in §7 on the decapitalize translation |
