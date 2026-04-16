# Skeleton Update Design: Reflecting Architectural Amendments §17.3–§17.8

**Date:** 2026-04-16
**Status:** Draft — pending review
**Companion:** [2026-04-12-multi-lang-pipeline.md](2026-04-12-multi-lang-pipeline.md) (especially §17.3–§17.8)
**Phase 2 Part 1 draft:** [2026-04-16-phase-2-part-1-ll1-parser-design.md](2026-04-16-phase-2-part-1-ll1-parser-design.md)
**Phase 1 design:** [2026-04-13-phase-1-walking-skeleton.md](2026-04-13-phase-1-walking-skeleton.md)

## 1. Goal and Scope

Update the Phase 1 walking skeleton so that its command surface, wiring, and propagation rules reflect architectural amendments §17.3–§17.8. Every command exists, connects to its neighbors, accepts `--verbose`/`--verbose-format`, and propagates them correctly. All commands produce minimal output — just enough to prove the pipeline is connected. Real functionality is added in later phases.

### What changes

- **4 new Level 0 commands** (leaf stubs): `plcc-ll1`, `plcc-parser-table`, `plcc-parser-list`, `plcc-lang-run`
- **5 new language plugin commands** (leaf stubs): `plcc-python-emit`, `plcc-python-run`, `plcc-java-emit`, `plcc-java-build`, `plcc-java-run`
- **1 rewritten command**: `plcc-tree` becomes a dispatcher (§17.6)
- **1 extended command**: `plcc-make` gains the `plcc-ll1` step (§17.4)
- **3 commands promoted from stubs to connected skeletons**: `plcc-scan`, `plcc-parse`, `plcc-rep`
- **All commands** gain `--verbose`/`--verbose-format` acceptance and propagation
- **1 new shared module**: `plcc.verbose` (verbose infrastructure)
- **New console scripts** in `pyproject.toml`
- **Updated tests** across all BATS tiers
- **New test fixtures** for Java and Python semantic sections

### What does NOT change

- `plcc-spec` keeps its LL(1) validation for now. Removing it is Phase 2 Part 1 work, done when `plcc-ll1` gets real implementation (see §7.2).
- No new functionality beyond wiring. `plcc-ll1` emits a stub JSON, `plcc-parser-table` passes tokens through as a minimal tree, etc.
- No new JSON schemas beyond what is needed for `ll1.json`.

### Walking skeleton principle

Stubs should only exist at leaf components — components that do not call other components. Non-leaf components must be connected skeletons that actually call their children, even if the children produce minimal output. A "stub" that does not call its children is not part of the skeleton; it is a disconnected bone.

## 2. New and Changed Commands

### 2.1 New Level 0 primitives (leaf stubs)

| Command | Module | Input | Output (stub) |
|---|---|---|---|
| `plcc-ll1` | `plcc.ll1.ll1_cli` | spec JSON (stdin or path), `--format=human` (no-op in skeleton) | Minimal ll1.json with empty FIRST/FOLLOW/predict sets, empty parse table, empty conflicts, empty left-recursion report |
| `plcc-parser-table` | `plcc.parser.table_cli` | token JSONL (stdin), `--ll1 <path>` | Minimal tree wrapping tokens (the Phase 1 `plcc-tree` pass-through logic moves here) |
| `plcc-parser-list` | `plcc.parser.list_cli` | (none) | Parser kind names, one per line. Scans PATH for `plcc-parser-*`, symmetric with `plcc-lang-list`. |

### 2.2 New language plugin commands (leaf stubs)

| Command | Module | Stub behavior |
|---|---|---|
| `plcc-python-emit` | `plcc.lang.ext.python.emit` | Generates a minimal `main.py` into `--output=<dir>` that reads parse-tree JSONL on stdin and prints a minimal evaluation line per tree |
| `plcc-python-run` | `plcc.lang.ext.python.run` | Execs `python <dir>/main.py`, forwarding stdin/stdout and `--verbose`/`--verbose-format` |
| `plcc-java-emit` | `plcc.lang.ext.java.emit` | Generates a minimal `Main.java` into `--output=<dir>` with the same stdin-to-stdout contract |
| `plcc-java-build` | `plcc.lang.ext.java.build` | Runs `javac` on the generated source in `--output=<dir>` |
| `plcc-java-run` | `plcc.lang.ext.java.run` | Execs `java -cp <dir> Main`, forwarding stdin/stdout and `--verbose`/`--verbose-format` |

All language plugin commands accept `--verbose`/`--verbose-format` per §17.8.10. Generated stub interpreters (`main.py`, `Main.java`) also accept both flags.

