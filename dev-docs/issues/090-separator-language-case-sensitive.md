# 090 - Make language name in semantic separator case-sensitive

**Type:** feat
**Date:** 2026-06-12

## Description

The language name in the semantic section separator (e.g. `% Python`,
`% Java`) is currently normalized to lowercase before being matched
against known language names. It should be treated as case-sensitive
instead — the casing the user writes is the casing that is used.

## Desired Behavior

| Separator | Language |
| --- | --- |
| `% Python` | Python |
| `% Java` | Java |
| `% python` | error — unknown language |
| `% PYTHON` | error — unknown language |

## Rationale

Language names are proper nouns and should be written with their
canonical casing (`Python`, `Java`). Silent case normalization hides
typos and gives users a false sense that any casing works.

## Notes

This is a breaking change for any spec file using non-canonical casing
such as `% python` or `% JAVA`. Users will need to update those
separators to use the correct casing.
