# Roadmap

## Open Issues

### Fix

- **[#160](issues/160-concurrent-plcc-build-dir-race.md) — Concurrent plcc-scan/plcc-make invocations race on shared build dir**
  Two CLI invocations sharing the same `./plcc-ng/` build dir race on temp-file creation/cleanup and crash with a raw `FileNotFoundError` traceback instead of a friendly error.

### Feat

- **[#161](issues/161-rename-plcc-rep-to-plcc-eval.md) — Consider renaming plcc-rep to plcc-eval for phase-naming consistency**
  `plcc-rep` is named after its interaction mode (REPL), not its phase, breaking the `scan`/`parse`/`?` naming pattern; an alias or rename to `plcc-eval` would restore it.

### Docs

- **[#163](issues/163-js-var-field-reserved-word.md) — Auto-named field colliding with a JavaScript reserved word breaks generated code**
  A capture like `<VAR>` auto-names its field `var`, and the JavaScript target's generated `constructor(var)` is a `SyntaxError` since `var` is reserved.
- **[#164](issues/164-multi-capture-alt-name-case-mismatch.md) — camelCase alt-names lowercased by the parser but not by code generation, breaking multi-capture rules**
  The parser always lowercases alt-names (`getAttributeName()`), but code generation preserves their case, so camelCase alt-names like `testExp` cause a `KeyError` at runtime.
- **[#166](issues/166-java-doc-quick-reference-not-ll1.md) — Java language guide's "Quick reference example" grammar is not LL(1)**
  The example's `Exp` rule is left-recursive, so `plcc-rep` rejects it with an LL(1) conflict — the doc's claimed output (`prints 3`) is false as written; needs left-factoring plus updating the "BNF to Java constructs" table that references its rule names.
- **[#167](issues/167-java-examples-doc-exp-missing-abstract-eval.md) — Java "subtraction language" example in examples.md doesn't compile — `Exp` never declares `eval()`**
  `Exp` is generated abstract (it has named alternatives) but no fragment declares `public abstract int eval();`, so every `.eval()` call on an `Exp`-typed reference fails with `cannot find symbol`.

### Chore

- **[#154](issues/154-update-python-semantic-release.md) — Update python-semantic-release**
  Pinned to 9.x (locked 9.21.2); latest is 10.5.3. Dev-only dependency, consider updating.
- **[#156](issues/156-mkdocs-1x-successor-decision.md) — Decide our MkDocs 1.x successor**
  mkdocs-material hard-pins mkdocs<2; mkdocs-kroki-plugin already pulls in properdocs. Not urgent yet, but we'll need to pick ProperDocs, Zensical, or stay pinned once MkDocs 1.x actually breaks.