### 2.3 New dispatcher

| Command | Module | Behavior |
|---|---|---|
| `plcc-lang-run` | `plcc.lang.run` | Constructs `plcc-<lang>-run`, execs it. Exits 0 (no-op) if command not on PATH. Forwards `--output`, `--verbose`, `--verbose-format`. |

This follows the established dispatcher no-op pattern used by `plcc-lang-build`: if `plcc-<lang>-run` is not found on PATH, the dispatcher exits 0 silently. Plugins only ship the commands they need. PlantUML does not ship a run command; the dispatcher handles this as a no-op.

### 2.4 Changed commands (connected)

| Command | Change |
|---|---|
| `plcc-tree` | Rewritten from pass-through to dispatcher. Accepts `--parser=<kind>` (default `table`), `--ll1 <path>`. Constructs `plcc-parser-<kind>`, execs it, forwards `--ll1`, `--verbose`, `--verbose-format`. |
| `plcc-make` | Gains `plcc-ll1` step between spec and model (step 3 in the amended §17.4 sequence). Level 2 verbose propagation to all children. |
| `plcc-scan` | Promoted from stub to connected skeleton. Runs `plcc-spec` then pipes source through `plcc-tokens`, prints tokens in human-readable format. Level 2 verbose propagation. |
| `plcc-parse` | Promoted from stub to connected skeleton. Runs `plcc-spec` → `plcc-ll1` → `plcc-tokens | plcc-tree`, prints tree in human-readable format. Level 2 verbose propagation. |
| `plcc-rep` | Promoted from stub to connected skeleton. Runs `plcc-spec` → `plcc-ll1` → `plcc-tokens | plcc-tree | plcc-lang-run`. Accepts `--tool=<name>` (default `Java`). Resolves tool name to language via spec.json semantics array. Level 2 verbose propagation. |

### 2.5 `plcc-rep --tool` semantics

`plcc-rep` accepts `--tool=<name>` to select which semantic section's interpreter to run. The tool name is the unique identifier across semantic sections in the grammar.

- If `--tool` is provided, look up the matching semantic section in spec.json.
- If `--tool` is not provided, default to `Java` (backwards compatibility with v8).

The grammar divider format is `% <tool> <language>`. When the divider omits the tool name, it defaults to the language name. For example, `% Java` means tool=Java, language=Java. `% diagram PlantUML` means tool=diagram, language=PlantUML.

### 2.6 New console scripts in `pyproject.toml`

```toml
plcc-ll1            = "plcc.ll1.ll1_cli:main"
plcc-parser-table   = "plcc.parser.table_cli:main"
plcc-parser-list    = "plcc.parser.list_cli:main"
plcc-lang-run       = "plcc.lang.run:main"
plcc-python-emit    = "plcc.lang.ext.python.emit:main"
plcc-python-run     = "plcc.lang.ext.python.run:main"
plcc-java-emit      = "plcc.lang.ext.java.emit:main"
plcc-java-build     = "plcc.lang.ext.java.build:main"
plcc-java-run       = "plcc.lang.ext.java.run:main"
```

### 2.7 Revised `plcc-make` phase sequence

1. Clean: `rm -rf build/`
2. Spec: `plcc-spec grammar.plcc > build/spec.json`
3. **LL(1): `plcc-ll1 build/spec.json > build/ll1.json`** (new)
4. Model: `plcc-model build/spec.json > build/model.json`
5. Emit: for each semantic section, `plcc-lang-emit --target=<lang> --output=build/<tool>/`
6. Build: for each semantic section, `plcc-lang-build --target=<lang> --output=build/<tool>/`

If `plcc-ll1` exits nonzero, `plcc-make` stops after step 3 and surfaces the diagnostic artifact.

### 2.8 Noted deviation

`plcc-spec` keeps its LL(1) validation even though §17.4 says it should stop. The skeleton's `plcc-ll1` is a stub that does not actually validate. When `plcc-ll1` gets real implementation (Phase 2 Part 1), validation is removed from `plcc-spec` at the same time.

## 3. Verbose Infrastructure (`plcc.verbose`)

### 3.1 Module location

`src/plcc/verbose.py` — a single module, not a package. Shared infrastructure used by every command.

### 3.2 `VerboseContext` API

The primary object. Created once per command invocation, used throughout.

