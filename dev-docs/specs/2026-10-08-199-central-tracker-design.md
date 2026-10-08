# Central change-request tracker (`ourPLCC/issues`) — design

Issue: [#199](../issues/199-adopt-backlog-md-central-tracker.md)
Date: 2026-10-08
Supersedes: [#189](../issues/189-align-issue-system-with-languages-ng.md)

## Problem

Each code repo keeps its own tracker in `dev-docs/issues/`, so every issue
write travels the same branch → PR → CI path as code:

- An issue found on an unrelated branch is either lost with that branch or
  needs its own PR just to land.
- `.next-id.txt` is incremented independently per branch, so concurrent
  filings collide.
- languages-ng runs a diverged fork of the system, and findings are moved
  between repos by hand (#160, #161, #185–#188).
- Closing moves files into `done/`, which keeps breaking links (#189 counted
  14 broken).

## Decision summary

One tracker repo, `ourPLCC/issues`, managed with
[Backlog.md](https://github.com/MrLesk/Backlog.md) (pinned version), shared by
plcc-ng, languages-ng, plcc-ng-demo, and plcc-ng-devcontainer. Items are
**change requests**, IDs `CR-N`. It is file-based (grep, diffs, scripted
edits, no auth for reads) and lives in a separate repo cloned alongside the
code repos (not a submodule, which would pin a commit per branch).

We adopt Backlog.md's own model wherever it fits and add only what it lacks:
three conventions (drafts are never cited; one project per CR; won't-do work
is completed with a `wontdo` label, never archived) and a small check script.

## Vocabulary

- **Change request (CR):** committed work in exactly one repo — a feature, a
  fix, or an infrastructure change — with testable acceptance criteria. ID
  `CR-N`. "Task" is avoided: superpowers plans are made of tasks and steps.
- **Draft:** an idea not yet committed to. ID `DRAFT-N` (separate, recycled
  sequence). Not shown on the board or in `task list`.
- **GitHub issue:** a conversation with a human, on a code repo. Not tracked
  work.

## Configuration (`backlog/config.yml`)

| Setting | Value | Reason |
| --- | --- | --- |
| `task_prefix` | `cr` | `CR-N`; fixed at init |
| `statuses` | `[To Do, In Progress, Done]` | Backlog.md defaults; `Done` is the name `task complete` requires |
| `default_status` | `To Do` | |
| `types` | `[fix, feat, docs, test, refactor, chore]` | Each equals its conventional-commit type (below) |
| `projects` | `[plcc-ng, languages-ng, plcc-ng-demo, plcc-ng-devcontainer, course-materials-ng]` | Validated on every CLI write |
| `labels` | `[wontdo]` | Marks `Done` CRs that were abandoned (see Lifecycle); not validated by the tool, so the check script does |
| `check_active_branches` | `true` | Required for the pre-allocation fetch: with `false`, no fetch happens and a clone allocates an ID another clone already pushed (verified) |
| `remote_operations` | `true` | Enables that fetch |
| `auto_commit` | `true` | One commit per CLI change; nothing lingers uncommitted |
| `bypass_git_hooks` | `false` | Hooks guard auto-commits (verified: a rejecting hook blocks the commit loudly) |

Not used until a need appears: `priority`, `ordinal` ranking, milestones,
Definition-of-Done defaults, `modified_files`, `documentation`. Types may be
added later by editing `types:`; removing one invalidates CRs that use it.

**Types.** A CR's type is the conventional-commit type of the change that
determines its version impact. A `feat` CR's branch may also carry `test:` or
`docs:` commits; the strongest commit must match the CR. `ci`, `build`, `perf`,
and `style` remain valid commit prefixes but are not CR types — infrastructure
work is `chore`.

## IDs

Legacy issues keep a recoverable number via a per-repo offset; new CRs start
at 1000.

| Range | Meaning |
| --- | --- |
| `CR-1`–`CR-399` | plcc-ng legacy issues, same number (offset +0) |
| `CR-400`–`CR-499` | plcc-ng legacy issues whose number was used twice (035, 039, 043): the second of each pair at +400 |
| `CR-501`–`CR-699` | languages-ng legacy issues (offset +500) |
| `CR-801`–`CR-899` | plcc-ng-demo legacy issues (offset +800) |
| `CR-999` | Seed: "Tracker begins here", `Done`, in `completed/` |
| `CR-1000`+ | New CRs, no project encoded |

Backlog.md allocates max + 1 over `tasks/` and `completed/` only, so the seed
fixes the start — and a number in `archive/` can be reused (verified), which
is why we never archive (see Lifecycle).

Lookups are numeric (`view 160`, `CR-160`, and `cr-160` all
resolve), so an old `#160` in plcc-ng history is `backlog task view 160`, and
languages-ng's `#12` is `512`. No zero-padding: each ID has one spelling, so
grep works. Subtasks would get dotted IDs (`CR-1000.1`), but we do not use
them (see "Cross-repo work").

**Collisions.** Every container on a machine shares one host clone (see
"Setup"), so one person's sessions never collide. Collisions between people
are possible until both push; `bin/check.bash` catches duplicates at pre-push
and in CI, and `backlog doctor --fix` renumbers the unpushed one.

## Lifecycle

```text
DRAFT-N ──promote──▶ To Do ──▶ In Progress ──▶ Done ──cleanup──▶ completed/
   ▲                   │            │           ▲
   └──demote (uncited)─┘            └───────────┘ (won't do: Done + wontdo label)
```

- **Draft vs CR — the litmus test: can you write testable acceptance
  criteria?** If not ("*whether* do we want this?"), it is a draft. If yes but
  *how* is open, it is a CR; working out *how* is the first part of
  `In Progress`.
- **Drafts are never cited** — not in CRs, specs, commits, or branch names. If
  something must refer to a draft's content, duplicate the content. Promotion
  assigns a new `CR-N` and leaves stale `DRAFT-N` references unrewritten
  (verified), and draft numbers are recycled.
- **Demote** only when nothing cites the CR: grep the tracker, grep the
  current repo, and `git log --grep` in it. Typical case: open questions about
  *what* found soon after promotion. If the CR is cited, rewrite its
  acceptance criteria instead.
- **Done** work moves to `completed/` via `backlog cleanup` (interactive, run
  periodically by a human) or `task complete`. It stays viewable by ID and
  greppable; tool search and edit no longer reach it. Reopening means filing a
  new CR that cites the old one.
- **Won't do, duplicate, or obsolete** → status `Done`, label `wontdo`, and a
  `--final-summary` saying why (for a duplicate, name the surviving CR); then
  `task complete`. The number stays reserved, the CR stays viewable by ID, it
  leaves the board, and dependents are unblocked (`--ready` treats `Done` as
  satisfied — review them).
- **Never `task archive`.** Archived CRs drop out of ID lookup, and archiving
  the highest-numbered CR lets its number be reallocated (verified).

## Cross-repo work

Every CR has exactly one `project`. Work spanning repos is one CR per repo,
ordered with `dependencies` (`--ready` hides a CR until its dependencies are
`Done`). No umbrella or parent CRs. This follows Backlog.md's own guidance
(subtasks for one subsystem; dependencies across independent components) and
keeps each CR's `type` meaningful for its repo's release.

## References and links

- **Between CRs:** bare IDs (`CR-160`), never paths. IDs survive the move to
  `completed/`; filenames contain spaces and title slugs.
- **CR → code:** relative links written as if the CR sits in `backlog/tasks/`:
  `[emit.py](../../../plcc-ng/src/plcc/java/emit.py)`. The repo name in the
  path identifies the project in search results, and ctrl-click works in the
  IDE for `tasks/` and `completed/` (same depth). Inside a code repo's
  container only that repo and the tracker are mounted, so links into *other*
  repos are readable but do not resolve there. Dead on GitHub (relative links
  cannot leave a repo) — accepted; local reading is the common case.
- **CR → spec:** in the CR's `references`, as a code link. New specs do
  **not** cite CRs: a spec states its own why and what. (Existing spec headers
  like `Issue: [#195](…)` are rewritten to `CR-195` during migration.)
- **CR → GitHub issue:** full URL in `references`.
- **Code → CR:** the branch name starts with the CR ID: `cr-1042-short-slug`.
  The merge commit (`Merge pull request #N from ourPLCC/cr-1042-…`) records it,
  so `git log --merges --grep cr-1042` finds the merge and `M^1..M^2` its
  commits. No per-commit trailers. This supports tracing code to intent
  (`git blame` → commit → merge → CR → spec) for changes too small to have a
  spec.
- **Ordering:** `dependencies` only.

## Workflow (superpowers mapping)

1. **File.** Search across all projects first (`backlog search`; duplicates
   and root causes often live in another repo). Create a CR if acceptance
   criteria are testable (most bugs), else a draft. Description = why; no
   implementation plan.
2. **Brainstorm.** The CR moves to `In Progress` (assignee set). A draft is
   promoted once *what* is settled. The spec goes in the code repo's
   `dev-docs/specs/`; the CR's acceptance criteria are updated to match and it
   references the spec.
3. **Plan and execute.** The plan lives in `.plans/` inside the worktree,
   gitignored, and is deleted with the worktree. Plans are not kept: the spec
   holds the why, commits the what, the CR's final summary the outcome. During
   automated execution, discovered work goes into the CR's notes
   (`--append-notes`), never into new CRs.
4. **Push, PR, merge, clear down.** Branch `cr-N-slug`; the PR names the CR.
   After merge: triage the CR's notes with the human (new draft, new CR, fold
   into an existing CR, or drop), check each acceptance criterion against
   evidence, write `--final-summary`, set `Done`.

**Close on verification** is unchanged: when only a later event can prove the
fix (e.g. a real release run), the CR stays `In Progress` after merge.

New CRs or drafts are created only with the human's approval (Backlog.md's
guidance), which steps 1, 2, and 4 provide.

## Search

`backlog search --project X` and `task list --search … --project X` filter by
project; plain output does not print each hit's project (`--json` does).
Plain grep cannot filter by project; add a `bin/` helper only if that proves
painful. Convention: search all projects before filing; filter by project when
working within one repo.

## GitHub Issues

Stay enabled on every public repo as the channel for humans: intake and
discussion. Never migrated. When one leads to work, the CR cites its URL in
`references`, and the GitHub issue gets a comment linking the CR.
course-materials-ng is managed by its author through GitHub Issues and PRs and
is not migrated; it remains an allowed `project` value for any work we do
there.

## The tracker repo

```text
ourPLCC/issues
├── README.md                 # the workflow guide (humans and agents)
├── .backlog-version          # pinned Backlog.md version, e.g. 1.53.0
├── backlog/config.yml
├── backlog/{tasks,completed,drafts}/
├── bin/check.bash
├── .githooks/{pre-commit,pre-push}
├── .github/workflows/check.yml
├── upstream/<version>/       # raw output of all five `backlog instructions` guides
└── migrate/                  # one-time conversion tooling, reused per repo
```

- **README.md** is the single workflow guide for humans and agents: this
  document's conventions, operationalized, plus the Backlog.md version it was
  checked against. GitHub shows it on the repo page; agents read
  `/workspaces/issues/README.md`. Agents are pointed here, never at
  `backlog instructions` (whose guidance conflicts with ours on plans,
  cleanup, and drafts). It includes recovering from a rejected push from the
  host (`git pull --rebase`, then `bin/check.bash` and, if IDs collided,
  `backlog doctor --fix` in a container).
- **`upstream/<version>/`:** raw output of each `backlog instructions` guide
  (`overview`, `task-creation`, `task-execution`, `task-finalization`,
  `init-required`) for the pinned version, kept for diffing. A version bump
  regenerates it, and relevant changes are folded into README.md in the same
  commit.
- **`.backlog-version`** is the one version pin; devcontainers and CI read it.
- **Push access** is restricted to the code repos' maintainers. Hooks in
  `.githooks/` run on maintainers' hosts, so tracker push access is code
  execution, the same trust as `bin/` in the code repos.

### `bin/check.bash`

Portable bash + grep/awk: runs on the host without Node or Backlog.md, and
must work with macOS's bash 3.2 and BSD tools (no associative arrays, no
`mapfile`, no GNU-only flags). Scans `backlog/` only. Fails on:

1. Duplicate IDs across `tasks/`, `completed/`, `archive/tasks/`, or a filename
   ID that differs from its frontmatter `id:` (compared case-insensitively:
   `cr-12` file, `CR-12` id).
2. A `DRAFT-N` mentioned in any file under `backlog/` other than that draft's
   own.
3. A CR without exactly one `project`, or with a project not in config.
4. A CR without a `type`, or with a type not in config.
5. A label not in config.
6. Any file in `archive/` (we never archive).
7. (pre-push and CI only) Untracked or modified files under `backlog/`:
   catches commits that silently failed (see "Git ownership").

The seed `CR-999` is exempt from rules 3 and 4.

Runs from `pre-commit` and `pre-push` (via `core.hooksPath .githooks`) and in
CI on every push to `main`, where `backlog doctor` also runs. CI only alerts
(writers push directly to `main`); fix by revert.

## Setup in each code repo

**`.devcontainer/devcontainer.json`:**

```jsonc
"initializeCommand": "test -d ../issues || git clone https://github.com/ourPLCC/issues ../issues; git -C ../issues config core.hooksPath .githooks",
"mounts": ["source=${localWorkspaceFolder}/../issues,target=/workspaces/issues,type=bind"],
"containerEnv": { "BACKLOG_CWD": "/workspaces/issues" },
"postCreateCommand": "npm i -g backlog.md@$(cat /workspaces/issues/.backlog-version) && git -C /workspaces/issues status >/dev/null && git -C ${containerWorkspaceFolder} status >/dev/null"
```

- The host keeps the ourPLCC code repos as siblings with the tracker clone
  beside them (`initializeCommand` creates it if missing); only that clone is
  mounted (not sibling code repos). It survives rebuilds and is shared by
  every container on the machine.
- Commits happen in the container; pushes happen from the host, where the
  credentials are.
- `BACKLOG_CWD` lets the CLI work from inside the code repo (verified).
  Because it is set container-wide, `migrate/` and the check script's tests
  must set `BACKLOG_CWD` explicitly to their target, or they would operate on
  the real tracker.
- CLI only; no MCP server (its tools lack drafts; Backlog.md recommends CLI).
- Hosts are Linux or macOS (`initializeCommand` runs in the host's POSIX
  shell); Windows hosts are out of scope.

**Git ownership.** Under git's "dubious ownership" refusal, Backlog.md fails
silently: it writes the file, exits 0, and skips the commit (verified). In
order: (1) rely on correct ownership — devcontainers remap the container
user's UID on Linux hosts, and Docker Desktop presents bind mounts as the
container user; (2) the `postCreateCommand` assertion fails loudly when the
container is created if git refuses either repo; (3) only if (2) shows a need, add
an exact-path exception through `containerEnv`
(`GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_n=safe.directory`/`GIT_CONFIG_VALUE_n`),
which reaches git processes spawned by tools (verified). Never
`safe.directory=*`, which would disable the protection everywhere. Check rule 7
is the backstop.

**Other files:**

- `.gitignore`: `.plans/`.
- `.claude/settings.json`: allow `Bash(backlog *)`.
- `CONTRIBUTING.md`: a short "Tracking work" section — report problems via
  GitHub Issues; maintainers follow the tracker README (GitHub URL); this
  repo's `project` value; branches start with `cr-N-`.
- `CLAUDE.md`: replaces the issue section with agent-only rules — read
  `/workspaces/issues/README.md` before tracker work; plans in `.plans/`;
  during automated execution, record discovered work in the CR's notes.

## Migration

### Conversion rules (`migrate/`)

Python 3 stdlib only. Writes Backlog.md task files directly (no CLI path sets
an ID), then verifies them with the tool. For each legacy issue file:

- **ID** `CR-<number + offset>` (leading zeros stripped); filename
  `cr-<N> - <Title-Slug>.md`. The slug need only approximate the CLI's
  (lookups use the frontmatter ID); check rule 1 verifies the `cr-<N>` part.
  Numbers used twice (plcc-ng 035, 039, 043): the second file of each pair,
  by filename order, maps to +400, listed in the report.
- **Frontmatter:** `id`, `title` (from the `# NNN - Title` heading),
  `status`, `type`, `project`, `created_date` (from `**Date:**` or the
  `date:` field), empty `assignee`, `labels`, `dependencies`.
- **Type mapping:** `bug`→`fix`; `enhancement`, `feature`→`feat`; `perf`→`fix`
  (same patch bump); `fix`, `feat`, `docs`, `test`, `refactor`, `chore`
  unchanged; anything else (e.g. `warning`) or missing is reported for manual
  mapping.
- **Status and location:** closed issues → `Done` in `completed/`; closed
  issues marked abandoned or superseded (e.g. plcc-ng 111, 114:
  `**Status:** abandoned`) → `Done` + `wontdo` in `completed/`; open issues
  per triage (below).
- **Body:** everything goes inside Backlog.md's Description section, between
  its `<!-- SECTION:DESCRIPTION:BEGIN/END -->` markers. The legacy
  `## Description` text comes first; every other legacy `##` section
  (`Steps to Reproduce`, `Desired Behavior`, `Notes`, …) follows, demoted to
  `###` with its heading kept. Without the markers the tool absorbs following
  sections on first edit, and sections outside them are invisible to
  `task view` and `backlog search` (verified) — and search is how duplicates
  are found before filing. The template HTML comment is dropped.
- **Links:** text inside code fences is never rewritten.
  - To code or docs: resolved against the issue's old location, rewritten to
    `../../../<repo>/<path>`. Links that predate a move (e.g. `docs/issues` →
    `dev-docs/issues`, issues → `done/`) are resolved by best effort; anything
    unresolved is reported.
  - To other legacy issues of the same repo — by path or `#N`, zero-padded or
    not: resolved **by number**, rewritten to `CR-<N + offset>`. If the linked
    slug does not match that number's actual title (e.g. plcc-ng 162 links
    `165-java-run-void-print-…`, but 165 is a different issue), it is still
    rewritten and also reported.
  - Qualified mentions of another repo's issues (`languages-ng #3`,
    `issue #3 in ourPLCC/languages-ng`, plcc-ng-demo `#2`): rewritten with
    *that* repo's offset (`CR-503`), or left as text and reported when the
    repo has no legacy tracker. `ourPLCC/<repo>#N` (a GitHub reference) is
    left alone.
  - Unqualified `#N` that is not a legacy issue of that repo (a PR or GitHub
    issue): rewritten to the GitHub URL.
  - Targets that do not exist: left as text and reported.
