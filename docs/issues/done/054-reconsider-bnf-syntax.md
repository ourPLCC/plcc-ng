# 054 - Reconsider BNF section syntax

**Type:** feat
**Date:** 2026-06-01

## Description

Reconsider the syntax used in the BNF section of a grammar to improve consistency and readability. Two specific changes are proposed:

1. **PascalCase for non-terminals** — Since non-terminals become class names in generated code, they should use PascalCase to match that convention (e.g. `<Expression>` instead of `<expression>`).

2. **Move alternative names inside the angle brackets, type first** — Currently, alternative names appear outside the brackets as a suffix after a colon. They should move inside, always in `<Type:name>` order:
   - On the RHS, `<NonTerminal>:field` becomes `<NonTerminal:field>`
   - On the LHS, `<NonTerminal>:SubClass` becomes `<NonTerminal:SubClass>`

## Example

Using `arith.plcc` as a before/after illustration:

**Before:**

```text
<program>              ::= <expr>:expr
<expr>                 ::= <term>:term <exprrest>:rest
<exprrest>:AddRest     ::= PLUS <term>:term <exprrest>:rest
<exprrest>:NilRest     ::=
<term>                 ::= <NUM>:num
```

**After:**

```text
<Program>              ::= <Expr:expr>
<Expr>                 ::= <Term:term> <ExprRest:rest>
<ExprRest:AddRest>     ::= PLUS <Term:term> <ExprRest:rest>
<ExprRest:NilRest>     ::=
<Term>                 ::= <NUM:num>
```

Another example:

```text
<Tree:Node> ::= LP <Tree:left> COMMA <Tree:right> RP
```

## Decision

**Use the proposed syntax.** After comparing with alternatives (`=` for field binding, `as` keyword, hybrid inside/outside, and sigil-prefixed subtypes), the proposed syntax is the best fit for students learning to study programming languages.

The `Type:name` notation inside `<>` is consistent on both sides — always type first, then the local name — which mirrors familiar `Type:identifier` patterns in Swift, Kotlin, and typed systems generally. PascalCase eliminates the silent `capitalize()` transform between grammar names and generated class names — students can read grammar and code side by side without a translation step. The two uses of `:` (field label on RHS, subclass declaration on LHS) are distinguished by the same case convention (`lower` vs `Upper`) that students already apply in the target language, so the overload reinforces rather than contradicts existing knowledge.

The `as` keyword alternative was the only close competitor on clarity, but it adds per-symbol verbosity (`<Expr as expr>`) that increases noise in rules without reducing cognitive load for students who already know `name:Type` notation.

## Notes

- The new inside-the-brackets syntax makes the relationship between the name and the non-terminal more visually cohesive.
- PascalCase alignment with generated class names reduces the conceptual gap between grammar and code.
- Error messages and tutorial material should explicitly state the LHS vs RHS distinction: on the LHS, `<NonTerminal:SubClass>` declares a subclass; on the RHS, `<NonTerminal:field>` names a captured value. This one sentence covers the entire learning curve for the dual use of `:`.
