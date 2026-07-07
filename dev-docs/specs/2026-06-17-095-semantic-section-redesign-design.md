# 095 — Semantic Section Redesign

**Date:** 2026-06-17
**Issue:** [095-redesign-semantic-section-format](../../../dev-docs/issues/095-redesign-semantic-section-format.md)

## Overview

Consolidate and simplify the semantic section format. The divider becomes a bare `%` with no metadata. The language name moves from the divider into the first line of the section body as a `LanguageDeclaration`. Only one semantic section is allowed. The `tool` concept is removed entirely.

This is a breaking change. No migration path, no deprecation bridge.

## Section 1: Rough parser — `Divider` simplification

`Divider` loses its `tool` and `language` fields. It becomes a pure positional marker:

```python
@dataclass
class Divider:
    line: Line
```

`parse_dividers.py` simplifies to a single pattern: a divider is a line that is exactly `%` (nothing after the percent, not even whitespace). Any `%` line with tokens after it raises `UnexpectedTokensOnDividerError` (replacing `TooManyDividerTokensError`). The old `% Language`, `% toolname Language`, and `% toolname` forms all become errors.

## Section 2: Semantic section parsing

### `LanguageDeclaration` dataclass

A new dataclass in `src/plcc/spec/semantics/`:

```python
@dataclass
class LanguageDeclaration:
    language: str
    line: Line
```

### Language extraction

`parse_semantic_spec.py` scans the section body (everything after the divider) for the first non-blank, non-comment line. A blank line is one that is empty or contains only whitespace. A comment line is one whose first non-whitespace character is `#`. That line is parsed as the `LanguageDeclaration`. The remaining lines are passed to `parse_code_fragments` unchanged.

If no non-blank, non-comment line exists before any code fragments, a `MissingLanguageDeclarationError` is raised (pointing to the divider's line).

### Single-section enforcement

`parseSpec.py` enforces at most one semantic section after `split_rough`. If `len(rough_sems) > 1`, a `MultipleSemanticsError` is raised pointing to the second divider's line.

### `SemanticSpec`

`tool` is removed. `language` is now populated from `LanguageDeclaration` rather than `Divider`:

```python
@dataclass
class SemanticSpec:
    language: str
    codeFragmentList: list[CodeFragment]
```

## Section 3: Data model — schema and `build_model`

### `spec.schema.json`

`semantics` collapses from an array to a single nullable object. An array of max 1 is an awkward type; null/object is cleaner and forces consumers to handle presence explicitly:

```json
"semantics": {
  "oneOf": [
    {
      "type": "object",
      "required": ["language"],
      "properties": {
        "language": { "type": "string" }
      }
    },
    { "type": "null" }
  ]
}
```

### `build_model.py`

`tool` is dropped from the semantic section dict. `language` is lowercased as before:

```python
{
    'language': s['language'].lower(),
    'fragments': fragments,
}
```

## Section 4: Build and CLI changes

### `make.py`

- The output directory for the semantic section becomes `build/<language>/` (e.g., `build/Python`), using the language name as declared in the spec.
- `tool_stages` is replaced by a `language_stage` (single value or absent).
- `validate_tool_name` is removed. Language name validation is implicit: `plcc-lang-emit --target=<language>` fails with a clear error if the language is not installed or wrongly cased.
- The staleness sentinel stage key changes from the tool name to the language name.

### `rep.py`

- `--tool=NAME` is removed from the CLI.
- `_resolve_tool` is replaced by a simple helper that reads `spec['semantics']`, errors if `null`, and returns the language name.

### `build/staleness.py`

Wherever the tool name was used as a stage key for staleness tracking, it is replaced by the language name.

## Error inventory

| Error | Where raised | Trigger |
| --- | --- | --- |
| `UnexpectedTokensOnDividerError` | `parse_dividers.py` | `%` line has tokens after it |
| `MissingLanguageDeclarationError` | `parse_semantic_spec.py` | No non-blank, non-comment line in section body |
| `MultipleSemanticsError` | `parseSpec.py` | More than one semantic section |

## What does not change

- `parse_code_fragments.py` — unchanged
- `TargetLocator`, `CodeFragment` — unchanged
- `Block`, `Include`, rough parsing infrastructure — unchanged
- Lexical and syntactic parsing — unchanged
- `plcc-lang-emit`, `plcc-lang-build`, `plcc-lang-run` interfaces — unchanged
