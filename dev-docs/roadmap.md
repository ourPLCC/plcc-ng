# Roadmap

## Open Issues

### Fix

- **[#160](issues/160-concurrent-plcc-build-dir-race.md) — Concurrent plcc-scan/plcc-make invocations race on shared build dir**
  Two CLI invocations sharing the same `./plcc-ng/` build dir race on temp-file creation/cleanup and crash with a raw `FileNotFoundError` traceback instead of a friendly error.
- **[#180](issues/180-ll1-schema-omits-conflict-type.md) — ll1 schema omits conflict_type**
  `plcc-ll1` emits `conflict_type` on every entry of `conflicts`, but `ll1.schema.json` declares neither the property nor its `first_first`/`first_follow` values.

### Feat

- **[#161](issues/161-rename-plcc-rep-to-plcc-eval.md) — Consider renaming plcc-rep to plcc-eval for phase-naming consistency**
  `plcc-rep` is named after its interaction mode (REPL), not its phase, breaking the `scan`/`parse`/`?` naming pattern; an alias or rename to `plcc-eval` would restore it.

### Test

- **[#178](issues/178-bats-version-declaration-unenforced.md) — Nothing enforces bats_require_minimum_version in bats files**
  A new bats file can use `BATS_TEST_TMPDIR` without declaring the version floor; on an older bats the variable is unset and paths silently degrade to `/work`.

### Chore

- **[#154](issues/154-update-python-semantic-release.md) — Update python-semantic-release**
  Pinned to 9.x (locked 9.21.2); latest is 10.5.3. Dev-only dependency, consider updating.
- **[#156](issues/156-mkdocs-1x-successor-decision.md) — Decide our MkDocs 1.x successor**
  mkdocs-material hard-pins mkdocs<2; mkdocs-kroki-plugin already pulls in properdocs. Not urgent yet, but we'll need to pick ProperDocs, Zensical, or stay pinned once MkDocs 1.x actually breaks.
