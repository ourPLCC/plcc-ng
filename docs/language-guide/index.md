# Language Guide

A plcc-ng grammar file describes a language in three sections, separated by
lines containing a single `%`:

```text
[Lexical specification]
%
[Syntactic specification]
%
[Semantic specification]
```

| Section | What it describes | Pipeline stage it drives |
|---|---|---|
| Lexical | Token and skip rules | Scanner (`plcc-scan`) |
| Syntactic | Grammar rules (BNF) | Parser (`plcc-parse`) |
| Semantic | Target-language code embedded in generated classes | Interpreter (`plcc-rep`) |

Each stage depends on the one before it:

```
plcc-rep  →  plcc-parse  →  plcc-scan
Semantic  →  Syntactic   →  Lexical
```

You can write a grammar with only a lexical section (no `%` needed), or a
grammar with lexical and syntactic sections but no semantic section. Add
sections as your language grows.

External files can be included in any section using:

```
%include FILENAME
```

## Pages in this guide

- [Token Rules](tokens.md) — `token` and `skip` syntax, scanning algorithm
- [Grammar Rules](grammar.md) — BNF rules, parse tree class hierarchy
- [Code Generation](code-generation.md) — embedding code, hooks, target language selection
- [Examples](examples.md) — worked examples of increasing complexity
