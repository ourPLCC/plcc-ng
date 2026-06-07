# 037 - Replace spec parser stack traces with human-readable syntax error messages

**Type:** fix
**Date:** 2026-05-25

## Description

When `plcc-spec` encounters a malformed grammar rule it currently crashes with a Python stack trace. For example, a missing space between `<stmt>` and `IfStmt` (which would normally be the class name after a colon) produces:

```
Traceback (most recent call last):
  ...
  File ".../parse_syntactic_spec.py", line 64, in parseSyntacticRule
    raise MalformedBNFError(self.line)
plcc.spec.syntax.MalformedBNFError.MalformedBNFError: Line(string='<stmt>IfStmt     ::= IF <expr> THEN <stmt> <elsePart>', number=25, file='grammar.plcc')
plcc-make: plcc-spec failed (exit 1)
```

The stack trace is useful for debugging the parser itself, but is actively harmful to a student trying to understand what they wrote wrong. The error contains everything needed for a good message — the file, line number, and the offending line — but none of it is formatted for a human.

The target output for the same error:

```
grammar.plcc:25: syntax error
  <stmt>IfStmt     ::= IF <expr> THEN <stmt> <elsePart>
  Expected: <NonTerminal> ::= ...
            <NonTerminal>:ClassName ::= ...
            <NonTerminal> **= ...
```

## What the code already has

`MalformedBNFError` already receives the full `Line` object, which carries `string`, `number`, and `file`. All the information for a good message is there.

The exception propagates uncaught all the way to `parseSpec.py`, which calls `syntax.parse_syntactic_spec` with no error handling. `plcc_spec_cli.py` does handle errors returned from `_load`, but `MalformedBNFError` is raised (not returned), so it bypasses that path and reaches Python's default exception handler — which prints the stack trace.

## Fix

Two changes are needed:

1. **Catch `MalformedBNFError` in `parseSpec.py`** (or in `parse_syntactic_spec.py`) and convert it into a structured error that can be collected and returned rather than raised.

2. **Give `MalformedBNFError` a readable `__str__`** so that when it is printed via the existing error-printing loop in `plcc_spec_cli.py`, it shows the file, line number, offending text, and a hint about the expected syntax — not a stack trace.

The `plcc_spec_cli.py` already has the right shape for this:

```python
if errors:
    for e in errors:
        print(e, file=sys.stderr)
    sys.exit(1)
```

So the cleanest fix is: catch the exception, wrap it as an error in the same list, and let the existing loop print it — with `__str__` returning the human-readable message.

## Notes

- The `isSyntacticRule` check in `SyntacticLineParser` gates whether `parseSyntacticRule` is called, so any line that passes that check and fails to match any of the three rule patterns triggers the error. The hint in the error message should show all three valid forms.
- Other parsers in this codebase (e.g. lexical) may have the same problem — worth checking for consistency once this is fixed.
- Do not suppress the stack trace globally; it should remain available in verbose/debug mode for parser development.
