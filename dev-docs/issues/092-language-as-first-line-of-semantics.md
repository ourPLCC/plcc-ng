# 092 - Move language specifier to first line of semantics section

**Type:** feat
**Date:** 2026-06-12

## Description

Currently the target language is declared on the section divider line
(`% Python`). It should move into the body of the semantics section:
the divider becomes a plain `%`, and the first non-blank, non-comment
line of the semantics section must be the language name on a line by
itself.

## Desired Behavior

```text
# Lexical section
token NUM '\d+'
skip  SPACE '\s+'

%

# Syntactic section
<Program> **= <NUM:num>

%

# Semantic section
Python

Program
%%%
def _run(self):
    print(sum(int(str(n)) for n in self.numList))
%%%
```

Rules:

- The divider between the syntactic and semantic sections is a plain `%`
  (same as the lexical/syntactic divider).
- Comments and blank lines before the language name are allowed.
- The first non-blank, non-comment line must be a recognized language
  name (`Python`, `Java`). Anything else is a syntax error.
- If the semantics section is absent, or the language line is missing,
  that is a syntax error.

## Rationale

Placing the language name inside the section body makes the divider
uniform (`%` everywhere) and keeps language-specific content inside the
section it belongs to. It also makes the language declaration visible
and editable in the same place as the semantic code.

## Notes

This is a breaking change. Any spec file using `% Python` or `% Java`
on the divider line will need to be updated to use a plain `%` and add
the language name as the first line of the semantics section.

This supersedes [[087-divider-language-first]], which proposed putting
the language on the divider line. If this issue is implemented, 087
should be closed as won't-do.

See also: [[091-single-semantic-section]].
