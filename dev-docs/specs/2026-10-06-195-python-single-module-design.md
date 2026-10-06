# Optional single-module Python output — design

Issue: [#195](../issues/195-python-single-module-output.md)
Date: 2026-10-06

## Problem

[`plcc-python-emit`](../../src/plcc/lang/ext/python/emit.py) writes one `.py`
file per class. Because each class is its own module, a class that needs to
name a sibling must import it, and the only way to say that in a spec is a
`Class:import` block. Specs therefore accumulate import blocks whose sole
purpose is to undo the file split — boilerplate that says nothing about the
language being defined.

Note that `Class:import` has a second, legitimate use: importing external
modules (`import re`) that a class body needs. That use survives this change.
Only the sibling-import use goes away.

## Goal

Let a spec ask for its generated classes in a single module, so sibling
imports become unnecessary.

Non-goal: a self-contained file that runs on its own. `runtime/` stays a
copied package and `main.py` stays the entry point. The goal is
spec-authoring ergonomics, not a redistributable artifact.

**Hard constraint.** Course materials depend on the current layout. A spec
that does not ask for the option generates byte-identical output to today.

## Decisions

| Question | Decision |
|---|---|
| Mechanism | One module, not generated sibling imports |
| What merges | Generated classes, `_Start`, standalone classes |
| What does not | `runtime/` stays a package; `main.py` stays the entry point |
| Spec syntax | Whitespace-separated options after the language name |
| Option enforcement | The language extension enforces its own list |
| Standalone class order | Before the generated classes, spec order among themselves |
| Stale sibling imports | Documented, not detected |

### Rejected: generate sibling imports instead

The alternative to merging is to keep one file per class and have the emitter
generate the imports, so the author never writes them. This does not work in
Python. Mutual top-level imports fail:

```
Prog.py:  from Expr import Expr        Expr.py:  from Prog import Prog
→ ImportError: cannot import name 'Prog' from partially initialized module 'Prog'
```

A recursive AST has mutually referring classes as a matter of course
(`Expr` ↔ `ExprRest` in `tests/fixtures/arith.plcc`), so this fails on
ordinary grammars. Moving the generated imports to the *bottom* of each file
avoids the cycle for method bodies but not for anything needed when the class
statement executes:

```
method-body use: Expr        ← works
class Prog(Expr): ...        ← NameError: name 'Expr' is not defined
```

That failing case includes `Class:class` mixins, and under auto-import the
parent/child pair itself becomes circular — so the approach would break
inheritance that works today. A single module removes the problem class
entirely: within one namespace no import can be circular, and the only
definition-order constraint is base classes.

### Rejected: compatibility shims

Writing a `Term.py` containing `from classes import Term` for each class would
let existing sibling imports keep resolving. Rejected: the file sprawl returns,
the now-pointless import blocks silently persist, and students face a file whose
only purpose is re-export.

### Rejected: validator-side option checking

Language extensions are out-of-process plugins discovered by scanning `PATH`
([`list.py`](../../src/plcc/lang/list.py) scans for `plcc-*-emit`;
[`emit.py`](../../src/plcc/lang/emit.py) resolves `plcc-<lang>-emit` and
`subprocess.run`s it). A validator that imported `plcc.lang.ext.<lang>.options`
would work for in-tree languages and break the plugin model for any other, and
would introduce a `spec/ → lang/` dependency that does not exist today.
Querying the plugin instead (`plcc-<lang>-emit --list-options`) would preserve
the model but imposes a new contract on every plugin and makes validation
**environment-sensitive** — the same spec would validate differently depending
on what is installed.

Reserved words set the precedent: a language-specific spec error enforced
inside the emitter, with shared logic in
[`lang/reserved_words.py`](../../src/plcc/lang/reserved_words.py) and
per-language data in `ext/python/reserved_words.py`. Options follow it.

## Design

### 1. Spec syntax and plumbing

Options are whitespace-separated tokens after the language name on the
declaration line. Order-insensitive, matched case-sensitively (lowercase by
convention, unlike the language name, which the emitter matches case-insensitively),
and a repeated option is ignored rather than an error. No options means today's
behavior.

```
%
Python single-module
```

- `_extract_language` in
  [`parse_semantic_spec.py`](../../src/plcc/spec/semantics/parse_semantic_spec.py)
  splits the stripped line instead of taking it whole: first token is the
  language, the rest are options.
- `LanguageDeclaration` gains `options`; `SemanticSpec` gains
  `options: list[str]`.
- Spec-JSON serialization needs no change — `plcc_spec_cli` emits
  `json.dumps(asdict(spec))`.
- `deserialize_semantic_spec` reads `sem.get('options', [])`, so older spec
  JSON still deserializes.
- `_build_semantic_sections` in
  [`build_model.py`](../../src/plcc/model/build_model.py) copies `options`
  into the section dict, carrying it to the emitter in `model.json`.
- `spec.schema.json` and `model.schema.json` gain an **optional** `options`
  array of strings. Neither schema sets `additionalProperties: false`, so this
  is additive and older JSON stays valid.

The language name itself stays clean, so [`make.py`](../../src/plcc/cmd/make.py)
is untouched — it uses `section['language']` as both the output directory name
and the `--target` value, and `validate_language_name` continues to see only
`Python`.

No new CLI flag. The option travels in the model, not the command line.

### 2. Option enforcement

- `ext/python/options.py` declares `SUPPORTED = {'single-module'}`, beside the
  existing `reserved_words.py`.
- A shared `lang/options.py` mirrors `reserved_words.py`'s two-function split:
  a pure `check_unknown_options(...)` returning messages, and a
  `reject_unknown_options(..., stage)` that prints to stderr and exits 1.
- `plcc-python-emit` calls it before writing anything.

```
plcc-python-emit: error: unknown option 'single-modual'
  supported options: single-module
```

A language that does not implement an option rejects it the same way, so
`Java single-module` fails with a clear message rather than being ignored.

### 3. The emitted module

Output tree with the option on:

```
DIR/
  classes.py
  main.py
  runtime/
    ...
```

`_Start.py` is no longer written; `_Start` is inlined. `classes.py` holds, in
order:

1. All `Class:top` fragments, spec order.
2. The runtime imports, **once**: `import runtime.base as _plcc` and
   `from runtime.base import LanguageError`.
3. All `Class:import` fragments, spec order.
4. Standalone class blocks, spec order, verbatim.
5. `_Start`, with its own copy of the runtime import dropped so (2) holds.
6. The generated classes, in model order.

**Why the file name is `classes.py`.** Class names must match `^[A-Z]`
(enforced by `InvalidClassNameError`), so a lowercase module name cannot
collide with a generated class, and it cannot collide with `main` or `runtime`.

**Why standalone blocks come before the generated classes.** A `Class:class`
fragment injects additional base classes into the generated class statement,
and a base class must be defined before the statement that uses it. A standalone
class whose *own* base is a generated class is therefore unsupported in
single-module mode; the documented workaround is to reference generated classes
from method bodies, which resolve at call time. Relative order among standalone
blocks is spec order, so a helper can subclass another helper.

**Why no topological sort is needed.** `_build_classes` appends each abstract
base immediately before the alternatives that extend it, and `extends` is only
ever `None` or that group's own base. Verified on `tests/fixtures/arith.plcc`:

```
1. Program   abstract=False extends=None
2. Expr      abstract=False extends=None
3. ExprRest  abstract=True  extends=None
4. AddRest   abstract=False extends=ExprRest
5. NilRest   abstract=False extends=ExprRest
6. Term      abstract=False extends=None
```

Parents already precede children. The one addition is `_Start`, which the
emitter injects as the start class's base, so it is placed ahead of the
generated classes.

**No import deduplication among fragments.** Emitting the runtime imports once
is a property of the template, not a dedup pass over author code. A fragment
body is an arbitrary block, not necessarily a single import line, and a repeated
Python import is a harmless no-op, so hoisted fragments are concatenated as
written.

### 4. `main.py`

Still written, still the entry point, still launched by
[`run.py`](../../src/plcc/lang/ext/python/run.py). Its per-class
`from <Class> import <Class>` lines become `from classes import <Class>`;
the registry code is unchanged. Nothing downstream of emit changes: there is
no `build.py` for Python, and `plcc-rep` invokes `main.py`.

### 5. Templates

`class_file.py.jinja` currently renders a whole file: imports plus one class.
Extract the class rendering into a Jinja macro that both the existing per-file
template and a new module template call, so there is one source of truth for
how a class renders. Duplicating the class body into a second template is
specifically what this avoids.

### 6. Migration of stale sibling imports

Turning the option on does not remove `Class:import` blocks — they are author
code and are hoisted verbatim. A block that imports a sibling class
(`from Term import Term`) will therefore fail at runtime, because `Term.py` no
longer exists, even though `Term` is defined in the same file.

This is **documented, not detected.** Detection would require matching import
text against known class names: a heuristic that misses aliased and dynamic
forms and can false-positive on an external module sharing a class's name. The
case is also narrow — a spec written with `single-module` from the start never
contains sibling imports, so this only affects deliberate conversions, where
the error appears on the first run and the fix is deleting one block.

Docs state the rule: when enabling `single-module`, remove import blocks that
import other generated classes; keep imports of external modules.

## Testing

Unit tier carries most of this, per CONTRIBUTING's "if a unit test can cover
it, write a unit test."

| Test | Asserts |
|---|---|
| `parse_semantic_spec_test.py` | `Python single-module` → `language='Python'`, `options=['single-module']`; bare `Python` → `[]`; extra whitespace; multiple options |
| `deserialize_test.py` | options round-trip; spec JSON without `options` → `[]` |
| `build_model_test.py` | options reach `semantic_sections` |
| `lang/options_test.py` (new) | unknown option prints and exits 1; known option silent |
| `ext/python/emit_test.py` | one `classes.py`, no per-class files, no `_Start.py`; standalone blocks precede generated classes; `_Start` precedes the start class; runtime imports appear exactly once; `main.py` imports from `classes`; unknown option rejected |

**The test that proves the point is e2e**, because it must actually run: a new
fixture spec with a genuine cross-class reference and **no import blocks at
all**, driven through `plcc-make` and `plcc-rep`. Every unit test above checks
emitted text; this one checks that the merged module imports and executes.

Also add a default-path test exercising a sibling `Class:import`. Nothing
exercises that hook today — `:import` appears only in `docs/` — so the behavior
being displaced is currently unguarded.

**Compatibility guard.** Every existing default-path test must pass
*unedited*. If this work requires changing `test_emit_produces_one_py_file_per_class`
or `tests/bats/integration/python-emit.bats`, that is the signal the default
changed.

## Docs

- `docs/language-guide/languages/python.md` — an options section documenting
  `single-module`, a single-module variant of the "Generated output" tree, and
  the migration rule from §6.
- `docs/language-guide/semantic.md` — the "Adding standalone classes" section
  notes where those blocks land when the option is on.
- A **docs fixture** for the new runnable example, under
  `tests/fixtures/docs/` (suggested name `lang-guide-python-single-module`),
  registered in the `MANIFEST` in `tests/docs/example_block_test.py`. Per
  CONTRIBUTING, add the fixture first and write the page from it.

Adding a fixture rather than raising the `UNCOVERED` fence count is a
deliberate choice: the page's existing quick reference is unguarded, and this
adds coverage instead of more exemption.

Run [bin/docs/build.bash](../../bin/docs/build.bash) before pushing, so nav or
link warnings fail rather than pass silently.

## Out of scope

- `single-module` for JavaScript, Java, or Haskell. JavaScript emits per-class
  files by the same pattern and may want it later; Java compiles its files
  together and has less to gain.
- Inlining `runtime/` or producing a single self-contained runnable file.
- Making the module name configurable.
- Deduplicating hoisted imports.
- The `_compute_kind` fall-through footgun noted in #195, where a misspelled
  class name silently becomes a standalone file. Same code, separate issue.

## Commit shape

Conventional commits, matching scopes already in the log. Roughly: the spec
plumbing (`feat(spec)`), the shared option check (`feat(lang)`), the emitter
and templates (`feat(python)`), schemas, docs plus fixture (`docs`), and
`bin/issues/close.bash 195` as the branch's final commit.

## Files changed

| File | Change |
|---|---|
| `src/plcc/spec/semantics/parse_semantic_spec.py` | split the language line |
| `src/plcc/spec/semantics/LanguageDeclaration.py` | add `options` |
| `src/plcc/spec/semantics/SemanticSpec.py` | add `options` |
| `src/plcc/spec/semantics/deserialize.py` | read `options`, default `[]` |
| `src/plcc/model/build_model.py` | carry `options` into the section |
| `src/plcc/schemas/spec.schema.json` | optional `options` |
| `src/plcc/schemas/model.schema.json` | optional `options` |
| `src/plcc/lang/options.py` | new: shared unknown-option check |
| `src/plcc/lang/ext/python/options.py` | new: `SUPPORTED` |
| `src/plcc/lang/ext/python/emit.py` | enforce options; single-module path |
| `src/plcc/lang/ext/python/templates/class_file.py.jinja` | extract class macro |
| `src/plcc/lang/ext/python/templates/module.py.jinja` | new: merged module |
| `src/plcc/lang/ext/python/templates/main.py.jinja` | import from `classes` |
| `docs/language-guide/languages/python.md` | options, output tree, migration |
| `docs/language-guide/semantic.md` | standalone-class placement note |
| `tests/fixtures/docs/lang-guide-python-single-module/` | new docs fixture |
| `tests/docs/example_block_test.py` | register fixture in `MANIFEST` |
| plus unit, e2e, and bats tests per **Testing** | |
