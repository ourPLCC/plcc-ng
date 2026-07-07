# Lexical specification

The lexical specification defines what the scanner recognizes and which
matches it should emit as a token.

## Syntax

```text
skip  NAME_1 'pattern'
token NAME_2 'pattern'
```

`token` rules emit a token when matched. `skip` rules consume input silently
(useful for whitespace and comments in the language you are implementing).

### Token names

Token names are composed of capital letters, underscore, and digits.
They must start with a letter.

Examples of valid token names:

- `NAME`
- `FIRST_NAME`
- `NAME_1`

Examples of invalid token names:

- `name`
- `name`
- `FIRST-NAME`
- `_NAME`
- `1_NAME`

### Patterns

Patterns are regular expressions enclosed in single or double quotes.
They use [Python's `re` syntax](https://docs.python.org/3/library/re.html)
(the scanner runs in Python).

Patterns may be enclosed in double or single quotes. This is useful when
trying to match those same characters while avoiding escape characters.

A few common patterns:

| Pattern | Matches |
| --- | --- |
| `'\d+'` | Whole Numbers |
| `'\s+'` | Whitespace including a newline |
| `'\w+'` | A word (only alphabetic, numeric, and underscore characters) |
| `'\n'` | A newline character |
| `'[a-zA-Z_]\w*'` | An word that does not begin with a digit |
| `'\+'` | A literal `+` (escaped) |
| `'\*'` | A literal `*` (escaped) |
| `'"[^"]*"'` | A double-quoted string |
| `'.*'` | Zero or more non-newline characters |

Patterns cannot match across multiple lines.
The scanner processes input one line at
a time, so every match is limited to the current line.

A pattern may still match the newline character at the end of the current
line. For example, '\n' matches a single newline character.

## Scanning algorithm

The scanner processes input from left to right, performing the following steps:

1. Use the first-longest-match rule to select a scanner rule, or raise an error if no rule matches.
2. Consume the matching text from the front of the input.
3. If the selected rule is a token rule, emit a token. If it is a skip rule, emit nothing.

### First-longest-match rule

To select a scanner rule:

1. Match every scanner rule against the front of the input.
2. The rule whose pattern matches the most characters wins.
3. If multiple rules match the same number of characters, the rule that appears first in the grammar wins.

In short, to determine which lexical rule to apply, the scanner uses a first-longest-match rule:
it first prefers the longest matching rule, and uses rule order only to break ties.

Let's look at some examples.

#### Example: longest match wins

Rules:

```text
token EQ '='
token EQEQ '=='
```

Input:

```text
==
```

Matches:

- EQ matches 1 character.
- EQEQ matches 2 characters.

Result:

EQEQ wins because it matches more characters.

#### Example: the first, longest-match wins

Rules:

```text
token WORD '[a-z]+'
token IF 'if'
```

Input:

```text
if
```

Matches:

- WORD matches 2 characters.
- IF matches 2 characters.

Result:

The match lengths are equal, so the rule that appears first in the grammar wins.
So, an `WORD` token containing the lexeme "if" would be emitted.

#### Example: skips compete with tokens

```text
skip WORD '[a-z]+'
token IF 'if'
```

And suppose our input is:

```text
if
```

Again the WORD rule would win, but since it is now a skip rule, no token would
be emitted.
