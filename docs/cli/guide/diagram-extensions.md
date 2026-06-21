# Diagram Extensions

Diagram extensions implement the emit, build, and run steps for a specific
diagram format. plcc-ng ships with Mermaid and PlantUML support.

## How diagram extensions plug in

[`plcc-diagram`](../commands/plcc-diagram.md) runs three dispatch commands:

1. [`plcc-diagram-emit --format=FMT`](../commands/plcc-diagram-emit.md) — calls `plcc-<fmt>-diagram-emit`
2. [`plcc-diagram-build --format=FMT`](../commands/plcc-diagram-build.md) — calls `plcc-<fmt>-diagram-build`
3. [`plcc-diagram-run --format=FMT`](../commands/plcc-diagram-run.md) — calls `plcc-<fmt>-diagram-run`

The default format is `plantuml`. Use [`plcc-diagram-list`](../commands/plcc-diagram-list.md)
to see what is installed.

## plcc-mermaid-diagram

Generates a Mermaid class diagram. Requires the `mmdc` CLI
(`npm install -g @mermaid-js/mermaid-cli`).

| Command | What it does |
| --- | --- |
| [`plcc-mermaid-diagram-emit`](../commands/plcc-mermaid-diagram-emit.md) | Reads model JSON from stdin; writes a `.mmd` Mermaid source file |
| [`plcc-mermaid-diagram-build`](../commands/plcc-mermaid-diagram-build.md) | Renders `.mmd` to PNG using `mmdc` |
| [`plcc-mermaid-diagram-run`](../commands/plcc-mermaid-diagram-run.md) | Prints the path to the rendered PNG |

## plcc-plantuml-diagram

Generates a PlantUML class diagram. Rendering is done via the public
`plantuml.com` API — no local PlantUML installation required.

| Command | What it does |
| --- | --- |
| [`plcc-plantuml-diagram-emit`](../commands/plcc-plantuml-diagram-emit.md) | Reads model JSON from stdin; writes a `.puml` PlantUML source file |
| [`plcc-plantuml-diagram-build`](../commands/plcc-plantuml-diagram-build.md) | Sends `.puml` to plantuml.com and writes the returned PNG |
| [`plcc-plantuml-diagram-run`](../commands/plcc-plantuml-diagram-run.md) | Prints the path to the rendered PNG |
