# 041 - plcc-diagram-build should not run during make-all

**Type:** fix
**Date:** 2026-05-25

## Description

`plcc-make` (make-all) currently runs `plcc-diagram-build`, which makes an outbound HTTP request to plantuml.com. This causes make-all to fail or hang whenever the network is unavailable, and creates unnecessary latency on every build.

Build steps should produce artifacts that can be inspected offline. Diagram rendering — which requires a network call — belongs only in the viewing flow (`plcc-diagram`), not in the build flow.

**Desired behavior:**

- `plcc-make` / make-all: runs `plcc-diagram-emit` to produce the `.puml` source file, but does **not** run `plcc-diagram-build` (no HTTP call, no PNG).
- `plcc-diagram` (the viewer command): runs `plcc-diagram-build` to render the `.puml` to PNG and then displays it.

## Steps to Reproduce

1. Disconnect from the network.
2. Run `plcc-diagram` on a grammar file that uses the plantuml format.
3. Observe that make-all fails or hangs waiting for plantuml.com.

## Notes

`plcc-diagram-emit` is already a separate command and produces the `.puml` file on its own. The build pipeline only needs to emit; the render step can be deferred to when the user actually asks to view the diagram.
