# CLAUDE.md

Read [CONTRIBUTING.md](CONTRIBUTING.md) before making changes. It describes the commands in [bin/](bin/), the test tiers, and the TDD inner loop used throughout this repository.

Do not write ad-hoc shell scripts. Check [bin/](bin/) first — the script you need probably already exists. If it does not, add one there and match the existing style.

## Creating and closing issues

Issue workflow conventions live in [dev-docs/issue-conventions.md](dev-docs/issue-conventions.md). The short version:

To add a new issue to [dev-docs/issues/](dev-docs/issues/), always use [bin/issues/new.bash](bin/issues/new.bash):

```bash
bin/issues/new.bash <slug> [type]
```

This reads [dev-docs/issues/.next-id.txt](dev-docs/issues/.next-id.txt) for the next ID, creates the file from the template with the date filled in, and increments the ID. Never assign issue numbers by hand or by scanning the directory. Add a roadmap entry in the same commit.

To close an issue, always use [bin/issues/close.bash](bin/issues/close.bash) — as the final commit of the branch that does the work. It moves the file to `done/` and updates [dev-docs/roadmap.md](dev-docs/roadmap.md). Verify consistency any time with [bin/issues/check.bash](bin/issues/check.bash).
