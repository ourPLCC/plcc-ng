# 199 - Move issue tracking to a central ourPLCC/issues repo using Backlog.md

**Type:** chore
**Date:** 2026-10-08

<!--
Classify by user-facing impact, not by whether something was "broken".
`fix` and `feat` bump the release version (see [tool.semantic_release]
in pyproject.toml); reserve them for changes to the shipped package
(src/). A bug in a test, script, or CI workflow (bin/, tests/,
.github/) is still a bug, but it's not user-facing — classify it
`test` or `chore` instead so it doesn't spin the version. `docs` is for
documentation content, and never bumps the version either way.
-->

## Description

Keeping the tracker inside this repo forces issue writes through the
same branch → PR → CI path as code, which causes three problems:

- **Which branch?** An issue found while working on an unrelated branch
  must be filed either on that branch (and is lost if the branch is
  abandoned) or on a new branch that needs its own PR just to land.
- **ID collisions.** `.next-id.txt` is incremented independently on
  each branch, so issues filed concurrently on different branches get
  the same number.
- **Cross-repo drift.** `languages-ng` runs a fork of this issue system
  that has diverged (see [#189](189-align-issue-system-with-languages-ng.md)),
  and upstream/downstream findings are migrated between repos by hand
  (#160, #161, #185–#188).

Proposal: a single file-based tracker in a new `ourPLCC/issues`
repository, managed with [Backlog.md](https://github.com/MrLesk/Backlog.md),
covering plcc-ng, languages-ng, plcc-ng-demo, plcc-ng-devcontainer, and
any other ourPLCC repos. Each code repo keeps a gitignored clone at
`.issues/`. With only one branch to write to, IDs are assigned in a
single sequence, and filing an issue never needs a PR in a code repo.
It also allows priorities to be set across all repos at once, which
matters with only a couple of maintainers.

This issue is to work out adoption and migration, not to carry them out.

## Notes

**Already decided (in the discussion that led to this issue):**

- File-based, not GitHub Issues: grep across code and issues, diffable
  edits to long design issues, scripted bulk changes, and no
  network/auth dependency all matter because issue management is mostly
  agent-driven.
- Separate repo, cloned alongside (gitignored `.issues/`), **not** a
  git submodule. A submodule pins a commit per branch, which brings the
  per-branch problem back.
- Backlog.md chosen over the alternatives surveyed (Beans,
  EnderRealm/ticket, issuectl, git-bug, Beads, …), mainly for maturity,
  its board/web UI, MCP support, and its Markdown + YAML frontmatter
  format, which keeps the data portable if the tool is ever dropped.

**Questions to settle:**

1. **Targets.** How does an issue say which repo(s) it is about? Leaning
   towards one target per issue, plus umbrella issues that link to
   per-repo child issues, because `type:` semantics differ per repo
   (`fix`/`feat` bump the plcc-ng version through semantic-release). How
   does that map onto Backlog.md's fields (labels, parent/subtasks,
   custom fields)? Per-repo filtering must be easy.
2. **ID namespace.** plcc-ng has used IDs up to 198 and languages-ng
   about 38, and those numbers appear in commits, CHANGELOGs, plans, and
   specs. Options: freeze each repo's existing tracker as a read-only
   archive and start the central tracker past both, or something else.
   How do Backlog.md's ID format (`task-N`) and settings fit?
3. **What migrates.** Only open issues (with a "moved to" stub left
   behind), or everything? What happens to `dev-docs/roadmap.md`, and to
   milestone lists (e.g. *Path to v1.0*)?
4. **Closing from code PRs.** The current rule is to close in the same
   PR as the work. With a separate repo the close cannot merge together
   with the work. Options: close by hand after merge, a commit trailer
   (`Closes: ourPLCC/issues#N`) handled by a post-merge Action, or
   something else. Keep the existing "close on verification" exception.
5. **Global prioritization.** How to keep one short, hand-ranked "next
   up" list across repos alongside per-repo views.
6. **Comments and outside contributors.** The tracker is readable on
   GitHub, but commenting is awkward. Consider GitHub Discussions on
   `ourPLCC/issues`, PRs against the tracker, and/or leaving GitHub
   Issues enabled on public code repos as an intake queue that gets
   triaged into the tracker.
7. **Agent and tooling setup.** Changes to each repo's CLAUDE.md and
   contributing docs, devcontainer cloning of `.issues/`, the
   Backlog.md MCP server, and retiring `bin/issues/` and
   [issue-conventions.md](../issue-conventions.md). Also the ownership
   quirk where git refuses this repo ("dubious ownership") in the
   devcontainer, which matters once a second repo is in play.
8. **Relation to [#189](189-align-issue-system-with-languages-ng.md).**
   Most of #189 (issues never move, status in frontmatter) is likely
   superseded by Backlog.md's own conventions. Decide whether to close
   #189 as superseded or do it first as a stepping stone.

**Things to check in Backlog.md:** the frontmatter schema and how
custom it can be, ID assignment (it scans active branches and takes a
fresh snapshot of the remote before choosing an ID), how archived and
completed tasks are stored, whether it can import existing Markdown
issues, and how well it works for long design issues like
[#197](197-language-neutral-fragment-hook-names.md) as opposed to small
tasks.
