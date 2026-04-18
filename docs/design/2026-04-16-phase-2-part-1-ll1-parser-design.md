# Phase 2 Part 1: LL(1) Table-Driven Parser — Design

**Date:** 2026-04-16
**Status:** DRAFT — This design was produced during the Phase 2 Part 1 brainstorm but has not been through the full approval cycle. It needs to be revisited after the walking skeleton is updated to reflect architectural amendments §17.3–§17.9. Several decisions captured here (parse tree schema, error shape, verbose protocol) are load-bearing and settled; the implementation scope and sequencing are not yet committed. The error shape is now settled per §17.9 (stderr + exit code; no tree-embedded errors).
**Companion architectural spec:** [2026-04-12-multi-lang-pipeline.md](2026-04-12-multi-lang-pipeline.md) (especially §17.3–§17.8)
**Roadmap reference:** [2026-04-12-multi-lang-implementation-plan.md](2026-04-12-multi-lang-implementation-plan.md) §5

## 1. Goal

Ship a complete, tested, table-driven LL(1) parser as a pipeline stage. Three new commands (`plcc-ll1`, `plcc-parser-table`, `plcc-parser-list`) plus a `plcc-tree` rewrite from pass-through to dispatcher. After Part 1, `plcc-tokens < program.txt | plcc-tree --ll1 ll1.json` produces a parse tree for any LL(1) grammar.

## 2. New and changed commands

### New Level 0 primitives

| Command | In | Out | Role |
| --- | --- | --- | --- |
| `plcc-ll1` | spec.json | ll1.json | LL(1) analysis: FIRST, FOLLOW, predict sets, parse table, conflict/left-recursion diagnostics. Pure filter per §17.9: always exits 0 on well-formed spec JSON; non-LL(1) is signaled by top-level `is_ll1: false` in the output, not by exit code. |
| `plcc-parser-table` | token JSONL (stdin), `--ll1 <path>` | parse tree JSON (stdout) | Table-driven LL(1) parser. Consumes the parse table from ll1.json, drives the parse, emits one parse tree. |
| `plcc-parser-list` | (none) | parser kind names, one per line | Walks PATH, collects `plcc-parser-*` executables, strips prefix. Symmetric with `plcc-lang-list`. |

### Changed commands

| Command | Change |
| --- | --- |
| `plcc-tree` | Rewritten from Phase 1 pass-through to dispatcher. Accepts `--parser=<kind>` (default `table`), execs `plcc-parser-<kind>`, forwards `--ll1`, `--verbose`, `--verbose-format`. |
| `plcc-spec` | Stops performing LL(1) validation. Becomes a faithful grammar-to-JSON translator only. |

### Not in Part 1 scope

Level 2 passthroughs (`--parser=` on `plcc-rep`, `plcc-parse`, `plcc-make`), `plcc-gen-parser`, interpreter, Python emitter. Those are Part 2 / Phase 3+.

## 3. Parse tree schema (A′)

One parse-tree schema used by both `plcc-tree` and `plcc-spec`.

### Internal node

```json
{
  "kind": "Expression",
  "pos": {"file": "program.txt", "line": 4, "col": 12, "endLine": 4, "endCol": 25},
  "children": [
    ["left", { "kind": "Term", "pos": "...", "children": "..." }],
    ["op", { "kind": "PLUS", "lexeme": "+", "pos": "..." }],
    ["right", { "kind": "Term", "pos": "...", "children": "..." }]
  ]
}
```

### Token leaf

Exactly the record `plcc-tokens` emits. No wrapper. Distinguished from internal nodes by absence of `children`.

### Design principles

- **Framing.** `plcc-tree` and `plcc-spec` each emit a single newline-terminated JSON document per invocation (also a valid one-line JSONL stream, composing directly with the interpreter under §17.7).
- **Positions.** Stored explicitly on every node (internal and leaf). Internal-node spans are computed at parse time from the full token stream before elision, not reconstructed from surviving leaves, because the tree is an AST with dropped tokens.
- **One token schema.** `plcc-tokens`' output contract is defined such that a token record is self-sufficient as a tree leaf. One schema across the pipeline; `plcc-tree` places tokens unchanged at leaves.
- **One parse-tree schema.** `plcc-spec` and `plcc-tree` both emit trees in this schema. Different `kind` vocabularies (meta-grammar kinds vs. user-grammar kinds), same structural shape. Enables a future PLCC-for-PLCC bootstrap.

