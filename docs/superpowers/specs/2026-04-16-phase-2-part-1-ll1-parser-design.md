# Phase 2 Part 1: LL(1) Table-Driven Parser — Design

**Date:** 2026-04-16 (finalized 2026-04-19)
**Status:** APPROVED
**Companion architectural spec:** [2026-04-12-multi-lang-pipeline.md](2026-04-12-multi-lang-pipeline.md) (especially §7–§9, §13)
**Roadmap reference:** [2026-04-12-multi-lang-implementation-plan.md](2026-04-12-multi-lang-implementation-plan.md) §5

## 1. Goal

Ship a complete, tested, table-driven LL(1) parser as a pipeline stage. After Part 1, `plcc-tokens < program.txt | plcc-tree --ll1 build/ll1.json` produces a parse tree for any LL(1) grammar.

## 2. Scope

Four changes ship in Part 1:

| Command | Change |
| --- | --- |
| `plcc-ll1` | Replace stub with real FIRST/FOLLOW/predict/parse-table computation, wiring up the existing plcc-ng LL(1) code |
| `plcc-parser-table` | Replace stub with real table-driven predictive parser consuming `ll1.json` |
| `plcc-spec` | Verify (or make) it a faithful translator only — remove any remaining LL(1) analysis call sites |
| `plcc-parser-list` | New command: scan PATH for `plcc-parser-*`, print one kind per line |

`plcc-tree` is already a complete dispatcher; no changes.

**Not in Part 1 scope:** Level 2 `--parser=` passthroughs, `plcc-gen-parser`, interpreter, Python emitter, `--format=human` on `plcc-ll1`.

## 3. `plcc-ll1`

### 3.1 Interface

- **Stdin:** spec JSON (stdin only; no file path argument). Callers redirect: `plcc-ll1 < build/spec.json`. The file path argument is omitted intentionally — it is unnecessary (shell redirection covers the use case) and its removal simplifies the implementation. The walking skeleton's existing optional positional is removed.
- **Stdout:** single `ll1.json` document (see §4).
- **Stderr:** errors via `VerboseContext.emit_error`; verbose events per §3.3. Errors are emitted regardless of verbose level.
- **Exit 0:** always, for any well-formed spec JSON input — including non-LL(1) grammars. A non-LL(1) result is signalled by `is_ll1: false` in the output, not by exit code.
- **Exit nonzero:** tool failures only — stdin not readable, malformed/unparseable spec JSON.

### 3.2 Implementation

Wire up the existing plcc-ng LL(1) computation code: FIRST set computation, FOLLOW set computation, predict set construction, parse table construction, conflict detection, and left-recursion cycle detection. **Do not delete or rewrite this code.** It is well-tested, student-produced work. Remove any LL(1) analysis call sites remaining in `plcc-spec`; preserve the implementation. If files must be relocated, use `git mv` to keep git history intact.

### 3.3 Verbose events

- **Level 0 (default):** silent — no stderr output regardless of whether the grammar is LL(1) or not. Errors (tool failures) are always emitted.
- **`-v`:** `started`, `finished`. The `finished` event includes a one-line summary: `is_ll1: true` or `N conflicts, M left-recursion cycles`.
- **`-vv`:** one event per nonterminal for its FIRST set (`first-set`), FOLLOW set (`follow-set`), and predict sets (`predict-set`); one `conflict` event per conflict; one `left-recursion` event per cycle.
- **`-vvv`:** one `fixpoint-step` event per iteration of the FIRST/FOLLOW closure algorithm, including what changed.

**JSONL payload shapes** (used when `--verbose-format=json`; all events share the base fields `stage`, `time`, `event` per arch spec §9.5):

| Event | Level | Additional payload fields |
| --- | --- | --- |
| `started` | 1 | _(none beyond base)_ |
| `finished` | 1 | `is_ll1: bool`, `conflicts: int`, `left_recursion_cycles: int` |
| `first-set` | 2 | `nonterminal: str`, `first: [str]` |
| `follow-set` | 2 | `nonterminal: str`, `follow: [str]` |
| `predict-set` | 2 | `nonterminal: str`, `predict: [[str]]` |
| `conflict` | 2 | `nonterminal: str`, `lookahead: str`, `productions: [[{symbol, field}]]` |
| `left-recursion` | 2 | `cycle: [str]` |
| `fixpoint-step` | 3 | `pass: int`, `changed: {nonterminal: str, set: "first"\|"follow", added: [str]}` |

