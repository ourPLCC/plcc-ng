# Token Rules

The lexical section of a `.plcc` file defines what the scanner recognizes.
Each line is either a `token` rule, a `skip` rule, or a comment.

## Syntax

```text
token NAME 'pattern'
skip  NAME 'pattern'
# This is a comment
```

`token` rules emit a token when matched. `skip` rules consume input silently
(useful for whitespace and comments in the language you are implementing).

### Naming rules

Token names must be all uppercase letters, digits, and underscores, starting
with a letter:

```text
token PLUS   '\+'
token WHOLE  '\d+'
skip  SPACE  '\s+'
skip  COMMENT '#[^\n]*'
```

### Patterns

Patterns are regular expressions enclosed in single or double quotes.
They follow Java `Pattern` syntax.

<!-- TODO: verify plcc-ng uses Java Pattern syntax or Python re syntax -->

A few common patterns:

| Pattern | Matches |
| --- | --- |
| `'\d+'` | One or more digits |
| `'\s+'` | One or more whitespace characters |
| `'[a-zA-Z_]\w*'` | An identifier |
| `'\+'` | A literal `+` (escaped) |
| `'"[^"]*"'` | A double-quoted string |

Patterns **cannot match across newlines**.

## Scan algorithm

The scanner processes input left-to-right, one rule at a time:

1. Find all rules whose pattern matches a non-empty prefix of the remaining input.
2. If none match, emit a lexical error and stop.
3. Among matching rules, prefer `skip` rules over `token` rules.
   Apply the first-listed skip rule that matches.
4. Among matching `token` rules, choose the one with the longest match.
   Break ties by taking the first-listed rule.
5. Remove the matched text from the input. If it was a `token` rule, emit the token.
6. Repeat from step 1.

The scanner emits tokens one at a time. The parser reads them on demand.
