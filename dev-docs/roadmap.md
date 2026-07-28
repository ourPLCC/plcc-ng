# Roadmap

## Open Issues

### Fix

- **[#160](issues/160-concurrent-plcc-build-dir-race.md) — Concurrent plcc-scan/plcc-make invocations race on shared build dir**
  Two CLI invocations sharing the same `./plcc-ng/` build dir race on temp-file creation/cleanup and crash with a raw `FileNotFoundError` traceback instead of a friendly error.
- **[#175](issues/175-build-sentinel-ignores-package-version.md) — Build sentinel ignores the installed PLCC-ng version**
  The build sentinel keys only on the spec hash and completed stages, so upgrading PLCC-ng doesn't invalidate a cached `plcc-ng/` build directory even when the new version changes generated artifacts.

### Feat

- **[#161](issues/161-rename-plcc-rep-to-plcc-eval.md) — Consider renaming plcc-rep to plcc-eval for phase-naming consistency**
  `plcc-rep` is named after its interaction mode (REPL), not its phase, breaking the `scan`/`parse`/`?` naming pattern; an alias or rename to `plcc-eval` would restore it.

### Test

- **[#176](issues/176-integration-tier-has-no-arbno-coverage.md) — Integration tier has no repetition-rule (arbno) coverage**
  `tests/bats/integration/` has no `**=` coverage at all; the `plcc-spec | plcc-ll1` boundary where issue #174's lookahead bug lived is only tested at the e2e and unit tiers.
- **[#177](issues/177-bats-helpers-leak-temp-dirs.md) — bats helpers in plcc-rep.bats leak temp build directories**
  `setup_arbno_build` and `setup_mid_body_arbno_build` each `mktemp -d` a build directory that `teardown()` never removes, leaving directories behind in `/tmp` after every e2e run.

### Chore

- **[#154](issues/154-update-python-semantic-release.md) — Update python-semantic-release**
  Pinned to 9.x (locked 9.21.2); latest is 10.5.3. Dev-only dependency, consider updating.
- **[#156](issues/156-mkdocs-1x-successor-decision.md) — Decide our MkDocs 1.x successor**
  mkdocs-material hard-pins mkdocs<2; mkdocs-kroki-plugin already pulls in properdocs. Not urgent yet, but we'll need to pick ProperDocs, Zensical, or stay pinned once MkDocs 1.x actually breaks.
