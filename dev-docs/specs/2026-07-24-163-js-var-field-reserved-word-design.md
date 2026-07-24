# Auto-named field colliding with a target language's reserved word — design

**Issue:** [163](../issues/done/163-js-var-field-reserved-word.md)
**Date:** 2026-07-24

## Problem

A grammar capture with no explicit field name (e.g. `<VAR>`) auto-derives
its field name by lowercasing the token name (`build_model.py`'s
`_extract_fields`/`_extract_arbno_fields`). That field name is then used
directly, unmodified, as a generated identifier by every language target's
templates:

| Target | Where `field.name` becomes an identifier |
| --- | --- |
| javascript | `constructor({{field.name}})` — parameter |
| python | `def __init__(self, {{field.name}})` — parameter |
| java | `public {{field.type}} {{field.name}};` — field declaration |
| haskell | `data X = X { {{field.name}} :: Token }` — record field |

None of the four `plcc-<lang>-emit` commands check the field name against
the target language's reserved words, so a field named `var` (or `class`,
`if`, `type`, ...) produces syntactically invalid code that fails only when
the *generated* file is loaded/compiled — e.g. `constructor(var) { ... }`
is a `SyntaxError` in JavaScript. The failure is confusing because nothing
in the plcc-ng pipeline itself reports it.

Only javascript has a filed bug report, but the collision is structurally
possible in all four targets (Java's risk is lower — field declarations,
not parameters — but a field literally named `class` or `new` would still
break `public Token class;`).

## Decision

Reject at emit time, per target language, with a clear error — no
auto-renaming/mangling of field names, and no change to the shared
language-neutral model (`build_model.py`). The check runs identically in
all four `plcc-<lang>-emit` commands; javascript is not special-cased.

### Plugin interface: one `RESERVED_WORDS` file per language

`src/plcc/lang/ext/<lang>/reserved_words.py`, each exporting a single
module-level `RESERVED_WORDS: frozenset[str]`:

- **javascript** — ECMA-262 keywords + strict-mode-reserved words (class
  bodies are always strict mode) + the `enum` future-reserved word:
  ```python
  RESERVED_WORDS = frozenset({
      'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger',
      'default', 'delete', 'do', 'else', 'enum', 'export', 'extends',
      'false', 'finally', 'for', 'function', 'if', 'implements', 'import',
      'in', 'instanceof', 'interface', 'let', 'new', 'null', 'package',
      'private', 'protected', 'public', 'return', 'static', 'super',
      'switch', 'this', 'throw', 'true', 'try', 'typeof', 'var', 'void',
      'while', 'with', 'yield',
  })
  ```

- **java** — the JLS 3.9 "reserved words" table (keywords + the `true`/
  `false`/`null` reserved literals). `var` is deliberately **excluded**:
  per JLS it's a reserved *type name* only in local-variable-inference
  contexts, and remains a legal field/parameter identifier elsewhere —
  confirmed against the actual template usage (field declaration, not a
  `var x = ...` position).
  ```python
  RESERVED_WORDS = frozenset({
      'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch',
      'char', 'class', 'const', 'continue', 'default', 'do', 'double',
      'else', 'enum', 'extends', 'false', 'final', 'finally', 'float',
      'for', 'goto', 'if', 'implements', 'import', 'instanceof', 'int',
      'interface', 'long', 'native', 'new', 'null', 'package', 'private',
      'protected', 'public', 'return', 'short', 'static', 'strictfp',
      'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
      'transient', 'true', 'try', 'void', 'volatile', 'while',
  })
  ```

- **python** — sourced live from the interpreter's own stdlib rather than
  hardcoded, so it can't drift from the Python version actually running
  plcc-ng. Deliberately uses `keyword.kwlist` (hard keywords only), not
  `keyword.softkwlist` (`match`, `case`, `_`, `type` remain legal
  identifiers in a parameter position):
  ```python
  import keyword

  RESERVED_WORDS = frozenset(keyword.kwlist)
  ```

- **haskell** — the Haskell 2010 Report §2.4 reserved identifiers. Uses
  2010, not GHC-extension keywords (`mdo`, `family`, `forall`, ...),
  because the generated `.cabal` file already pins
  `default-language: Haskell2010`:
  ```python
  RESERVED_WORDS = frozenset({
      'case', 'class', 'data', 'default', 'deriving', 'do', 'else',
      'foreign', 'if', 'import', 'in', 'infix', 'infixl', 'infixr',
      'instance', 'let', 'module', 'newtype', 'of', 'then', 'type',
      'where', '_',
  })
  ```

Arbno/list fields (`varList`) never collide — `build_model.py` always
appends `List` to their name, so no special-casing is needed for them.

### Shared check + enforcement: one place owns the logic

`src/plcc/lang/reserved_words.py` (new, sibling to `lang/emit.py` and
`lang/build.py`):

```python
def check_reserved_field_names(classes, language, reserved_words):
    """Return one message per (class, field) colliding with a reserved word."""
    errors = []
    for cls in classes:
        for field in cls['fields']:
            if field['name'] in reserved_words:
                errors.append(
                    f"class '{cls['name']}' field '{field['name']}' collides "
                    f"with the {language} reserved word '{field['name']}' — "
                    f"rename the capture, e.g. <{field['name'].upper()}:name>"
                )
    return errors


def reject_reserved_field_names(classes, language, reserved_words, stage):
    """Print each collision to stderr and exit(1) if any are found."""
    errors = check_reserved_field_names(classes, language, reserved_words)
    if errors:
        for e in errors:
            print(f"{stage}: error: {e}", file=sys.stderr)
        sys.exit(1)
```

