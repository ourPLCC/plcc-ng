# Enforce `bats_require_minimum_version` in bats files — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the test suite fail when a `.bats` file omits
`bats_require_minimum_version 1.5.0`, so the declaration that keeps
`BATS_TEST_TMPDIR` from silently degrading can no longer be forgotten.

**Architecture:** One new lint test appended to the existing
`tests/bats/commands/bats-temp-dirs.bats`, beside the `mktemp` lint it belongs
with. It walks every `*.bats` file under `tests/bats/` and asserts line 3 is
exactly `bats_require_minimum_version 1.5.0`. The repository supplies its own
red: `tests/bats/integration/spec-model.bats` is the one file of 58 missing the
line, so the lint fails on a real offender before that file is fixed. No `src/`
changes.

**Tech Stack:** bats-core (pinned to 1.11.0 by `bin/install/bats.bash`), plus
`find`, `sed`, and `sort` from GNU coreutils — all already assumed by the
existing tests in this file.

**Spec:** [2026-07-29-178-bats-version-declaration-unenforced-design.md](../specs/2026-07-29-178-bats-version-declaration-unenforced-design.md)
**Issue:** [178](../issues/178-bats-version-declaration-unenforced.md)

## Global Constraints

- Work in the `arbno-mid-body-terminal` worktree at
  `/workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal`, on branch
  `arbno-mid-body-terminal`. Always `cd` there explicitly at the start of every
  bash invocation; a bare shell may reset to the main checkout at
  `/workspaces/plcc-ng`, which is a *different* checkout on `main`. Running
  tests from the wrong directory produces confusing failures.
- The required line is exactly `bats_require_minimum_version 1.5.0` — that
  string, at line 3, in every `*.bats` file under `tests/bats/`. Not 1.4.0 (the
  version that introduced `BATS_TEST_TMPDIR`), not 1.11.0 (the pinned runner).
  All 57 files that already declare it use 1.5.0; the lint's job is to hold that
  uniformity, not to re-derive the number.
- **Do not change any `.py` file, and do not touch anything under `src/`.** This
  is test and documentation work only.
- **Do not edit the 57 `.bats` files that already comply.** Exactly one file
  changes: `tests/bats/integration/spec-model.bats`. If a step has you editing a
  second one, the lint is wrong — stop and re-read this plan.
- The new lint goes in the existing `tests/bats/commands/bats-temp-dirs.bats`.
  Do not create a new file, and do not modify the two tests already in it.
- Do not use `assert_success`, `assert_failure`, `fail`, or any other
  `bats-assert` helper. That library is not installed. Use plain `[ ... ]` tests
  and `return 1`, as every existing test in this repository does.
- Bats tests never call `mktemp`; name paths under `BATS_TEST_TMPDIR` instead —
  the sibling lint in this very file enforces that. No `teardown()`, no `trap`,
  no trailing `rm`.
- Do not add an entry to `docs/whats-new.md`. That file carries user-visible
  highlights; nothing a user of PLCC-ng can observe changes here.
- Keep the tree green at every commit. The new lint is red until
  `spec-model.bats` gains its declaration, so the lint and that one-line fix
  land in the **same** commit (Task 1). Observing the red *before* committing is
  a required step, not an optional one.

---

## Background an implementer needs

`BATS_TEST_TMPDIR` is a per-test temporary directory that the bats runner
creates and removes on its own. This repository's tests name every temporary
path under it and carry no cleanup code at all — see the *Temporary files in
bats tests* section of `CONTRIBUTING.md`. That variable arrived in bats 1.4.0.
On an older runner it is simply unset, so `"${BATS_TEST_TMPDIR}/work"` expands
to `/work` and the test writes outside its sandbox instead of failing.