- **Provenance:** the Description ends with `Migrated from <repo> #<N>.`, so
  the old number is greppable and searchable.
- **Duplicated upstream findings:** a languages-ng issue that was already
  copied into plcc-ng by hand (162–164, 185–188 originated there) becomes
  `Done` + `wontdo`, with a final summary naming the plcc-ng CR.

**Triage of open issues.** Each open legacy issue becomes a CR in `tasks/`
(`To Do`, or `In Progress` if active) unless it fails the litmus test *and*
nothing cites it — no other issue, spec, plan, or non-bookkeeping commit
(`docs(issues): file/close …` commits do not count) — in which case it becomes a draft
(losing its number; the provenance line keeps it greppable). The triage list
is produced for human review, not applied silently.

**Verification:** the number of files per folder equals the expected count
from the input; `backlog task view <id>` succeeds for every converted ID
(`task list` omits `completed/`, so it cannot be the count); `backlog doctor`
and `bin/check.bash` are clean; and the report lists unmapped types,
duplicate-number remaps, slug mismatches, and unresolved links.

### In the migrated code repo

- Delete `dev-docs/issues/` (including `done/`, `TEMPLATE.md`, `index.md`,
  `.next-id.txt`), `dev-docs/roadmap.md`, `dev-docs/issue-conventions.md`,
  `bin/issues/`, and `tests/bats/commands/issues-close.bats`.