```python
class VerboseContext:
    def __init__(self, stage, events_enum, level=0, fmt="text"):
        """
        stage: executable name (e.g. "plcc-ll1")
        events_enum: the command's Events enum class (stored for parity testing)
        level: verbosity level 0-3
        fmt: "text" or "json"
        """

    @classmethod
    def from_args(cls, stage, events_enum, args):
        """Construct from parsed docopt args dict."""

    def emit(self, event, level=1, **payload):
        """
        Emit a verbose event if current level >= requested level.
        event: member of the command's Events enum.
        payload: arbitrary key-value pairs (always includes 'message').
        Renders as text or JSON per self.fmt. Writes to stderr.
        """

    def child_flags(self):
        """Level 0 / dispatchers: return ['--verbose=N', '--verbose-format=F'] unchanged."""

    def child_flags_for_orchestrator(self, min_level=None):
        """Level 2: return ['--verbose=max(N, min_level)', '--verbose-format=json']."""

    def parse_child_events(self, stderr_bytes):
        """Parse JSONL lines from a child's captured stderr. Returns list of dicts."""

    def reformat_child_events(self, events):
        """Re-emit parsed child events in user's requested format on stderr."""
```

### 3.3 Docopt fragment

A string constant for commands to include in their docstring:

```python
VERBOSE_OPTIONS = """
    -v --verbose=LEVEL      Verbosity level 0-3 [default: 0].
    --verbose-format=FMT    Output format: text or json [default: text].
"""
```

### 3.4 Per-command event enums

Each command defines its own `Events` enum. Values are stable event-kind identifiers used in JSON records (§17.8.5). For skeleton stubs that have nothing to say, the enum has just `STARTED` and `FINISHED`:

```python
import enum

class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"
```

The enum is passed to `VerboseContext` at construction. This enables mechanical parity testing: iterate the enum, assert both renderers handle every member.

### 3.5 Rendering

Two renderers, both built into `VerboseContext`:

- **Text** (§17.8.4): `plcc-ll1: started: reading spec.json` — stage-name prefix, present tense, one event per line, line-atomic writes to stderr.
- **JSON** (§17.8.5): `{"stage": "plcc-ll1", "time": 123456789, "event": "started", "message": "reading spec.json"}` — JSONL on stderr, monotonic nanosecond timestamp, stable event kind.

Both renderers handle every event identically for now (stage prefix + event + message). See §7.1 for the escalation path to per-command custom renderers.

### 3.6 Propagation rules

Encoded in two methods, matching §17.8.3:

- **`child_flags()`** — Level 0 stages and dispatchers. Returns both flags unchanged. Used by `plcc-tree`, `plcc-lang-emit`, `plcc-lang-build`, `plcc-lang-run`, and all plugin commands that spawn subprocesses.
- **`child_flags_for_orchestrator(min_level=N)`** — Level 2 orchestrators. Forces `--verbose-format=json` on children. Sets verbosity to `max(user_level, min_level)`. Used by `plcc-make`, `plcc-scan`, `plcc-parse`, `plcc-rep`.

### 3.7 Level 2 stderr capture

Level 2 orchestrators spawn children with `subprocess.Popen(stderr=PIPE)`, read captured JSONL, call `parse_child_events()` to deserialize, then `reformat_child_events()` to re-emit in the user's requested format. This is a naive pass-through reformat in the skeleton — events are re-rendered one-for-one. Future phases may aggregate, filter, or restructure child events into higher-level summaries.

### 3.8 Usage pattern for a typical command

```python
"""plcc-ll1
    Perform LL(1) analysis on a grammar spec.

Usage:
    plcc-ll1 [options] [SPEC_JSON]

Arguments:
    SPEC_JSON   Path to spec JSON file. Use - or omit to read from stdin.

Options:
    --format=FMT    Output format: json or human [default: json].
    -h --help       Show this message.
""" + VERBOSE_OPTIONS

import enum
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"

def main(argv=None):
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-ll1", Events, args)
    verbose.emit(Events.STARTED, message="reading spec")
    # ... stub work ...
    verbose.emit(Events.FINISHED, message="done")
```

## 4. Module Layout

