# 015 - Default generated code should compile and run out of the box

**Type:** feat
**Date:** 2026-05-14

## Description

In the original PLCC, a grammar with no semantics section would still produce
code that compiles **and** runs, printing a string representation of the root
AST node. In plcc-ng the generated code compiles but fails at runtime because
the runner calls the configured default method on the root node and no
implementation exists (no one wrote one in the semantics section).

The original PLCC solved this by generating a base class for the root node type
that provided a default implementation of the default method. That base class
was named something like `Start`, `StartNode`, `StartSymbol`, `Root`, or
`RootNode` — the exact name is TBD and will be workshopped during design.

## Notes

Two layers of configuration affect the default method name:

1. **Grammar file** — the grammar author can specify a custom default method
   name.
2. **Language extension** — if no name is given in the grammar file, the
   language extension supplies a fallback default name.

The fix must respect both layers: generate the base class using whichever
default method name is ultimately in effect, and have its implementation print
(or otherwise render) the string representation of the root AST node.

Design questions to resolve:
- What should the base class be named?
- Should the base class be generated into the build output, injected by the
  language extension, or both?
- Should the printed representation be the raw `toString`/`__str__` of the root
  node, or something richer (e.g. a pretty-printed tree)?
