# plcc-trees Error Handling Design

**Date:** 2026-05-15

## Motivation

`plcc-scan` is the model for how a PLCC pipeline tool should work: `plcc-tokens`
emits a JSONL stream of records (tokens and errors interleaved), and `plcc-scan`
iterates them uniformly and renders each one. Errors are not special — they are
just records.

`plcc-parse` does not follow this model. `plcc-parser-table` emits a single
record (a tree *or* an error, never both), `plcc-parse` special-cases empty
stdout as a "need more input" signal, and `IncompleteInputError` is signalled
by producing no output rather than emitting a record. This causes several bugs
and limits capability.

This design makes `plcc-parse` work like `plcc-scan`.

**Issues resolved:** 008 (multi-program streaming), 012 (error record missing
source position), 019 (parse error not student-friendly), 022 (extra tokens
suppresses tree).

---

## Design

### 1. Rename: `plcc-tree` → `plcc-trees`

The tool is renamed to reflect that it can now emit multiple tree records in one
invocation. The dispatcher logic in `tree_cli.py` is otherwise unchanged — it
still finds the parser plugin and pipes stdin/stdout through it.

Plugin names (`plcc-parser-table`, `plcc-parser-list`) are unchanged.

---

### 2. `plcc-tokens` emits a `$` sentinel at EOF

When `plcc-tokens` reaches end of input (stdin closed, file exhausted),
it emits one final record:

```json
{"kind": "token", "name": "$", "lexeme": "", "source": {"file": "...", "line": N, "column": M}}
```

The source position is immediately after the last token (or line 1, column 1
for empty input).

This guarantees that `plcc-parser-table` always has a well-defined end-of-stream
marker. `IncompleteInputError` ("hit end of token stream mid-parse") becomes
impossible — it becomes a regular `ParseError`: `"expected X, got $"`.

---

### 3. `predictive_parser.py`: API change and `IncompleteInputError` removal

**Signature change:**

```python
# Before
def parse(ll1: dict, tokens: list) -> dict

# After
def parse(ll1: dict, tokens: list) -> tuple[dict, int]
```

Returns `(tree, consumed_count)` where `consumed_count` is the number of tokens
consumed (not counting `$`). The function no longer raises on trailing tokens —
it stops at the first unconsumed token and returns.

**`IncompleteInputError` removed.** Because `$` is always present in the token
stream, an unexpected end-of-input is a `ParseError` where the offending token
is `$`. The distinction between "hit EOF" and "bad token" disappears.

**`ParseError` carries source.** The exception gains a `source` field holding
the offending token's source dict:

```python
class ParseError(Exception):
    def __init__(self, message, source=None):
        super().__init__(message)
        self.source = source or {}
```

