# 164 - camelCase alt-names lowercased by the parser but not by code generation, breaking multi-capture rules

**Type:** docs
**Date:** 2026-07-23

## Description

When a grammar alternative captures the same nonterminal more than once
with camelCase alt-names (e.g. `<Exp:testExp>`, `<Exp:trueExp>`,
`<Exp:falseExp>` in an `if...then...else` rule), the generated Python/Java
class fields keep the alt-name's original case (`testExp`, `trueExp`,
`falseExp`), but the parser always lowercases alt-names when building the
runtime parse tree it hands to the registry. The two disagree, so
`plcc-rep`/`plcc-parse` fail at runtime with e.g.:

```
Specification error: KeyError: "No class for rule 'IfExp' with fields {'testexp', 'trueexp', 'falseexp'}"
```

Root cause (found by reading the installed package,
`plcc/spec/syntax/CapturingSymbol.py`):

```python
def getAttributeName(self):
    if self.altName is None:
        return self.name.lower()
    else:
        return self.altName.lower()   # always lowercased
```

versus code generation (`plcc/model/build_model.py`), which uses the
alt-name as written, uncased:

```python
field_name = symbol.get('altName') or symbol.get('name', '').lower()
```

## Steps to Reproduce

1. `grammar.plcc`:
   ```
   skip WHITESPACE '\s+'
   token LIT '\d+'
   token IF 'if'
   token THEN 'then'
   token ELSE 'else'
   %
   <Program>    ::= <Exp>
   <Exp:LitExp> ::= <LIT>
   <Exp:IfExp>  ::= IF <Exp:testExp> THEN <Exp:trueExp> ELSE <Exp:falseExp>
   ```
2. `spec.plcc` (Python), with `IfExp.eval()` referencing `self.testExp`,
   `self.trueExp`, `self.falseExp` — matching the grammar's declared
   alt-names exactly.
3. `echo "if 1 then 2 else 3" | plcc-rep`
4. Actual: `Specification error: KeyError: "No class for rule 'IfExp'
   with fields {'testexp', 'trueexp', 'falseexp'}"`. Expected: `2`.

Reproduced identically against the Java target (same error, "No class
for rule 'IfExp' with fields [testexp, trueexp, falseexp]"), consistent
with the root cause living in the shared, language-agnostic
`plcc/spec/syntax` module rather than in either target's code generator.
JavaScript wasn't separately reproduced but is presumably affected for
the same reason.

## Notes

**Workaround confirmed working in both Python and Java:** write the
alt-name entirely in lowercase in the grammar (`<Exp:testexp>`,
`<Exp:trueexp>`, `<Exp:falseexp>`) so the generated field name and the
parser's lowercased attribute name already agree. Semantic-section code
then reads `self.testexp` / `self.trueexp` / `self.falseexp` (all
lowercase) instead of the camelCase spelling.

Originally filed as issue #6 in `ourPLCC/languages-ng`
(`dev-docs/issues/006-multi-capture-alt-name-case-mismatch.md`), found
while spiking a downstream plan's `IfExp` mechanics there. That repo
adopted the all-lowercase alt-name spelling in its shared `grammar.plcc`
to work around this, the same way `VAR` needed renaming for the
JavaScript reserved-word collision (see issue #163).

Either `getAttributeName()` should stop lowercasing alt-names (matching
code generation's case-preserving behavior), or code generation should
lowercase alt-names to match the parser — whichever is chosen, the two
should agree.
