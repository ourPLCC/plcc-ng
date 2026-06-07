# 079 - Use diagrams to illustrate concepts in the docs

**Type:** docs
**Date:** 2026-06-07

## Description

The docs explain concepts in prose only. Diagrams (pipeline flow, parse tree structure, stage relationships, etc.) would make these concepts significantly easier to grasp.

## Question

Which diagramming tool should we adopt? Two leading options:

- **Mermaid** — rendered natively by many static-site frameworks (MkDocs Material, Docusaurus) and GitHub. No build-time dependency. Diagrams live as fenced code blocks in Markdown.
- **PlantUML** — more expressive for UML-style diagrams but requires a Java build-time dependency or an external render server.

## Notes

Mermaid is likely the lower-friction choice given its native support in common doc frameworks and GitHub previews. PlantUML may be worth it if we need richer UML diagrams. The decision should account for whatever doc framework is in use.
