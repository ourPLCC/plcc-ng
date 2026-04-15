# PLCC Multi-Language Pipeline Architecture

**Date:** 2026-04-12
**Status:** Draft — pending review
**Target release:** PLCC v9.0.0

## 1. Goal

Make PLCC adoptable by faculty whose students do not know Java, by refactoring PLCC into a Unix-style pipeline of small JSON-filter tools and a plugin-based code generator that can emit interpreters in multiple target languages.

## 2. Non-Goals

- Replacing or competing with production compiler toolchains. Generated interpreters are pedagogical artifacts, not production software.
- Supporting non-OO target languages. Retargeting is limited to modern OO languages because the pedagogy depends on class hierarchy and polymorphic dispatch.
- Pluggable scanners, parsers, or verifiers. Only emitters are pluggable in v9. Verifiers may become pluggable in a later version if demand emerges.
- Bit-exact compatibility with v8's generated Java output. See §13.
- Windows-native shell pipelines. Cross-platform support comes from Python orchestration, not from shell portability. See §6.

## 3. Motivation and Context

PLCC is an educational compiler-compiler used to teach programming language concepts. As of v8.0.2 it generates only Java, which limits adoption to courses and institutions where students already know Java. Faculty at institutions that teach Python, TypeScript, or other languages as their primary language cannot adopt PLCC without imposing a language-learning burden on their students.

A parallel project, `plcc-ng`, is a clean-room rewrite in Python by students using TDD. It has completed spec parsing (lexical, syntactic, and semantic sections), a working scanner, LL(1) validation, and CLIs for `spec` and `scan`. It has not built the parser runtime or code generator. plcc-ng has accumulated 282 commits of student work.

This design builds on plcc-ng's foundation rather than starting over, preserves the student contributions from plcc-ng's history, and refactors the result into a pipeline architecture that supports multiple target languages through a plugin system.

## 4. Architecture Overview

PLCC v9 is a pipeline of small tools communicating through JSON. The pipeline has two layers:

- **Level 0** primitives are single-responsibility JSON filters. Each reads a specific JSON format on stdin (or a file path argument) and writes a specific JSON format on stdout. Primitives are composable by hand on a Unix command line.
- **Level 2** user-facing commands are Python orchestrators that compose Level 0 primitives into pipelines using `subprocess.Popen`. They match the vocabulary of existing PLCC learning materials.

Level 1 (intermediate compositions) is deliberately unoccupied in v9. It may emerge later if pedagogical use cases justify it.

```
                     ┌──────────────────────────────────────────────┐
                     │                 Level 2                      │
                     │  plcc-make   plcc-scan   plcc-parse  plcc-rep│
                     └───────────────────┬──────────────────────────┘
                                         │ orchestrates
                                         ▼
         ┌────────────┬──────────────┬─────────────┬────────────┬───────────────┐
         │ plcc-spec  │ plcc-tokens  │ plcc-tree   │ plcc-model │plcc-lang-emit │
         │            │              │             │            │               │
         │ grammar    │ text stream  │ token JSONL │ spec JSON  │ model JSON    │
         │   ↓        │   ↓          │   ↓         │   ↓        │   ↓           │
         │ spec JSON  │ token JSONL  │ tree JSONL  │ model JSON │ files         │
         └────────────┴──────────────┴─────────────┴────────────┴───────────────┘
                                                                   │
                                                                   ▼
                                                  ┌──────────────────────────┐
                                                  │  Language plugin commands │
                                                  │  plcc-<lang>-emit (PATH) │
                                                  └──────────────────────────┘
```

## 5. Level 0 Primitives

Each primitive is a pip console-script entry point provided by the `plcc` package. The four pure JSON filters are named after their output. The `plcc-lang-*` commands form a separate tier that manages and dispatches to language plugins (see §10).

| Command | Input | Output | Role |
|---|---|---|---|
| `plcc-spec` | grammar file path | spec JSON (stdout) | Parse a `.plcc` grammar file into a structured spec. One-shot; single JSON document. Already exists in plcc-ng as `spec`; renamed for namespace hygiene. |
| `plcc-tokens` | text stream (stdin) + spec JSON path | token JSONL (stdout) | Tokenize a character stream into a line-delimited JSON stream of tokens. Streaming; stateless; runs until EOF. |
| `plcc-tree` | token JSONL (stdin) + spec JSON path | tree JSONL (stdout) | Parse tokens into abstract syntax trees. Knows program boundaries from the grammar's start symbol. Long-running; emits one JSON tree per line, one per completed program. |
| `plcc-model` | spec JSON (stdin or path) | model JSON (stdout) | Transform a language spec into a language-neutral OO code model: classes, inheritance, attributes, constructors, method slots, and opaque semantic blocks. One-shot; single JSON document. |
| `plcc-lang-emit` | model JSON (stdin) + `--target=<lang>` + `--output=<dir>` | source files in `<dir>` | Dispatcher: constructs `plcc-<lang>-emit` and execs it via PATH. The plugin writes generated source files and copies its bundled runtime into `<dir>`. |
| `plcc-lang-build` | `--target=<lang>` + `--output=<dir>` | compiled artifacts in `<dir>` | Dispatcher: constructs `plcc-<lang>-build` and execs it via PATH if present. Exits 0 silently if no build command is installed for that language. |
| `plcc-lang-list` | — | language names (stdout) | Scans PATH for commands matching `plcc-*-emit`; prints one language name per line. |

