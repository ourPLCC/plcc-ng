# Optional single-module Python output — design

Issue: [#195](../issues/195-python-single-module-output.md)
Date: 2026-10-06

> **Blocked on [#197](../issues/197-language-neutral-fragment-hook-names.md)** —
> on *resolving* the hook names there, not on implementing them. This mode needs
> module-targeted hooks, and publishing provisional names would mean renaming a
> published hook later. Hook names below are written in #197's sketch vocabulary
> (`module:preamble`, `module:import`, `module:head`, `module:tail`) and are
> **provisional**; the regions and their ordering are settled, only the
> identifiers are open. #197's multi-module hooks and deprecation path need not
> land first.

## Problem

[`plcc-python-emit`](../../src/plcc/lang/ext/python/emit.py) writes one `.py`
file per class. Because each class is its own module, a class that needs to
name a sibling must import it, and the only way to say that in a spec is a
`Class:import` block. Specs therefore accumulate import blocks whose sole
purpose is to undo the file split — boilerplate that says nothing about the
language being defined.

Note that `Class:import` has a second, legitimate use: importing external
modules (`import re`) that a class body needs. That use does not go away — but
it moves, because the hook itself does not survive this mode. `Class:import`
and `Class:top` are defined in terms of a per-class file ("the import section
of *this class's* file"), and single-module abolishes that file. They are not
merely redundant here; they are incoherent, so this mode replaces them with
module-targeted hooks rather than quietly relocating their contents.

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
| What merges | Generated classes, `_Start`, free-standing author code |
| What does not | `runtime/` stays a package; `main.py` stays the entry point |
| Spec syntax | Whitespace-separated options after the language name |
| Option enforcement | The language extension enforces its own list |
| Per-class file hooks | `Class:top` and `Class:import` are errors in this mode |
| Module hooks | Three regions, author chooses; names pending #197 |
| Free-standing code position | Author's choice of region, not emitter-chosen |
| Stale sibling imports | A hard error by construction, since the hook is gone |

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

### Rejected: hoisting author code into place

An earlier draft kept `Class:top` and `Class:import` working by concatenating
their bodies into the merged module's prologue, and lifting any
`from __future__ import …` line out of them so it could legally come first
(`SyntaxError: from __future__ imports must occur at the beginning of the file`
otherwise). Rejected as magic: it silently rewrites author code, and the rule
"your future imports get moved, but ours go above yours" exists only because
one block was conflating two regions that Python keeps separate.

Naming the regions explicitly costs the author one retarget and removes the
transform, the ordering rule, and the failure mode together.

### Rejected: emitter-chosen position for free-standing code

The same draft placed every standalone-class block ahead of the generated
classes, which makes `Class:class` mixins resolve but leaves a helper that
subclasses a generated class impossible, documented as a limitation. With
explicit regions the author picks the side their dependencies require, and both
cases work. Note that under this mode a standalone block's class *name* does no
work at all — it selected a filename, and there is no longer a file — so the
block is simply free-standing module code, which is what the region hooks
already express.

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

1. `module:preamble` fragments, spec order.
2. The runtime imports, **once**: `import runtime.base as _plcc` and
   `from runtime.base import LanguageError`.
3. `module:import` fragments, spec order.
4. `module:head` fragments, spec order, verbatim.
5. `_Start`, with its own copy of the runtime import dropped so (2) holds.
6. The generated classes, in model order.
7. `module:tail` fragments, spec order, verbatim.

**Why the file name is `classes.py`.** Class names must match `^[A-Z]`
(enforced by `InvalidClassNameError`), so a lowercase module name cannot
collide with a generated class, and it cannot collide with `main` or `runtime`.

**Why three author regions and not one.** Python forces exactly three, and no
more:

- **Preamble.** `from __future__ import …` must precede every other statement;
  anything else is a `SyntaxError`. This is a syntax-enforced region, the direct
  analogue of Haskell's `{-# LANGUAGE #-}` pragmas and JavaScript's
  `'use strict'`.
- **Before the classes.** Anything a class statement needs *as it executes*:
  imports, module constants, and base classes named by a `Class:class` mixin
  fragment.
- **After the classes.** Anything that needs the classes to already exist at
  definition time — most obviously a helper that subclasses a generated class.

One region cannot serve these, because the emitter contributes to more than one
of them: the runtime imports today, and `from __future__ import annotations` if
opt-in type annotations land. With a single author block there is no position
that works once the emitter needs to place something on the far side of it.
Ordering *within* a region is immaterial — multiple future imports are mutually
order-independent, and so are plain imports — so there is no ordering rule to
document beyond which region a block targets.

Regions (2) and (3) are distinct only because the emitter owns (2); Python does
not require imports to precede other module-level code, which is why
`module:import` and `module:head` are adjacent rather than separated by
anything structural.

**`Class:top` and `Class:import` are errors in this mode**, not silently
relocated. Both name a per-class file that does not exist here. The error tells
the author which module hook to use, and that error is what makes stale
sibling imports a build-time failure rather than a runtime `ModuleNotFoundError`
— see §6.

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

### 6. Migration

Opting in is not a one-word change: it converts hooks. Every `Class:top` and
`Class:import` block in the spec becomes an error naming the module hook to use
instead.

```
plcc-python-emit: error: Expr:import is not available under single-module
  'Class:import' targets the import section of Expr's own file, and
  single-module has no per-class file.
  Use module:import for an external import, or module:preamble for a
  '__future__' import.
```

That error is the migration tool, and it is why no heuristic is needed. The
author sorts each block themselves:

- an import of a **sibling class** is deleted — the class is in the same module
- an import of an **external module** moves to `module:import`
- a `__future__` import moves to `module:preamble`

Only the author can reliably tell those apart. An earlier draft tried to detect
the sibling case by matching import text against known class names, which
misses aliased and dynamic forms and can false-positive on an external module
sharing a class's name. Outlawing the hook makes the classification the
author's, which is where the knowledge actually is, and turns what would have
been a runtime `ModuleNotFoundError` into a build-time error that names the fix.

Free-standing (standalone-class) blocks convert the same way, to `module:head`
or `module:tail` depending on which side of the generated classes their
dependencies require.

## Testing

Unit tier carries most of this, per CONTRIBUTING's "if a unit test can cover
it, write a unit test."

| Test | Asserts |
|---|---|
| `parse_semantic_spec_test.py` | `Python single-module` → `language='Python'`, `options=['single-module']`; bare `Python` → `[]`; extra whitespace; multiple options |
| `deserialize_test.py` | options round-trip; spec JSON without `options` → `[]` |
| `build_model_test.py` | options reach `semantic_sections` |
| `lang/options_test.py` (new) | unknown option prints and exits 1; known option silent |
| `parse_target_locator_test.py` | the reserved `module` target parses with each slot |
| `validation_test.py` | `module` is exempt from the `^[A-Z]` class-name rule; a bare `module` with no slot is still an error |
| `build_model_test.py` | each module slot gets its own kind, distinct from `Class:top`/`Class:import` |
| `ext/python/emit_test.py` | one `classes.py`, no per-class files, no `_Start.py`; region order (preamble → runtime imports → import → head → `_Start` → classes → tail); runtime imports appear exactly once; `main.py` imports from `classes`; unknown option rejected |
| `ext/python/emit_test.py` | `Class:top` and `Class:import` each error under `single-module`, and the message names the module hook to use |

**The test that proves the point is e2e**, because it must actually run: a new
fixture spec with a genuine cross-class reference and **no import blocks at
all**, driven through `plcc-make` and `plcc-rep`. Every unit test above checks
emitted text; this one checks that the merged module imports and executes.

A second e2e case earns its place: a `module:tail` block defining a helper that
**subclasses a generated class**. That is the case the rejected emitter-chosen
ordering could not express at all, and only an executing test shows the class
statement resolving.

Also add a default-path test exercising a sibling `Class:import`. Nothing
exercises that hook today — `:import` appears only in `docs/` — so the behavior
being displaced is currently unguarded.

**Compatibility guard.** Every existing default-path test must pass
*unedited*. If this work requires changing `test_emit_produces_one_py_file_per_class`
or `tests/bats/integration/python-emit.bats`, that is the signal the default
changed.

## Docs

- `docs/language-guide/languages/python.md` — an options section documenting
  `single-module`, a single-module variant of the "Generated output" tree, the
  module hooks and their regions, and the migration rule from §6. The existing
  fragment-kinds table needs a column or a note saying which kinds are
  unavailable in this mode.
- `docs/language-guide/semantic.md` — the "Adding standalone classes" section
  explains that in single-module mode there is no per-class file, so such code
  is written as `module:head` or `module:tail` and the author picks the side.
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
- **The hook vocabulary itself**
  ([#197](../issues/197-language-neutral-fragment-hook-names.md)): naming the
  slots, offering them on class targets in multi-module mode, migrating the
  existing docs, and deprecating `top`/`class`/`file`. This spec consumes the
  names and implements only the module target under `single-module`.
- Java's silently discarded `top` fragment
  ([#196](../issues/196-java-top-fragment-silently-dropped.md)), found while
  auditing how `top` behaves per target.
- Opt-in type annotations. Worth noting the interaction, since it motivated the
  preamble region: annotations must be deferred regardless of layout, because
  grammar order makes field types forward references as a rule (`Program`
  annotates `Expr`, defined later) and the reference graph is cyclic, so no
  class order exists that would avoid it. `from __future__ import annotations`
  is the fix on `requires-python = ">=3.12"`, which is exactly why the preamble
  region has to be addressable by both the emitter and the author.

## Commit shape

Conventional commits, matching scopes already in the log. Roughly: the spec
plumbing (`feat(spec)`), the reserved `module` target and its slots
(`feat(spec)`), the shared option check (`feat(lang)`), the emitter and
templates (`feat(python)`), schemas, docs plus fixture (`docs`), and
`bin/issues/close.bash 195` as the branch's final commit.

Note the first commit cannot land until #197 fixes the slot names, since they
appear in the parser, the validator, the model kinds, the emitter, and the docs
at once.

## Files changed

| File | Change |
|---|---|
| `src/plcc/spec/semantics/parse_semantic_spec.py` | split the language line |
| `src/plcc/spec/semantics/LanguageDeclaration.py` | add `options` |
| `src/plcc/spec/semantics/SemanticSpec.py` | add `options` |
| `src/plcc/spec/semantics/deserialize.py` | read `options`, default `[]` |
| `src/plcc/spec/semantics/validation.py` | exempt the reserved `module` target from `^[A-Z]` |
| `src/plcc/model/build_model.py` | carry `options`; give each module slot its own kind |
| `src/plcc/schemas/spec.schema.json` | optional `options` |
| `src/plcc/schemas/model.schema.json` | optional `options` |
| `src/plcc/lang/options.py` | new: shared unknown-option check |
| `src/plcc/lang/ext/python/options.py` | new: `SUPPORTED` |
| `src/plcc/lang/ext/python/emit.py` | enforce options; single-module path; reject `Class:top`/`Class:import` in this mode |
| `src/plcc/lang/ext/python/templates/class_file.py.jinja` | extract class macro |
| `src/plcc/lang/ext/python/templates/module.py.jinja` | new: merged module |
| `src/plcc/lang/ext/python/templates/main.py.jinja` | import from `classes` |
| `docs/language-guide/languages/python.md` | options, output tree, module hooks, which kinds are unavailable, migration |
| `docs/language-guide/semantic.md` | free-standing code via `module:head`/`module:tail` |
| `tests/fixtures/docs/lang-guide-python-single-module/` | new docs fixture |
| `tests/docs/example_block_test.py` | register fixture in `MANIFEST` |
| plus unit, e2e, and bats tests per **Testing** | |
