# PlantUML Inheritance Arrow Direction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reverse the PlantUML inheritance arrow notation from `Child --|> Parent` to `Parent <|-- Child` so that generated diagrams render with parent classes at the top.

**Architecture:** One f-string change in `build_diagram` (emit.py:52) and two updated test assertions in `emit_test.py`. No new files, no interface changes.

**Tech Stack:** Python, pytest (`bin/test/units.bash`)

## Global Constraints

- TDD inner loop: write failing test → confirm failure → implement → confirm pass → commit
- `bin/test/units.bash` is the test runner for this tier; run it exactly as shown

---

### Task 1: Flip the inheritance arrow

**Files:**
- Modify: `src/plcc/diagram/plantuml/emit_test.py:52-60`
- Modify: `src/plcc/diagram/plantuml/emit.py:52`

**Interfaces:**
- Consumes: `build_diagram(model)` — already exists, returns a `str`
- Produces: no interface change; the output format of `build_diagram` changes from `Child --|> Parent` to `Parent <|-- Child`

- [ ] **Step 1: Update the failing test**

In `src/plcc/diagram/plantuml/emit_test.py`, update `test_build_diagram_inheritance_arrow` (lines 52–55) and `test_build_diagram_no_arrow_for_no_extends` (line 60):

```python
def test_build_diagram_inheritance_arrow():
    result = build_diagram(_ARITH_MODEL)
    assert 'ExprRest <|-- AddRest' in result
    assert 'ExprRest <|-- NilRest' in result


def test_build_diagram_no_arrow_for_no_extends():
    result = build_diagram(_ARITH_MODEL)
    assert '<|-- Program' not in result
```

- [ ] **Step 2: Run the tests and confirm they fail**

```bash
bin/test/units.bash src/plcc/diagram/plantuml/emit_test.py -v
```

Expected: `test_build_diagram_inheritance_arrow` FAILS (asserts new notation, implementation still emits old notation). `test_build_diagram_no_arrow_for_no_extends` may also fail depending on how the old assertion matched.

- [ ] **Step 3: Update the implementation**

In `src/plcc/diagram/plantuml/emit.py`, change line 52 inside `build_diagram`:

```python
# before
lines.append(f'{cls["name"]} --|> {cls["extends"]}')
# after
lines.append(f'{cls["extends"]} <|-- {cls["name"]}')
```

- [ ] **Step 4: Run the tests and confirm they pass**

```bash
bin/test/units.bash src/plcc/diagram/plantuml/emit_test.py -v
```

Expected: all tests in `emit_test.py` pass.

- [ ] **Step 5: Run the full unit suite to check for regressions**

```bash
bin/test/units.bash
```

Expected: all tests pass, 0 failures.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/diagram/plantuml/emit.py src/plcc/diagram/plantuml/emit_test.py
git commit -m "feat(diagram): point plantuml inheritance arrows up (Parent <|-- Child)"
```
