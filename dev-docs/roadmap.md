# Roadmap

## Open Issues

### Docs

- **[#159](issues/159-migration-guide-missing-breaking-changes-callout.md) — Migration guide buries breaking behavior changes**
  `plcc-parse`'s dropped `-t`/`OK` output and `plcc-scan`'s new output format are only mentioned in a comparison table, not called out as breaking changes.

### Test

- **[#153](issues/153-test-artifacts-outside-project-dir.md) — Test artifacts land outside the project directory**
  Tests that run plcc-make must build in a directory created outside the project; plcc-ng/'s default build-dir name matches the project's own, and .gitignore doesn't exclude it.

### Chore

- **[#154](issues/154-update-python-semantic-release.md) — Update python-semantic-release**
  Pinned to 9.x (locked 9.21.2); latest is 10.5.3. Dev-only dependency, consider updating.
- **[#155](issues/155-test-scripts-path-filter.md) — Top-level test scripts should accept a path filter**
  bin/test/commands.bash, integration.bash, e2e.bash ignore arguments and always run their whole tier; only units.bash forwards args to pytest.
- **[#156](issues/156-mkdocs-1x-successor-decision.md) — Decide our MkDocs 1.x successor**
  mkdocs-material hard-pins mkdocs<2; mkdocs-kroki-plugin already pulls in properdocs. Not urgent yet, but we'll need to pick ProperDocs, Zensical, or stay pinned once MkDocs 1.x actually breaks.
