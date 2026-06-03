# 058 - Collocate lexical patterns

**Type:** feat
**Date:** 2026-06-02

## Description

The regular expressions that define the lexical shapes of the spec format are currently scattered inline across multiple parsing stages. This makes them hard to find and creates silent drift when a shape is represented by both a loose parse-time pattern and a strict validate-time pattern in different files.

Collocate all lexical patterns into a single module as named constants. This gives a single place to change when a shape changes, and makes the loose/canonical relationship explicit.

## Design

Patterns fall into two categories:

**Delimiter patterns** — one form each, no downstream validator:
- `BLOCK_OPEN_RE`, `BLOCK_CLOSE_RE` (currently both `%%%`, separate constants to allow future asymmetry per issue 055)
- `DIVIDER_RE` (the `%` line; used for both lex/syn and syn/sem boundaries, disambiguated by position)

**Content patterns** — each has a canonical (strict) form used by validators and a loose form used by the liberal parser:
- `RULE_TYPE_RE` — matches `token` or `skip`
- `TOKEN_NAME_RE` — matches a lexical token name

Non-terminal patterns are composite and get a three-level hierarchy:
- **Name sub-patterns** (validators use these directly):
  - `NON_TERM_NAME_RE`
  - `ALT_NAME_RE`
  - `FIELD_NAME_RE`
- **Structural patterns** (composed from sub-patterns, used after the boundary is found):
  - `NON_TERM_LHS_RE`
  - `NON_TERM_RHS_RE`
- **Loose boundary patterns** (independent, used by the liberal parser):
  - `NON_TERM_LHS_LOOSE`
  - `NON_TERM_RHS_LOOSE`

The loose boundary patterns do not compose from the sub-patterns — they match anything inside `<>` and are structurally stable across name-shape changes.

## Notes

- The syntactic parser currently parses non-terminal names and alternate names with the structural regex partially duplicated across `_matchLeft()` and `_parseSymbol()`. These will need to be refactored to reference the shared constants and may require light reorganization.
- The `%` divider is intentionally a single constant even though it serves two roles (lex/syn and syn/sem). Separate constants with the same value would imply independent configurability that does not exist.
- This lays the groundwork for experimenting with different lexical shapes (issues 054, 055, 056) by making each shape a one-place change.
