# CLAUDE.md

Read [CONTRIBUTING.md](CONTRIBUTING.md) before making changes. It describes the commands in [bin/](bin/), the test tiers, and the TDD inner loop used throughout this repository.

Do not write ad-hoc shell scripts. Check [bin/](bin/) first — the script you need probably already exists. If it does not, add one there and match the existing style.

## Creating issues

To add a new issue to [docs/issues/](docs/issues/), always use [bin/issues/new.bash](bin/issues/new.bash):

```bash
bin/issues/new.bash <slug> [type]
```

This reads [docs/issues/.next-id.txt](docs/issues/.next-id.txt) for the next ID, creates the file from the template with the date filled in, and increments the ID. Never assign issue numbers by hand or by scanning the directory.
