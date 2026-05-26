# 043 - parseSpec drops rough-parse errors

**Type:** fix
**Date:** 2026-05-26

## Description

`parseSpec()` silently discards any errors returned by `rough.parseRough()`. The variable `errors` is assigned on line 7 then immediately overwritten on line 10 when `lexical.parseLexicalSpec()` returns its own error list. Only lexical and syntactic errors reach the caller; rough-parse errors are lost.

```python
def parseSpec(string, file=None, startLineNumber=1):
    rough_, errors = rough.parseRough(string, file, startLineNumber)  # captured here
    ...
    lex_, errors = lexical.parseLexicalSpec(rough_lex)                # overwritten here
    syn_, syn_errors = syntax.parse_syntactic_spec(rough_syn)
    ...
    return Spec(...), errors + syn_errors                              # rough errors gone
```

## Fix

Use separate variables for each phase and combine all three:

```python
rough_, rough_errors = rough.parseRough(string, file, startLineNumber)
...
lex_, lex_errors = lexical.parseLexicalSpec(rough_lex)
syn_, syn_errors = syntax.parse_syntactic_spec(rough_syn)
...
return Spec(...), rough_errors + lex_errors + syn_errors
```

## Notes

- Discovered during review of issue 037 (MalformedBNFError human-readable messages). Pre-existing before that change.
- Verify whether `rough.parseRough` ever actually returns non-empty errors in practice before writing the fix — if it never does, the bug is latent but still worth closing.