**Text format** (used when `--verbose-format=text`): every line begins `plcc-ll1: <event>: <message>` per arch spec §9.4.

**Python enum note:** Event names containing hyphens (e.g. `first-set`) cannot be Python identifiers. Use enum members with underscores and set `.value` to the hyphenated string: `FIRST_SET = "first-set"`. The `VerboseContext.emit()` call receives the enum member; the hyphenated string appears in the output.

### 3.4 `--format=human` (deferred)

Human-readable rendering of `ll1.json` is deferred. The intended future shape is a separate tool (e.g. `plcc-ll1-human`) that reads `ll1.json` from stdin and renders it as readable tables, callable directly by a student or by a Level 2 orchestrator. `plcc-ll1` may later add `--format=human` as a flag that delegates to that tool. No work in Part 1.

## 4. `ll1.json` schema

Output of `plcc-ll1`. A single JSON document:

```json
{
  "is_ll1": true,
  "start_symbol": "Expr",
  "first_sets": {
    "Expr": ["NUM", "LPAREN"]
  },
  "follow_sets": {
    "Expr": ["RPAREN", "$"]
  },
  "predict_sets": {
    "Expr": [["NUM", "LPAREN"], ["MINUS"]]
  },
  "parse_table": {
    "Expr": {
      "NUM":    [{"symbol": "Term",    "field": "t"}, {"symbol": "ExprRest", "field": "r"}],
      "LPAREN": [{"symbol": "LPAREN", "field": null}, {"symbol": "Expr",     "field": "e"}, {"symbol": "RPAREN", "field": null}]
    },
    "ExprRest": {
      "$":      [],
      "RPAREN": []
    }
  },
  "conflicts": [
    {
      "nonterminal": "Stmt",
      "lookahead": "IF",
      "productions": [
        [{"symbol": "IF", "field": null}, {"symbol": "Expr", "field": "cond"}, {"symbol": "Stmt", "field": "then"}],
        [{"symbol": "IF", "field": null}, {"symbol": "Expr", "field": "cond"}, {"symbol": "Stmt", "field": "then"}, {"symbol": "ELSE", "field": null}, {"symbol": "Stmt", "field": "els"}]
      ]
    }
  ],
  "left_recursion": [
    {"cycle": ["A", "B", "A"]}
  ]
}
```

### Field definitions

- **`is_ll1`** — boolean. True iff `conflicts` and `left_recursion` are both empty.
- **`start_symbol`** — string. The grammar's start symbol; used by `plcc-parser-table` to initialise the parse stack.
- **`first_sets`** — nonterminal → array of terminal-name strings. The empty string `""` represents ε (the nonterminal can derive the empty string).
- **`follow_sets`** — nonterminal → array of terminal-name strings. `"$"` is the end-of-input marker (conventional notation; `$` is not a valid token name). `$` appearing in a FOLLOW set means the nonterminal may appear at the end of a complete input.
- **`predict_sets`** — nonterminal → array of arrays of terminal-name strings, one inner array per alternative in grammar order. Each inner array lists the terminals (and possibly `$`) that select that alternative. A conflict is visible here when the same terminal appears in two inner arrays for the same nonterminal.
- **`parse_table`** — nonterminal → lookahead → single production. Each production is an array of `{"symbol": <name>, "field": <string|null>}` objects. `field: null` means the symbol is elided from the parse tree; a non-null string is the child's field name in the tree. The lookahead key is the terminal's name string (matching the `name` field in token JSONL), or `"$"` for end-of-input. Empty productions (`[]`) represent ε-derivations. When `is_ll1` is false, conflicting cells are **omitted** from the parse table; the `conflicts` array is the authoritative diagnostic. The parse table is only reliable for parsing when `is_ll1` is true.
- **`conflicts`** — array; empty when `is_ll1` is true. Each entry: `{"nonterminal": <str>, "lookahead": <str>, "productions": [[...], [...]]}`. The `productions` field lists all competing productions in full (each as an array of `{symbol, field}` objects) so the reader can diagnose the conflict without scanning the parse table.
- **`left_recursion`** — array; empty when no left recursion is detected. Each entry: `{"cycle": [...]}` where the array lists the nonterminals forming the left-recursive cycle, with the first nonterminal repeated at the end to make the cycle explicit.