```
src/plcc/
├── verbose.py              → NEW: shared verbose infrastructure
├── spec/                   → plcc-spec (unchanged)
├── tokens/                 → plcc-tokens (adds verbose flags)
├── ll1/                    → NEW: plcc-ll1
│   └── ll1_cli.py
├── tree/                   → plcc-tree (rewritten to dispatcher)
│   └── tree_cli.py
├── parser/                 → NEW: parser plugin ecosystem
│   ├── table_cli.py        → plcc-parser-table
│   └── list_cli.py         → plcc-parser-list
├── model/                  → plcc-model (adds verbose flags)
├── lang/
│   ├── emit.py             → plcc-lang-emit (adds verbose forwarding)
│   ├── build.py            → plcc-lang-build (adds verbose forwarding)
│   ├── run.py              → NEW: plcc-lang-run (dispatcher)
│   ├── list.py             → plcc-lang-list (adds verbose flags)
│   └── ext/
│       ├── plantuml/       → plcc-plantuml-emit (adds verbose flags)
│       │   └── emit.py
│       ├── python/         → NEW: Python language plugin
│       │   ├── emit.py     → plcc-python-emit
│       │   ├── run.py      → plcc-python-run
│       │   └── runtime/    → stub main.py template
│       └── java/           → NEW: Java language plugin
│           ├── emit.py     → plcc-java-emit
│           ├── build.py    → plcc-java-build
│           ├── run.py      → plcc-java-run
│           └── runtime/    → stub Main.java template
└── cmd/
    ├── make.py             → plcc-make (adds ll1 step, Level 2 verbose)
    ├── scan.py             → plcc-scan (promoted to connected skeleton)
    ├── parse.py            → plcc-parse (promoted to connected skeleton)
    └── rep.py              → plcc-rep (promoted to connected skeleton)
```

The `runtime/` directories under each language plugin hold the template files that `plcc-<lang>-emit` copies into the output directory. For the skeleton, these are minimal — a `main.py` that reads JSONL stdin and prints one line per tree, a `Main.java` that does the same.

## 5. Test Updates

### 5.1 New BATS command tests (`tests/bats/commands/`)

One `.bats` file per new command:

| File | Tests |
|---|---|
| `plcc-ll1.bats` | Entry point is installed and executable, `--help`, spec JSON in → ll1 JSON out, schema-valid output |
| `plcc-parser-table.bats` | Entry point is installed and executable, `--help`, `--ll1` required, token JSONL in → tree JSON out, schema-valid |
| `plcc-parser-list.bats` | Entry point is installed and executable, finds `plcc-parser-table` |
| `plcc-lang-run.bats` | Entry point is installed and executable, `--help`, dispatches to `plcc-python-run` |
| `plcc-python-emit.bats` | Entry point is installed and executable, produces `main.py` in output dir |
| `plcc-python-run.bats` | Entry point is installed and executable, execs generated `main.py`, parse-tree JSONL in → evaluation output |
| `plcc-java-emit.bats` | Entry point is installed and executable, produces `Main.java` in output dir |
| `plcc-java-build.bats` | Entry point is installed and executable, compiles generated `Main.java` |
| `plcc-java-run.bats` | Entry point is installed and executable, execs compiled class, parse-tree JSONL in → evaluation output |

### 5.2 Updated BATS command tests

| File | Change |
|---|---|
| `plcc-tree.bats` | `--spec` → `--ll1`, verify it dispatches to `plcc-parser-table` |
| `plcc-make.bats` | Verify `build/ll1.json` is produced |
| `plcc-skeletons.bats` | Removed — `plcc-scan`, `plcc-parse`, `plcc-rep` are no longer stubs |
| `plcc-scan.bats` | New: tests the connected pipeline (spec → tokens → human output) |
| `plcc-parse.bats` | New: tests the connected pipeline (spec → ll1 → tokens → tree → human output) |
| `plcc-rep.bats` | New: tests the connected pipeline end-to-end with `--tool` |

### 5.3 Verbose flag tests

Every command test file includes a test verifying the command accepts `--verbose` and `--verbose-format` without error. A small integration test verifies:

- Level 0 stages forward flags to children unchanged
- Level 2 orchestrators force `--verbose-format=json` on children
- Verbose output goes to stderr, not stdout (pipeline data stays clean)

### 5.4 Updated integration tests (`tests/bats/integration/`)

| File | Change |
|---|---|
| `tokens-tree.bats` | Updated for `plcc-tree`'s new interface (`--ll1` instead of `--spec`) |
| `spec-ll1.bats` | New: `plcc-spec \| plcc-ll1` produces valid ll1.json |
| `ll1-tree.bats` | New: token JSONL + ll1.json through `plcc-tree` produces valid tree |

### 5.5 Updated e2e tests

| File | Change |
|---|---|
| `happy-path.bats` | Verify `build/ll1.json` exists. Verify `plcc-make` with Java and Python semantic sections produces output in both dirs. |

### 5.6 Unit tests for `plcc.verbose`

Pytest unit tests in `src/plcc/verbose_test.py` covering:

- `VerboseContext` construction and `from_args`
- Text rendering format matches §17.8.4 conventions
- JSON rendering format matches §17.8.5 conventions
- `child_flags()` returns flags unchanged
- `child_flags_for_orchestrator()` forces json format and raises level
- `parse_child_events()` round-trips with JSON rendering
- Event enum parity: both renderers handle every enum member

