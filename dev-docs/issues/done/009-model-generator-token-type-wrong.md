# 009 - Model generator emits token name as field type instead of Token

**Type:** fix
**Date:** 2026-05-11

## Description

The model generator incorrectly uses the token name as the field type for some
token references in a rule, rather than the expected `Token`. The bug is
inconsistent: tokens with certain names are affected while others in the same
rule are not.

## Steps to Reproduce

Grammar:

```
skip WS '\s+'
token A  'a'
token AA 'aa'
token ID '\w+'
%
<prog> ::= <A> <AA> <ID>
```

Generated model (trimmed to the `fields` array of `Prog`):

```json
{
  "name": "a",
  "type": "A",      <- wrong: should be Token
  "is_list": false
},
{
  "name": "aa",
  "type": "Token",  <- correct
  "is_list": false
},
{
  "name": "id",
  "type": "Token",  <- correct
  "is_list": false
}
```

Token `A` is assigned `"type": "A"` instead of `"type": "Token"`. Tokens `AA`
and `ID` in the same rule are assigned `"type": "Token"` correctly.

## Notes

- The difference between `A` and `AA`/`ID` is unclear. Possible causes:
  single-character name, name collision with a generated class name, or an
  ordering/lookup issue in the type-resolution step.
- Any generated code that depends on the model (e.g. Python emitter) will
  produce an incorrect class reference for the affected field.
