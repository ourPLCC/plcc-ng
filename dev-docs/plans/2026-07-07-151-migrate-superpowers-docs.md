# Migrate docs/superpowers/ into dev-docs/ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move `docs/superpowers/specs/` (50 files) and `docs/superpowers/plans/` (51 files) into `dev-docs/specs/` and `dev-docs/plans/` via `git mv`, fix every link broken by the move (including two tiers of links that were already broken before the move, for unrelated reasons), and remove the now-empty `docs/superpowers/`.

**Architecture:** `git mv` the directories first, then run a one-off Python script (kept in a scratch directory, never committed) that rewrites every markdown link in the moved files to point correctly at their new depth — fixing three tiers of breakage discovered during investigation (see spec). A verification pass confirms every link in the result resolves to a real file before anything is committed.

**Tech Stack:** bash, git, Python 3 (stdlib only — `posixpath`, `re`, `subprocess`).

## Global Constraints

- No filename collisions between `docs/superpowers/{specs,plans}/` and `dev-docs/{specs,plans}/` (verified in the spec investigation) — plain `git mv *.md` into the existing directories is safe.
- The one-off script is never added to `bin/` or committed to the repo — it's a throwaway migration aid, not a reusable tool.
- Every relative link inside the moved files must resolve to an existing file after this plan completes — this is the plan's own acceptance test, checked mechanically rather than sampled.
- `bin/issues/check.bash` and `bin/test/units.bash` must stay green throughout.
- Issue 151 is closed via `bin/issues/close.bash` as the final commit, per `dev-docs/issue-conventions.md`.

---

### Task 1: Move the directories

**Files:**
- Move: `docs/superpowers/specs/*.md` → `dev-docs/specs/`
- Move: `docs/superpowers/plans/*.md` → `dev-docs/plans/`
- Delete: `docs/superpowers/specs/`, `docs/superpowers/plans/`, `docs/superpowers/` (now-empty directories)

