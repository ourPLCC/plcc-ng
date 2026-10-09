# CLAUDE.md

Read [CONTRIBUTING.md](CONTRIBUTING.md) before making changes. It describes the commands in [bin/](bin/), the test tiers, and the TDD inner loop used throughout this repository.

Do not write ad-hoc shell scripts. Check [bin/](bin/) first — the script you need probably already exists. If it does not, add one there and match the existing style.

## Tracking work

Work is tracked as change requests (CRs) in the central tracker at
`/workspaces/change-requests` ([ourPLCC/change-requests](https://github.com/ourPLCC/change-requests)),
shared by all ourPLCC repos. Before any tracker work, read
`/workspaces/change-requests/README.md` — it is the workflow guide. Do not use
`backlog instructions`; its guidance differs from ours. This repo's project
value is `plcc-ng`.

Agent-specific rules:

- Use the `backlog` CLI (`BACKLOG_CWD` points it at the tracker). Never edit
  tracker files by hand.
- Create CRs or drafts only with the human's approval. During automated plan
  execution, record discovered work in the CR's notes
  (`backlog task edit CR-N --append-notes "…"`); it is triaged with the human
  at clear-down.
- Plans go in `.plans/` (gitignored, inside the worktree) and are never
  committed. Specs go in `dev-docs/specs/` and do not cite CRs; the CR
  references the spec.
- Branch names start with the CR ID: `cr-1042-short-slug`.
- Legacy issue numbers resolve as CRs: plcc-ng `#160` is `CR-160`
  (`backlog task view 160`).
