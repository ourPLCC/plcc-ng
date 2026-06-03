# 059 - Parse PLCC grammar files using a PLCC-generated parser

**Type:** feat
**Date:** 2026-06-03

## Description

The current spec parser is hand-rolled across several sub-packages (`rough/`,
`lexical/`, `syntax/`, `semantics/`). The long-term goal is to specify the
PLCC grammar file format as a PLCC grammar and use plcc-ng itself to generate
the parser — both as a demonstration of the tool's capability and to eliminate
the hand-maintained parsers.

## Architecture

The pipeline has two distinct stages:

**Stage 1 — Rough parser (preprocessor, stays hand-rolled)**
Resolves `%include` directives and assembles a single flat character stream.
Injects `# line N "file"` markers at file boundaries (like cpp). Does not
parse grammar structure. Stays hand-rolled because include resolution is a
text-assembly problem, not a grammar problem.

Constraints on `%include`:
- Not allowed inside code blocks (`%%%...%%%`)
- Must appear on a line by itself
- Can appear anywhere else in any section
- Semantics: insert the lines of the included file at that point

**Stage 2 — PLCC-generated parser**
Consumes the flat character stream produced by Stage 1. Recognizes sections,
dividers, lexical rules, syntactic rules, semantic code fragments, and code
blocks. Produces a parse tree from which the existing data model is derived via
a transformer.

## Provenance

The scanner runtime handles `# line N "file"` markers transparently — silently
updating `(file, lineno)` state and producing no token. Every token emitted by
the scanner carries the current `(file, lineno)`. Grammar specs never mention
provenance. Students using PLCC to build their own parsers get accurate
file/line error messages for free; their parsers do not need a rough parser
because their input has no includes.

## Prerequisites

This issue depends on:

1. **Multi-line token support in plcc-ng** — required to recognize `%%%...%%%`
   code blocks, the only multi-line structure in a PLCC grammar file.
2. **Line-directive handling in the PLCC scanner runtime** — so provenance
   flows through the generated scanner without appearing in the grammar spec.

## Decomposition

Once prerequisites are in place:

1. Simplify the rough parser: narrow it to include resolution + line-directive
   emission; strip divider parsing and structural logic (moves downstream).
2. Write the PLCC grammar for the spec format.
3. Write the transformer from the generated parse tree to the existing
   `spec.json` data model.
4. Wire together and retire the hand-rolled section parsers.

## Notes

- Error handling: stopping at the first error is acceptable. A clear
  `file:line` message is sufficient for the student audience.
- The PLCC grammar for the spec format serves as a reference specification of
  the format and lays the groundwork for experimenting with alternative lexical
  shapes (issues 054, 055, 056).
- Long-term: the grammar for the spec format could itself be written in PLCC
  and parsed by a plcc-ng-generated parser — a metacircular specification.