Naming rationale: the four pure filters (`spec`, `tokens`, `tree`, `model`) are named after their output. The `plcc-lang-*` commands are named after the layer they manage (language plugins) — they form the boundary between the core pipeline and the plugin ecosystem. `tree` is preferred over `ast` because it is approachable without jargon; `tokens` is preferred over `lex` or `tokenize` because it is a noun and matches the output. `model` is preferred over `code-model` for brevity.

## 6. Level 2 Commands

Level 2 commands are Python modules published as pip console-script entry points. They orchestrate Level 0 primitives using `subprocess.Popen`, wire stdin/stdout between stages, handle tty detection and prompting, and present errors to the user.

| Command | Role | Replaces |
|---|---|---|
| `plcc-make` | Build the project from a grammar file. Always cleans `build/` before rebuilding. See §9 for phase sequence. | `plccmk` |
| `plcc-scan` | Pedagogical scanner view. Reads source input, runs it through `plcc-tokens`, prints tokens in a human-readable format. | `scan` |
| `plcc-parse` | Pedagogical parser view. Reads source input, runs it through `plcc-tokens` then `plcc-tree`, prints parse trees in a human-readable format. | (new; previously part of `rep`) |
| `plcc-rep` | REPL. Reads source input (files then stdin if interactive), runs it through `plcc-tokens` then `plcc-tree` then the interpreter, prints evaluation results. Handles prompting in tty mode. | `rep` |

All Level 2 commands take the same input model: zero or more file arguments followed by stdin. Files are concatenated in order, then stdin is appended. In interactive mode (`sys.stdin.isatty()`), the orchestrator emits prompts to stderr before each read.

**No shell dependency.** Layer 2 orchestrators do not invoke `cat`, `sh`, or any external shell. They open files through `pathlib`, read stdin through `sys.stdin`, and write bytes to the first subprocess's stdin pipe. This works identically on Linux, macOS, and Windows without platform branching.

Students or instructors who want to run the primitives by hand from a Unix shell can do so. That usage is documented as a teaching aid but is not the path any installed Level 2 command takes.

## 7. JSON Contracts

This section describes the shape of data flowing between stages at a high level. Exact schemas are the implementation plan's responsibility; this spec establishes only the contract and the error-record discipline.

**One-shot vs. streaming.** Two of the primitives run as streaming pipeline stages and use JSONL (one JSON document per line) so they can emit output incrementally as input arrives:

- `plcc-tokens` — token JSONL
- `plcc-tree` — tree JSONL

The other three primitives run once per invocation and produce a single JSON document (or, for `plcc-lang-emit`, files on disk):

- `plcc-spec` — spec JSON (single document)
- `plcc-model` — model JSON (single document)
- `plcc-lang-emit` — files

The distinction matters for the REPL: tokens and trees flow through the pipe continuously as the student types programs, while spec and model are built once at `plcc-make` time and reused.

### 7.1 Spec JSON

Output of `plcc-spec`. Contains lexical rules, syntactic rules, semantic sections (one per `% <tool> <language>` divider), and metadata needed by downstream primitives. Already produced by plcc-ng's existing `spec` command; the shape of the v9 spec JSON starts from whatever plcc-ng emits today and is refined as downstream primitives require.

### 7.2 Token JSONL

Output of `plcc-tokens`. One JSON object per line, each describing a single token: kind, lexeme, source position. A final line marks end-of-stream. Error tokens are in-band records per §8.

### 7.3 Tree JSONL

Output of `plcc-tree`. One JSON object per line, each describing an abstract syntax tree rooted at the grammar's start symbol for one completed program. Long-running: `plcc-tree` emits one tree line and resumes reading tokens for the next program.

### 7.4 Model JSON

Output of `plcc-model`. A single JSON document — a language-neutral description of the OO class hierarchy that an emitter will realize in its target language:

- **Classes** with inheritance relationships
- **Attributes** with types described abstractly (primitive, reference, optional, list-of)
- **Constructors** with parameter lists and field bindings
- **Method slots** — named methods with parameter lists and opaque bodies
- **Semantic blocks** — opaque strings carrying target-language code from the grammar's `%%%` sections, tagged with the source language

The code model is the retargeting pivot. Every emitter consumes this format; adding a new target language means writing an emitter that reads model JSON and produces source files. The code model does not know anything about any specific target language.

### 7.5 Error Records

See §8.

## 8. Error Handling

Errors travel through the pipeline as in-band JSON records. Every JSON filter in the pipeline knows how to recognize, pass through, and (where appropriate) emit a record of the form:

```json
{ "kind": "error", "stage": "plcc-tree", "severity": "error",
  "message": "expected ';' after expression", "source": { ... } }
```

Downstream stages pass error records through unchanged unless they consume them (e.g. an interpreter renders the error to the user and resumes reading the next program). This keeps the REPL robust by construction: a single malformed program produces an error record, the interpreter prints it, and the pipeline continues serving subsequent programs. No stage restarts, no pipe teardown.

`stderr` and nonzero exit codes are reserved for **tool failures**, not input errors. A missing spec file, an internal bug, an I/O error, or a plugin-discovery failure writes to stderr and exits nonzero. A syntax error in a student's program is an in-band error record and does not affect exit status.

## 9. Build Output Layout

`plcc-make` produces all generated artifacts under a single top-level `build/` directory:

```
build/
├── spec.json         # output of plcc-spec
├── model.json        # output of plcc-model
├── Java/             # output of plcc-lang-emit for the first semantic section
│   ├── <generated .java files>
│   └── runtime/      # runtime library copied from the Java emitter plugin
├── py/               # output of plcc-lang-emit for a second semantic section
│   ├── <generated .py files>
│   └── runtime/      # runtime library copied from the Python emitter plugin
└── ...
```

