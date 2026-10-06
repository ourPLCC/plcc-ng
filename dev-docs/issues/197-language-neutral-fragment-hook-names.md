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
