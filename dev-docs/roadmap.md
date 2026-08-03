# Roadmap

## Open Issues

### Fix

- **[#160](issues/160-concurrent-plcc-build-dir-race.md) — Concurrent plcc-scan/plcc-make invocations race on shared build dir**
  Two CLI invocations sharing the same `./plcc-ng/` build dir race on temp-file creation/cleanup and crash with a raw `FileNotFoundError` traceback instead of a friendly error.

### Feat

- **[#161](issues/161-rename-plcc-rep-to-plcc-eval.md) — Consider renaming plcc-rep to plcc-eval for phase-naming consistency**
  `plcc-rep` is named after its interaction mode (REPL), not its phase, breaking the `scan`/`parse`/`?` naming pattern; an alias or rename to `plcc-eval` would restore it.

### Docs

- **[#181](issues/181-docs-run-contract-stale-python-examples.md) — Python examples in docs still use the pre-2.0.0 `_run()` print contract**
  All three `=== "Python"` tabs in `docs/` print from `_run()` instead of returning, so each exits 1 with a `specification_error`; the leaked `print` makes the documented output appear anyway, which is why it went unnoticed.

### Test

- **[#182](issues/182-test-doc-example-drift.md) — Nothing executes the examples in docs/, so they drift silently**
  No test runs any example from `docs/`, and `ci.yml` skips CI for docs-only PRs — so a doc example can break, or contradict its own documented output, with every tier green.

### Chore

- **[#154](issues/154-update-python-semantic-release.md) — Update python-semantic-release**
  Pinned to 9.x (locked 9.21.2); latest is 10.5.3. Dev-only dependency, consider updating.
- **[#156](issues/156-mkdocs-1x-successor-decision.md) — Decide our MkDocs 1.x successor**
  mkdocs-material hard-pins mkdocs<2; mkdocs-kroki-plugin already pulls in properdocs. Not urgent yet, but we'll need to pick ProperDocs, Zensical, or stay pinned once MkDocs 1.x actually breaks.