## 6. Fixtures

The current trivial grammar (`tests/fixtures/trivial.plcc`) has only a PlantUML semantic section and is referenced by many Phase 1 tests. To avoid disrupting those tests, new fixture files are added for additional semantic sections.

| File | Semantic sections | Exercises |
|---|---|---|
| `trivial.plcc` | `% diagram PlantUML` | Existing Phase 1 tests (unchanged) |
| `trivial-java.plcc` | `% Java Java` | Java emit/build/run pipeline |
| `trivial-python.plcc` | `% py Python` | Python emit/run pipeline |
| `trivial-full.plcc` | All three sections | E2E happy path, `plcc-rep` with `--tool` |

All four share the same lexical and syntactic rules (`NUM '\d+'` and `<program> ::= <NUM>`). They differ only in their semantic sections.

## 7. Design Decisions and Escalation Paths

### 7.1 Verbose infrastructure: Approach B (context object), not C (base class)

**Decision:** `VerboseContext` is a plain object with shared renderers. Each command defines its own `Events` enum and passes it to the context at construction. Rendering logic lives in `VerboseContext`, not in per-command overrides.

**Escalation to C:** If commands start needing custom rendering — for example, `plcc-parser-table` wants to format shift/expand events as indented traces rather than flat `stage: event: message` lines — the shared renderers become a bottleneck. The signal is: someone adds an `if event == Events.EXPAND:` branch inside `VerboseContext.emit()`. That is the wrong place for per-command logic, and it is time to move to Approach C.

**What C looks like:** A `StageVerbose` base class with overridable `render_text(event, **payload)` and `render_json(event, **payload)` methods. Each command subclasses it — 3 lines: class declaration, `events_enum` class attribute, `stage` class attribute. Custom rendering for specific events goes into the subclass's `render_text`/`render_json` overrides. Migration from B: change each command's `VerboseContext.from_args(stage, events, args)` to `MyCommandVerbose.from_args(args)` (~1 line per command), and move any custom rendering logic from the shared module into the subclass. The shared module gains ~20 lines (the base class and default render methods); each command gains ~3 lines (the subclass declaration).

### 7.2 `plcc-spec` keeps LL(1) validation

**Decision:** `plcc-spec` retains its existing LL(1) validation even though §17.4 says it should stop. `plcc-ll1` is a stub.

**Escalation:** When `plcc-ll1` gets real implementation (Phase 2 Part 1), validation is removed from `plcc-spec` at the same time. Not before — removing it while `plcc-ll1` is a stub would leave no LL(1) checking anywhere in the pipeline.

### 7.3 `plcc-lang-build` and `plcc-lang-run` dispatcher no-op pattern

**Decision:** When `plcc-<lang>-build` or `plcc-<lang>-run` is not found on PATH, the dispatcher exits 0 silently. Plugins only ship the commands they need. PlantUML does not ship build or run commands; the dispatchers handle this as no-ops.

**Escalation:** If dispatchers need to distinguish "intentionally no-op" from "plugin is broken/missing," a future amendment could add a `plcc-<lang>-capabilities` command or a manifest. Not needed until a concrete debugging problem arises.

### 7.4 `plcc-rep --tool` defaults to `Java`

**Decision:** `--tool` defaults to `Java` for backwards compatibility with v8. Tool name is the unique identifier across semantic sections; when the grammar's divider omits the tool name, it defaults to the language name.

**Escalation:** If the default proves confusing (e.g., grammars without a Java section fail silently), revisit. Blast radius is small — only `plcc-rep`'s argument parsing.

## 8. Architectural Amendments Introduced by This Design

This design introduces one new obligation on language plugins not present in the original architecture:

**`plcc-<lang>-run` (optional):** Language plugins may provide a `plcc-<lang>-run` command that knows how to start the generated interpreter for that language. The command accepts `--output=<dir>` (the build output directory), reads parse-tree JSONL on stdin (forwarded from upstream pipeline stages), and writes evaluation output on stdout. It accepts `--verbose`/`--verbose-format` per §17.8.10.

This follows the established `plcc-lang-*` dispatcher pattern (§17.2) and the dispatcher no-op convention from §2.3 of this design. `plcc-lang-run --target=<lang> --output=<dir>` constructs `plcc-<lang>-run` and execs it. If the command is not on PATH, the dispatcher exits 0.

This amendment should be recorded as §17.9 in the architectural spec after this design is approved.
