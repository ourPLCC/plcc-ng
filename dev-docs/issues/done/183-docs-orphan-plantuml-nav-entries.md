# 183 - Orphan plantuml nav entries put three dead links in the published docs

**Type:** docs
**Date:** 2026-08-04

## Description

`mkdocs.yml` lists three command pages that do not exist:

```yaml
- plcc-plantuml-diagram-build: cli/commands/plcc-plantuml-diagram-build.md
- plcc-plantuml-diagram-emit: cli/commands/plcc-plantuml-diagram-emit.md
- plcc-plantuml-diagram-run: cli/commands/plcc-plantuml-diagram-run.md
```

They are leftovers from #113, which renamed the diagram commands. The renamed
pages are all already in the nav at lines 61-69, so these three entries are pure
orphans — deleting them loses nothing.

The published site therefore carries three dead nav links. The deploy itself is
not failing: `.github/workflows/docs.yml` publishes via `mike deploy`, which
builds without `--strict`, and `mkdocs.yml` sets no `strict:` key, so a missing
nav target is a warning rather than an error.

**Nothing in CI runs `mkdocs build --strict`** — not `docs.yml`, not `ci.yml`,
not any script in `bin/`. That is why this reached `main` and stayed. It is the
same shape of gap as #182: the check that would have caught it was never wired
up.

## Steps to Reproduce

1. `pdm run mkdocs build --strict`

```
The following pages exist in the docs directory, but are not included in the "nav" configuration:
  ...
Aborted with 3 warnings in strict mode!
```

## Notes

Found while running `mkdocs build --strict` as a manual verification step during
the #181/#182 work, not by any automated check.

Two parts to the fix:

- Delete the three orphan entries from `mkdocs.yml`.
- Add a `mkdocs build --strict` step to `.github/workflows/docs-tests.yml`,
  which #182 introduced and which already triggers on `mkdocs.yml` and
  `docs/**`. That makes a broken doc link fail the PR that introduces it,
  instead of surfacing on the live site.

Placing the gate in `docs-tests.yml` rather than `docs.yml` is deliberate:
`docs.yml` runs only on push to `main` and on release, so a gate there would
catch problems only after merge.
