# Roadmap

## Open Issues

### Fix

- **[#160](issues/160-concurrent-plcc-build-dir-race.md) — Concurrent plcc-scan/plcc-make invocations race on shared build dir**
  Two CLI invocations sharing the same `./plcc-ng/` build dir race on temp-file creation/cleanup and crash with a raw `FileNotFoundError` traceback instead of a friendly error.
- **[#170](issues/170-arbno-follow-set-missing-eof.md) — LL(1) FOLLOW-set computation drops end-of-input for nullable nonterminals not registered first**
  `_allRulesCanDeriveEmpty` only checks a nonterminal's first-registered production for nullability, so `**=` (arbno) rules whose repeated element has a nested epsilon alternative wrongly reject valid input at end-of-input (`no production for '<X>'`).

### Feat

- **[#161](issues/161-rename-plcc-rep-to-plcc-eval.md) — Consider renaming plcc-rep to plcc-eval for phase-naming consistency**
  `plcc-rep` is named after its interaction mode (REPL), not its phase, breaking the `scan`/`parse`/`?` naming pattern; an alias or rename to `plcc-eval` would restore it.

### Docs

- **[#167](issues/167-java-examples-doc-exp-missing-abstract-eval.md) — Java "subtraction language" example in examples.md doesn't compile — `Exp` never declares `eval()`**
  `Exp` is generated abstract (it has named alternatives) but no fragment declares `public abstract int eval();`, so every `.eval()` call on an `Exp`-typed reference fails with `cannot find symbol`.
- **[#169](issues/169-whats-new-entry-for-next-release.md) — Add whats-new.md entry for the next release before merging this branch**
  `docs/whats-new.md` hasn't been updated since the v1.0.0 entry; this branch has accumulated a release's worth of user-facing changes (several `fix!`/`BREAKING CHANGE` commits) that need a summarized entry before merge.
- **[#171](issues/171-javascript-doc-quick-reference-not-ll1.md) — JavaScript language guide's "Quick reference example" grammar is not LL(1)**
  Same left-recursive `Exp` rule as #166's Java version; `plcc-rep` rejects it with the same LL(1) conflict.
- **[#172](issues/172-python-doc-quick-reference-not-ll1.md) — Python language guide's "Quick reference example" grammar is not LL(1)**
  Same left-recursive `Exp` rule as #166's Java version; `plcc-rep` rejects it with the same LL(1) conflict.
- **[#173](issues/173-haskell-doc-quick-reference-not-ll1.md) — Haskell language guide's "Quick reference example" grammar is not LL(1)**
  Same left-recursive `Exp` rule as #166's Java version, but the fix must respect Haskell's fragment-naming constraint (pattern-matched clauses in one `Op` fragment, not per-alternative fragments).

### Chore

- **[#154](issues/154-update-python-semantic-release.md) — Update python-semantic-release**
  Pinned to 9.x (locked 9.21.2); latest is 10.5.3. Dev-only dependency, consider updating.
- **[#156](issues/156-mkdocs-1x-successor-decision.md) — Decide our MkDocs 1.x successor**
  mkdocs-material hard-pins mkdocs<2; mkdocs-kroki-plugin already pulls in properdocs. Not urgent yet, but we'll need to pick ProperDocs, Zensical, or stay pinned once MkDocs 1.x actually breaks.
