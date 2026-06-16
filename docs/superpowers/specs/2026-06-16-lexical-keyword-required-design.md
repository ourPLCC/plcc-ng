# Design: Require `token` or `skip` in Lexical Rules (Issue 088)

**Date:** 2026-06-16
**Type:** feat

## Summary

Lexical rules must begin with an explicit `token` or `skip` keyword. A rule that omits the keyword is a syntax error. All existing fixture files already comply; only parser unit tests need updating.

## Motivation

Requiring an explicit keyword makes each rule's intent unambiguous, improves readability, and simplifies the grammar file format for both the parser and students.

## Behavior

**Valid:**
```
token NUM '\d+'
skip  SPACE '\s+'
```

**Invalid (syntax error):**
```
NUM '\d+'
```

## Architecture

The change is confined to the lexical spec parser subsystem:

```
src/plcc/spec/lexical/
  Parser.py               ← one regex change + error dispatch
  KeywordExpected.py      ← new error class (new file)
  __init__.py             ← export KeywordExpected
  parse_lexical_test.py   ← tests updated
```

No changes to fixture files, rule classes (`TokenRule`, `SkipRule`), `LexicalSpec`, or any layer above.

## Parser change (`Parser.py`)

In `_processLine`, replace the optional keyword match with a required one:

**Before:**
```python
m = re.compile(r'^\s*(token|skip)?').match(string, index)
type_ = m[1] if m[1] is not None else 'token'
index += len(m[0])
```

**After:**
```python
m = re.compile(r'^\s*(token|skip)').match(string, index)
if m is None:
    wsl = self._getLengthOfLeadingWhitespace(string, index)
    self.errors.append(KeywordExpected(line=line, index=index + wsl))
    return
type_ = m[1]
index += len(m[0])
```

When the keyword is absent: one `KeywordExpected` error is collected, the line is skipped, and parsing continues on the next line — identical to how `NameExpected`, `PatternExpected`, and other line-level errors work.

## New error class (`KeywordExpected.py`)

```python
from .LexicalSpecError import LexicalSpecError

class KeywordExpected(LexicalSpecError):
    def __init__(self, line, index=None, column=None):
        super().__init__(line=line, index=index, column=column,
            message="Expected 'token' or 'skip'."
        )
```

Exported from `__init__.py` alongside the other error classes.

## Test updates (`parse_lexical_test.py`)

**Tests whose bare-name input was incidental** — add `token` keyword so each test keeps testing its original concern:
- `test_choice_of_pattern_delimiter`
- `test_trailing_comment`
- `test_no_leading_space_required`
- `test_names_start_with_uppercase_or_underscore_and_may_contain_numbers`
- `test_two_duplicate_names`
- `test_multiple_of_same_duplication`

**Tests whose purpose was the implicit-token behavior itself** — repurposed to test the new error:
- `test_implicit_token_rule` → renamed `test_keyword_is_required`; asserts one `KeywordExpected` error and zero rules
- `test_implicit_token_produces_TokenRule` → removed (redundant with the above)

**Unaffected:** `test_no_space` (`tokenSPACE' '`) — the literal string `token` is present, just without a space before the name.

## Error handling

Consistent with all other line-level errors in `Parser._processLine`: error is appended to `self.errors`, method returns early, no rule is added for that line, parsing continues.
