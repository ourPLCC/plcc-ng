# 036 - Improve LL(1) conflict error messages

**Type:** feat
**Date:** 2026-05-25

## Description

The current `ll1.json` output reports conflicts as raw data — nonterminal, lookahead token, and a list of conflicting productions. This is useful for tools that consume the JSON, but the human-facing error message derived from it gives students little help understanding *why* a conflict exists or *how to fix it*.

We want conflict messages that:

1. Show the conflicting productions as readable grammar rules (not JSON arrays).
2. Distinguish the two types of LL(1) conflict, because each has a different cause and a different fix:
   - **FIRST/FIRST conflict** — two non-empty productions for the same nonterminal both start with the same lookahead token.
   - **FIRST/FOLLOW conflict** — one production is ε (empty), and the lookahead token also appears in the FOLLOW set of the nonterminal, so the parser can't decide whether to expand or skip.
3. For FIRST/FIRST conflicts, suggest left-factoring as a concrete fix (with an example derived from the actual conflicting productions).
4. For FIRST/FOLLOW conflicts, point at the surrounding rule(s) that put the lookahead into FOLLOW — because the real problem often isn't the nonterminal itself but how it is used elsewhere in the grammar.

### Example target output (FIRST/FOLLOW)

```
LL(1) conflict: <elsePart> on lookahead ELSE

  Both of these productions apply:
    <elsePart> ::= ELSE <stmt>
    <elsePart> ::=              (empty)

  This is a FIRST/FOLLOW conflict: ELSE can start the first production,
  but also appears in the FOLLOW set of <elsePart>, making the empty
  production ambiguous here.

  Tip: look at the rule(s) that use <elsePart> — one of them places
  ELSE in a position that follows <elsePart>, creating the ambiguity.
  This often means the grammar is genuinely ambiguous (e.g., the
  dangling-else problem) and must be restructured.
```

### Example target output (FIRST/FIRST)

```
LL(1) conflict: <expr> on lookahead ID

  Both of these productions apply:
    <expr> ::= ID PLUS <expr>
    <expr> ::= ID MINUS <expr>

  This is a FIRST/FIRST conflict: both productions start with ID, so
  the parser cannot choose between them.

  Tip: left-factor the common prefix:
    <expr>     ::= ID <exprTail>
    <exprTail> ::= PLUS <expr>
    <exprTail> ::= MINUS <expr>
```

## What the analyzer already captures

The data needed to produce these messages is already computed in `ll1_result_builder.py`:

- `follow_sets` — FOLLOW sets for every nonterminal, keyed by name. These are included in `ll1.json`.
- `conflicts` — each conflict already has `nonterminal`, `lookahead`, and `productions` (the conflicting RHSes).

**Determining conflict type** is straightforward from the conflict data itself:
- If any production in `productions` is `[]` (empty), it is a **FIRST/FOLLOW** conflict.
- If all productions are non-empty, it is a **FIRST/FIRST** conflict.

**Identifying which rules put the lookahead into FOLLOW** (for FIRST/FOLLOW) is not directly surfaced — the follow sets show *what* is in FOLLOW but not *why*. Surfacing the contributing rules would require storing provenance during `build_follow_sets`, which is not currently done. A simpler short-term tip is to tell the user to search the grammar for rules that contain `<elsePart>` followed by (or at the end of) another rule that can begin with the lookahead.

**Generating a left-factoring suggestion** (for FIRST/FIRST) is mechanically possible: extract the longest common prefix of the conflicting productions, name a fresh nonterminal for the remainder, and show the factored form. The conflict data contains enough information to do this.

## Notes

- The `field` values in each production symbol are for code generation only and play no role in LL(1) analysis or error messages — they should be ignored when formatting conflict output.
- Students are unlikely to know what FIRST/FOLLOW means; the error message should explain the concept inline rather than assuming prior knowledge.
- There may be multiple conflicts for the same nonterminal on different lookaheads; each should be reported separately.
