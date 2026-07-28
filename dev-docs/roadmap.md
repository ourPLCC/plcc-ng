# Roadmap

## Open Issues

### Fix

- **[#160](issues/160-concurrent-plcc-build-dir-race.md) — Concurrent plcc-scan/plcc-make invocations race on shared build dir**
  Two CLI invocations sharing the same `./plcc-ng/` build dir race on temp-file creation/cleanup and crash with a raw `FileNotFoundError` traceback instead of a friendly error.
- **[#174](issues/174-arbno-drops-mid-body-terminal.md) — arbno drops mid-body non-capturing terminal**
  A separator-less arbno (`**=`) body silently loses a non-capturing terminal sitting between two capturing symbols: it analyzes as LL(1) but the runtime table omits the terminal, so parsing fails.

### Feat

- **[#161](issues/161-rename-plcc-rep-to-plcc-eval.md) — Consider renaming plcc-rep to plcc-eval for phase-naming consistency**
  `plcc-rep` is named after its interaction mode (REPL), not its phase, breaking the `scan`/`parse`/`?` naming pattern; an alias or rename to `plcc-eval` would restore it.

### Chore

- **[#154](issues/154-update-python-semantic-release.md) — Update python-semantic-release**
  Pinned to 9.x (locked 9.21.2); latest is 10.5.3. Dev-only dependency, consider updating.
- **[#156](issues/156-mkdocs-1x-successor-decision.md) — Decide our MkDocs 1.x successor**
  mkdocs-material hard-pins mkdocs<2; mkdocs-kroki-plugin already pulls in properdocs. Not urgent yet, but we'll need to pick ProperDocs, Zensical, or stay pinned once MkDocs 1.x actually breaks.
