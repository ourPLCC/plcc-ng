# PlantUML Inheritance Arrow Direction

**Date:** 2026-06-24
**Issue:** [108 - PlantUML diagram: point inheritance arrows up](../../../dev-docs/issues/108-plantuml-inheritance-direction.md)

## Problem

`plcc-plantuml-diagram-emit` generates inheritance relationships using `Child --|> Parent`. PlantUML's layout engine treats the left-hand side of an arrow as the layout source and places it above the right-hand side, so this notation renders with children at the top and the parent at the bottom — the opposite of the traditional UML convention.

## Decision

Reverse the arrow notation to `Parent <|-- Child`. Both forms express the same inheritance relationship in PlantUML, but putting the parent on the left makes it the layout source, so PlantUML places it above the children. Verified correct in the PlantUML online editor.

## Changes

### `src/plcc/diagram/plantuml/emit.py`

In `build_diagram`, flip the f-string that emits the inheritance arrow:

```python
# before
lines.append(f'{cls["name"]} --|> {cls["extends"]}')
# after
lines.append(f'{cls["extends"]} <|-- {cls["name"]}')
```

### `src/plcc/diagram/plantuml/emit_test.py`

Update `test_build_diagram_inheritance_arrow` to assert the new notation:

```python
# before
assert 'AddRest --|> ExprRest' in result
assert 'NilRest --|> ExprRest' in result
# after
assert 'ExprRest <|-- AddRest' in result
assert 'ExprRest <|-- NilRest' in result
```

## Scope

Two files, two lines of production code, two test assertions. No other behaviour changes.