`bats_require_minimum_version 1.5.0` is a bats built-in that aborts the run with
a clear message when the runner is too old. Every file declares it as line 3,
immediately after the shebang and one blank line:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "..." {
```

`tests/bats/commands/bats-temp-dirs.bats` already holds two tests: one
behavioural (bats really does remove `BATS_TEST_TMPDIR` after a run) and one
lint (no bats file calls `mktemp`). The new test is a second lint in the same
style. Read the existing `mktemp` lint before writing it — the new one mirrors
its structure, its guard, and its message shape.

One difference is worth understanding up front. The `mktemp` lint has to exclude
its own file, because a lint that greps for `mktemp` necessarily contains the
string `mktemp`; that is what the `awk -v self="${BATS_TEST_FILENAME}:"` guard
does. The new lint needs no such exclusion: its own file already satisfies the
rule it enforces, so it can scan itself like any other file.

**Running the tier:**

```bash
bin/test/commands.bash tests/bats/commands/bats-temp-dirs.bats
```

That script caches its output keyed on git state, so re-running after an edit is
always a real run, never a stale replay.

---

## Task 1: The version-declaration lint

**Files:**
- Modify: `tests/bats/commands/bats-temp-dirs.bats` (append one `@test` after
  the existing `no bats test file calls mktemp` test, which ends the file)
- Modify: `tests/bats/integration/spec-model.bats:1-2` (insert the declaration)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: a passing test named `every bats test file declares the required
  bats version`. Task 2 refers to it by that exact name in prose.

- [ ] **Step 1: Write the failing lint**

Append this to the end of `tests/bats/commands/bats-temp-dirs.bats`, after the
closing brace of the `mktemp` test. Leave one blank line between the two tests,
matching the spacing already in the file.

```bash
@test "every bats test file declares the required bats version" {
    local required='bats_require_minimum_version 1.5.0'
    local bats_dir
    bats_dir="$(git rev-parse --show-toplevel)/tests/bats"

    if [ ! -d "${bats_dir}" ] || [ ! -r "${bats_dir}" ]; then
        printf 'Expected a readable bats test directory at %s but found none.\n' "${bats_dir}" >&2
        return 1
    fi

    # sed prints nothing for a file shorter than three lines, which compares
    # unequal to ${required} and is correctly reported. No special case needed.
    local offenders='' scanned=0 file
    while IFS= read -r -d '' file; do
        scanned=$(( scanned + 1 ))
        if [ "$(sed -n '3p' -- "${file}")" != "${required}" ]; then
            offenders+="${file}"$'\n'
        fi
    done < <(find "${bats_dir}" -name '*.bats' -type f -print0 | sort -z)

    # A readable directory with no .bats files inside would leave ${offenders}
    # empty and report a false PASS. Same reasoning as the guard above: fail
    # loudly rather than silently check nothing.
    if [ "${scanned}" -eq 0 ]; then
        printf 'Found no .bats files under %s. This lint checked nothing.\n' "${bats_dir}" >&2
        return 1
    fi

    if [ -n "${offenders}" ]; then
        printf 'Every bats test file must declare the bats version floor, as\n' >&2
        printf 'line 3, exactly:\n\n    %s\n\n' "${required}" >&2
        printf 'BATS_TEST_TMPDIR requires bats 1.4.0 or later. Without the\n' >&2
        printf 'declaration an older runner leaves it unset, and paths under it\n' >&2
        printf 'silently resolve outside the sandbox instead of failing.\n\n' >&2
        printf 'Missing the declaration:\n\n%s' "${offenders}" >&2
        return 1
    fi
}
```

Note this lint scans its **own** file too, and passes on it —
`bats-temp-dirs.bats` already has the declaration at line 3. Do not add a
self-exclusion.

- [ ] **Step 2: Run it and confirm it fails on the real offender**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/commands.bash tests/bats/commands/bats-temp-dirs.bats
```

Expected: the run fails. The new test's output names exactly one file:

```text
Missing the declaration:

/workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal/tests/bats/integration/spec-model.bats
```

This is the proof the scan reaches every tier's directory and reports a usable
path. If the failure names **zero** files the scan is broken (check the `find`
and the process substitution); if it names **more than one**, the expected line
or its position is wrong — re-read the required string, character for
character, before changing anything else.

Do not proceed until you have seen this failure. Do not create a temporary
`.bats` file to manufacture it — the repository already supplies the red.

- [ ] **Step 3: Verify the two guards by hand**

These fire only on trees that do not exist in this repository, so they are
checked once against a scratch directory and not committed. Run both commands
verbatim:

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
SCRATCH="$(mktemp -d)"

# Guard A: a directory with no .bats files must fail, not pass.
find "${SCRATCH}" -name '*.bats' -type f -print0 | sort -z | wc -c
# Expected: 0   (so `scanned` stays 0 and the lint returns 1)

# Guard B: a file shorter than three lines must be reported.
printf '#!/usr/bin/env bats\n\n' > "${SCRATCH}/short.bats"
sed -n '3p' -- "${SCRATCH}/short.bats" | wc -c
# Expected: 0   (empty output, which != the required line, so it is an offender)

rm -rf "${SCRATCH}"
```

`mktemp` here is a one-off shell command in your terminal, **not** something
written into a `.bats` file — the `mktemp` lint scans files, and nothing from
this step is saved.

- [ ] **Step 4: Fix the one offender**

Edit `tests/bats/integration/spec-model.bats` so its first four lines read:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

```

That is: keep the existing shebang on line 1, insert a blank line 2, the
declaration on line 3, and a blank line 4 before the existing `setup()`. Change
nothing else in the file.

- [ ] **Step 5: Run the tier and confirm green**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/commands.bash tests/bats/commands/bats-temp-dirs.bats
```

Expected: 3 tests, all passing — the two that were already there plus `every
bats test file declares the required bats version`.

Then confirm the edited file still runs, since it now has a line it did not
before:

```bash
bin/test/integration.bash tests/bats/integration/spec-model.bats
```

Expected: PASS, with the same test count as before the edit.

- [ ] **Step 6: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git add tests/bats/commands/bats-temp-dirs.bats tests/bats/integration/spec-model.bats
git commit -m "test(bats): enforce the bats version declaration in every bats file

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

Both files go in one commit: the lint is red without the `spec-model.bats` fix,
and the tree must be green at every commit.

---

## Task 2: Document the requirement

**Files:**
- Modify: `CONTRIBUTING.md` (the *Temporary files in bats tests* section, whose
  last line is currently "`tests/bats/commands/bats-temp-dirs.bats` enforces
  this.")

**Interfaces:**
- Consumes: the test name from Task 1, `every bats test file declares the
  required bats version`.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Extend the section**

In `CONTRIBUTING.md`, the *Temporary files in bats tests* section ends with this
paragraph:

~~~markdown
Bats creates that directory per test, and removes it (along with every other
test's) when the whole run ends, whether the tests pass or fail, so tests need
no cleanup code — no `teardown()`, no `trap`, no trailing `rm`. Use `bats
--no-tempdir-cleanup` to keep the files while debugging.
`tests/bats/commands/bats-temp-dirs.bats` enforces this.
~~~

Replace its final sentence — "`tests/bats/commands/bats-temp-dirs.bats` enforces
this." — so the section ends like this instead (the ` ``` ` lines below are
literal text to write into `CONTRIBUTING.md`, not this plan's own fences):

~~~markdown
Bats creates that directory per test, and removes it (along with every other
test's) when the whole run ends, whether the tests pass or fail, so tests need
no cleanup code — no `teardown()`, no `trap`, no trailing `rm`. Use `bats
--no-tempdir-cleanup` to keep the files while debugging.

`BATS_TEST_TMPDIR` requires bats 1.4.0 or later; on an older runner it is unset
and paths under it silently resolve outside the sandbox. Every bats file
therefore declares the floor as its third line, after the shebang and a blank
line:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0
```

`tests/bats/commands/bats-temp-dirs.bats` enforces both rules.
~~~

Keep the surrounding text exactly as it is. No heading is added here.

- [ ] **Step 2: Verify the links and the claim**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
grep -n -A 24 'Temporary files in bats tests' CONTRIBUTING.md
```

Expected: the new paragraph reads correctly in context, the fenced `bash` block
is closed, and the surrounding sections are untouched.

- [ ] **Step 3: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git add CONTRIBUTING.md
git commit -m "docs(contributing): document the bats version declaration rule

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 3: Full suite and close the issue

**Files:**
- Modify: `dev-docs/issues/178-bats-version-declaration-unenforced.md` (moved to
  `dev-docs/issues/done/` by the script — do not move it by hand)
- Modify: `dev-docs/roadmap.md` (edited by the script)

**Interfaces:**
- Consumes: green tiers from Tasks 1 and 2.
- Produces: nothing.

- [ ] **Step 1: Run the full functional suite**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/functional.bash
```

Expected: all four tiers pass. The new lint scans every tier's files, so any
stray `.bats` edit anywhere surfaces here. If a file other than
`spec-model.bats` is reported, someone edited a compliant file — revert that
edit rather than relaxing the lint.

- [ ] **Step 2: Close the issue**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/issues/close.bash 178
```

The script moves the issue file to `dev-docs/issues/done/`, removes its **Open
Issues** entry from `dev-docs/roadmap.md` (and the `### Test` heading if 178 was
the last entry under it), rewrites `dev-docs/` links that pointed at the old
path — including the ones in this plan and in the design spec — runs
`bin/issues/check.bash`, and stages the result.

- [ ] **Step 3: Review the staged bookkeeping**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git diff --cached
bin/issues/check.bash
```

Expected: `check.bash` exits 0. In the diff, confirm the roadmap's **Open
Issues** section no longer lists #178 and that no milestone rationale prose was
mangled — that text is not auto-edited and is the one thing the script cannot
get right on its own.

- [ ] **Step 4: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git commit -m "docs(issues): close issue 178 (bats version declaration lint), update roadmap

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

This is the branch's final commit for this issue, per
`dev-docs/issue-conventions.md`.