This is the one place the message format, stderr target, and exit code
live — the reason for pulling it out of each `emit.py`, not just the
per-language word lists.

### Wiring: each `emit.py` opts in with two lines

Each of `src/plcc/lang/ext/{javascript,java,python,haskell}/emit.py` adds:

```python
from .reserved_words import RESERVED_WORDS
from plcc.lang.reserved_words import reject_reserved_field_names
```

and calls `reject_reserved_field_names(classes, '<lang>', RESERVED_WORDS,
stage='plcc-<lang>-emit')` immediately after `classes = model['classes']`
and **before** `output_dir.mkdir(...)` / copying runtime files / rendering
any template — so a rejected emit leaves no output directory behind.
`plcc-lang-emit` (`src/plcc/lang/emit.py`) is untouched: it's a pure
subprocess dispatcher that pipes `stdin` straight through to
`plcc-<lang>-emit` (`emit.py:43-46`) and never parses the model itself, so
it structurally cannot own this check.

## Testing

Per CONTRIBUTING.md's TDD loop: failing test first, then minimal code to
pass it, at each site.

- `src/plcc/lang/reserved_words_test.py` (new): `check_reserved_field_names`
  — collision case, no-collision case, and a list-suffixed field
  (`varList`) that must *not* collide even though `var` is reserved.
  `reject_reserved_field_names` — asserts stderr content and `SystemExit`
  code on collision, and that it's a no-op (no exit) when clean.
- One case added to each `src/plcc/lang/ext/<lang>/emit_test.py`: a
  minimal model fixture (matching the existing `_minimal_model()` /
  `_arith_model()` pattern already in `javascript/emit_test.py`) with a
  field named after a reserved word for that language → `run_main` exits
  1, expected stderr, and no files written under `--output`.
- E2E regression (`tests/bats/e2e/plcc-rep.bats` + a new
  `tests/fixtures/*.plcc`), mirroring this issue's own repro: a grammar
  with `token VAR '[A-Za-z]\w*'` and `<Exp:VarExp> ::= <VAR>` (no explicit
  field name), run through `plcc-rep` targeting javascript — asserts the
  friendly rejection message, not a raw `SyntaxError` from a loaded `.js`
  file.

## Docs

- `docs/language-guide/syntactic.md`, in the "Capturing terminals" /
  "Capturing nonterminals" sections (right after the existing
  same-field-name-collision notes at ~lines 92-101 and 118-127): add a
  general note that a field name — whether explicit (`:fieldname`) or
  auto-derived — is illegal if, once translated into an identifier, it
  collides with a reserved word of the semantic implementation language
  in use (e.g. `<VAR>` producing field `var`, reserved in JavaScript).
  Critically, note that this is a *late* check: it is only detected when
  you attempt to evaluate the semantics for a specific target language
  (e.g. `plcc-rep`, or an explicit `plcc-<lang>-emit`), not at grammar
  validation time (`plcc-scan`/`plcc-parse`/`plcc-validate-*`) — those
  stages are language-neutral and don't know which target you'll
  eventually emit for, so a grammar can pass validation cleanly and still
  fail later, per-target, at emit time.
- `docs/language-guide/languages/javascript.md`: note that field names
  colliding with a JavaScript reserved word are rejected at generation
  time, with the `<VAR:name>` workaround, and a pointer back to
  `syntactic.md` for the general rule.
- Same note added to the equivalent java/python/haskell language-guide
  pages, since all four targets now enforce this.

## Files changed

| File | Change |
| --- | --- |
| `src/plcc/lang/reserved_words.py` (new) | `check_reserved_field_names`, `reject_reserved_field_names` |
| `src/plcc/lang/reserved_words_test.py` (new) | Unit tests for both functions |
| `src/plcc/lang/ext/javascript/reserved_words.py` (new) | `RESERVED_WORDS` (ECMA-262 + strict-mode) |
| `src/plcc/lang/ext/java/reserved_words.py` (new) | `RESERVED_WORDS` (JLS 3.9) |
| `src/plcc/lang/ext/python/reserved_words.py` (new) | `RESERVED_WORDS = frozenset(keyword.kwlist)` |
| `src/plcc/lang/ext/haskell/reserved_words.py` (new) | `RESERVED_WORDS` (Haskell 2010 §2.4) |
| `src/plcc/lang/ext/javascript/emit.py` | Wire in `reject_reserved_field_names` before output-dir creation |
| `src/plcc/lang/ext/java/emit.py` | Same |
| `src/plcc/lang/ext/python/emit.py` | Same |
| `src/plcc/lang/ext/haskell/emit.py` | Same |
| `src/plcc/lang/ext/{javascript,java,python,haskell}/emit_test.py` | Reserved-word-collision test case |
| `tests/fixtures/*.plcc` (new) | Grammar reproducing issue #163's `VAR` example |
| `tests/bats/e2e/plcc-rep.bats` | New case: friendly rejection instead of a raw generated-code `SyntaxError` |
| `docs/language-guide/syntactic.md` | General note: reserved-word field names are illegal, detected only at per-target emit/evaluation time, not at grammar-validation time |
| `docs/language-guide/languages/{javascript,java,python,haskell}.md` | Document the reserved-word restriction, pointing back to `syntactic.md` |