Key properties:

- **Single directory to clean.** `plcc-make` always runs `rm -rf build/` before rebuilding. There is no `-c` flag in v9; clean-and-rebuild is the default and only behavior. (A future option to skip cleaning can be added if a concrete need arises.)
- **Single `.gitignore` line.** `build/` in the project's `.gitignore` excludes every generated artifact.
- **Intermediate files are visible.** `spec.json` and `model.json` live at the top of `build/` where students can `cat` them. This supports the pedagogy: the pipeline is inspectable, not magical.
- **One output subdirectory per semantic section.** Each `% <tool> <language>` divider in the grammar produces one subdirectory named `<tool>`, emitted by the plugin for `<language>`. The name is taken verbatim from the grammar; `plcc-make` does not normalize casing. A divider written as `% Java Java` produces `build/Java/`; one written as `% java Java` produces `build/java/`. Learning materials should standardize on a casing convention.
- **Generated output is disposable.** Students are expected to regenerate frequently. Source (the grammar file) is what persists; `build/` is ephemeral.

`plcc-make` phase sequence:

1. **Clean:** `rm -rf build/`
2. **Spec:** `plcc-spec grammar > build/spec.json`
3. **Model:** `plcc-model build/spec.json > build/model.json`
4. **Emit:** for each semantic section, `plcc-lang-emit --target=<lang> --output=build/<tool>/ < build/model.json`
5. **Build:** for each semantic section, `plcc-lang-build --target=<lang> --output=build/<tool>/` (silently skipped if no build command is installed for that language)

If any phase fails, `plcc-make` reports the error and stops; subsequent phases do not run.

## 10. Language Plugin System

Language plugins are discovered via PATH. A plugin is any executable named `plcc-<lang>-emit` present on the user's PATH. No entry point group, no registry, no Python packaging machinery is required beyond `pip install` placing the command on PATH.

### 10.1 Plugin Contract

A language plugin consists of one required command and one optional command:

**`plcc-<lang>-emit` (required)**

- Reads model JSON from stdin
- Accepts `--output=<dir>` (required) and `--semantics=hide|note|comment|body` (optional, default `body`)
- Writes generated source files into `<dir>`
- Copies its bundled runtime into `<dir>/runtime/`
- Exits 0 on success; exits nonzero and writes to stderr on failure
- A malformed model is a tool failure (nonzero exit), not an in-band error record

**`plcc-<lang>-build` (optional)**

- Accepts `--output=<dir>` (required)
- Compiles or prepares files already in `<dir>` (e.g. runs `javac`)
- Exits 0 on success; exits nonzero and writes to stderr on failure
- Absence from PATH means no build step for that language — not an error

The `--semantics` flag controls how semantic `%%%` blocks appear in emitted output. PlantUML and similar diagram emitters use `--semantics=note` or `--semantics=hide`; interpreter emitters use `--semantics=body`. The mechanism by which the user specifies `--semantics` (as a flag to `plcc-make` or embedded in the grammar file) is left to the Phase 1 design document.

Because the contract is stdin/stdout/exit codes, a plugin does not need to be a Python package. `pip install` is the conventional delivery mechanism, but the runtime contract has no Python dependency.

### 10.2 Plugin Package Layout

Each language plugin package bundles its own runtime library. A reference layout for a third-party plugin (e.g. `plcc-rust`):

```
plcc_rust/
├── __main__.py          # entry point for plcc-rust-emit console script
├── templates/           # generation templates (Jinja or equivalent)
└── runtime/             # copied verbatim into build/<tool>/runtime/
    └── ...              # target-language runtime files
```

Declared in `pyproject.toml` as:

```toml
[project.scripts]
plcc-rust-emit = "plcc_rust:emit_main"
```

The runtime lives inside the plugin so that:

- **Plugin authors own their runtime.** A plugin for a new language defines both the generated code shape and the base classes those generated classes inherit from. No coordination with plcc core required.
- **Output is self-contained.** A student running `cd build/py && python main.py` needs nothing beyond their target language's interpreter. No separate runtime package on PyPI, no Maven Central lookup, no crates.io.
- **One install per language.** `pip install plcc-rust` brings in emission logic, templates, and runtime in a single unit. Runtime bugs are fixed by releasing a new version of the plugin package.
- **Regeneration is cheap.** Students regenerate frequently (source is what persists, `build/` is disposable), so "runtime is copied into every rebuild" is not a cost.

### 10.3 Discovery

`plcc-lang-emit --target=<lang>` constructs the command name `plcc-<lang>-emit` and execs it as a subprocess. Discovery is PATH-based: if the command exists on PATH, the plugin is installed; if not, `plcc-lang-emit` exits nonzero with:

```text
No emitter found for '<lang>'. Is plcc-<lang>-emit installed?
Run plcc-lang-list to see what is available.
```

`plcc-lang-list` scans PATH for executables matching `plcc-*-emit`, strips the prefix and suffix, and prints one language name per line.

### 10.4 Built-in Emitters

The `plcc` core package ships with three built-in language plugins, declared as console scripts in `plcc`'s own `pyproject.toml`:

```toml
[project.scripts]
plcc-plantuml-emit = "plcc.lang.plantuml:emit_main"
plcc-python-emit   = "plcc.lang.python:emit_main"
plcc-java-emit     = "plcc.lang.java:emit_main"
plcc-java-build    = "plcc.lang.java:build_main"
```

A plain `pip install plcc` installs all three out of the box. No separate packages, no entry point groups.

