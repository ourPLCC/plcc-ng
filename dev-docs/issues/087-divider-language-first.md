# 087 - Change semantic divider syntax to `% Language tool` with required language

**Type:** feat
**Date:** 2026-06-08

## Description

The current semantic section divider syntax is `% tool language`, with both
fields optional. This should change to `% Language tool`, where:

- `Language` comes first and is **required**.
- `tool` comes second and is **optional** (defaults to the language name when omitted).

## Desired Behavior

| Divider | Language | Tool name |
| --- | --- | --- |
| `% Python` | Python | Python |
| `% Python sum` | Python | sum |
| `% Java` | Java | Java |
| `% Java eval` | Java | eval |
| `%` | *(error — language required)* | — |

The bare `%` divider (currently valid, defaults to Java/Java) becomes a syntax
error. Users must explicitly state the target language.

## Rationale

- Language is the more important of the two fields — it determines what code is
  generated. Putting it first makes the most significant information immediately
  visible.
- Requiring the language eliminates the silent Java default, which is surprising
  for users who do not intend to use Java.

## Notes

This is a breaking change. Any grammar file using `%` alone or `% toolname language`
order will need to be updated.

See also: [[054-reconsider-bnf-syntax]] for prior precedent of making breaking
syntax changes.
