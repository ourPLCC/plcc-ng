# 023 - Tree output does not annotate empty productions

**Type:** feat
**Date:** 2026-05-14

## Description

When a non-terminal matches an empty production, it appears in the tree as a
leaf node with no children and no indication of why:

```
exp
  NUM '1' [-:1:1]
  exp2
```

A student seeing `exp2` with nothing beneath it may momentarily wonder whether
it is a mistake or an incomplete parse. The node is correct — it represents an
empty production — but nothing in the output says so.

Annotating it would make the intent immediately clear:

```
exp
  NUM '1' [-:1:1]
  exp2 (empty)
```

## Notes

- The annotation should appear only when the node has no children (i.e. matched
  an empty production). Nodes with children are self-explanatory.
- `(empty)` is a suggested label; the exact wording is open to discussion.
- This is a display-only change; the tree structure and parse semantics are
  unaffected.
