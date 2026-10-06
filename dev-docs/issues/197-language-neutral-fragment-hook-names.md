# 197 - Language-neutral names for fragment hooks

**Type:** feat
**Date:** 2026-10-06

<!--
Classify by user-facing impact, not by whether something was "broken".
`fix` and `feat` bump the release version (see [tool.semantic_release]
in pyproject.toml); reserve them for changes to the shipped package
(src/). A bug in a test, script, or CI workflow (bin/, tests/,
.github/) is still a bug, but it's not user-facing — classify it
`test` or `chore` instead so it doesn't spin the version. `docs` is for
documentation content, and never bumps the version either way.
-->

## Description

The fragment-hook names (`top`, `import`, `class`, `init`, `body`, and the
unnamed `file` kind) were coined for Java and do not generalize. Collected from
the four `docs/language-guide/languages/*.md` hook tables as they stand today:

| Slot | Java | Python | JavaScript | Haskell |
| --- | --- | --- | --- | --- |
| `top` | package decls | constants/directives | `'use strict'` | `{-# LANGUAGE … #-}` |
| `import` | import section | import section | after requires | after imports |
| `class` | implements/extends | extra bases | *absent* | *absent* |
| `init` | constructor body | `__init__` body | constructor body | *absent* |
| `body` | class body | class body | class body | **module body** |
| `file` | replaces entire file | replaces entire file | replaces entire file | replaces entire file |

Three distinct problems:

1. **`top` means four different things.** They unify only as "the earliest
   legal position for whatever this language requires first." The name
   describes a position in a file rather than the concept, which is why each
   page has to explain it from scratch — and why it is
   [silently unimplemented in Java](196-java-top-fragment-silently-dropped.md).
2. **`body` changes scope between targets.** Class members in the three OO
   targets, top-level function definitions in Haskell. One name, two scopes.
