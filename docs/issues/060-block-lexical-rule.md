# 060 - Add `block` lexical rule type for multi-line token capture

**Type:** feat
**Date:** 2026-06-03

## Description

Add a `block` rule type to the lexical section (alongside `skip` and `token`) that allows a grammar author to capture multi-line content between two delimiter patterns as a single token.

```
block BODY '<<<' '>>>'
```

When the scanner encounters the opening delimiter (`<<<`), it enters block mode, buffers raw lines until it finds the closing delimiter (`>>>`), then emits a single `BODY` token whose lexeme is the content between the delimiters. The grammar author uses `BODY` exactly like any other token — no special non-terminals, no `$LINE` tokens, no mode flags in the grammar.

Example grammar usage:

```
block BODY '<<<' '>>>'
token OTHER '\S+'
skip  WS    '\s+'
%
<stuff>:Inline ::= OTHER
<stuff>:Block  ::= BODY
```

## Notes

- This is the standard scanner-level solution to heredoc-like constructs. The scanner absorbs all the complexity; the parser sees a clean single token.
- The scanner must become stateful across lines: when the opening delimiter is matched mid-line, it switches to buffering mode and keeps consuming lines until the closing delimiter is found.
- The lexeme of the `block` token should contain only the content between the delimiters (not the delimiters themselves), consistent with how languages typically expose heredoc content.
- Semantic code that needs line-by-line access can call `splitlines()` on the lexeme — no PLCC machinery required.
- This eliminates the need for the `^^`-prefixed sentinel hack and the `<lines> **= <>` empty-non-terminal pattern that the original PLCC used to approximate this behavior.