Third-party plugins (`plcc-rust`, `plcc-typescript`, etc.) are published as independent PyPI packages following the naming convention `plcc-<lang>`. Installing one places `plcc-<lang>-emit` (and optionally `plcc-<lang>-build`) on PATH, making the language immediately available to `plcc-lang-emit`.

## 11. First Non-Java Target: Python

The primary proof point for the retargeting architecture in v9 is `plcc-python-emit`. Python is chosen because:

- It is the highest-leverage adoption win. Many institutions teach Python as their primary language; their faculty cannot currently adopt PLCC.
- Its dynamic typing puts pressure on the code model abstraction. A code model that survives emission to Python without Java-ism leaks is much more likely to also survive emission to TypeScript, C#, or Rust later.
- Students in most CS curricula already know some Python, so the emitted interpreter is immediately readable to them.

`plcc-python-emit` must round-trip through the `languages` test repository (§13) in both its emitted code and its embedded runtime.

## 12. Distribution and Packaging

PLCC v9 is distributed through PyPI as `plcc`. All Level 0 primitives and Level 2 commands are console-script entry points declared in `pyproject.toml`. Installing the package provides every command on the user's `PATH`.

```
pip install plcc
```

Cross-platform by construction. No shell scripts, no environment variable setup, no OS-specific installers. The command a student or instructor runs to get a working PLCC is the same on Windows, macOS, and Linux.

Third-party language plugins are separate PyPI packages following the naming convention `plcc-<lang>`. Installing one places `plcc-<lang>-emit` (and optionally `plcc-<lang>-build`) on PATH.

```sh
pip install plcc plcc-rust
```

This distribution model replaces the v8 model, which required cloning the repo and configuring environment variables — an adoption barrier that disproportionately affects students on Windows and instructors supporting multiple operating systems.

## 13. Backwards Compatibility

v9 provides **semantic backwards compatibility** for v8 grammar files, not bit-exact compatibility. A grammar file written against v8 passed to v9's `plcc-make` produces a working Java interpreter with the same runtime behavior. Generated class names, method signatures, and file layout may differ from v8's output; faculty tests of student programs continue to pass; faculty who inspected generated Java source may see differences.

### The `languages` test oracle

Backwards compatibility is not an aspiration in v9. It is a runnable, concrete signal. The `languages` repository contains the example languages referenced in PLCC's learning materials, along with tests that verify each language can be parsed by PLCC, have Java code generated, compiled, and run against example programs.

**v9 is considered backwards compatible when the full `languages` test suite passes against it.**

This test suite becomes part of v9's acceptance criteria. It runs in CI throughout development to catch regressions early rather than at the end. The Java language plugin (`plcc-java-emit`) is designed and tested against this suite.

The suite is not comprehensive — its coverage of runtime behavior is shallow — but it is concrete, already written, and exercises the full pipeline end to end against realistic grammars.

## 14. Revisions to Prior Brainstorming Decisions

This spec adjusts three decisions from earlier brainstorming sessions in light of the PyPI distribution commitment:

- **Decision #6** (originally: "Layer 2 commands compose Layer 0 primitives via shell scripts") is revised: Layer 2 commands are Python modules that orchestrate Layer 0 primitives using `subprocess.Popen`. Rationale: shell scripts do not work as pip entry points and break cross-platform installation on Windows.
- **Decision #11** (originally: `plcc-repl` as a Level 0 primitive that concatenates files and stdin with optional prompting) is revised: the input-assembly tool is eliminated. Layer 2 orchestrators open files with `pathlib` and read stdin with `sys.stdin`, writing bytes directly into the first subprocess's stdin pipe. Prompt logic consolidates in Layer 2 where tty detection already lives. Rationale: a Python-orchestrated pipeline does not need a dedicated input-assembly primitive; the job is trivial Python code.
- **Decision #12** (Layer 2 scripts detect tty and pass `--prompt` to both `plcc-repl` and the last pipeline stage) is simplified: Layer 2 orchestrators handle all prompting directly, since there is no longer a `plcc-repl` primitive to pass flags to.

These revisions preserve the spirit of the original decisions (single-responsibility primitives, honest Unix composition, responsive interactive mode) while removing machinery that existed only to work around limitations the new distribution model eliminates.

## 15. Deferred and Out of Scope

- **Pluggable verifiers.** Future extension; no work in v9.
- **Pluggable scanners and parsers.** The Level 0 primitives `plcc-tokens` and `plcc-tree` remain the only implementations in v9.
- **Level 1 intermediate compositions.** Deferred until a pedagogical use case emerges.
- **Non-OO target languages.** Retargeting in v9 is limited to modern OO languages.
- **Exact JSON schemas.** This spec establishes contracts and error-record discipline; schema details are the implementation plan's responsibility.
- **Migration of existing PLCC users to v9 on a timeline.** The cutover strategy supports parallel operation; the decision of when individual faculty migrate is their own.
- **Integration of plcc-ng into the plcc repository.** Deferred until v9 is complete and has demonstrated buy-in. Development of v9 happens entirely within the plcc-ng repository.

## 16. Open Risks

- **Code model generality.** The code model is the retargeting pivot. If it accidentally encodes Java-isms, emission to Python will surface them, but late-discovered abstraction leaks could require rework of every emitter. Mitigation: emit to Python as early in the implementation plan as possible, before investing in the Java emitter's polish.
- **Runtime library drift across languages.** Each emitter plugin owns its runtime, so different languages' interpreters can drift in behavior. Mitigation: the `languages` test suite exercises Java runtime behavior; a parallel language-agnostic test suite should exercise Python runtime behavior as the Python emitter matures.
- **plcc-ng code that does not fit the pipeline shape.** plcc-ng's 282 commits include spec parsing and a scanner, but its internal structure shares dataclasses across package boundaries. Re-homing that code into Level 0 primitives with JSON contracts may reveal coupling that requires restructuring, not just relocation. Mitigation: the implementation plan begins with extracting `plcc-spec` as a standalone primitive to surface these issues early.
- **Learning materials lag.** Learning materials need to be updated to match v9's commands and behavior before v9 can be widely adopted. Mitigation: name a specific maintainer responsible for the learning materials update, with a review checkpoint after the Python emitter lands.

