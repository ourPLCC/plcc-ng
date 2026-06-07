# 068 - Remove lexical block optional second pattern

**Type:** feat
**Date:** 2026-06-05

## Description

Each token in the lexical section can currently be defined with an optional second regex pattern. Remove this feature — each token definition should have exactly one pattern.

## Notes

- Simplifies the lexical block grammar and the parser/lexer implementation.
- Any grammars relying on the second pattern will need to be updated; check test fixtures and examples.
