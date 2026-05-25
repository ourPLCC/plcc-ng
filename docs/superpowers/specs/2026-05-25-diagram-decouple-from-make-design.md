# Design: Decouple Diagram Operations from plcc-make

**Date:** 2026-05-25
**Branch:** fix/xdg-open-missing

## Problem

Diagram rendering is an optional, network-dependent operation (HTTP call to plantuml.com). Currently `plcc-make` runs both `plcc-diagram-emit` and `plcc-diagram-build` as part of its pipeline, which causes failures or hangs when the network is unavailable and adds unnecessary latency to every build. Diagrams are not essential to the core PLCC workflow and should be fully decoupled from it.

Additionally, `plcc-plantuml-diagram-run` and `plcc-mermaid-diagram-run` use platform-specific viewer launchers (`xdg-open`, `open`, `os.startfile`) that fail in headless environments (containers, CI). The intended audience (students in IDE terminals) benefits more from a printed file path they can click through than from an auto-launched viewer.

## Desired Behavior

- **`plcc-make`**: no diagram operations at any build level. Produces spec, model, and language artifacts only.
- **`plcc-diagram`**: owns the full diagram workflow — builds the model if needed, emits the diagram source, renders it to PNG, and prints the output path.

## Changes

### 1. `plcc-make` — remove all diagram operations

- Remove `--through=diagram` level. Replace with `--through=model`, which builds spec → model (no LL(1) check, no code generation). Valid levels become: `scan`, `parse`, `model`, `all`.
- Remove `--diagram-format` option.
- Delete the diagram emit/build block (currently lines 165–191 of `make.py`).
- Remove `'diagram'` from the `_REQUIRED` dict and the `required_stages` logic.
- Update docstring and `--help` output.

### 2. `plcc-diagram` — orchestrate the full diagram workflow

- Call `plcc-make --through=model --grammar-file={grammar}` first to ensure `build/model.json` is current. Keep `--grammar-file` option; pass it through to make.
- Remove `--through=diagram` call; remove any direct reference to `plcc-make`'s diagram level.
- After make succeeds, orchestrate in sequence:
  1. `plcc-diagram-emit --format={fmt}` (stdin: `build/model.json`, stdout: `build/diagram/diagram.{ext}`)
  2. `plcc-diagram-build --format={fmt} --input=build/diagram/diagram.{ext} --output=build/diagram/diagram.png`
  3. `plcc-diagram-run --format={fmt} --input=build/diagram/diagram.png`

### 3. `plcc-plantuml-diagram-run` and `plcc-mermaid-diagram-run` — print path, not open viewer

- Remove `_open_file`, all platform detection (`platform.system()`), and all viewer launcher calls (`xdg-open`, `open`, `os.startfile`).
- Replace with `print(path)` to stdout.
- Remove `os`, `platform`, `subprocess` imports that are no longer needed.
- The error-handling fix on this branch (try/except around `_open_file`) is superseded by this change.

## Testing

Each changed module follows the existing pattern: unit tests in `*_test.py` beside the module, mocking subprocess calls. Tests to add or update:

- `make_test.py`: verify `--through=model` builds to model only; verify `--through=diagram` is rejected; verify no diagram commands are invoked at any level.
- `diagram_test.py`: verify `plcc-make --through=model` is called; verify emit → build → run are called in sequence after make succeeds.
- `plantuml/run_test.py` and `mermaid/run_test.py`: verify `print(path)` is called; remove tests for `xdg-open`, `open`, and `startfile`.
