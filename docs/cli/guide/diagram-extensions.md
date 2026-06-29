# Diagram Extensions

Diagram extensions implement the emit, build, and run steps for a specific
diagram format. plcc-ng ships with PlantUML support.

## How diagram extensions plug in

[`plcc-diagram`](../commands/plcc-diagram.md) runs three dispatch commands:

1. [`plcc-diagram-emit --format=FMT`](../commands/plcc-diagram-emit.md) — calls `plcc-diagram-<type>-<fmt>-emit`
2. [`plcc-diagram-build --format=FMT`](../commands/plcc-diagram-build.md) — calls `plcc-diagram-<fmt>-build`
3. [`plcc-diagram-run --format=FMT`](../commands/plcc-diagram-run.md) — calls `plcc-diagram-<fmt>-run`

The default format is `plantuml`. Use [`plcc-diagram-list`](../commands/plcc-diagram-list.md)
to see what is installed.

## plcc-plantuml-diagram

Generates a PlantUML class diagram. Rendering is done via the public
`plantuml.com` API — no local PlantUML installation required.

| Command | What it does |
| --- | --- |
| [`plcc-diagram-class-plantuml-emit`](../commands/plcc-diagram-class-plantuml-emit.md) | Reads model JSON from stdin; writes a `.puml` PlantUML source file |
| `plcc-diagram-plantuml-build` | Sends `.puml` to plantuml.com and writes the returned PNG |
| `plcc-diagram-plantuml-run` | Prints the path to the rendered PNG |
