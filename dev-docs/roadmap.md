# Roadmap

## Dev-docs cleanup

Resolved #145 (mkdocs `--strict` warnings) by deciding to decommission
the dev-docs site rather than work around `docs_dir`'s constraints, and
split the remaining work into these issues. Order: decommission first
since it's the largest scope cut and removes the premise that a strict
build must stay green; the rest are independent content/tooling
hygiene with no urgency relative to each other. Completed items are
checked off (and stay listed) so this section tracks progress; it
retires once every item below is checked off.

1. [x] [#148](issues/done/148-decommission-dev-docs-mkdocs-site.md) — remove the mkdocs-dev.yml build/deploy and its published gh-pages content; ~70% of #145's warnings exist only because of this build.
2. [x] [#149](issues/done/149-fix-stale-issues-done-links.md) — fix broken issues/NNN links that should point to issues/done/; independent of #148, real breakage on GitHub either way.
3. [x] [#150](issues/done/150-close-script-auto-fix-links.md) — harden close.bash to prevent #149's bug class from recurring.
4. [x] [#151](issues/done/151-migrate-superpowers-docs-to-dev-docs.md) — migrate docs/superpowers/specs/ and docs/superpowers/plans/ into dev-docs/; discovered while working #150, same content/tooling hygiene as the rest of this cleanup.

## Open Issues

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
- **[#158](issues/158-current-version-docs-missed-pre-157-changes.md) — Current-version docs missed pre-157 changes**
  #157's sync only applies to pushes after it landed; docs-only changes merged between the v1.0.0 tag and 157's fix (e.g. the heading-case standardization) never reached the live 1.0/latest docs and need a one-time manual backfill.
