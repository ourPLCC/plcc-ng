# Acknowledgments Page Design

**Issue:** 101
**Date:** 2026-06-22

## Goal

Add a standalone acknowledgments page to the plcc-ng docs site that credits significant contributors, institutions/funding sources, and notable open-source dependencies.

## Placement

A standalone page in the top-level nav, added after `Changelog`. This makes it easy to link externally, keeps it visible as project-meta content, and avoids crowding the home page.

Nav entry in `mkdocs.yml`:

```yaml
- Acknowledgments: acknowledgments.md
```

## Page Structure

File: `docs/acknowledgments.md`

Three `##` sections, consistent with the existing flat-prose style used throughout the docs:

### Contributors

Named maintainers listed explicitly (placeholder — to be filled in by maintainer before merge), followed by a link to the GitHub contributors page for the full list:

> For a full list of contributors, see the [GitHub contributors page](https://github.com/ourPLCC/plcc-ng/graphs/contributors).

### Institutions & Funding

Placeholder — to be filled in by maintainer before merge.

### Open-Source Dependencies

Placeholder — to be filled in by maintainer before merge.

## Out of Scope

- Footer links (not needed; the nav page is sufficient)
- Automated contributor generation (GitHub link covers this)
- Grid cards or other Material-specific markup (flat prose matches existing style)
