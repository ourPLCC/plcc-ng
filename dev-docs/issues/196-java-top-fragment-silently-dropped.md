# 196 - A Java `top` fragment is silently discarded

**Type:** fix
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

[`docs/language-guide/languages/java.md`](../../docs/language-guide/languages/java.md)
documents a `top` fragment kind for Java — *"Top of the file, before the class
/ Package declarations"* — but the Java emitter never emits it. A
`SomeClass:top` block in a Java spec is accepted, validated, carried all the
way into `model.json`, and then dropped on the floor without an error, a
warning, or any output.

The code never selects the fragment.
[`java/emit.py`](../../src/plcc/lang/ext/java/emit.py) renders its class
template with four fragment kinds:

```python
content = class_template.render(
    cls=cls,
    import_fragments=[f for f in frags if f['kind'] == 'import'],
    class_fragments=[f for f in frags if f['kind'] == 'class'],
    init_fragments=[f for f in frags if f['kind'] == 'init'],
    body_fragments=[f for f in frags if f['kind'] == 'body'],
)
```

There is no `top_fragments` argument, and
`templates/class_file.java.jinja` contains no reference to one. Compare
[`python/emit.py`](../../src/plcc/lang/ext/python/emit.py), which passes
`top_fragments=[f for f in frags if f['kind'] == 'top']`, and whose template
renders it first.

`'top'` is a recognized modifier in
[`build_model.py`](../../src/plcc/model/build_model.py)'s `_compute_kind`, so
nothing upstream rejects the block — which is why the failure is silent rather
than an error.

Java is the only affected target:

| Target | `top` in `emit.py` | `top` in template |
| --- | --- | --- |
| Python | yes | yes |
| JavaScript | yes | yes |
| Haskell | yes | n/a (no Jinja templates) |
| **Java** | **no** | **no** |

## Steps to Reproduce

1. Write a Java spec with a `top` fragment on any grammar class:

   ```text
   SomeClass:top
   %%%
   // marker comment
   %%%
   ```

2. Run `plcc-make` (or `plcc-java-emit` directly on the model JSON).
3. Inspect the generated `SomeClass.java`.

The block's content is absent, and the command exits 0.

## Notes

Two defensible fixes, and they are not equivalent:

1. **Implement it.** Pass `top_fragments` and render it ahead of the imports,
   matching Python and JavaScript. Note that what the docs claim it is *for* —
   package declarations — is questionable: plcc-ng generates Java into a flat
   directory with no package statement, and a user-supplied `package` line
   would break the build layout rather than help. So implementing the hook
   faithfully may deliver a feature whose documented use case does not work.
2. **Remove it from the Java docs.** If there is no legal Java construct that
   belongs above the import section in generated output, the honest fix is to
   drop the row from the fragment-kinds table and reject `top` for the Java
   target, so the error is loud instead of silent.

Deciding between them needs an answer to "what would a Java author legitimately
put there?" — worth settling before writing code.

Either way, the silent discard is the bug: an accepted, validated block that
produces nothing is the worst of the three outcomes.

Found while scoping [#195](195-python-single-module-output.md), which audits
how the `top` and `import` hooks behave per target because those hooks are
file-relative and a single module has no per-class file.
