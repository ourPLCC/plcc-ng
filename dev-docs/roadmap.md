# Roadmap

## Dev-docs cleanup

Resolved #145 (mkdocs `--strict` warnings) by deciding to decommission
the dev-docs site rather than work around `docs_dir`'s constraints, and
split the remaining work into these three issues. Order: decommission
first since it's the largest scope cut and removes the premise that a
strict build must stay green; the other two are independent
content/tooling hygiene with no urgency relative to each other.
Completed items are checked off (and stay listed) so this section
tracks progress; it retires when all three ship.

1. [x] [#148](issues/done/148-decommission-dev-docs-mkdocs-site.md) — remove the mkdocs-dev.yml build/deploy and its published gh-pages content; ~70% of #145's warnings exist only because of this build.
2. [x] [#149](issues/done/149-fix-stale-issues-done-links.md) — fix broken issues/NNN links that should point to issues/done/; independent of #148, real breakage on GitHub either way.
3. [x] [#150](issues/done/150-close-script-auto-fix-links.md) — harden close.bash to prevent #149's bug class from recurring.

## Open Issues

### Docs

- **[#147](issues/147-capitalization-of-section-headings.md) — Capitalization of section headings**
  Section heading capitalization is inconsistent across the docs; needs a single agreed-upon rule.
- **[#151](issues/151-migrate-superpowers-docs-to-dev-docs.md) — Migrate docs/superpowers/ into dev-docs/**
  docs/superpowers/specs/ and docs/superpowers/plans/ duplicate dev-docs/specs/ and dev-docs/plans/; consolidate into the latter.

### Test

- **[#152](issues/152-test-cache-content-hash-invalidation.md) — Test cache stale-hit on content-only changes**
  bin/test/_cache.bash keys on the dirty-file list, not content; editing an already-dirty file can replay a stale cached result.
- **[#153](issues/153-test-artifacts-outside-project-dir.md) — Test artifacts land outside the project directory**
  Tests that run plcc-make must build in a directory created outside the project; plcc-ng/'s default build-dir name matches the project's own, and .gitignore doesn't exclude it.

### Chore

- **[#154](issues/154-update-python-semantic-release.md) — Update python-semantic-release**
  Pinned to 9.x (locked 9.21.2); latest is 10.5.3. Dev-only dependency, consider updating.
