# Language Plugin Command Contract

**Date:** 2026-04-12
**Status:** Approved
**Amends:** `docs/design/2026-04-12-multi-lang-pipeline.md` §5, §9, §10
**Resolves:** open question in implementation plan §12 ("plcc-make/plcc-emit calling convention")

## 1. Decision Summary

Emitter plugins expose CLI commands, not Python callables. The plugin contract is defined entirely in terms of stdin, stdout, flags, and exit codes. The `importlib.metadata` entry point discovery mechanism is dropped in favour of PATH-based discovery. The `plcc.emitters` entry point group is eliminated.

## 2. Command Taxonomy

Three tiers:

| Tier | Commands | Role |
|---|---|---|
| Dispatchers (Level 0) | `plcc-lang-emit`, `plcc-lang-build`, `plcc-lang-list` | Manage and invoke language plugins |
| Plugin commands | `plcc-<lang>-emit`, `plcc-<lang>-build` | Language-specific implementation |
| Unchanged Level 0 | `plcc-spec`, `plcc-tokens`, `plcc-tree`, `plcc-model` | Existing pipeline stages |

`plcc-emit` is retired. `plcc-lang-emit` replaces it in the Level 0 table and in `plcc-make`'s phase sequence.

Built-in plugins are declared as console scripts in `plcc`'s own `pyproject.toml`:

```toml
[project.scripts]
plcc-plantuml-emit = "plcc.lang.plantuml:emit_main"
plcc-python-emit   = "plcc.lang.python:emit_main"
plcc-java-emit     = "plcc.lang.java:emit_main"
plcc-java-build    = "plcc.lang.java:build_main"
```

No `plcc.emitters` or `plcc.langs` entry point group is declared or used.

## 3. Plugin Contract

### 3.1 `plcc-<lang>-emit` (required)

- Reads model JSON from stdin
- Accepts `--output=<dir>` (required) and `--semantics=hide|note|comment|body` (optional, default `body`)
- Writes generated source files into `<dir>`
- Copies its bundled runtime into `<dir>/runtime/`
- Exits 0 on success; exits nonzero and writes a message to stderr on failure
- A malformed or unsupported model is a tool failure (nonzero exit), not an in-band error record

### 3.2 `plcc-<lang>-build` (optional)

- Accepts `--output=<dir>` (required)
- Compiles or prepares files already in `<dir>` (e.g. runs `javac`)
- Exits 0 on success; exits nonzero and writes a message to stderr on failure
- Absence from PATH means no build step for that language — not an error

### 3.3 Language independence

Because the contract is stdin/stdout/exit codes, a plugin does not need to be a Python package. `pip install` is the conventional delivery mechanism, but the runtime contract has no Python dependency.

## 4. Dispatchers

### 4.1 `plcc-lang-emit --target=<lang> --output=<dir> [--semantics=<value>]`

Constructs `plcc-<lang>-emit`, passes stdin through, forwards `--output` and `--semantics`, and execs it as a subprocess. If the command is not found on PATH, exits nonzero with:

```
No emitter found for '<lang>'. Is plcc-<lang>-emit installed?
Run plcc-lang-list to see what is available.
```

### 4.2 `plcc-lang-build --target=<lang> --output=<dir>`

Constructs `plcc-<lang>-build` and execs it with `--output` if found on PATH. If not found, exits 0 silently — absence is not a failure.

### 4.3 `plcc-lang-list`

Walks each directory in `PATH`, collects executables matching `plcc-*-emit`, strips the `plcc-` prefix and `-emit` suffix to extract the language name, and prints deduplicated names one per line.

All three dispatchers are thin. Their only logic is name construction, PATH lookup, and error messaging. The actual work is always in the plugin command.

## 5. `plcc-make` Integration

Updated phase sequence:

1. **Clean:** `rm -rf build/`
2. **Spec:** `plcc-spec grammar.plcc > build/spec.json`
3. **Model:** `plcc-model build/spec.json > build/model.json`
4. **Emit:** for each semantic section, `plcc-lang-emit --target=<lang> --output=build/<tool>/ < build/model.json`
5. **Build:** for each semantic section, `plcc-lang-build --target=<lang> --output=build/<tool>/` (silently skipped if plugin has no build step)

`plcc-make` always calls `plcc-lang-emit` and `plcc-lang-build`, never the plugin commands directly. The naming convention is encapsulated in the dispatchers.

## 6. Changes Required in Existing Documents

### 6.1 `docs/design/2026-04-12-multi-lang-pipeline.md`

Add §17.2 as an architectural amendment. Specific section changes:

- **§4 diagram** — replace `plcc-emit` with `plcc-lang-emit` in the Level 0 row
- **§5 Level 0 table** — retire the `plcc-emit` row; add `plcc-lang-emit`, `plcc-lang-build`, `plcc-lang-list`; update naming rationale note
- **§9 phase sequence** — steps 4 and 5 updated to use `plcc-lang-emit` and `plcc-lang-build`
- **§10 title** — "Emitter Plugin System" → "Language Plugin System"
- **§10.1** — rewrite plugin contract from Python callables to CLI command signatures
- **§10.2** — update plugin package layout to show `pyproject.toml` console script declaration instead of `__init__.py` with `emit()`/`build()`
- **§10.3** — replace `importlib.metadata` discovery code with PATH-based description
- **§10.4** — update built-in emitters to show console script declarations in `plcc`'s `pyproject.toml`; remove all references to `plcc.emitters` entry point group

### 6.2 `docs/design/2026-04-12-multi-lang-implementation-plan.md`

- **Naming throughout** — `plcc-emit-java` → `plcc-java-emit`, `plcc-emit-python` → `plcc-python-emit`, `plcc-emit-plantuml` → `plcc-plantuml-emit`; `plcc-emit` (dispatcher) → `plcc-lang-emit`
- **§4.2 Phase 1 strategy** — skeleton builds `plcc-lang-emit`, `plcc-lang-build`, `plcc-lang-list` as dispatchers; `plcc-plantuml-emit` is a console script entry point, not an entry point group member; PATH discovery replaces `importlib.metadata` machinery
- **§4.4 Phase 1 acceptance criteria** — reword plugin discovery criterion: "`plcc-plantuml-emit` is discovered via PATH; `plcc-lang-list` finds it"
- **§4.6 Phase 1 design doc scope** — drop mention of `plcc.emitters` entry point group
- **§7.2 Phase 4** — update plugin consolidation names; drop entry point group registration note
- **§12** — move `plcc-make`/`plcc-emit` calling convention question to §12.1 as resolved: `plcc-make` calls `plcc-lang-emit` and `plcc-lang-build` as subprocesses