Every `raise ParseError(...)` in `predictive_parser.py` is updated to pass the
offending token's `source`. Messages use `name` not the Python dict literal
(fixing issue 019's position-format problem at the source).

---

### 4. `plcc-parser-table`: skip-and-retry loop, JSONL stream output

The single-record emit is replaced by a loop:

```python
cursor = 0
while tokens[cursor]["name"] != "$":
    try:
        tree, consumed = parse(ll1, tokens[cursor:])
        print(json.dumps(tree), flush=True)
        cursor += consumed
    except ParseError as e:
        record = {
            "kind": "error",
            "message": str(e),
            "stage": "plcc-parser-table",
            "source": e.source,
        }
        print(json.dumps(record), flush=True)
        cursor += 1
```

**On success:** emit the tree record, advance cursor by consumed tokens, and
immediately try again from the next token. This naturally handles multiple
programs in one input (issue 008) and the trailing-tokens case (issue 022):
the tree is emitted first, then any remaining tokens produce errors.

**On error:** emit an error record for the token at `cursor`, advance by one,
and retry from the next token. This mirrors how `plcc-tokens` handles an
unrecognised character: emit an error for that position, advance, try again.

**Cascading errors** at end of incomplete input are expected and acceptable.
Each error is one short line when rendered by `plcc-parse` — the same pattern
students already see from `plcc-scan`.

**Lex error passthrough is unchanged.** If any lex error records are present
in the token stream, they are passed through to stdout and the parse loop does
not run. This is existing behaviour; revisiting it is left to a future issue.

**Exit code:** `plcc-parser-table` exits 0 as long as it ran normally, matching
`plcc-tokens` behaviour. Callers determine success by inspecting records.

---

### 5. `plcc-parse`: uniform record iteration

`ParseHandler.feed()` is rewritten to mirror `ScanHandler.feed()`:

```python
def feed(self, content, source):
    # ... run plcc-tokens | plcc-trees subprocess ...
    had_output = False
    for raw in stdout.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        record = json.loads(raw)
        had_output = True
        if record.get("kind") == "error":
            loc = _location_str(record.get("source", {}))
            stage = record.get("stage", "plcc-parse")
            message = record.get("message", "error")
            print(f"{loc}: error: {message}", file=sys.stderr)
            self.had_error = True
        elif record.get("kind") == "tree":
            _print_tree(record, indent=0)
    return had_output
```

- No empty-stdout special case.
- No `"kind" == "error"` early return — both trees and errors are rendered
  in the order they arrive.
- `had_error` flag is retained: `plcc-parse` exits 1 if any parse errors were
  seen, matching current behaviour.
- Returns `True` if any records were emitted, `False` if stdout was empty (used
  by `SourceRunner` in `EOF` mode to distinguish "nothing happened" from a real
  result — see §6).

**Error rendering** uses `file:line:col: error: message` format throughout,
fixing issue 019's student-facing presentation.

---

### 6. `SourceRunner`: explicit `submit_on` parameter

The implicit "feed returns False = need more input" contract is removed.
`SourceRunner` gains a required `submit_on` parameter:

```python
class SubmitOn(enum.Enum):
    EOL = "eol"   # each newline submits — plcc-scan
    EOF = "eof"   # ^D submits — plcc-parse

class SourceRunner:
    def __init__(self, submit_on, hint=HINT, prompt=PROMPT, continuation=CONTINUATION):
        ...
```

**`SubmitOn.EOL` (plcc-scan):** behaviour is unchanged. After each newline,
`feed()` is called immediately. The handler always returns True (scan always
produces output), so the buffer always resets. Continuation prompt is never
shown.

**`SubmitOn.EOF` (plcc-parse):** newlines accumulate — each new line appends to
the buffer and switches to the `...` prompt. `feed()` is only called when ^D
is received (empty line = true EOF, or partial line = ^D mid-typing). Blank
lines also accumulate rather than force-submitting.

`SubmitOn` is defined in `source_runner.py`; importers pull it from there.

Call sites:

```python
# plcc/cmd/scan.py
runner = SourceRunner(submit_on=SubmitOn.EOL)

# plcc/cmd/parse.py
runner = SourceRunner(submit_on=SubmitOn.EOF)
```

---

## Summary of changes by file

| File | Change |
|---|---|
| `tokens/tokens_cli.py` | Emit `$` sentinel token at EOF |
| `tree_cli.py` | Rename `plcc-tree` → `plcc-trees` in `__doc__` and entry point |
| `parser/predictive_parser.py` | Remove `IncompleteInputError`; `parse()` returns `(tree, consumed)`; `ParseError` carries `source` |
| `parser/table_cli.py` | Replace single-emit with skip-and-retry loop; add `source` to error records |
| `cmd/parse.py` | Rewrite `ParseHandler.feed()` for uniform record iteration; update error rendering |
| `cmd/source_runner.py` | Add `SubmitOn` enum; make `submit_on` a required parameter; implement `EOF` accumulation mode |
| `cmd/scan.py` | Pass `submit_on=SubmitOn.EOL` to `SourceRunner` |

---

## Issues resolved

| Issue | Description | How resolved |
|---|---|---|
| 008 | Multi-program streaming | Loop naturally emits multiple trees from one input |
| 012 | Error record missing source position | `ParseError` carries source; error records include `source` field |
| 019 | Parse error not student-friendly | Uniform rendering uses `file:line:col: error: message`; no raw JSON on stderr |
| 022 | Extra tokens suppresses tree | Tree is emitted before the trailing-token error in the loop |