**Interfaces:**
- Produces: a commit whose parent (`HEAD~1` at the time Task 2's script runs, since no other commits land in between) diffs as pure renames (`R100 docs/superpowers/specs/X.md dev-docs/specs/X.md` etc.). Task 2's script reads `git diff --name-status -M HEAD~1 HEAD` to discover exactly which files moved and from where — it must run before any later task adds another commit, or the range needs adjusting to name this task's actual commit SHA instead of `HEAD~1`.

- [ ] **Step 1: Move the files with git mv**

```bash
git mv docs/superpowers/specs/*.md dev-docs/specs/
git mv docs/superpowers/plans/*.md dev-docs/plans/
```

- [ ] **Step 2: Remove the now-empty source directories**

```bash
rmdir docs/superpowers/specs docs/superpowers/plans docs/superpowers
```

- [ ] **Step 3: Confirm the move**

Run: `git status --short | head -5` and `git status --short | wc -l`
Expected: every line starts with `R  ` (renamed, staged); total line count is 101 (50 specs + 51 plans). Confirm `docs/superpowers` no longer exists: `ls docs/superpowers` should print `No such file or directory`.

- [ ] **Step 4: Commit**

```bash
git commit -m "$(cat <<'EOF'
docs(specs): git mv docs/superpowers/{specs,plans} into dev-docs/

Preserves history for the move itself; links are fixed in the next
commit so this one stays a pure rename.
EOF
)"
```

---

### Task 2: Write the link-fix script

**Files:**
- Create: a scratch file `fix_links.py` in your scratchpad directory (NOT inside the repo — this script is never committed)

**Interfaces:**
- Produces: a script invocable as `python3 fix_links.py` (apply), `python3 fix_links.py --dry-run` (preview only, no writes), `python3 fix_links.py --verify` (check every link resolves, exit 1 if not). Must be run with cwd set to the repo root (the worktree root).
- Consumes: `git diff --name-status -M HEAD~1 HEAD` output from Task 1's commit, to discover which files moved. This assumes Task 1's move commit is still the current `HEAD` when the script runs (true for Tasks 2-4 in this plan, since none of them commit before this script's last invocation in Task 4).

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""One-off link-fix + verify script for issue 151's docs/superpowers -> dev-docs migration.
Run from the repo root. Not part of the repo; lives only in a scratch directory."""
import posixpath
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path.cwd()

LINK_RE = re.compile(r"\]\(([^)\s][^)]*)\)")
ISSUE_LINK_RE = re.compile(r"^dev-docs/issues/(?:done/)?(\d+)-")

TIER2_PREFIX_REMAP = {
    "docs/superpowers/commands/": "docs/cli/commands/",
    "docs/superpowers/guide/": "docs/cli/guide/",
    "docs/superpowers/bin/release/": "bin/release/",
}
TIER2_EXACT_REMAP = {
    "docs/superpowers/v1.0-criteria.md": "dev-docs/v1.0-criteria.md",
}


def build_issue_index():
    index = {}
    for sub in ("dev-docs/issues", "dev-docs/issues/done"):
        for f in sorted((REPO_ROOT / sub).glob("*.md")):
            m = re.match(r"(\d+)-", f.name)
            if m:
                index[int(m.group(1))] = f"{sub}/{f.name}"
    return index


ISSUE_INDEX = build_issue_index()


def remap(resolved):
    if resolved.startswith("docs/superpowers/specs/"):
        return "dev-docs/specs/" + resolved[len("docs/superpowers/specs/"):]
    if resolved.startswith("docs/superpowers/plans/"):
        return "dev-docs/plans/" + resolved[len("docs/superpowers/plans/"):]
    for old, new in TIER2_PREFIX_REMAP.items():
        if resolved.startswith(old):
            return new + resolved[len(old):]
    if resolved in TIER2_EXACT_REMAP:
        return TIER2_EXACT_REMAP[resolved]
    m = ISSUE_LINK_RE.match(resolved)
    if m:
        num = int(m.group(1))
        if num in ISSUE_INDEX and ISSUE_INDEX[num] != resolved:
            return ISSUE_INDEX[num]
    return resolved


def fix_links(path, old_dir, new_dir, dry_run=False):
    text = path.read_text()
    changes = []

    def repl(m):
        target = m.group(1)
        if target.startswith(("http://", "https://", "mailto:")):
            return m.group(0)
        target_path, sep, fragment = target.partition("#")
        if target_path == "":
            return m.group(0)
        resolved = posixpath.normpath(posixpath.join(old_dir, target_path))
        new_target = remap(resolved)
        new_rel = posixpath.relpath(new_target, new_dir)
        new_link = new_rel + (("#" + fragment) if sep else "")
        if new_link != target:
            changes.append((target, new_link))
        return f"]({new_link})"

    new_text = LINK_RE.sub(repl, text)
    if changes and not dry_run:
        path.write_text(new_text)
    return changes


def moved_files():
    # Task 1's git mv is already committed by the time this runs, so read
    # the rename from that commit (HEAD~1..HEAD), not the (now-empty) index.
    out = subprocess.run(
        ["git", "diff", "--name-status", "-M", "HEAD~1", "HEAD"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    specs, plans = [], []
    for line in out.splitlines():
        parts = line.split("\t")
        if parts[0].startswith("R") and len(parts) == 3:
            old, new = parts[1], parts[2]
            if old.startswith("docs/superpowers/specs/"):
                specs.append(Path(new).name)
            elif old.startswith("docs/superpowers/plans/"):
                plans.append(Path(new).name)
    return specs, plans


def run(dry_run):
    specs, plans = moved_files()
    assert len(specs) == 50, f"expected 50 moved specs, found {len(specs)}"
    assert len(plans) == 51, f"expected 51 moved plans, found {len(plans)}"

    total_changes = 0
    for name in specs:
        changes = fix_links(
            REPO_ROOT / "dev-docs/specs" / name,
            "docs/superpowers/specs", "dev-docs/specs", dry_run,
        )
        for old, new in changes:
            print(f"dev-docs/specs/{name}: [{old}] -> [{new}]")
        total_changes += len(changes)

    for name in plans:
        changes = fix_links(
            REPO_ROOT / "dev-docs/plans" / name,
            "docs/superpowers/plans", "dev-docs/plans", dry_run,
        )
        for old, new in changes:
            print(f"dev-docs/plans/{name}: [{old}] -> [{new}]")
        total_changes += len(changes)

    changes = fix_links(
        REPO_ROOT / "dev-docs/issues/done/141-whats-new-user-release-notes.md",
        "dev-docs/issues/done", "dev-docs/issues/done", dry_run,
    )
    for old, new in changes:
        print(f"dev-docs/issues/done/141-whats-new-user-release-notes.md: [{old}] -> [{new}]")
    total_changes += len(changes)

    print(f"\n{'would change' if dry_run else 'changed'}: {total_changes} links")


def verify():
    failures = []
    targets = list((REPO_ROOT / "dev-docs/specs").glob("*.md"))
    targets += list((REPO_ROOT / "dev-docs/plans").glob("*.md"))
    targets.append(REPO_ROOT / "dev-docs/issues/done/141-whats-new-user-release-notes.md")
    for f in targets:
        file_dir = str(f.parent.relative_to(REPO_ROOT))
        text = f.read_text()
        for m in LINK_RE.finditer(text):
            target = m.group(1)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            target_path, _, _ = target.partition("#")
            if target_path == "":
                continue
            resolved = posixpath.normpath(posixpath.join(file_dir, target_path))
            if not (REPO_ROOT / resolved).exists():
                failures.append(f"{f.relative_to(REPO_ROOT)}: [{target}] -> {resolved} (missing)")
    if failures:
        print(f"{len(failures)} broken link(s):")
        for line in failures:
            print(" ", line)
        sys.exit(1)
    print(f"OK: all links resolve across {len(targets)} files")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--dry-run":
        run(dry_run=True)
    elif len(sys.argv) == 2 and sys.argv[1] == "--verify":
        verify()
    elif len(sys.argv) == 1:
        run(dry_run=False)
    else:
        print("usage: fix_links.py [--dry-run|--verify]", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 2: No test run for this step** — the script is exercised directly in Task 3 (dry run) and Task 4 (apply), which double as its test.

---

### Task 3: Dry-run and spot-check the script

**Files:** none modified — read-only preview.

- [ ] **Step 1: Run the dry run from the repo root**

```bash
python3 /path/to/your/scratchpad/fix_links.py --dry-run
```

Expected: a list of `file: [old] -> [new]` lines followed by `would change: N links` (N somewhere in the 60-90 range — every issue-reference link plus every `docs/cli`/`docs/language-guide`/`bin` link plus every already-correctly-relative link needing rebasing).

- [ ] **Step 2: Spot-check three known cases in the output**

Confirm these three lines (or their equivalents) appear:

1. Tier 3 (stale issue slug after close):
   `dev-docs/specs/2026-06-15-084-banner-opt-in-design.md: [../../../dev-docs/issues/084-make-no-banner-the-default-print-banner-to-stderr-with-v.md] -> [../issues/done/084-no-banner-default.md]`

2. Tier 2 (already-wrong prefix, unrelated to the move):
   `dev-docs/plans/2026-06-21-100-docs-cli-restructure.md: [../commands/plcc-trees.md] -> [../../docs/cli/commands/plcc-trees.md]`

3. Tier 1 (previously-correct link, rebased for the new depth):
   a line for `plcc-haskell-build.md` (or any `docs/cli/commands` target) changing from a `../../cli/commands/...` or `../../../cli/commands/...` style old value to `../../docs/cli/commands/...`.

If any of these three don't appear as expected, stop and re-check the script logic before proceeding — do not run it for real against unverified logic.

- [ ] **Step 3: Note the two links the script cannot fix**

Look for `2026-07-04-136-release-notes-unification-design.md` in the dry-run output. Two links reference it via an already-double-broken relative path (`../../docs/superpowers/specs/2026-07-04-136-...md`, which resolves to a nonexistent `docs/docs/superpowers/...` or `dev-docs/docs/superpowers/...` path) that the remap table doesn't recognize. These are handled explicitly in Task 4, Step 3 — no script change needed.

---

### Task 4: Apply the fix and hand-correct the two known-unfixable links

**Files:**
- Modify: all 50 files in `dev-docs/specs/`, all 51 files in `dev-docs/plans/` (only those with links needing changes will actually be rewritten)
- Modify: `dev-docs/plans/2026-07-04-136-release-notes-unification.md` (hand fix)
- Modify: `dev-docs/issues/done/141-whats-new-user-release-notes.md` (hand fix)

- [ ] **Step 1: Run the script for real**

```bash
python3 /path/to/your/scratchpad/fix_links.py
```

Expected: same file list as the dry run, ending in `changed: N links` (same N as the dry run).

- [ ] **Step 2: Confirm the working tree shows the expected file count changed**

```bash
git status --short | grep '^ M' | wc -l
```

Expected: a number less than or equal to 101 + 1 (some moved files may have had zero links needing change, e.g. files with no outbound links at all).

- [ ] **Step 3: Hand-fix the two known-unfixable links**

In `dev-docs/plans/2026-07-04-136-release-notes-unification.md`, find:

```
[the issue-136 design spec](../../docs/superpowers/specs/2026-07-04-136-release-notes-unification-design.md)):
```

Replace with:

```
[the issue-136 design spec](../specs/2026-07-04-136-release-notes-unification-design.md)):
```

In `dev-docs/issues/done/141-whats-new-user-release-notes.md`, find the identical old text and replace with:

```
[the issue-136 design spec](../../specs/2026-07-04-136-release-notes-unification-design.md)):
```

- [ ] **Step 4: Commit**

```bash
git add dev-docs/
git commit -m "$(cat <<'EOF'
docs(specs): fix links broken by the docs/superpowers migration

Rebases every relative link in the moved specs/plans for their new
depth, redirects issue-reference links at their current issues/done/
location (many had gone stale independently of this move, matching
the #149 bug class that excluded this then-frozen directory), and
corrects two links to docs/cli/*, docs/language-guide/*, and
dev-docs/v1.0-criteria.md that were already wrong before the move.
EOF
)"
```

---

### Task 5: Verify every link resolves

**Files:** none modified (verification only), unless failures are found.

- [ ] **Step 1: Run the script's verify mode**

```bash
python3 /path/to/your/scratchpad/fix_links.py --verify
```

Expected: `OK: all links resolve across 102 files` (50 specs + 51 plans + 1 issues-done file — `len(specs) + len(plans) + 1`).

- [ ] **Step 2: If failures are reported, fix them**

Each failure line shows the file, the link text, and the (nonexistent) resolved path. Open the file, inspect the surrounding context, and correct the link by hand using the same reasoning as Task 4 Step 3 (compute the correct root-relative target, then the correct relative path from the file's directory). Re-run Step 1 until it reports OK.

- [ ] **Step 3: Confirm no stray references remain anywhere in the repo**

```bash
grep -rn "docs/superpowers" . --include="*.md" 2>/dev/null | grep -v "^\./\.git/"
```

Expected: no output.

- [ ] **Step 4: Commit any fixes from Step 2** (skip if Step 1 passed clean on the first run)

```bash
git add dev-docs/
git commit -m "docs(specs): fix remaining broken links found by verification"
```

---

### Task 6: Run the project's own checks

**Files:** none modified.

- [ ] **Step 1: Issue/roadmap consistency check**

```bash
bin/issues/check.bash
```

Expected: `OK: <N> open issues, roadmap consistent, next id <M>` — unaffected by this change, confirms nothing here disturbed issue bookkeeping.

- [ ] **Step 2: Unit test baseline**

```bash
bin/test/units.bash
```

Expected: same pass count as the pre-work baseline (1175 passed, 1 skipped) — this is a docs-only change, so no test should be affected.

---

### Task 7: Close issue 151

**Files:**
- Move: `dev-docs/issues/151-migrate-superpowers-docs-to-dev-docs.md` → `dev-docs/issues/done/`
- Modify: `dev-docs/roadmap.md`

- [ ] **Step 1: Close the issue**

```bash
bin/issues/close.bash 151
```

Expected output ends with:
```
closed: dev-docs/issues/done/151-migrate-superpowers-docs-to-dev-docs.md
Review dev-docs/roadmap.md (milestone rationale text is not auto-edited), then commit:
  docs(issues): close issue 151 (<short title>), update roadmap
```

- [ ] **Step 2: Review the roadmap diff**

```bash
git diff --cached dev-docs/roadmap.md
```

Confirm the milestone entry's checkbox for #151 is checked and its link now points at `issues/done/151-migrate-superpowers-docs-to-dev-docs.md`, and the Open Issues bullet for #151 is gone.

- [ ] **Step 3: Commit as the final commit of the branch**

```bash
git commit -m "$(cat <<'EOF'
docs(issues): close issue 151 (migrate superpowers docs to dev-docs), update roadmap
EOF
)"
```
