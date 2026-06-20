# 079 - Use diagrams to illustrate concepts in the docs

**Type:** docs
**Date:** 2026-06-07

## Description

The docs explain concepts in prose only. Diagrams (pipeline flow, parse tree structure, stage relationships, etc.) would make these concepts significantly easier to grasp.

## Question

Which diagramming tool should we adopt? Two leading options:

- **Mermaid** — rendered natively by many static-site frameworks (MkDocs Material, Docusaurus) and GitHub. No build-time dependency. Diagrams live as fenced code blocks in Markdown.
- **PlantUML** — more expressive for UML-style diagrams but requires a Java build-time dependency or an external render server.

## Decision

Keep PlantUML via the existing Kroki plugin. PlantUML is already integrated and
has proven more capable in practice. Mermaid is easy to add via MkDocs Material
if a specific need arises, but there is no reason to switch now.
