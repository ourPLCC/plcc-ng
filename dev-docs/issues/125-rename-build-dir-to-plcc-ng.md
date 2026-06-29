# 125 - Rename `build/` output directory to `plcc-ng/`

**Type:** refactor
**Date:** 2026-06-29

## Description

plcc-ng currently writes its generated output into a directory named `build/`. This is a very common name used by many build tools (Maven, Gradle, CMake, npm, etc.), which creates a risk of name collisions when plcc-ng is used alongside other tools in the same project. Renaming the output directory to `plcc-ng/` makes the ownership of that directory unambiguous.

## Notes

- Find all places in the codebase that reference `build/` as the output directory and update them to `plcc-ng/`
- Update any user-facing documentation that mentions `build/`
- This is a breaking change for users who depend on the `build/` path — note it in CHANGELOG
- Consider whether `.gitignore` templates or quickstart examples need updating
