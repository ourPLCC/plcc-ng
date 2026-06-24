# 108 - PlantUML diagram: point inheritance arrows up

**Type:** feat
**Date:** 2026-06-24

## Description

The PlantUML diagram emitter generates inheritance relationships as `Child --|> Parent`, which causes PlantUML's layout engine to place the child class above the parent. This renders with the parent at the bottom and arrows pointing down — the opposite of the traditional UML convention (parent at top, arrows pointing up toward the parent).

The fix is to reverse the arrow notation to `Parent <|-- Child`. Both forms express the same inheritance relationship, but putting the parent on the left makes it the layout "source", so PlantUML places it above the children.

## Notes

Discovered while testing `plcc-diagram` on the `arith.plcc` spec in `t/`. Verified in the PlantUML online editor that reversing the notation produces the correct traditional layout.

The change belongs in the emit step — specifically the line in `src/plcc/diagram/plantuml/emit.py` that generates the inheritance arrow for each rule.