## 4. LL(1) analysis JSON (ll1.json)

`plcc-ll1` emits a single JSON document containing:

- **FIRST sets** — per nonterminal
- **FOLLOW sets** — per nonterminal
- **Predict sets** — per production alternative
- **Parse table** — indexed by (nonterminal, lookahead) → production
- **Conflicts** — empty on success; on failure, each conflict names the nonterminal, the lookahead, and the competing productions
- **Left-recursion report** — empty on success; on failure, lists the cycles
- **`--format=human`** — alternative output mode that renders the same data as readable tables for student inspection

Exact field names and nesting are design-doc details to be finalized when this draft is promoted.

## 5. `plcc-parser-table` internals

- **Input:** token JSONL on stdin (reads to EOF), ll1.json via `--ll1 <path>`.
- **Algorithm:** Standard predictive-parsing loop. Push start symbol. At each step: if top-of-stack is a terminal, match against current token (shift); if nonterminal, consult parse table with (nonterminal, lookahead) to select production (expand). Build the A′ tree as it goes.
- **On error:** emit structured error via the §17.8 verbose infrastructure per §17.9; return immediately with a nonzero exit code. No tree is produced.
- **AST elision:** Tokens present in the grammar rule but not assigned a field name (e.g. punctuation like `(`, `)`, `;`) are consumed during parsing but not included as children in the tree. Internal-node spans are computed before elision so positions remain correct.
- **Output:** Single newline-terminated JSON document on stdout.
- **Verbose output (§17.8):** Accepts `--verbose`/`--verbose-format`. At `-vv`, emits shift/expand/complete events with rule-stack depth, enabling Level 2 reformatting into v8-style indented parse traces.

## 6. `plcc-spec` changes

`plcc-spec` currently computes FIRST sets, FOLLOW sets, the parse table, and conflict reports internally, then discards them. Part 1:

1. **Removes LL(1) validation** from `plcc-spec`. It becomes a faithful translator: `.plcc` → spec.json. No analysis, no conflict checking.
2. **Verifies spec.json output** against the unified parse-tree schema (A′ shape, positions on every node, single JSON document framing). If it already matches, document it. If it doesn't, migrate it.
3. **The LL(1) computation code** currently inside `plcc-spec` is extracted and repackaged as the core of `plcc-ll1`.

## 7. Cross-cutting concerns

**`--verbose` / `--verbose-format` (§17.8):** Every new and changed command accepts both flags from day one. Accept-and-forward is mandatory. `plcc-parser-table` ships with actual emission at all three levels. Other commands emit at least `-v` milestones.

**Error contract (§17.9):** Every Level 0 stage follows the uniform stderr + exit-code error model. When `plcc-tokens` cannot tokenize its input, it emits a structured error on stderr and exits nonzero; `plcc-parser-table` does the same when it hits a syntax error in its token stream. Neither emits error records into the token stream or Error nodes into the parse tree. Orchestrators that drive the pipeline (`plcc-rep`, `plcc-parse`) detect upstream-first failure, capture the JSONL stderr from children (always spawned with `--verbose-format=json`), and report the first failing stage's error.

**`plcc-make` phase sequence update:** Gains the `plcc-ll1` step between spec and model (step 3 in the amended §17.4 sequence). Per §17.9, `plcc-make` captures `plcc-ll1`'s stdout to `build/ll1.json`, reads back `is_ll1`, and on `false` prints a human-readable summary of the conflicts and left-recursion report on stderr and exits nonzero.

## 8. Deferred items

| Item | Deferred to |
| --- | --- |
| Level 2 `--parser=` passthroughs | Part 2 / Phase 4 |
| `plcc-gen-parser` (recursive-descent generation) | Phase 3+ |
| `plcc-parse` human-friendly UX (v8-style trace) | Part 2 |
| Interpreter, Python emitter, REPL | Part 2 |
| Entry-point method name (`$run()` replacement) | Part 2 |
| Parse-tree JSONL schema for evaluation records | Part 2 |
| Left-factoring candidate detection in `plcc-ll1` | Phase 3+ |
| Scanner pluggability | Post-v9 |
| Dynamic verbosity mid-session | Future amendment |