- Rewrite links into `dev-docs/issues/…` elsewhere in the repo (specs, frozen
  plans, `dev-docs/index.md`, CONTRIBUTING.md, CLAUDE.md, reviews) to bare
  `CR-N`. Link-only edits; frozen plans are otherwise untouched.
- `CHANGELOG.md` is generated and left alone; its numbers resolve under the
  +0 offset.
- `dev-docs/plans/` is frozen: kept, nothing added.

### Order and scope of #199

**#199 delivers this spec plus the bootstrap,** in two phases with a human
checkpoint:

- **Phase 1 — stand up the tracker locally.** Tracker repo contents (README,
  config, check script and its tests, hooks, CI, `.backlog-version`,
  `upstream/` snapshot, seed `CR-999`, `migrate/`), then a dry-run migration
  of plcc-ng's issues into it. Nothing published.
- **Checkpoint (human):** review converted CRs, the triage list, and the
  report; create `ourPLCC/issues` on GitHub with maintainer-only push; push
  from the host.
- **Phase 2 — switch plcc-ng over** on a branch: **re-run the migration from
  `main`** (the freeze point — issues filed or closed elsewhere since the dry
  run are picked up; the reviewed triage decisions are reapplied, and anything
  new is triaged then), devcontainer, CLAUDE.md, CONTRIBUTING.md,
  `.gitignore`, settings, link rewriting, retiring the old tracker. From this
  point no new issues are filed in `dev-docs/issues/`. **Human checkpoint before merge:** rebuild from the branch on the
  host and confirm the container starts and `backlog task list` works
  (fallback: check out `main` and rebuild). Close #189 (superseded) and,
  last, #199 with `bin/issues/close.bash` before deleting it.

