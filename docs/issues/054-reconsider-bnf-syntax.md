# 054 - Reconsider BNF section syntax

**Type:** feat
**Date:** 2026-06-01

## Description

Reconsider the syntax used in the BNF section of a grammar to improve consistency and readability. Two specific changes are proposed:

1. **PascalCase for non-terminals** — Since non-terminals become class names in generated code, they should use PascalCase to match that convention (e.g. `<Expression>` instead of `<expression>`).

2. **Move alternative names inside the angle brackets** — Currently, alternative names appear outside the brackets as a suffix after a colon. They should move inside:
   - On the RHS, `<NonTerminal>:field` becomes `<field:NonTerminal>`
   - On the LHS, `<NonTerminal>:SubClass` becomes `<SubClass:NonTerminal>`

## Notes

- The new inside-the-brackets syntax makes the relationship between the name and the non-terminal more visually cohesive.
- PascalCase alignment with generated class names reduces the conceptual gap between grammar and code.