**Note on field naming:** The architectural spec §7.2 uses the shorter names `first`, `follow`, `predict`. This design doc uses `first_sets`, `follow_sets`, `predict_sets` to match the walking-skeleton stub and the existing `ll1.schema.json`. The architectural spec should be amended to use the `_sets` suffix.

**Schema file deliverable:** `src/plcc/schemas/ll1.schema.json` must be updated to add `start_symbol` as a required field and to tighten the types of all fields to match the definitions above.

## 5. `plcc-parser-table`

### 5.1 Interface

- **Stdin:** token JSONL (reads to EOF).
- **`--ll1=<path>`:** required; path to `ll1.json`. Both `--ll1=<path>` and `--ll1 <path>` forms are accepted (docopt handles both).
- **Stdout:** single newline-terminated parse tree JSON document (see §6). The tree is assembled entirely in memory and written to stdout atomically only on exit 0. Nothing is written to stdout on failure.
- **Stderr:** errors via `VerboseContext.emit_error`; verbose events per §5.3. Errors are emitted regardless of verbose level.
- **Exit 0:** successful parse.
- **Exit nonzero:** syntax error in the token stream, or tool failure (missing/malformed `ll1.json`, malformed token JSONL).

### 5.2 Algorithm

Standard predictive-parsing loop. All tokens are read into memory before parsing begins.

1. **Load.** Load and parse `ll1.json`. If `is_ll1` is false, emit an error and exit nonzero — a non-LL(1) grammar cannot be parsed by this stage.
2. **Read tokens.** Read all token JSONL from stdin to EOF, collecting records into an array. Append a synthetic end-of-input sentinel with `name: "$"` after the last real token.
3. **Initialise.** Push `start_symbol` from `ll1.json` onto the parse stack. Set the lookahead cursor to the first token.
4. **Loop.** Repeat until the stack is empty:
   - Let `top` = top of stack; let `lookahead` = `name` field of the current token (or `"$"` for the sentinel).
   - **If `top` is a terminal:** If `top == lookahead`, shift: record the token, advance the cursor, pop the stack. Otherwise, emit a syntax error (unexpected token `lookahead`, expected `top`) and exit nonzero.
   - **If `top` is a nonterminal:** Look up `parse_table[top][lookahead]`. If no entry exists, emit a syntax error (unexpected token `lookahead`, no production for `top`) and exit nonzero. Otherwise, expand: pop `top`, push the production's symbols in reverse order (so the first symbol ends on top).
5. **End check.** When the stack is empty: if the current token is the `$` sentinel, the parse is successful — emit the tree and exit 0. If any non-sentinel tokens remain, emit a syntax error (unexpected token after complete parse) and exit nonzero.

**Lookahead key:** The lookahead used to index `parse_table` is the token's `name` field from the token JSONL record, or the literal string `"$"` for end-of-input. This matches the keys in `parse_table` and the terminals in `predict_sets` and `follow_sets`.

**AST elision:** Only symbols with `field` non-null in the production entry become children in the tree. Symbols with `field: null` are consumed from the token stream during the shift step but not recorded as children.

**Span computation:** When expanding a nonterminal, record the `source` position of the first token that will be consumed by the production (including any leading elided tokens). When the production is complete, record the `source` position of the last token consumed (including any trailing elided tokens). The internal node's `source` is:

- `file`, `line`, `column` — from the first token consumed by the production.
- `endLine`, `endColumn` — from the last token consumed: `endLine` is that token's `source.line`; `endColumn` is `source.column + len(lexeme) - 1` (1-indexed, inclusive — the column of the last character of the lexeme).

**Error handling:** On any syntax error, emit one structured error via `VerboseContext.emit_error` with the unexpected token's `source` position and a message naming the unexpected token and what was expected. Exit nonzero immediately. No error recovery; no partial tree.

### 5.3 Verbose events

- **Level 0 (default):** silent — no stderr output on success.
- **`-v`:** `started`, `finished`.
- **`-vv`:** `expand`, `shift`, `complete`.
- **`-vvv`:** `predict-lookup`.

**JSONL payload shapes:**

| Event | Level | Additional payload fields |
| --- | --- | --- |
| `started` | 1 | `ll1_path: str` |
| `finished` | 1 | `token_count: int`, `rule_count: int` |
| `expand` | 2 | `nonterminal: str`, `production: [{symbol: str, field: str\|null}]` |
| `shift` | 2 | `name: str`, `lexeme: str`, `source: {file, line, column}` |
| `complete` | 2 | `nonterminal: str` |
| `predict-lookup` | 3 | `nonterminal: str`, `lookahead: str`, `production: [{symbol, field}]` |

