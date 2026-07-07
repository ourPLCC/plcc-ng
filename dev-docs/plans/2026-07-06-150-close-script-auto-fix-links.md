# Close Script Auto-Fix Links (Issue 150) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden `bin/issues/close.bash` so closing an issue also fixes every link the move breaks: other `dev-docs/` files' links to the issue's old open path, and the moved file's own outbound links that now sit one directory deeper.

**Architecture:** Two new passes inserted into the existing bash script between the roadmap edits and the final `bin/issues/check.bash` call. Pass 3 does a recursive grep+sed across `dev-docs/**/*.md` to repoint external inbound links. Pass 4 runs three disjoint `sed` substitutions against the moved file itself to fix its outbound links.

**Tech Stack:** bash, GNU `sed`/`grep`, bats (`tests/bats/commands/issues-close.bats`).

**Spec:** `dev-docs/specs/2026-07-06-150-close-script-auto-fix-links-design.md`

## Global Constraints

- Run everything from the worktree root; `cd` is never needed since `close.bash` resolves its own project root from `BASH_SOURCE`.
- Match the existing script's style: plain (non-`-F`) `sed`/`grep` patterns, no defensive over-escaping beyond what's needed for correctness (see Task 2 for the one place escaping matters).
- TDD per CONTRIBUTING: extend the bats file and watch new cases fail before touching `close.bash`.
- Test command: `bin/test/commands.bash tests/bats/commands/issues-close.bats` runs the *entire* `commands.bash` suite (it doesn't filter to one file) — read the output for `issues-close.bats`'s own lines, and confirm `0` failures overall.
- Commit message types: `test(issues)` for the bats-only commit, `chore(issues)` for the `close.bash` implementation commit — this is internal repo tooling, not part of the shipped package, so it must not trigger a semantic-release version bump.

---

### Task 1: Extend `issues-close.bats` with fixtures and failing tests for both new passes

**Files:**
- Modify: `tests/bats/commands/issues-close.bats`

**Interfaces:**
- Consumes: nothing from other tasks — this task only adds test fixtures and assertions against `close.bash`'s current (unmodified) behavior, so all five new `@test` blocks are expected to fail.
- Produces: the fixture shape (issue 001's body content, `dev-docs/issues/done/005-already-done.md`, `dev-docs/specs/2026-01-01-example-design.md`, `dev-docs/v1.0-criteria.md`) that Task 2 must satisfy. Task 2 does not modify this file.

- [ ] **Step 1: Add fixture files and richer body content to issue 001 in `setup()`**

Replace this line in `setup()`:

```bash
    echo '# 1 - first-bug' > "${REPO}/dev-docs/issues/001-first-bug.md"
```

with:

```bash
    cat > "${REPO}/dev-docs/issues/001-first-bug.md" <<'EOF'
# 1 - first-bug

See also issue [005](done/005-already-done.md) and issue
[003](003-a-feature.md). Related design doc:
[v1.0 criteria](../v1.0-criteria.md).
EOF
```

Then, immediately after the existing four `echo` lines that create issues 001–003 and `.next-id.txt`, add:

```bash
    echo '# 5 - already-done' > "${REPO}/dev-docs/issues/done/005-already-done.md"
    echo '# v1.0 criteria' > "${REPO}/dev-docs/v1.0-criteria.md"

    mkdir -p "${REPO}/dev-docs/specs"
    cat > "${REPO}/dev-docs/specs/2026-01-01-example-design.md" <<'EOF'
# Example design

Fixes issue [1](issues/001-first-bug.md) using the same approach as
issue [2](issues/002-second-bug.md).
EOF
```

(`dev-docs/issues/done` already exists — it's created by the `mkdir -p` at the top of `setup()`.)

- [ ] **Step 2: Add the five new `@test` blocks**

Append to the end of the file:

```bash
@test "closing an issue rewrites an external link to the issue's done/ path" {
    run "${REPO}/bin/issues/close.bash" 1
    [ "$status" -eq 0 ]
    grep -qF '(issues/done/001-first-bug.md)' "${REPO}/dev-docs/specs/2026-01-01-example-design.md"
    ! grep -qF '(issues/001-first-bug.md)' "${REPO}/dev-docs/specs/2026-01-01-example-design.md"
}

@test "closing an issue leaves an unrelated external link untouched" {
    run "${REPO}/bin/issues/close.bash" 1
    [ "$status" -eq 0 ]
    grep -qF '(issues/002-second-bug.md)' "${REPO}/dev-docs/specs/2026-01-01-example-design.md"
}

@test "closing an issue strips the done/ prefix from an already-closed sibling link" {
    run "${REPO}/bin/issues/close.bash" 1
    [ "$status" -eq 0 ]
    grep -qF '(005-already-done.md)' "${REPO}/dev-docs/issues/done/001-first-bug.md"
    ! grep -qF '(done/005-already-done.md)' "${REPO}/dev-docs/issues/done/001-first-bug.md"
}

@test "closing an issue adds a leading ../ to a link that already climbs above issues/" {
    run "${REPO}/bin/issues/close.bash" 1
    [ "$status" -eq 0 ]
    grep -qF '(../../v1.0-criteria.md)' "${REPO}/dev-docs/issues/done/001-first-bug.md"
}

@test "closing an issue adds a leading ../ to a bare link to a still-open sibling" {
    run "${REPO}/bin/issues/close.bash" 1
    [ "$status" -eq 0 ]
    grep -qF '(../003-a-feature.md)' "${REPO}/dev-docs/issues/done/001-first-bug.md"
}
```

- [ ] **Step 3: Run the suite and confirm the five new tests fail, and only those**

Run: `PLCC_NO_TEST_CACHE=1 bin/test/commands.bash tests/bats/commands/issues-close.bats 2>&1 | grep -A1 -E 'first-bug|link|sibling|climbs'`

Expected: the 5 new tests show `not ok`, each failing on the `grep -qF` line looking for the *rewritten* form (since `close.bash` doesn't rewrite anything yet). The other 4 existing `issues-close.bats` tests still show `ok`.

- [ ] **Step 4: Commit**

```bash
git add tests/bats/commands/issues-close.bats
git commit -m "$(cat <<'EOF'
test(issues): add failing cases for close.bash link auto-fix (issue 150)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Implement Pass 3 (external inbound links) and Pass 4 (internal outbound links) in `close.bash`

**Files:**
- Modify: `bin/issues/close.bash:81-83` (insert between the existing `git add "${ROADMAP}"` line and the `bin/issues/check.bash` line)
- Modify: `dev-docs/issue-conventions.md` (one sentence, documents the new behavior)

**Interfaces:**
- Consumes: `${basename}` (already defined earlier in the script as the moved file's filename, e.g. `001-first-bug.md`), `${DONE_DIR}` (already defined as `dev-docs/issues/done`).
- Produces: nothing consumed by a later task — this is the last code task.

- [ ] **Step 1: Insert Pass 3 and Pass 4 into `close.bash`**

In `bin/issues/close.bash`, find:

```bash
mv "${ROADMAP}.tmp" "${ROADMAP}"
git add "${ROADMAP}"

bin/issues/check.bash
```

Replace with:

```bash
mv "${ROADMAP}.tmp" "${ROADMAP}"
git add "${ROADMAP}"

# Pass 3: external inbound links. Other dev-docs/ files may still link to
# this issue's old open path; repoint them at issues/done/. Depth-agnostic:
# done/ is a subdirectory of issues/, so no existing "../" needs adjusting.
while IFS= read -r f; do
    sed -i "s|issues/${basename}|issues/done/${basename}|g" "${f}"
    git add "${f}"
done < <(grep -rl --include='*.md' "issues/${basename}" dev-docs | grep -vF "${DONE_DIR}/${basename}" || true)

# Pass 4: internal outbound links, now that this file itself sits one level
# deeper (issues/done/ instead of issues/). Three link shapes, keyed off
# what immediately follows "](", mutually exclusive:
#   done/...   -> strip the done/ prefix (already-closed issues are now true siblings)
#   ../...     -> one more ../ (anything climbing out of issues/ needs an extra level)
#   NNN-*.md   -> prepend ../ (bare links to still-open siblings now live one level up)
moved_file="${DONE_DIR}/${basename}"
sed -i \
    -e 's|](done/|](|g' \
    -e 's|](\.\./|](../../|g' \
    "${moved_file}"
sed -i -E 's|\]\(([0-9]{3}-[^)]+\.md)\)|](../\1)|g' "${moved_file}"
git add "${moved_file}"

bin/issues/check.bash
```

- [ ] **Step 2: Add one sentence to `dev-docs/issue-conventions.md`**

Find this sentence in the "Closing an issue" section:

```markdown
It moves the issue file to `issues/done/`, removes the Open Issues entry (and its group heading if now empty), checks the issue's box in any milestone list, and stages the changes.
```

Replace with:

```markdown
It moves the issue file to `issues/done/`, removes the Open Issues entry (and its group heading if now empty), checks the issue's box in any milestone list, rewrites any `dev-docs/` links to the issue's old path, adjusts the moved file's own links for its new depth, and stages the changes.
```

- [ ] **Step 3: Run the full bats suite and confirm all tests pass**

Run: `PLCC_NO_TEST_CACHE=1 bin/test/commands.bash tests/bats/commands/issues-close.bats 2>&1 | tail -20`

Expected: all `issues-close.bats` tests show `ok`, and the summary line has `0` failures (this command runs the whole `commands.bash` suite, not just this file — check for `# fail 0` or equivalent at the end).

- [ ] **Step 4: Run `bin/test/functional.bash` to confirm no regressions elsewhere**

Run: `PLCC_NO_TEST_CACHE=1 bin/test/functional.bash 2>&1 | tail -20`

Expected: exit 0, `0` failures.

- [ ] **Step 5: Commit**

```bash
git add bin/issues/close.bash dev-docs/issue-conventions.md
git commit -m "$(cat <<'EOF'
chore(issues): auto-fix links on close.bash (issue 150)

close.bash now rewrites other dev-docs/ files' links to the closed
issue's old open path, and adjusts the moved file's own outbound
links for its new depth under issues/done/ — preventing the stale-
link class fixed once already in issue 149 from recurring on every
future close.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Close issue 150

**Files:**
- Modify: `dev-docs/roadmap.md`, moves `dev-docs/issues/done/150-close-script-auto-fix-links.md` to `dev-docs/issues/done/`

**Interfaces:**
- Consumes: the working `bin/issues/close.bash` from Task 2.
- Produces: nothing further in this plan.

- [ ] **Step 1: Run `close.bash` on issue 150**

Run: `bin/issues/close.bash 150`

Expected: prints `closed: dev-docs/issues/done/150-close-script-auto-fix-links.md` followed by the reminder to review the roadmap and commit. Since this is the *first* real (non-test-fixture) use of the new Pass 3/4 logic, also check by hand whether anything changed under `dev-docs/` beyond `roadmap.md` and the moved issue file — the design doc committed earlier links to `dev-docs/issues/done/150-close-script-auto-fix-links.md`, so Pass 3 is expected to rewrite that one link in `dev-docs/specs/2026-07-06-150-close-script-auto-fix-links-design.md` to point at `issues/done/`.

- [ ] **Step 2: Review the roadmap diff**

Run: `git diff --staged dev-docs/roadmap.md`

Expected: issue 150's Open Issues entry is gone; no milestone list references it (issue 150 isn't in a milestone section, so no checkbox change expected).

- [ ] **Step 3: Verify consistency**

Run: `bin/issues/check.bash`

Expected: `OK: <N> open issues, roadmap consistent, next id <M>`, exit 0. (`close.bash` already ran this internally in Step 1; this is a standalone confirmation after reviewing/staging.)

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
docs(issues): close issue 150 (close script auto-fix links), update roadmap

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```