## 17. Architectural Amendments

### 17.1 Amends §10.4: Built-in emitter packaging (from roadmap review, 2026-04-12)

**Original §10.4** described the three built-in emitters as "installed as dependencies" of the `plcc` core package, implying separate PyPI packages (`plcc-emit-java`, `plcc-emit-python`, `plcc-emit-plantuml`).

**Amendment:** superseded by §17.2. The built-in emitters are bundled inside the `plcc` package and exposed as console scripts, not as entry point group members. See §17.2 for the full decision.

### 17.2 Amends §10: Language plugin command contract (from brainstorming, 2026-04-12)

**Original §10** defined the plugin contract as Python callables (`emit()`, `build()`), discovered via `importlib.metadata` entry points under a `plcc.emitters` group.

**Amendment:** the plugin contract is redefined as CLI commands. `§10` has been rewritten in place to reflect this. The key decisions:

- The plugin obligation is to provide `plcc-<lang>-emit` on PATH (required) and optionally `plcc-<lang>-build`.
- Discovery is PATH-based: `plcc-lang-emit --target=<lang>` constructs `plcc-<lang>-emit` and execs it. No entry point group, no registry.
- `plcc-emit` is retired. The dispatchers are `plcc-lang-emit`, `plcc-lang-build`, and `plcc-lang-list`.
- Built-in plugins are console scripts declared in `plcc`'s `pyproject.toml` (§10.4). The `plcc.emitters` entry point group is eliminated entirely.
- Third-party plugins follow the naming convention `plcc-<lang>` (package) / `plcc-<lang>-emit` (command).

**Rationale:** the callable contract ran plugin code inside `plcc-emit`'s own process, collapsing the boundary the pipeline architecture was designed to enforce. Commands run in isolated subprocesses, honour the same stdin/stdout/exit-code contract as every other Level 0 primitive, and do not require plugins to be Python packages.

### 17.3 Amends §5, §7.3: `plcc-tree` is one-shot, not long-running (from Phase 2 Part 1 brainstorm, 2026-04-15)

**Original §5** and **§7.3** describe `plcc-tree` as a long-running stage that "emits one tree line and resumes reading tokens for the next program." That framing conflated pipeline-stage lifetime with session lifetime.

**Amendment.** `plcc-tree` is a **one-shot** stage. It reads token JSONL on stdin until EOF, parses exactly one program, emits the resulting parse tree as a single newline-terminated JSON document on stdout, and exits. There is no long-running mode and no multi-program mode. Batch use parses multiple programs by spawning `plcc-tree` per program.

The "single newline-terminated JSON document" framing is deliberately also a valid one-line JSONL stream: the same bytes compose cleanly with downstream consumers that expect JSONL (notably the long-lived interpreter under §17.7, which reads a stream of trees over the course of a session). No adapter is needed between `plcc-tree`'s output and the interpreter's input — the orchestrator simply pipes one into the other.

Session-scope lifetime moves to the interpreter (§17.7). `plcc-rep` (and other Level 2 orchestrators) spawn fresh `plcc-tokens` and `plcc-tree` subprocesses per input chunk and pipe their combined output into the long-lived interpreter's stdin.

**Rationale.** State lives in the interpreter — loaded libraries, definitions, runtime environment. Stages that hold no state are simpler as stateless one-shots spawned per input chunk than as long-running processes coordinating program-boundary framing with an upstream streaming tokenizer. Fork/exec cost for `plcc-tokens` and `plcc-tree` is imperceptible in interactive use and a one-time cost in batch use. The simplification applies to `plcc-tree`'s implementation, the test matrix, and the output framing: there is exactly one mode, not a one-shot mode for build time and a long-running mode for REPL time, and there is exactly one tree per invocation rather than a stream of trees from a stream of programs.

The one-shot stdin/stdout/EOF I/O contract described here is inherited by any parser plugin dispatched from `plcc-tree` under §17.6: every `plcc-parser-<kind>` reads token JSONL until EOF, parses one program, and emits one parse tree as a newline-terminated JSON document. There is no long-running parser-plugin mode and no multi-tree-per-invocation mode.

#### Revised §5 row for `plcc-tree`

| Command | Input | Output | Role |
| --- | --- | --- | --- |
| `plcc-tree` | token JSONL (stdin), `--ll1 <path>` (required), `--parser=<kind>` (optional, default `table`) | parse tree as a single newline-terminated JSON document (stdout) | One-shot dispatcher (§17.6). Reads token JSONL to EOF, execs `plcc-parser-<kind>` forwarding `--ll1`, exits when the dispatched plugin exits. One parse tree per invocation. No long-running mode, no multi-program mode. Output is also a valid one-line JSONL stream so it composes directly with the long-lived interpreter under §17.7. |

#### Revised §7.3

> `plcc-tree` is a one-shot pipeline stage. It reads token JSONL on stdin until EOF, parses one program, and emits that parse tree as a single newline-terminated JSON document. It does not stay resident across programs, and it does not parse multiple programs per invocation; session-scope lifetime is held by the interpreter (§17.7), and orchestrators spawn fresh `plcc-tokens | plcc-tree` subpipelines per input chunk. Because `plcc-tree`'s output is also a valid one-line JSONL stream, it composes directly with the interpreter's JSONL stdin without an adapter.

