# 071 - Add upgrade instructions to docs

**Type:** docs
**Date:** 2026-06-07

## Description

The docs have no page explaining how to upgrade an existing plcc-ng installation to a newer version. Users who installed plcc-ng previously have no documented path for upgrading.

## Desired Behavior

Add an "Upgrading" page (or section) to the docs that covers:

- The standard upgrade command (e.g. `pip install --upgrade plcc-ng`).
- Any version-specific migration steps or breaking changes to watch for.
- How to verify the installed version after upgrading.

## Notes

This could live alongside the existing installation docs. If there is a changelog or release notes page, linking from there would help users find it.
