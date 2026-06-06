# Design: Reconsider BNF Syntax (Issue 054)

**Date:** 2026-06-06
**Branch:** 054-reconsider-bnf-syntax

## Summary

Move the `:name` annotation from outside the angle brackets to inside, and require PascalCase for all nonterminal names. This is a clean breaking change — no backward compatibility.

## New Syntax

The colon+name moves inside `<>`. Nonterminal names are PascalCase. Field names remain lowercase-first.

| Position | Old | New |
|----------|-----|-----|
| LHS nonterminal | `<expr> ::=` | `<Expr> ::=` |
| LHS with altName | `<expr>:AddRest ::=` | `<Expr:AddRest> ::=` |
| RHS nonterminal (no field) | `<expr>` | `<Expr>` |
| RHS nonterminal (with field) | `<expr>:rest` | `<Expr:rest>` |
| RHS terminal (with field) | `<NUM>:num` | `<NUM:num>` |

### Example (`arith.plcc`)

```
# Before
<program>          ::= <Expr>:expr
<Expr>             ::= <Term>:term <ExprRest>:rest
<ExprRest>:AddRest ::= PLUS <Term>:term <ExprRest>:rest
<ExprRest>:NilRest ::=
<Term>             ::= <NUM>:num

# After
<Program>          ::= <Expr:expr>
<Expr>             ::= <Term:term> <ExprRest:rest>
<ExprRest:AddRest> ::= PLUS <Term:term> <ExprRest:rest>
<ExprRest:NilRest> ::=
<Term>             ::= <NUM:num>
```

## Naming Rules

LHS nonterminal names, LHS altNames, and RHS nonterminal names are all class names and share one rule. RHS field names are a separate category.

| What | Rule | Example |
|------|------|---------|
| LHS nonterminal name | PascalCase (`^[A-Z][a-zA-Z0-9_]*$`) | `Expr`, `E` |
| LHS altName (subclass) | PascalCase (`^[A-Z][a-zA-Z0-9_]*$`) | `AddRest` |
| RHS nonterminal name | PascalCase (`^[A-Z][a-zA-Z0-9_]*$`) | `Expr`, `E` |
| RHS field name | camelCase (`^[a-z][a-zA-Z0-9_]*$`) | `rest`, `e` |

Single-character names are legal (`<E>`, field `e`).

The dual use of `:` is disambiguated by case: `<Expr:AddRest>` on the LHS declares a subclass (uppercase second part); `<Expr:rest>` on the RHS names a field (lowercase second part).

## Parser Changes

Two regexes in `parse_syntactic_spec.py` change to move the `altName` capture inside `<>`:

**LHS** (`_matchLeft` and the `lhs` group in `_buildMatches`):
```python
# Before
r"<(?P<nonTerminal>\S*)>(?::(?P<altName>\S+))?\s*"
# After
r"<(?P<nonTerminal>[^:>]+)(?::(?P<altName>[^>]+))?>\s*"
```

**RHS** (`_parseSymbol`):
```python
# Before
r"<(?P<name>\S*)>(?::(?P<altName>\S+))?"
# After
r"<(?P<name>[^:>]+)(?::(?P<altName>[^>]+))?>"
```

The `lhs` detection pattern in `_buildMatches` changes from `<\S+>(?::\S+)?` to `<[^>]+>`.

The old `<Name>:field` form fails to match the new regexes and falls through to `MalformedBNFError`. No special detection or migration hint is needed.

`MalformedBNFError.py` updates its example syntax string to show the new form.

## Validation Changes

### Shared class-name utility

New file: `src/plcc/spec/syntax/validations/class_name.py`

```python
import re

CLASS_NAME_RE = re.compile(r"^[A-Z][a-zA-Z0-9_]*$")

def is_valid_class_name(name: str) -> bool:
    return bool(CLASS_NAME_RE.match(name))
```

### `validate_lhs.py`

- `_checkName`: replace `^[a-z][a-zA-Z0-9_]+$` with `is_valid_class_name`
- `_checkAltName`: replace `^[A-Z][a-zA-Z0-9_]+$` with `is_valid_class_name`
- `_getResolvedName`: drop `name.capitalize()` fallback — name is already PascalCase, use it directly

### `validate_rhs.py`

- `_validateNonTerminal`: replace `^[a-z][a-zA-Z0-9_]+$` with `is_valid_class_name` for the nonterminal name check
- `_validateNonTerminalAltName` (field name): update regex from `^[a-z][a-zA-Z0-9_]+$` to `^[a-z][a-zA-Z0-9_]*$` (allow single-char field names)

### `build_model.py`

Remove the capitalize transform on line 38:
```python
# Before
class_name = nt_name[:1].upper() + nt_name[1:]
# After
class_name = nt_name
```

## Synthetic Rules (`replace_repeating_with_standard_rules.py`)

The repeating-rule expander generates internal `StandardSyntacticRule` objects with synthetic `LhsNonTerminal` nodes. These are not re-parsed and do not go through `validate_lhs`, so their `altName` is not validated.

The synthetic altName changes from `"void"` to `"#nil"`. The `#` prefix is consistent with the existing convention in this file (`self.ntsep = self.rule.lhs.name + "#"`) and makes the synthetic nature unambiguous. A user cannot accidentally use `#nil` as a valid altName since it fails the class-name regex.

The `line` strings (used only in error reporting) update to reflect the new syntax format, e.g.:
```python
# Before
line=f"<{self.rule.lhs.name}>:void ::="
# After
line=f"<{self.rule.lhs.name}:#nil> ::="
```

## Files to Change

**Parser & model:**
- `src/plcc/spec/syntax/parse_syntactic_spec.py`
- `src/plcc/spec/syntax/MalformedBNFError.py`
- `src/plcc/model/build_model.py`

**Validation:**
- `src/plcc/spec/syntax/validations/class_name.py` (new)
- `src/plcc/spec/syntax/validations/validate_lhs.py`
- `src/plcc/spec/syntax/validations/validate_rhs.py`
- `src/plcc/spec/syntax/validations/replace_repeating_with_standard_rules.py`

**Tests & fixtures:**
- `src/plcc/spec/syntax/parse_syntactic_spec_test.py`
- `src/plcc/spec/syntax/MalformedBNFError_test.py`
- `src/plcc/spec/syntax/validations/validate_lhs_test.py`
- `src/plcc/spec/syntax/validations/validate_rhs_test.py`
- `src/plcc/spec/syntax/validations/replace_repeating_with_standard_rules_test.py`
- `src/plcc/spec/syntax/validations/validate_syntactic_spec_test.py`
- `tests/fixtures/arith.plcc`
- `tests/fixtures/trivial.plcc`
- `tests/fixtures/trivial-java.plcc`
- `tests/fixtures/trivial-python.plcc`
- `tests/fixtures/trivial-arbno.plcc`
- `tests/fixtures/trivial-full.plcc`
