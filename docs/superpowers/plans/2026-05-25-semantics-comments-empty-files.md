# Semantics Comments Create Empty Files — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Filter `#` comment lines from the semantics section at parse time so they never reach the emitters and never create empty files in the build output.

**Architecture:** Extend `isEmpty()` in `parse_code_fragments.py` to treat lines beginning with `#` as empty. Comments are dropped before a `TargetLocator` is created, so they never appear in `SemanticSpec`, `spec.json`, `model.json`, or any language emitter. Remove the now-dead `startswith('#')` band-aid from the Java emitter and its associated test.

**Tech Stack:** Python, pytest. All work is in `src/plcc/`.

**Worktree:** `.worktrees/fix/semantics-comments-empty-files` — run all commands from this directory.

---

## File Map

| Action | File | Change |
|--------|------|--------|
| Modify | `src/plcc/spec/semantics/parse_code_fragments.py` | Add `#` check to `isEmpty()` |
| Modify | `src/plcc/spec/semantics/parse_code_fragments_test.py` | Add one test |
| Modify | `src/plcc/lang/ext/java/emit.py` | Remove `startswith('#')` guard from `_group_fragments` |
| Modify | `src/plcc/lang/ext/java/emit_test.py` | Remove `test_hash_comment_class_name_is_skipped` |

---

### Task 1: Filter comment lines at parse time (TDD)

**Files:**
- Modify: `src/plcc/spec/semantics/parse_code_fragments_test.py`
- Modify: `src/plcc/spec/semantics/parse_code_fragments.py`

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/spec/semantics/parse_code_fragments_test.py` (after `test_empty_lines_ignored`):

```python
def test_comment_line_is_ignored():
    lines = [make_line('# a comment'), make_line('Class:init'), make_block()]
    assert parse_code_fragments(lines) == [
        CodeFragment(make_target_locator(lines[1], 'Class', 'init'), make_block())]
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
python -m pytest src/plcc/spec/semantics/parse_code_fragments_test.py::test_comment_line_is_ignored -v
```

Expected: `FAILED` — the comment line is currently parsed as a `TargetLocator` with `className='# a comment'`, producing an unexpected extra `CodeFragment`.

- [ ] **Step 3: Fix `isEmpty()` in `parse_code_fragments.py`**

In `src/plcc/spec/semantics/parse_code_fragments.py`, replace the `isEmpty` function:

```python
def isEmpty(locatorOrBlock):
    if locatorOrBlock is None:
        return True
    if isinstance(locatorOrBlock, Line):
        s = locatorOrBlock.string
        return s is None or s.strip() == '' or s.lstrip().startswith('#')
    return False
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
python -m pytest src/plcc/spec/semantics/parse_code_fragments_test.py::test_comment_line_is_ignored -v
```

Expected: `PASSED`

- [ ] **Step 5: Run the full test file to check for regressions**

```bash
python -m pytest src/plcc/spec/semantics/parse_code_fragments_test.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/spec/semantics/parse_code_fragments.py \
        src/plcc/spec/semantics/parse_code_fragments_test.py
git commit -m "$(cat <<'EOF'
fix: treat # comment lines in semantics section as empty

Closes issue 040.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Remove the Java emitter band-aid

**Files:**
- Modify: `src/plcc/lang/ext/java/emit.py:113-119`
- Modify: `src/plcc/lang/ext/java/emit_test.py:216-223`

- [ ] **Step 1: Remove the `startswith('#')` guard from `_group_fragments`**

In `src/plcc/lang/ext/java/emit.py`, replace `_group_fragments`:

```python
def _group_fragments(fragments):
    groups = {}
    for frag in fragments:
        groups.setdefault(frag['class_name'], []).append(frag)
    return groups
```

- [ ] **Step 2: Remove `test_hash_comment_class_name_is_skipped`**

In `src/plcc/lang/ext/java/emit_test.py`, delete this entire test (lines 216–223):

```python
def test_hash_comment_class_name_is_skipped(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "# a comment", "kind": "body", "body": "// ignored"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    assert not (tmp_path / '# a comment.java').exists()
```

- [ ] **Step 3: Run the full unit test suite**

```bash
bin/test/units.bash 2>&1 | tail -5
```

Expected: all tests pass (count increases by 0 net — one test removed, one added in Task 1).

- [ ] **Step 4: Commit**

```bash
git add src/plcc/lang/ext/java/emit.py \
        src/plcc/lang/ext/java/emit_test.py
git commit -m "$(cat <<'EOF'
refactor: remove # comment guard from java emitter (dead code after 040 fix)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```
