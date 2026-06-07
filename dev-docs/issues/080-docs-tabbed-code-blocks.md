# 080 - Tabbed code blocks for language-specific alternatives

**Type:** docs
**Date:** 2026-06-07

## Description

When the docs show code examples that differ by target language (e.g. Java vs Python semantics), all variants are shown at once. Users who only care about one language have to visually skip the others throughout the docs.

## Desired Behavior

Where a page shows the same concept in multiple languages, present each language variant as a tab so the user can select the one they care about. Ideally the selected language persists across pages for the session.

## Notes

Many static-site doc frameworks support this natively:

- **MkDocs Material** — content tabs with `=== "Java"` / `=== "Python"` syntax; selection can be synced across the page.
- **Docusaurus** — `<Tabs>` / `<TabItem>` components with grouped tab syncing built in.

The right approach depends on which framework the docs use. This feature would pair well with whatever language-specific content exists or is added in the future.
