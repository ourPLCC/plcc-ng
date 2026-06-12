# 091 - Remove multiple semantic sections and the tool name

**Type:** feat
**Date:** 2026-06-12

## Description

A spec file can currently contain multiple semantic sections, each
introduced by a separator like `% toolname Language`. The `toolname`
field names a "tool" that can be selected at runtime with
`plcc-rep --tool=toolname`. This should be removed:

- A spec file may contain only one semantic section.
- The tool name is removed from the separator. The separator becomes
  simply `% Language` (as already required by issue 087).
- The `--tool` flag on `plcc-rep` (and any other command that uses it)
  is removed.

## Desired Behavior

Valid:

```text
% Python

Program
%%%
def _run(self):
    ...
%%%
```

Invalid (syntax error — only one semantic section allowed):

```text
% Python

Program
%%%
def _run(self):
    ...
%%%

% Java

Program
%%%
public void _run() { ... }
%%%
```

## Rationale

Multiple semantic sections exist to support generating implementations
in more than one target language from a single spec file. In practice
this adds complexity for a use case that is rarely needed and hard to
explain to students. A single semantic section with a single target
language is simpler and sufficient.

## Notes

This is a breaking change. Any spec file with more than one semantic
section, or that uses a tool name in the separator, will need to be
updated.

See also: [[087-divider-language-first]] which already requires the
language to come first and removes the default Java behavior.
