# 168 - Bare captures derive field names by full-lowercasing instead of decapitalizing

**Type:** fix
**Date:** 2026-07-24

<!--
Classify by user-facing impact, not by whether something was "broken".
`fix` and `feat` bump the release version (see [tool.semantic_release]
in pyproject.toml); reserve them for changes to the shipped package
(src/). A bug in a test, script, or CI workflow (bin/, tests/,
.github/) is still a bug, but it's not user-facing — classify it
`test` or `chore` instead so it doesn't spin the version. `docs` is for
documentation content, and never bumps the version either way.
-->

## Description

When a captured symbol has no explicit alt-name, the field name is derived
from the symbol's own grammar name by lowercasing the *entire* string, not
by decapitalizing just the first letter. For a single-word symbol this is
invisible (`Term` → `term` either way), but for a multi-word PascalCase
nonterminal or terminal, full-lowercasing destroys the word boundary:

```
<OneMore>  ->  onemore     (current)
           ->  oneMore     (expected: PascalCase -> camelCase)
```

This is the same class of defect as
[#164](../164-multi-capture-alt-name-case-mismatch.md) (case handling in
field-name derivation) but is a distinct bug: it affects the *bare*-name
fallback branch, not the alt-name branch, and unlike #164 it does not
crash today because both sides that derive the field name — the runtime
parser (`spec_json_decoder.py::_field()` / `_arbno_field()`) and code
generation (`build_model.py::_extract_fields()` / `_extract_arbno_fields()`)
— already agree on full-lowercasing for the bare-name case, so there's no
codegen/runtime mismatch, just a naming-convention wart.

Found while investigating #164: fixing #164 intentionally leaves this
bare-name branch untouched, since correcting it would change generated
field names for every multi-word bare nonterminal/terminal across all
existing grammars — a much bigger behavior change than the alt-name fix,
and out of scope for that issue.

## Steps to Reproduce

1. `grammar.plcc`:
   ```
   token LIT '\d+'
   %
   <Program>  ::= <OneMore>
   <OneMore>  ::= <LIT>
   ```
2. No alt-name is given for the `<OneMore>` capture in `<Program>`'s rule.
3. Generated field / runtime parse-tree field for that capture is
   `onemore`. Expected (matching PascalCase -> camelCase convention):
   `oneMore`.

## Notes

Relevant code (same sites touched by #164's fix, different branch of the
same ternary/`or` expression):

- `src/plcc/ll1/spec_json_decoder.py::_field()` and `_arbno_field()` —
  the `name` fallback branch of `(alt if alt else name).lower()`.
- `src/plcc/model/build_model.py::_extract_fields()` and
  `_extract_arbno_fields()` — the `.lower()` fallback when no `altName`
  is present.

A fix would decapitalize (`name[0].lower() + name[1:]`) rather than
lowercase the whole string, matching standard PascalCase -> camelCase
conversion. Needs care around terminals (`NUM`, conventionally
SCREAMING_SNAKE_CASE) vs nonterminals (`OneMore`, conventionally
PascalCase) — decapitalizing `NUM` gives `nUM`, not `num`; the two kinds
of bare names may need different treatment.