languages-ng and plcc-ng-demo are filed as the tracker's first new CRs
(`CR-1000`, `CR-1001`, project = that repo) and migrated in their own repos
from this spec. languages-ng's issues use frontmatter with `closed:` and a
`target:` field; `target:` maps to `project` (an upstream finding about
plcc-ng becomes a `CR-5xx` with `project: plcc-ng`). plcc-ng-devcontainer has
no legacy issues and needs only the setup changes.

## Rejected alternatives

| Alternative | Why not |
| --- | --- |
| GitHub Issues as the tracker | No grep across code and issues, no scripted bulk edits, network and auth dependency |
| Submodule for the tracker | Pins a commit per branch, reintroducing per-branch state |
| Other tools (Beans, ticket, git-bug, Beads, …) | Per-repo by design (Beads is multi-repo but stores data in Dolt, not Markdown); none is built for a central file-based tracker |
| Our own scripts, centralized | Fits exactly, but no board, web UI, remote-aware ID allocation, or `doctor` |
| Keeping everything in `tasks/` forever | Fights the tool; board grows without bound. ID-only citation makes moves harmless |
| `task archive` for won't-do work | Archived CRs drop out of ID lookup, and archiving the highest-numbered CR frees its number for reuse; `Done` + `wontdo` + `complete` keeps both |
| `Needs Design` / `Ready` statuses | Mixes design maturity with lifecycle; Backlog.md does design inside `In Progress` and uses drafts for undecided *what* |
| Milestones, priority, ordinal as roadmap | No current need; the roadmap had already shrunk to the open-issue list |
| Plans stored in CRs (`--plan`) | Plans are rarely revisited and would dominate the tracker's text and search |
| Freezing old trackers and starting at 200 | Leaves history split across repos with stubs; offsets make every old number resolvable in one place |
| `ISSUE-`, `TSK-` prefixes | Longer on every card; "issue" collides with GitHub Issues; "task" collides with plan tasks |
| `.issues/` clone inside each repo | Links cannot name their project; absent in worktrees |
| Bind-mounting the whole host parent directory | Exposes every sibling repo to the container |
| Per-commit `Refs: CR-N` trailers | The branch name in the merge commit gives the same trace for free |
