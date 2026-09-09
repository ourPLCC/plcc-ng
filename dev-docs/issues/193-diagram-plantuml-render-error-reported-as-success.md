# 193 - plcc-diagram reports success when PlantUML renders an error image

**Type:** fix
**Date:** 2026-09-09

<!--
Classify by user-facing impact, not by whether something was "broken".
`fix` and `feat` bump the release version (see [tool.semantic_release]
in pyproject.toml); reserve them for changes to the shipped package
(src/). A bug in a test, script, or CI workflow (bin/, tests/,
.github/) is still a bug, but it's not user-facing — classify it
`test` or `chore` instead so it doesn't spin the version. `docs` is for
documentation content, and never bumps the version either way.
-->

## Description

When the PlantUML source `plcc-diagram` sends to `plantuml.com` is malformed,
the server responds **HTTP 200** with a PNG that renders the words
**"Syntax error!"** instead of a diagram.
[`diagram/plantuml/build.py`](../../src/plcc/diagram/plantuml/build.py) reads
that PNG and writes it to the output path unconditionally:

```python
with urllib.request.urlopen(req, timeout=30) as response:
    png_bytes = response.read()
...
with open(output_file, 'wb') as f:
    f.write(png_bytes)
```

There is no check on the response, so a failed render is indistinguishable from
a successful one. `plcc-diagram-plantuml-build` exits **0**, the run
orchestrators propagate that, and `plcc-diagram` prints the output path as if it
had succeeded. Nothing signals a problem until a human opens the PNG.

The `except` clause only catches transport failures (DNS, connection refused,
timeout, a non-2xx status). A 200 carrying an error image sails straight
through.

This was raised as the secondary half of
[#192](done/192-syntax-diagram-empty-alternative-invalid-ebnf.md) and split off
deliberately: #192 removed the one emitter bug known to trigger it, but any
future malformed emission — or a valid `.puml` the server rejects for its own
reasons — still fails silently. It is a separate concern with its own remedy.

## Steps to Reproduce

Hand `plcc-diagram-plantuml-build` a `.puml` file PlantUML rejects:

```console
$ printf "@startebnf\nA = 'X' | ;\n@endebnf\n" > bad.puml
$ plcc-diagram-plantuml-build --input=bad.puml --output=bad.png
$ echo $?
0
$ file bad.png
bad.png: PNG image data, 112 x 36, ...
```

`bad.png` renders as *"Syntax error!"*. The command exited 0 and wrote the file
without complaint. The dangling-alternative source above is exactly what #192's
emitter bug produced.

Measured against `plantuml.com` on 2026-09-09, PlantUML server version
`1.2026.8beta1`, with #192 applied.

## Notes

**What the response actually carries.** `plantuml.com`'s `/png/` endpoint gives
no programmatic error signal — checked directly for the source above:

- HTTP status is **200**, same as a successful render.
- There is **no** `X-PlantUML-Diagram-Error` header (some self-hosted PlantUML
  server configurations reportedly set one; plantuml.com's proxied deployment
  does not).
- `X-Plantuml-Diagram-Width`/`-Height` are present for both success and error;
  the error image happens to be a fixed `112 x 36` but keying on that is
  fragile.

The one signal that did work: the **`/svg/` endpoint** returns the same HTTP
200 with no error header, but the body is text and, on failure, contains a
literal `<text ...>Syntax error!</text>` node (verified: a good render's text
nodes were the grammar symbols, the bad one's single text node was
`Syntax error!`).

**Suggested direction** (needs a decision, no strong preference):

- Validate each render with a lightweight `/svg/` fetch of the same source and
  fail if the SVG body contains `Syntax error!` (or `>Syntax Error<`), printing
  that to stderr and `sys.exit(1)` — matching the existing transport-failure
  path in `build.py`.
- Or match the known error-PNG signature (dimensions / byte length). Cheaper,
  but brittle across PlantUML versions and diagram types.
- Add a `build_test.py` case that stubs an error response and asserts a
  non-zero exit and no output file written.
- Consider whether `plcc-diagram` should name which diagram failed when a run
  renders several.

**Scope.** `class.png` and `syntax.png` go through the same code path, so a fix
covers both. No emitter change is implied — this is about the build step
treating a 200 as success.
