# 111 — Redesign Mermaid diagram build to use kroki.io

**Date:** 2026-06-24
**Issue:** [111 - Redesign the Mermaid diagram extension](../issues/done/111-mermaid-extension-redesign.md)

## Problem

`plcc-mermaid-diagram-build` currently invokes `mmdc` (the Mermaid CLI) to render `.mmd` source to PNG. `mmdc` requires a global npm install and does not work in most dev environments, so users who choose `--format=mermaid` get a build failure with no diagram.

## Contract (unchanged)

The diagram extension contract has three roles:

1. **emit** — produce source code in a text-based diagram language (`.mmd`)
2. **build** — render that source into a viewable form (PNG), using whatever strategy fits the format
3. **run** — help the user view the result

`build` and `run` are a coupled pair: what `build` produces, `run` consumes. Multiple build-run pairs can reuse the same `emit`.

## Solution

Replace the broken `mmdc` CLI strategy in `build` with an HTTP call to [kroki.io](https://kroki.io), which renders Mermaid diagrams server-side and returns PNG bytes — no local tools required. This is the same pattern already used by `plcc-plantuml-diagram-build` (which calls `plantuml.com`).

## Design

### `mermaid/build.py`

- Remove all `shutil`/`subprocess` logic.
- Encode the `.mmd` source: `zlib.compress()` → `base64.urlsafe_b64encode()` → strip `=` padding.
- GET `https://kroki.io/mermaid/png/<encoded>` with a `User-Agent` header.
- On success: write response bytes to `--output` (PNG file).
- On any exception: print to stderr and `sys.exit(1)`.
- Docstring: *"Render a Mermaid diagram source file to a PNG image via kroki.io."*

### `mermaid/emit.py` — no change

Still produces `.mmd` (raw Mermaid syntax) to stdout.

### `mermaid/run.py` — no change

Still prints the path to the PNG file. The orchestrator passes `diagram.png`; run just surfaces it to the user.

### `cmd/diagram.py` — no change

The orchestrator is already format-agnostic. `build` still outputs `diagram.png`; the pipeline is unchanged.

## Testing

`mermaid/build_test.py` — replace existing mmdc-focused tests:

| Test | What it verifies |
|---|---|
| `test_missing_required_args_exits_nonzero` | arg-parsing contract (unchanged) |
| `test_renders_png_via_kroki` | mock `urlopen` returns fake PNG bytes → output file written with those bytes |
| `test_http_error_prints_message_and_exits` | mock `urlopen` raises `URLError` → nonzero exit + stderr message |
| `test_encodes_source_in_url` | capture URL passed to `urlopen` → assert `kroki.io/mermaid/png/` prefix and non-empty payload |

## Out of scope

- Keeping an `mmdc`-based build strategy for CI/headless use (can be a future extension under a different entry point).
- Changing `run` to open an image viewer automatically.