3. **`file` is named after an artifact.** It means "replaces the entire file",
   which presumes one file per class. [#195](195-python-single-module-output.md)
   abolishes that presumption, leaving the name describing something that no
   longer exists.

`class` is also awkward on its own terms: the target of a locator is already a
class, so `Expr:class` names it twice, and what the hook actually targets is
the declaration line.

## Notes

### Sketch: target + slot

The DSL already has the right shape — `Target:slot` — but has only ever had one
kind of target. Adding a reserved `module` target may be the whole move:

| Target | Slot | Means |
| --- | --- | --- |
| `module` | `preamble` | earliest legal position — pragmas, `__future__`, `'use strict'`, package |
| `module` | `import` | dependency declarations |
| `module` | `head` | top-level code before the generated types |
| `module` | `tail` | top-level code after the generated types |
| *Class* | `decl` | declaration line — supertypes, interfaces, mixins |
| *Class* | `init` | initializer body |
| *Class* | `body` | members |

`preamble` names the concept `top` only gestured at. `decl` replaces `class`.
`init` and `body` survive, with `body` now unambiguously class-scoped, which
resolves the Haskell scope inconsistency — Haskell's top-level functions become
`module:tail`.

The property that makes this worth doing: **in multi-module mode each class is
a module**, so the same slots apply with a class target (`Expr:preamble`,
`Expr:import`). Under #195's single-module mode they diverge and the target
becomes `module:`. One vocabulary, two targets, so changing modes is a
meaningful retarget rather than a rename.

### Open questions

- **Free-standing code in multi-module mode.** Today that is the `file` kind —
  its own file. `module:head` does not say *which* module. A named target such
  as `MyHelper:module` ("this block is a module called MyHelper") may fit, but
  this is unresolved.
- **Is `import` still meaningful on a class target under single-module?**
  Probably module-only there, since per-class imports have no referent.
- **`head`/`tail` are only load-bearing in some targets.** Definition order
  matters in Python and JavaScript; Java resolves regardless and Haskell's
  top-level bindings are mutually recursive. Two slots that collapse into one
  for half the targets — document rather than pretend it is universal.
- **Do the OO slots need neutral names at all?** `init` and `body` are
  arguably fine; Haskell simply does not offer them. Renaming for symmetry
  alone may cost more than it returns.

### Migration

Specs are in active classroom use, so the old names cannot simply change
meaning. The intended path is additive: introduce the new names alongside the
old, migrate the docs, let specs convert at their own pace, and only then
consider deprecating the originals. Nothing here should break a spec that is
never touched.

### Relationship to #195

[#195](195-python-single-module-output.md) is blocked on **resolving these
names**, not on implementing them. Its single-module mode needs module-targeted
hooks, and shipping it with provisional names would mean renaming a published
hook later. Once the vocabulary is decided, #195 can adopt the agreed names and
proceed independently; the multi-module hooks and the deprecation path can land
on their own schedule.

## Design discussion (2026-10-06)

A brainstorming session moved away from the sketch above. It is recorded here
in three parts: what was decided, what was recommended but not yet decided, and
what was found along the way. Nothing here is implemented yet.

### Decided

**Keep the existing names; add rather than rename.** Renaming is too much work
for authors and docs. The sketch's `preamble`, `decl`, `head` and `tail` are
dropped. `top`, `import`, `class`, `init` and `body` keep their current meaning.
The additions are two slots, `before` and `after`, and a reserved `module`
target.

| Hook | Multi-module, non-terminal `X` | Multi-module, standalone `X` | Single-module ([#195](195-python-single-module-output.md)) |
| --- | --- | --- | --- |
| `X:top` | as today | top of `X`'s module | error |
| `X:import` | as today | imports of `X`'s module | error |
| `X:before` | after imports, before the generated class | module content | error |
| `X:after` | after the generated class | module content (same as `before`) | error |
| `X:class` / `X:init` / `X:body` | as today | error — no class | as today |
| `X:raw` | error | verbatim whole module | allowed — a separate module |
| `module:top/import/before/after` | error — no single module | error | the merged module's regions |

- **`module` cannot clash with a class name.** Locator names must match
  `^[A-Z]`, so the lowercase `module` is free to reserve as a target.
- **A standalone `X` is a module with no generated class.** The same slots
  apply to it. With no class to sit beside, `before` and `after` both mean the
  module's content.
- **`X:raw` is the explicit form of today's bare standalone `X`.** It is the
  whole module, written verbatim, with nothing generated by the emitter. It
  replaces the `file` kind, a name that describes an artifact rather than
  behaviour.
  - It is valid only on a standalone target, and it cannot be combined with
    any other `X:` slot.
  - It is **allowed in single-module mode**. #195's goal is to remove sibling
    imports between generated classes, not to produce one file. The output
    already includes `main.py` and `runtime/`, and an explicitly raw author
    module is just one more file. This revises #195's spec: the `file` kind is
    still an error there, and `raw` is the supported replacement.
- **For a non-terminal `X`, bare `X` means `X:body`.** This is the original
  PLCC convention, kept unchanged.
- **Haskell's `X:body` can keep its current meaning.** It means top-level code
  after the generated type, so `X:after` is now the neutral spelling of the
  same thing.
- **#195 adopts `module:top`, `module:import`, `module:before` and
  `module:after`** in place of the provisional `module:preamble`, `import`,
  `head` and `tail`. The regions and their order are unchanged. Its spec needs
  that edit, plus the `raw` revision above.

### Recommended, not yet decided

- **A strict mode, where every locator must name its slot.** Bare `X` is
  rejected in favour of `X:body` or `X:raw`.
  - **Where to declare it.** The original proposal was a `--strict` CLI flag.
    The recommendation is to declare it in the spec instead: otherwise the same
    spec is accepted or rejected depending on who runs it, and #195 already
    avoided a CLI flag for the same reason. Strict applies to every language
    and would be checked by the core validator, so it may need its own place
    in the spec rather than #195's option list after the language name, which
    each language extension checks for itself.
  - **How much it covers.** It could also reject the legacy forms (`top`, and
    so on) if any are deprecated later. With no renames, it may only ever need
    to cover bare names.
- **Defer the structured standalone form** (`Helper:top`, `import`, `before`,
  `after`) and ship only `Helper:raw` at first. `raw` covers everything bare
  `Helper` does today. The structured form needs each emitter to define what a
  module with no class contains: runtime imports, Haskell's `module … where`
  line, and JavaScript and Haskell exports. Turning that error into a feature
  later is not a break.
- **Single-module `Class:before` and `Class:after`** could mean "right next to
  this class". They stay an error for now, so the feature can be added later
  without a break.

### Found along the way

- **An unknown slot name is silently accepted.**
  [`_compute_kind`](../../src/plcc/model/build_model.py) only recognises `top`,
  `import`, `class` and `init`. Anything else becomes `body` if the class is in
  the grammar, and `file` otherwise.
  - Reproduced: `Term:imprt` puts `import re` inside the class body. The build
    exits 0, and the mistake later surfaces as a `NameError` in a method.
  - The locator regex accepts only lowercase slot names, so `Term:Import` is
    read as a class named `Term:Import`, and the block becomes a file of that
    name.
  - `body` itself is never actually recognised; it works only by falling
    through. So `Helper:body` on a standalone name is a `file`, not a body.
  - No case was found where the fallback is wanted. The slot vocabulary should
    become a closed set, and an unknown name an error. It needs its own `fix`
    issue (not yet filed), which should land before any new slot names. Until
    then, a spec using `X:before` on an older plcc-ng would build cleanly with
    the code in the wrong place.
- **Generated-file name collisions** are filed as
  [#198](198-generated-file-name-collisions.md). The tables above assume its
  guarantee: an author-named module, `raw` ones included, never collides with
  plcc-ng's own files.
