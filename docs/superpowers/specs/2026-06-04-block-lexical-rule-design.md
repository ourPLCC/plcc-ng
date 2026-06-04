# Block Lexical Rule Design

**Date:** 2026-06-04
**Issue:** 060

## Problem

The lexical section supports single-line `token` and `skip` rules. There is no way to capture multi-line content (heredoc-like constructs, multi-line comments, code blocks) as a single token. The original PLCC approximated this with a `^^`-prefixed sentinel hack and an empty `<lines> **= <>` non-terminal — scanner-level machinery that pollutes the grammar with structural noise.

## Decision

Extend `token` and `skip` rules with an optional second pattern. When a second pattern is present, the rule is a block rule: the first pattern is the open delimiter, the second is the close delimiter. The scanner enters block mode when the open delimiter wins the match competition, buffers all content until the close delimiter is found, and emits a single `Token` or `Skip` whose lexeme is the content between the delimiters (exclusive).

```
skip MULTILINE_COMMENT '/\*' '*\/'
token CODE_BLOCK       '<<<' '>>>'
```

Both patterns are regexes, consistent with existing single-pattern rules. No new keyword is introduced — the presence of a second pattern is sufficient.

## Data Model

### Replace `LexicalRule` with two concrete rule types

`LexicalRule` (the existing dataclass with `isSkip: bool`) is deleted and replaced with:

**`TokenRule`** and **`SkipRule`** (in `src/plcc/spec/lexical/`):

```python
@dataclass
class TokenRule:
    line: Line
    name: str
    pattern: str
    close_pattern: str | None = None

@dataclass
class SkipRule:
    line: Line
    name: str
    pattern: str
    close_pattern: str | None = None
```

Each has a `make_match(match, line, index)` method:
- `close_pattern is None` → returns `Token` (TokenRule) or `Skip` (SkipRule)
- `close_pattern is set` → returns `BlockOpened(rule=self, lexeme=..., line=..., column=...)`

Each has a `make_block_result(lexeme, line, column)` method:
- `TokenRule` → returns `Token`
- `SkipRule` → returns `Skip`

`make_block_result` is called by `Scanner._scanBlock` once block content is assembled. It is never called on rules where `close_pattern is None`.

### `LexicalRule` Protocol

A `typing.Protocol` named `LexicalRule` (in `src/plcc/spec/lexical/LexicalRule.py`, replacing the existing dataclass) defines the shared interface:

```python
class LexicalRule(Protocol):
    line: Line
    name: str
    pattern: str
    close_pattern: str | None
    def make_match(self, match, line, index) -> Token | Skip | BlockOpened: ...
    def make_block_result(self, lexeme: str, line: Line, column: int) -> Token | Skip: ...
```

`TokenRule` and `SkipRule` satisfy this protocol structurally — no inheritance required.

**Circular import note:** The Protocol's `make_match` return type includes `BlockOpened` (from `src/plcc/scan/`), but `BlockOpened.rule` references `TokenRule | SkipRule` (from `src/plcc/spec/lexical/`). Resolve with `TYPE_CHECKING` guards: use `if TYPE_CHECKING:` imports and string-quoted annotations in both files so the cycle is type-checker-only and does not exist at runtime.

### New scan types

**`BlockOpened`** (new, in `src/plcc/scan/`): sentinel returned by `Matcher`, never yielded to callers.

```python
@dataclass
class BlockOpened:
    rule: TokenRule | SkipRule   # carries close_pattern and make_block_result
    lexeme: str                  # the matched open-delimiter text
    line: Line
    column: int
```

**`UnclosedBlockError`** (new, in `src/plcc/scan/`): yielded when EOF is reached while in block mode.

```python
@dataclass
class UnclosedBlockError:
    line: Line      # opening delimiter's line
    column: int     # opening delimiter's column
    rule: TokenRule | SkipRule
```

### `LexicalSpec`

`ruleList: list[LexicalRule]` — the Protocol type. `TokenRule` and `SkipRule` instances (with or without `close_pattern`) all satisfy it. No separate block rule list.

## Matcher

`Matcher` requires no algorithmic changes. The open pattern of a block rule competes in the same first-longest-match algorithm as all other rules (established by issue 056). Declaration-order tiebreaking applies uniformly.

The only change: `_makeSkipOrToken(match, rule, line, index)` becomes `rule.make_match(match, line, index)`. The dispatch moves into the rule. `_getLongestMatch` is unchanged — it compares by `len(m.lexeme)`, which works for `BlockOpened` as well as `Token` and `Skip`.

`Matcher.match` now returns `Token | Skip | BlockOpened | LexError`.

## Lexical Spec Parser

`Parser._processLine` is extended to parse an optional second delimited pattern after the first.

Current flow: keyword → name → first pattern → trailing comment check.

New flow: keyword → name → first pattern → **optional second pattern** → trailing comment check.

After parsing the first pattern, the parser peeks at the remaining string. If a non-whitespace character is found (the opening delimiter of a second pattern), it parses a second delimited pattern using the same delimiter logic. If the remainder is blank or a comment, no second pattern is present.

On success:
- One pattern → `TokenRule` or `SkipRule` with `close_pattern=None`
- Two patterns → `TokenRule` or `SkipRule` with `close_pattern` set

Error cases for the second pattern reuse the same error types as the first: `PatternCompilationError`, `PatternDelimiterExpected`, `UnexpectedContent`. No new error types are needed.

## Scanner

`scan(lines)` is restructured to expose the line iterator to `_scanLine`:

```python
def scan(self, lines):
    it = iter(lines)
    for line in it:
        yield from self._scanLine(line, it)
```

`_scanLine(line, it, start=0)` gains `it` (the shared iterator) and an optional `start` index so that the tail of a close-delimiter line can be scanned from mid-line. When `matcher.match` returns `BlockOpened`, `_scanLine` delegates to `_scanBlock` and returns — `_scanBlock` owns all output from that point until the block closes.

**`_scanBlock(opened, line, start, it)`:**

1. Compile `opened.rule.close_pattern` into a regex.
2. Search for the close pattern in `line.string[start:]` (tail of the opening line). This handles the same-line case — `'<<<content>>>'` — without special casing. All match positions below are absolute indices into `line.string`, computed as `start + match.start()` / `start + match.end()`.
3. **Close found on the opening line:** `lexeme = line.string[start:abs_close_start]`; yield `opened.rule.make_block_result(lexeme, opened.line, opened.column)`; yield from `_scanLine(line, it, start=abs_close_end)`.
4. **Close not found on opening line:** `buffer = line.string[start:]`; consume lines from `it`:
   - Close found on a subsequent line: search `line.string` from position 0; `buffer += '\n' + line.string[:match.start()]`; yield `opened.rule.make_block_result(buffer, opened.line, opened.column)`; yield from `_scanLine(line, it, start=match.end())`.
   - Close not found on a subsequent line: `buffer += '\n' + line.string`; continue.
   - Iterator exhausted: yield `UnclosedBlockError(line=opened.line, column=opened.column, rule=opened.rule)`.

The `Token` or `Skip` emitted in all success cases carries the opening delimiter's `line` and `column`.

## Compatibility note

The "skip priority" asymmetry (where a skip could preempt a longer block open) was eliminated by issue 056 before this feature was designed. All patterns — skips, tokens, and block opens — compete uniformly under first-longest-match.
