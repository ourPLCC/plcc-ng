# Design: `plcc-scan --trace` Output Readability (Issue 117)

## Goal

Redesign the `--trace` output of `plcc-scan` to be clearly readable by students learning how the first-longest-match scanning algorithm works. The output should make each step of the algorithm — what position is being scanned, which rules competed, and which rule won and why — immediately obvious without explanation.

## Audience

Students learning the scanning algorithm. The primary value of `--trace` is educational: showing all the rules that competed at each position and making the winner and the reason for winning explicit.

## Output Format

Each scan step produces one block. Blocks are separated by a blank line.

### Block structure

```
Scanning <file>:<line>:<col>:
<source_line><↵ if line ends with newline; tabs replaced with →>
<caret pointing to scan column>

Candidates:
<table>
* longest match wins; ties broken by earliest rule (#)

Result:
<type> <Name> '<pattern>' '<lexeme>'
```

### Source line display

- The raw source line is printed with no indentation.
- If the line ends with a newline character, `↵` is appended so the caret can land on it.
- Tab characters in the source line are replaced with `→` (one character per tab) so the caret column stays accurate.
- The caret (`^`) is placed on the next line, offset by `col - 1` spaces.

### Candidates table

Only rules that matched one or more characters appear. Rules that failed to match are omitted.

Columns (in order): `#`, `Type`, `Name`, `Pattern`, `Len`, `Match`

| Column | Content |
|--------|---------|
| `#` | Declaration order of the rule in the spec (1-based) |
| `Type` | `token` or `skip` |
| `Name` | Rule name (e.g. `NUM`) |
| `Pattern` | The regex pattern (e.g. `'\d+'`) |
| `Len` | Number of characters matched |
| `Match` | The matched lexeme in single quotes |

Column values are space-aligned. A header row appears above the data rows.

#### Winner marker

One `*` appears in the table, on the value that decided the winner:

- **No tie:** `*` is placed after the `Len` value of the winning row (longest match).
- **Tie** (two or more rows share the highest `Len`): `*` is placed after the `#` value of the winning row (earliest rule in spec).

A legend line appears immediately below the table:

```
* longest match wins; ties broken by earliest rule (#)
```

### Result line

```
Result:
<type> <Name> '<pattern>' '<lexeme>'
```

For example: `token NUM '\d+' '42'` or `skip WS '\s+' '\n'`.

## Examples

### No tie

Input: `42` (spec has `token ONE '\d'`, `token NUM '\d+'`, `skip WS '\s+'`)

```
Scanning -:1:1:
42↵
^

Candidates:
#   Type   Name  Pattern  Len   Match
1   token  ONE   '\d'     1     '4'
2   token  NUM   '\d+'    2*    '42'
* longest match wins; ties broken by earliest rule (#)

Result:
token NUM '\d+' '42'

Scanning -:1:3:
42↵
  ^

Candidates:
#   Type  Name  Pattern  Len  Match
3   skip  WS    '\s+'    1    '\n'
* longest match wins; ties broken by earliest rule (#)

Result:
skip WS '\s+' '\n'
```

### Tie broken by position

Input: `+` (spec has `token PLUS '\+'` at position 1, `token OP '[+]'` at position 2)

```
Scanning -:1:1:
+↵
^

Candidates:
#    Type   Name  Pattern  Len  Match
1*   token  PLUS  '\+'     1    '+'
2    token  OP    '[+]'    1    '+'
* longest match wins; ties broken by earliest rule (#)

Result:
token PLUS '\+' '+'
```

## Scope of Changes

### Display layer (`src/plcc/cmd/scan.py`)

`_render_record` is replaced with the new block format. This is the primary change.

### Small data layer change (`src/plcc/scan/matcher.py`)

Each attempt record in the `attempts` list needs to include the rule's declaration order (`#`). Add a `rule_index` field (1-based) to each attempt dict in `Matcher.match()`. This is the only change to the JSONL data layer.

Zero-match candidates are already absent from the `attempts` field and remain omitted in the new format.

### Tests

- Update `tests/bats/commands/plcc-scan.bats` to match the new format.
- The existing tests check for specific strings (`Candidates:`, `-> NUM`, `-:1:1: token: NUM`) that will change. New tests should assert the new header, table columns, legend, and result format.
