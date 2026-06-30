# 126 - Add command reference page for `plcc-diagram-syntax`

**Type:** docs
**Date:** 2026-06-30

## Description

Issue 123 renamed `plcc-diagram-syntactic` to `plcc-diagram-syntax`, but no command reference page was created or updated for the new name. There is no `docs/cli/commands/plcc-diagram-syntax.md` file, and no user-facing docs reference `plcc-diagram-syntax` by name.

## Notes

- Add `docs/cli/commands/plcc-diagram-syntax.md` modeled after the other `plcc-diagram-*` command pages.
- Wire it into `mkdocs.yml` nav.
- Check whether `plcc-diagram-syntactic` appears anywhere in user-facing docs and remove/replace it.
