# 195 - Optionally generate Python output as a single module

**Type:** feat
**Date:** 2026-10-05

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

A spec should be able to ask for its Python output as a single module
instead of one file per class.

Today [`plcc-python-emit`](../../src/plcc/lang/ext/python/emit.py) writes a
separate `.py` file for every class: its `main` loops over `model['classes']`
and writes `<ClassName>.py` for each, plus `_Start.py`, plus one file per
standalone-class fragment, plus `main.py`, plus a copied `runtime/` package.
Because each class is its own module, any reference from one generated class
to another has to be imported by hand. That is what the `Class:import` hook
is for, and it means a spec accumulates `Class:import` blocks whose only
purpose is to undo the file split — boilerplate that carries no information
about the language being defined.

Collapsing the output into one module would make those imports unnecessary:
classes in the same module see each other without any import at all.

**This must be opt-in, requested by the spec.** Course materials depend on
the current layout, so the existing one-file-per-class behavior has to remain
the default and stay byte-for-byte unchanged for specs that do not ask for
anything different.

### Open questions for design

The boundaries are deliberately left open here; they are the substance of the
design discussion, not settled by this issue.

- **How a spec requests it.** There is no spec-level option mechanism of any
  kind today (see Notes), so one has to be designed — or the option has to
  ride on something that already exists. Whether that mechanism is general
  (an options facility usable by future features) or narrow (one flag for
  this one behavior) is open, as is whether it is a separable piece of work.
- **Standalone classes.** Blocks naming a class that no grammar rule produces
  are currently written verbatim to their own file. Folding them into the
  single module seems right, but it needs checking — see Notes for what makes
  it non-obvious.
- **How much is "the module."** Generated classes clearly. Whether `_Start`,
  `main.py`, and the copied `runtime/` package are in or out is open.
- **Other targets.** JavaScript emits per-class files by the same pattern and
  may want the same option. Java compiles its files together, so it has less
  to gain. Whether this issue covers them, or Python leads and the others
  follow, is open.

## Notes

Observations from reading the current emitter, recorded so the design
discussion does not have to rediscover them.

**There is no spec-level option mechanism at all.** Nothing in
[`src/plcc/spec/`](../../src/plcc/spec/) parses an option, pragma, or setting;
every `Options:` string in the tree is docopt CLI usage. So "specified in the
spec" is new ground rather than a new value for an existing knob.

**The language-declaration line is an exact whole-line match.**
`parse_semantic_spec`'s `_extract_language` takes the entire stripped line as
the language name, and the emitter's `_find_python_section` matches it by
lowercased equality against `'python'`. An option appended to that line (say
`Python single-module`) would therefore parse as a language *named*
`python single-module` and match no section — producing no output rather than
an error. Whatever the syntax turns out to be, that silent-miss path is worth
keeping in mind.

**Class definition order matters once the files merge.**
[`class_file.py.jinja`](../../src/plcc/lang/ext/python/templates/class_file.py.jinja)
emits `class X(Parent)` and a matching `from Parent import Parent`, so a base
class is resolved when the class statement executes, not later. In one module
the parent must therefore appear earlier in the file. The good news is that
`build_model`'s `_build_classes` already appends each abstract base ahead of
the alternatives that extend it, and `extends` only ever names that same
group's base — so the existing class order already satisfies this. `_Start` is
the exception: the emitter injects it as the start class's base while writing
it to its own file, so a merged module has to place it before its subclass.

**Standalone classes can be dependencies of generated classes, not just
neighbors.** A `Class:class` fragment injects additional base classes into the
generated class statement. If one of those names is defined by a standalone
block, then the merged file has to order that block *before* the class that
mixes it in. This is the main reason the standalone-class question above is
not simply "put them in too": their position can be load-bearing. Their
current contract is also the strongest verbatim guarantee in the emitter —
the block's body is written byte-for-byte with no scaffolding added — and a
block authored as a complete file may hold module docstrings, its own
imports, or top-level statements that read differently once concatenated with
others.

**`main.py` imports every class by module name.**
[`main.py.jinja`](../../src/plcc/lang/ext/python/templates/main.py.jinja)
renders `from <Class> import <Class>` per class before registering them, so
it changes with the layout whether or not it becomes part of the module
itself.

**Per-class boilerplate would be duplicated.** Every generated class file
begins with `import runtime.base as _plcc` and
`from runtime.base import LanguageError`. Merged naively that is one copy per
class — harmless but worth hoisting.

**Nothing exercises `Class:import` today.** The string `:import` appears only
in [docs/language-guide/](../../docs/language-guide/); no test or fixture
writes an import block and then resolves a real cross-class reference through
it. Since this feature's whole point is making those blocks unnecessary, there
is no regression test standing guard over the behavior it replaces. Worth
closing that gap alongside the work, so "the import blocks are no longer
needed" can be demonstrated rather than asserted.

**Pre-existing footgun noticed while reading `_compute_kind`.** The
standalone-class path is reached by *falling through*: `build_model`'s
`_compute_kind` returns `'file'` whenever the locator carries no recognized
modifier and the class name is not a known grammar class. A misspelled class
name on a body block therefore becomes a silent new standalone file instead of
an error. Not part of this feature, but it touches the same code and may
deserve its own issue.
