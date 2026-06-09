# Syntactic Section

The syntactic section of a `.plcc` file defines the grammar of your language
in a BNF-flavored notation. Each rule maps a non-terminal to a sequence of
symbols on its right-hand side.

## Naming conventions

| Kind | Format | Example |
| --- | --- | --- |
| Non-terminal (class name) | PascalCase, angle-bracketed | `<Expr>`, `<Program>` |
| Terminal (token name) | UPPER_CASE | `PLUS`, `NUM` |
| Field name (captured symbol) | camelCase | `expr`, `num`, `rest` |
| Alt-name (subclass) | PascalCase | `AddExpr`, `NilRest` |

## Basic rules

```text
<Program> ::= <Expr:expr>
<Expr>    ::= <Term:term> <ExprRest:rest>
<Term>    ::= <NUM:num>
```

Each rule becomes a class. Captured symbols (those inside `<...>` with a
field name) become instance variables on that class.

### Capturing terminals

Wrap a terminal in angle brackets and give it a field name to capture it:

```text
<Term> ::= <NUM:num>   # captures NUM as field `num`
<Term> ::= NUM         # matches NUM but does not capture it
```

### Capturing non-terminals

Give a non-terminal a field name with `:fieldname`:

```text
<Program> ::= <Expr:expr>   # captures Expr as field `expr`
<Program> ::= <Expr>        # matches Expr but does not capture it
```

## Alternative rules and subclasses

When a non-terminal has multiple rules, each alternative gets an alt-name
that becomes a subclass:

```text
<Expr:LitExpr> ::= <NUM:num>
<Expr:AddExpr> ::= PLUS <Expr:left> <Expr:right>
```

This generates:

```
abstract class Expr
class LitExpr extends Expr  { Token num; }
class AddExpr extends Expr  { Expr left; Expr right; }
```

<!-- TODO: verify the exact generated class hierarchy for plcc-ng (may differ from PLCC's Java) -->

The first rule in the file defines the start symbol.

## Repetition rules

The `**=` form matches zero or more occurrences of a pattern, with an optional
separator:

```text
<Args>    **= <Expr:expr>
<ArgList> **= <Expr:expr> +COMMA
```

Captured symbols become parallel lists:

```text
<Args> **= <Expr:expr>
# generates: Args { List<Expr> exprList; }

<Pairs> **= <WHOLE:x> <WHOLE:y> +COMMA
# generates: Pairs { List<Token> xList; List<Token> yList; }
```

The `+SEPARATOR` token is consumed between repetitions but not captured.

<!-- TODO: verify repetition rule syntax and generated field names in plcc-ng -->

## Parse algorithm

plcc-ng uses recursive-descent LL(1) parsing. Each non-terminal gets a parse
method. The method reads the next token and dispatches to the correct
alternative, then matches the RHS left-to-right: tokens are consumed directly,
non-terminals call their own parse methods.

A grammar is valid only if it is LL(1): each alternative must be
distinguishable by a single lookahead token. plcc-ng reports LL(1) conflicts
when it detects them.