### 17.4 Amends §5, §9: Introduce `plcc-ll1` primitive for LL(1) analysis (from Phase 2 Part 1 brainstorm, 2026-04-15)

**Original §5** lists `plcc-spec` as the stage that parses a grammar file and emits spec JSON, and folds LL(1) validation into `plcc-spec` implicitly (the plcc-ng implementation computes FIRST sets, FOLLOW sets, the parse table, and conflict reports inside `plcc-spec`, then discards them).

**Amendment.** A new Level 0 primitive, `plcc-ll1`, is introduced between `plcc-spec` and `plcc-tree` / `plcc-model`. Its contract:

| Command | Input | Output | Role |
|---|---|---|---|
| `plcc-ll1` | spec JSON (stdin or path) | LL(1) analysis JSON (stdout) | Perform LL(1) analysis on the grammar: compute FIRST, FOLLOW, and predict sets; build the parsing table; detect conflicts and left-recursion cycles. One-shot; single JSON document. Nonzero exit on non-LL(1) grammars with the diagnostic artifact still written to stdout so students can inspect the failure — a deliberate exception to the usual "nonzero exit means stdout is undefined" rule, justified by the pedagogical value of the diagnostic. |

The emitted analysis JSON contains: FIRST sets, FOLLOW sets, predict sets, parse table, conflicts (empty on success), left-recursion report (empty on success), and a `human` rendering mode available via `--format=human` on the command (exact schema is a phase-design-doc decision).

**`plcc-spec` stops running LL(1) validation.** It becomes what its name already suggests: a faithful translation of the `.plcc` grammar file into JSON, suitable as input for many tools — the LL(1) validator (now `plcc-ll1`), linters, pretty-printers, optimizers. Analysis moves downstream where it belongs.

**`plcc-tree`** (per §17.6, a dispatcher over `plcc-parser-<kind>` plugins) requires a `--ll1 <path>` flag and forwards it to the dispatched parser plugin. The built-in `plcc-parser-table` consumes `ll1.json` directly and does not recompute FIRST/FOLLOW/etc. at runtime. Other parser plugins are free to use `ll1.json` as they see fit.

**`plcc-make`** phase sequence gains a stage:

1. Clean: `rm -rf build/`
2. Spec: `plcc-spec grammar.plcc > build/spec.json`
3. **LL(1): `plcc-ll1 build/spec.json > build/ll1.json`**
4. Model: `plcc-model build/spec.json > build/model.json`
5. Emit: for each semantic section, `plcc-lang-emit …`
6. Build: for each semantic section, `plcc-lang-build …`

If `plcc-ll1` exits nonzero (the grammar is not LL(1)), `plcc-make` stops after step 3 and surfaces the diagnostic artifact.

**Rationale.** LL(1) analysis is a derived artifact, not a translation of the grammar file, so embedding it in `spec.json` would violate the philosophy that `spec.json` is a faithful parse tree of the `.plcc` file. Extracting the analysis into its own stage (a) preserves that philosophy, (b) exposes the analysis data as a first-class pedagogical artifact (the very thing PLCC exists to teach), (c) gives downstream consumers — `plcc-tree` today, future parse-tree-generator generators tomorrow — a stable JSON contract to consume, (d) factors the one-JSON-stage-per-responsibility architecture honestly. The data is already computed inside plcc-ng's existing validator; this amendment surfaces it rather than discarding it.

**Pedagogical diagnostics in scope from day one.** FIRST, FOLLOW, predict, parse table, conflicts, and the left-recursion cycle report are all first-class outputs of `plcc-ll1`, not deferred features. Left-factoring candidate detection is deferred to a later phase because it requires new logic beyond what the validator currently computes.

**`plcc-model` is unchanged.** It still consumes `spec.json` only and does not depend on `ll1.json`. Model construction is a translation of the spec into the canonical model representation; LL(1) analysis is a separate concern that flows to `plcc-tree` / parser plugins, not to `plcc-model`.

#### Revised §5 rows

| Command | Input | Output | Role |
| --- | --- | --- | --- |
| `plcc-spec` | `.plcc` grammar file (path or stdin) | spec JSON (stdout) | Faithful translation of the grammar file into JSON. **Does not** perform LL(1) analysis. One-shot; single JSON document. |
| `plcc-ll1` | spec JSON (stdin or path) | LL(1) analysis JSON (stdout) | New in §17.4. Compute FIRST/FOLLOW/predict, build parse table, detect conflicts and left-recursion. One-shot; single JSON document. Nonzero exit on non-LL(1) grammars; diagnostic artifact still written. |

### 17.5 Amends §9, §10, §11: Generated components are pipeline stages (from Phase 2 Part 1 brainstorm, 2026-04-15)

**Original §9** shows `cd build/py && python main.py < program.txt` as a way to invoke the generated Python interpreter against raw source. **Original §10.1** describes the emitter plugin as producing generated source files plus a bundled runtime, with the implication (reinforced by §11) that the generated artifact is a standalone interpreter containing its own tokenizer, parser, and evaluator.

**Amendment.** Every generated component is a **pipeline stage** that communicates via JSON on stdin/stdout, not a standalone program. Specifically:

- A **generated interpreter** reads parse-tree JSONL on stdin, deserializes each tree into an object tree whose classes are the ones generated from the grammar, calls the root entry-point method (exact name TBD; see note below), and writes evaluation output (format TBD) on stdout. **It has no scanner and no parser.** To deserialize trees, it uses whatever off-the-shelf JSON library ships with its target language.
- A **generated parse-tree-generator** (future, via parser pluggability in §17.6) reads token JSONL on stdin, deserializes each token, runs its parsing algorithm, and emits parse-tree JSONL on stdout. **It has no scanner.** To deserialize tokens, it uses its target language's JSON library.
- A **generated tokenizer** is out of scope in v9 (§17.6 narrows §2's pluggability non-goal to leave scanners non-pluggable).

**Consequences for §9.** `cd build/py && python main.py < program.txt` no longer works on raw source. To invoke a generated interpreter standalone, a student must compose the upstream stages:

```sh
plcc-tokens --spec build/spec.json < program.txt \
  | plcc-tree --ll1 build/ll1.json \
  | python build/py/main.py
```

`plcc-rep` automates this orchestration and is the primary way students interact with generated interpreters.

**Consequences for §10.1.** The "bundled runtime" a language plugin copies into `<dir>/runtime/` is narrowed to: (a) base classes for the generated grammar classes, (b) JSON deserialization helpers for parse trees (and for tokens, if the plugin also emits a parse-tree-generator), (c) the entry-point orchestration that invokes the root method on each deserialized tree, (d) error-record rendering support per §8. It **does not** include a parser or a scanner. This is a simpler, narrower runtime than §10.1 originally implied.

#### Revised §10.1 runtime contents

> The runtime bundled by a language plugin into `<dir>/runtime/` consists of:
>
> 1. Base classes for the generated grammar classes (one base per nonterminal kind, plus token base classes).
> 2. Parse-tree JSON deserialization helpers that reconstruct an object tree from parse-tree JSONL on stdin.
> 3. Optional token JSON deserialization helpers, included only if the plugin also emits a parse-tree-generator.
> 4. An entry-point harness that reads parse-tree JSONL from stdin, deserializes one tree per line, calls the root entry-point method on each, and writes evaluation records to stdout.
> 5. Error-record rendering helpers per §8.
>
> The runtime explicitly does **not** include a tokenizer, a parser, or any code for reading raw program source. Generated components are pipeline stages and rely on upstream stages for tokenization and parsing.

**Consequences for §11.** The Python emitter proof point stated in §11 still stands, but "round-trip through the `languages` test repository" now means "the generated Python interpreter pipeline stage correctly evaluates parse trees the upstream pipeline produces," not "the generated Python interpreter runs programs end-to-end standalone."

**Entry-point method name.** `$run()` (the name used by v8) is not portable: Python, C#, Rust, Go, and Swift all reject `$` in identifiers. The portable name is deferred to the Phase 2 Part 2 brainstorm, which is the first phase that emits an interpreter and thus has to commit to a name.

**Rationale.** Treating generated components as pipeline stages (rather than monolithic standalone programs) eliminates a two-layer mental model where the "parser inside `plcc-rep`" and the "parser inside the generated interpreter" appear to be different things. Under the pipeline-stage framing, there is one parse-tree-generator in use at a time, and it serves both the interactive Level 2 commands and the composition used when invoking generated interpreters. Students see one pipeline and one JSON contract. The generated artifact's responsibility narrows to "take trees, run trees," which is the pedagogical essence of an interpreter and eliminates the need for every emitter to independently reinvent tokenization and parsing in its target language.

### 17.6 Amends §2, §5, §10, §15: Parsers are pluggable (from Phase 2 Part 1 brainstorm, 2026-04-15)

**Original §2** lists "Pluggable scanners, parsers, or verifiers" among the v9 non-goals: "Only emitters are pluggable in v9."

**Amendment.** The non-goal is narrowed. **Parsers (parse-tree-generators) are pluggable in v9.** Scanners and verifiers remain non-pluggable for v9.

### 17.6.1 Revised §2 non-goal

> Pluggable scanners and verifiers. Scanners and verifiers remain non-pluggable in v9. Parsers (parse-tree-generators) are pluggable; see §17.6 for the plugin contract.

### 17.6.2 Plugin contract

Parser plugins follow the same PATH-based discovery mechanism as language plugins (§17.2). A parser plugin is any executable named `plcc-parser-<kind>` on PATH whose contract is:

- Reads token JSONL on stdin
- Accepts `--ll1 <path>` (required)
- Emits parse-tree JSONL on stdout
- Exits 0 on success; exits nonzero and writes to stderr on tool failure
- Syntax errors in the token stream are in-band error records (§8), not tool failures
- Error-recovery strategy (panic-mode, phrase-level, etc.) is plugin-defined and not constrained by this contract; the Part 1 design doc commits `plcc-parser-table` to a specific strategy

Symmetry with §10 / §17.2: same stdin/stdout/exit-code shape as every other Level 0 primitive; PATH-based discovery; language-agnostic (a parser plugin need not be a Python package).

### 17.6.3 Dispatcher

`plcc-tree` becomes a dispatcher. Its contract:

- Accepts `--parser=<kind>` (optional, default `table`)
- Accepts `--ll1 <path>` (required)
- Reads token JSONL on stdin
- Constructs `plcc-parser-<kind>` and execs it, forwarding `--ll1` and wiring stdin/stdout through
- If `plcc-parser-<kind>` is not found on PATH, exits nonzero with a message naming the missing command and pointing at `plcc-parser-list`

### 17.6.4 Built-in parser

The `plcc` package declares one built-in parser plugin in its `pyproject.toml`:

```toml
[project.scripts]
plcc-parser-table = "plcc.parser.table:main"
```

`plcc-parser-table` is the table-driven LL(1) parser that consumes `ll1.json` and produces parse-tree JSONL. It is the Phase 2 Part 1 deliverable. A plain `pip install plcc` makes it available and makes `plcc-tree --parser=table` (the default) work out of the box.

### 17.6.5 `plcc-parser-list`

Symmetric with `plcc-lang-list`. Walks PATH, collects executables matching `plcc-parser-*`, strips prefix/suffix, prints parser kind names one per line.

### 17.6.6 Recursive-descent parser generation (forward-looking)

A future Level 0 stage, working name `plcc-gen-parser` (named outside the `plcc-parser-*` glob to avoid being mistaken for a parser plugin by `plcc-tree` or `plcc-parser-list`), will generate parser source code in a target language from `ll1.json`. A built-in invocation always generates Python source, producing a parser plugin that can be installed alongside `plcc-parser-table` and selected via `--parser=`. Language plugins may optionally provide their own target-language parser generators (e.g. a Java parser generator emitted into `build/Java/`). The generated parser is itself a pipeline-stage parse-tree-generator under §17.5: token JSONL in, parse-tree JSONL out, no scanner. Recursive-descent generation is **not** Part 1 scope; the Part 1 design doc describes the intended shape as a forward-looking note so the later phase slides in without reshaping.

### 17.6.7 Level 2 passthroughs

`plcc-rep`, `plcc-scan`, `plcc-parse`, and `plcc-make` grow a `--parser=<kind>` flag that plumbs through to `plcc-tree`. The default is `table` everywhere. Part 1 ships only `plcc-parser-table` and `plcc-tree`'s dispatcher; the Level 2 passthroughs land in Part 2 and Phase 4.

### 17.6.8 Rationale

The one-role-per-stage reframing in §17.5 makes parser pluggability a natural fit rather than a carve-out. Under §17.5, the parse-tree-generator is already one pipeline stage regardless of whether it is the built-in Python table-driven parser, a generated Python recursive-descent parser, or a parser generated in a different target language — every variant reads token JSONL and emits parse-tree JSONL. The question is only how that stage is discovered and dispatched. PATH-based discovery (§17.2's pattern) is the cleanest answer: it reuses infrastructure Phase 1 has already built, composes with `pip install`, and matches the Unix-idiomatic pattern the architecture already uses for language plugins.

PLCC's pedagogical context is programming languages courses, in which parser implementation strategies are part of the curriculum even when parsers are not student-written. Making parse-tree-generators visibly pluggable lets faculty show students a table-driven parser, a recursive-descent parser, and any other strategy side-by-side against the same grammar — the same pluggability axis that makes language-level retargeting work. Scanner and verifier pluggability remain out of scope because (a) lexical analysis in PLCC's context is a DFA-driven data problem rather than an algorithmic variation, (b) verifiers in v9 consist of exactly one implementation (`plcc-ll1` from §17.4) and pluggability is meaningless without multiple implementations. These constraints may loosen post-v9.

### 17.6.9 §15 update

The "Pluggable scanners and parsers" bullet in §15 is narrowed: pluggable scanners remain deferred; pluggable parsers are introduced in v9 per this amendment.

### 17.7 Amends §9: Interpreters are long-lived, `plcc-tokens` and `plcc-tree` are spawned per chunk (from Phase 2 Part 1 brainstorm, 2026-04-15)

**Original §9** does not explicitly describe the lifetime of pipeline subprocesses inside a `plcc-rep` session.

**Amendment.** In any session-scoped Level 2 command that includes an interpreter (primarily `plcc-rep`):

- The **interpreter** subprocess is **long-lived** for the duration of the session. It accepts parse-tree JSONL on stdin continuously, evaluates each tree as it arrives, and emits one evaluation record (also JSONL) per tree on stdout. The framing is line-delimited JSON in both directions, matching every other stdin/stdout contract in the pipeline; no out-of-band delimiter is needed.
- `plcc-tokens` and `plcc-tree` (and any parser plugin dispatched from `plcc-tree`) are **one-shot per input chunk**. For each input chunk — a library file, the main program file, or an interactive REPL entry — the orchestrator spawns a fresh `plcc-tokens | plcc-tree` subpipeline, feeds the chunk through, reads the resulting parse-tree JSONL, and pipes it into the long-lived interpreter's stdin. Then the orchestrator waits for the interpreter's evaluation output before accepting the next chunk.
- One evaluation record per parse tree. The exact schema of evaluation records (including how they represent printed output, errors, and multiple results per program) is a Phase 2 Part 2 design-doc decision.

`plcc-rep` invocation forms, already described in §6, compose cleanly under this model:

- `plcc-rep grammar.plcc` — interactive; prompts, reads chunks from tty, evaluates each.
- `plcc-rep grammar.plcc < program.txt` — batch; feeds the file as a single chunk.
- `plcc-rep grammar.plcc lib1.txt lib2.txt` — loads libraries as sequential chunks into the interpreter, then enters interactive mode. State from the libraries is visible to subsequent chunks because the interpreter is long-lived.
- `plcc-rep grammar.plcc lib1.txt lib2.txt < program.txt` — loads libraries, then runs program.txt as the final chunk, then exits.

**Rationale.** Only stages that hold state need to be long-lived. The interpreter holds state (loaded library definitions, runtime environment) and therefore must persist for the duration of the session. `plcc-tokens` and `plcc-tree` hold no state; spawning them per chunk is simpler than coordinating program-boundary framing across long-running streaming stages. The fork/exec/JSON-load cost per chunk is imperceptible in interactive use and negligible in batch use.
