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

- **Stdin:** spec JSON (stdin only). Callers redirect: `plcc-ll1 < build/spec.json`.
- **Stdout:** single `ll1.json` document (see §4).
- **Stderr:** errors via `VerboseContext.emit_error`; verbose events per §3.3. Errors are emitted regardless of verbose level.
- **Exit 0:** always, for any well-formed spec JSON input — including non-LL(1) grammars. A non-LL(1) result is signalled by `is_ll1: false` in the output, not by exit code.
- **Exit nonzero:** tool failures only — stdin not readable, malformed/unparseable spec JSON.

### 3.2 Implementation

Wire up the existing plcc-ng LL(1) computation code: FIRST set computation, FOLLOW set computation, predict set construction, parse table construction, conflict detection, and left-recursion cycle detection. **Do not delete or rewrite this code.** It is well-tested, student-produced work. Remove any LL(1) analysis call sites remaining in `plcc-spec`; preserve the implementation. If files must be relocated, use `git mv` to keep git history intact.

### 3.3 Verbose events

- **Level 0 (default):** silent — no stderr output on success.
- **`-v`:** `started`, `finished` with one-line summary (`is_ll1: true` or `N conflicts, M left-recursion cycles`).
- **`-vv`:** per-nonterminal FIRST, FOLLOW, and predict sets; each conflict with its competing productions named; each left-recursion cycle.
- **`-vvv`:** individual fixpoint iteration steps for FIRST/FOLLOW closure.

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
      "NUM": [{"symbol": "Term", "field": "t"}, {"symbol": "ExprRest", "field": "r"}],
      "LPAREN": [{"symbol": "LPAREN", "field": null}, {"symbol": "Expr", "field": "e"}, {"symbol": "RPAREN", "field": null}]
    }
  },
  "conflicts": [
    {
      "nonterminal": "Expr",
      "lookahead": "PLUS",
      "productions": [
        [{"symbol": "PLUS", "field": null}, {"symbol": "Expr", "field": "right"}],
        []
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
- **`first_sets`** — nonterminal → list of terminal names. The empty string `""` represents ε.
- **`follow_sets`** — nonterminal → list of terminal names. `"$"` is the end-of-input marker (conventional notation; not a valid token name).
- **`predict_sets`** — nonterminal → list of predict sets, one per alternative in grammar order. Each predict set is a list of terminals that select that alternative. A conflict is visible here when the same terminal appears in two inner lists.
- **`parse_table`** — nonterminal → lookahead → single production. Each production is a list of `{"symbol": <name>, "field": <string|null>}` objects. `field: null` means the symbol is elided from the parse tree; a non-null string is the child's field name. The parse table is only authoritative when `is_ll1` is true; conflicting cells are omitted or contain an arbitrary one of the competing productions.
- **`conflicts`** — array; empty when `is_ll1` is true. Each entry: `{"nonterminal": ..., "lookahead": ..., "productions": [[...], [...]]}`. The `productions` field is the self-contained diagnostic — it lists all competing productions in full so the reader can diagnose the conflict without scanning the parse table.
- **`left_recursion`** — array; empty when no left recursion is detected. Each entry: `{"cycle": [...]}` — the list of nonterminals forming the left-recursive cycle.

## 5. `plcc-parser-table`

### 5.1 Interface

- **Stdin:** token JSONL (reads to EOF).
- **`--ll1=<path>`:** required; path to `ll1.json`.
- **Stdout:** single newline-terminated parse tree JSON document (see §6).
- **Stderr:** errors via `VerboseContext.emit_error`; verbose events per §5.3. Errors emitted regardless of verbose level.
- **Exit 0:** successful parse.
- **Exit nonzero:** syntax error in the token stream, or tool failure (missing/malformed `ll1.json`, malformed token JSONL). No partial tree emitted.

### 5.2 Algorithm

Standard predictive-parsing loop:

1. Load `ll1.json`. Check `is_ll1`; exit with an error if false — a non-LL(1) grammar cannot be parsed by this stage.
2. Read all token JSONL from stdin.
3. Push the grammar's start symbol. Maintain a parse stack and a position cursor into the token stream.
4. At each step:
   - If top-of-stack is a terminal: match against the current token (shift). If mismatch, emit error and exit nonzero.
   - If top-of-stack is a nonterminal: look up `parse_table[nonterminal][lookahead]` (expand). If no entry, emit error and exit nonzero.
5. On successful parse: emit the tree and exit 0.

**AST elision:** Only symbols with `field` non-null in the production entry become children in the tree. Symbols with `field: null` are consumed from the token stream but not included as children.

**Span computation:** Internal node `source` spans the full extent of the production — from the first token consumed to the last, including elided tokens. Computed before elision so positions are correct even when punctuation is dropped.

**Error handling:** On any syntax error, emit one structured error via `VerboseContext.emit_error` with the unexpected token's `source` position and a message naming the unexpected token and what was expected. Exit nonzero immediately. No error recovery; no partial tree.

### 5.3 Verbose events

- **Level 0 (default):** silent — no stderr output on success.
- **`-v`:** `started`, `finished` (with token count and rule count).
- **`-vv`:** `expand` (nonterminal being expanded + production RHS), `shift` (token name, lexeme, position), `complete` (nonterminal name). Together these three event types give a Level 2 orchestrator enough information to reconstruct a full nested, indented parse trace.
- **`-vvv`:** `predict-lookup` (nonterminal + lookahead + parse table entry consulted).

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
    ["left", {"kind": "tree", "rule": "Term", "source": {...}, "children": [...]}],
    ["op",   {"kind": "token", "name": "PLUS", "lexeme": "+", "source": {...}}],
    ["right",{"kind": "tree", "rule": "Term", "source": {...}, "children": [...]}]
  ]
}
```

### Token leaf

Placed unchanged from `plcc-tokens` output — no wrapper, no modification:

```json
{"kind": "token", "name": "NUM", "lexeme": "42", "source": {"file": "prog.txt", "line": 4, "column": 12}}
```

### Design rules

- **`children`** is a list of `[field_name, node]` pairs. Only named (non-elided) symbols appear; elided symbols are absent.
- **`source` on internal nodes** spans the full production extent including elided tokens, computed before elision. Fields: `file`, `line`, `column`, `endLine`, `endColumn`.
- **`source` on token leaves** is the token's own position as emitted by `plcc-tokens`. Fields: `file`, `line`, `column` (no end position — token extent is derivable from `lexeme` length).
- **Discriminator:** `kind: "tree"` vs `kind: "token"`. Internal nodes always have `children`; token leaves never do.

## 7. `plcc-spec` changes

Remove any LL(1) analysis call sites remaining inside `plcc-spec`. The implementation of FIRST/FOLLOW/predict/parse-table computation is preserved — only calls to it from `plcc-spec` are removed. `plcc-spec` becomes a faithful grammar-to-JSON translator with no analysis. If the walking skeleton already reflects this separation, verify and document; no further change required.

## 8. `plcc-parser-list`

New command. Scans PATH for executables matching `plcc-parser-*`, strips the `plcc-parser-` prefix, and prints one parser kind per line. Symmetric with `plcc-lang-list`. No required arguments. Accepts `--verbose`/`--verbose-format` (nothing to emit at any level).

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
