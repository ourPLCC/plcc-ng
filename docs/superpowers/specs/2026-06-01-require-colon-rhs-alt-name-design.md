# Design: Require Colon in RHS `<...>:name` Syntax (Issue 052)

## Problem

The RHS parser in `parse_syntactic_spec.py` silently accepts both `<word>hello` and `<word>:hello` as equivalent. This is inconsistent with the LHS parser, which already requires the colon. The no-colon form should be a syntax error.

Two lines cause the permissiveness:

- `_parseSymbol` (line 88): uses `re.match` with `r"<(?P<name>\S*)>(?P<altName>\S+)?"` — captures anything after `>` as `altName` regardless of whether a colon is present, and `re.match` doesn't require the full string to be consumed.
- `_parseCapturing` (line 97): `altName.strip(":")` silently discards the colon if present, making both forms identical.

## Solution

**Approach A — `fullmatch` + `<` guard.**

### Change 1 — `_parseSymbol` in `parse_syntactic_spec.py`

Replace `re.match` with `re.fullmatch` and update the regex to require the colon:

```python
capturing = re.fullmatch(r"<(?P<name>\S*)>(?::(?P<altName>\S+))?", symbol)
if capturing:
    return self._parseCapturing(capturing["name"], capturing["altName"])
if symbol.startswith("<"):
    raise MalformedBNFError(self.line)
return Terminal(symbol)
```

- `<word>hello` fails `fullmatch` (trailing `hello` is not consumed); the `<` guard raises `MalformedBNFError`.
- `<word>:hello` matches; `altName` captures `hello` (colon consumed by regex).
- `<word>` matches; `altName` is `None`.
- Plain terminals (e.g. `WORD`) don't start with `<`; fall through to `Terminal(symbol)` unchanged.

### Change 2 — `_parseCapturing` in `parse_syntactic_spec.py`

Remove the `strip(":")` line — the colon is now consumed by the regex, so `altName` never includes it:

```python
# delete this line:
altName = altName.strip(":") if altName is not None else altName
```

### Change 3 — `test_named_rhs_non_terminal` in `parse_syntactic_spec_test.py`

Convert the existing success-case test for `<word>hello` into an error-case test:

```python
def test_named_rhs_non_terminal_without_colon_is_an_error():
    line = makeLine("<noun> ::= WORD WORD <word>hello")
    spec, errors = parse_syntactic_spec([makeDivider(), line])
    assert len(errors) == 1
    assert isinstance(errors[0], MalformedBNFError)
```

The existing `test_colon_rhs_non_terminal` (covers `<word>:hello`) is unchanged.

## Error Message

`MalformedBNFError._EXAMPLES` already demonstrates the correct colon syntax:

```
  <nonTerminal>:ClassName ::= TOKEN <TOKEN>:field1 <rhs>:field2
```

No changes needed to the error message.

## Files Changed

| File | Change |
|------|--------|
| `src/plcc/spec/syntax/parse_syntactic_spec.py` | Fix `_parseSymbol` regex + guard; remove `strip(":")` from `_parseCapturing` |
| `src/plcc/spec/syntax/parse_syntactic_spec_test.py` | Convert `test_named_rhs_non_terminal` to an error case |