**Text format:** every line begins `plcc-parser-table: <event>: <message>` per arch spec §9.4.

**Python enum note:** `predict-lookup` cannot be a Python identifier. Use `PREDICT_LOOKUP = "predict-lookup"` in the `Events` enum. Pass the enum member to `VerboseContext.emit()`; the hyphenated string appears in the output.

## 6. Parse tree schema

Output of `plcc-parser-table` (and transitively of any `plcc-parser-<kind>` plugin).

### Internal node

```json
{
  "kind": "tree",
  "rule": "Expr",
  "source": {
    "file": "prog.txt",
    "line": 4,
    "column": 12,
    "endLine": 4,
    "endColumn": 25
  },
  "children": [
    ["left", {"kind": "tree", "rule": "Term", "source": {"file": "prog.txt", "line": 4, "column": 12, "endLine": 4, "endColumn": 13}, "children": [...]}],
    ["op",   {"kind": "token", "name": "PLUS", "lexeme": "+", "source": {"file": "prog.txt", "line": 4, "column": 15}}],
    ["right",{"kind": "tree", "rule": "Term", "source": {"file": "prog.txt", "line": 4, "column": 17, "endLine": 4, "endColumn": 25}, "children": [...]}]
  ]
}
```

### Token leaf

Placed unchanged from `plcc-tokens` output — no wrapper, no modification:

```json
{"kind": "token", "name": "NUM", "lexeme": "42", "source": {"file": "prog.txt", "line": 4, "column": 12}}
```

### Design rules

- **`children`** is an array of `[field_name, node]` two-element arrays. Only named (non-elided) symbols appear; elided symbols are absent.
- **`source` on internal nodes** spans the full production extent including elided tokens, computed before elision. Fields: `file`, `line`, `column`, `endLine`, `endColumn`. `endColumn` is the column of the last character of the last token consumed (1-indexed, inclusive). Formula: `endColumn = last_token.source.column + len(last_token.lexeme) - 1`.
- **`source` on token leaves** is the token's own position as emitted by `plcc-tokens`. Fields: `file`, `line`, `column` (no end position — the extent is derivable from `lexeme` length using the same formula).
- **Discriminator:** `kind: "tree"` vs `kind: "token"`. Internal nodes always have `children`; token leaves never do.

**Schema file deliverable:** `src/plcc/schemas/tree.schema.json` must be updated to reflect the `[field_name, node]` children structure. The existing schema (which defines `children` as an array of objects with a `kind` field) is superseded by this design.

## 7. `plcc-spec` changes

Inspect `plcc-spec`'s source for any LL(1)-related imports or call sites (FIRST/FOLLOW/predict set computation, parse table construction, conflict checking). If none are found — which is likely given the walking skeleton already separates the two — add a short code comment in `plcc-spec`'s main module confirming the separation: `# No LL(1) analysis here; see plcc-ll1.`. If LL(1) call sites are found, remove them and add the comment. The LL(1) computation code itself is not touched.

## 8. `plcc-parser-list`

New command. Scans PATH for executables matching `plcc-parser-*`, strips the `plcc-parser-` prefix, and prints one parser kind per line. Symmetric with `plcc-lang-list`. No required arguments. **Must accept `--verbose` and `--verbose-format`** (per arch spec §9, accept-and-propagate is mandatory for every stage; nothing is emitted at any level, but the flags must not be rejected).

## 9. Deferred items

| Item | Deferred to |
| --- | --- |
| `--format=human` on `plcc-ll1` | Future phase; will delegate to a separate `plcc-ll1-human` tool |
| Level 2 `--parser=` passthroughs | Part 2 / Phase 4 |
| `plcc-gen-parser` (recursive-descent generation) | Phase 3+ |
| `plcc-parse` human-friendly UX (v8-style trace) | Part 2 |
| Interpreter, Python emitter, REPL | Part 2 |
| Entry-point method name (`$run()` replacement) | Part 2 |
| Left-factoring candidate detection in `plcc-ll1` | Phase 3+ |
| Scanner pluggability | Post-v9 |
| Dynamic verbosity mid-session | Future amendment |
