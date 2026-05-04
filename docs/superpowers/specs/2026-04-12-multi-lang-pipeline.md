# PLCC Multi-Language Pipeline Architecture

**Date:** 2026-04-12 (rewritten 2026-04-18 — amendments merged into main body)
**Status:** Draft — pending review
**Target release:** PLCC v9.0.0

## 1. Goal

Make PLCC adoptable by faculty whose students do not know Java, by refactoring PLCC into a Unix-style pipeline of small JSON-filter tools and a plugin-based code generator that can emit interpreters in multiple target languages.

## 2. Non-Goals

- Replacing or competing with production compiler toolchains. Generated interpreters are pedagogical artifacts, not production software.
- Supporting non-OO target languages. Retargeting is limited to modern OO languages because the pedagogy depends on class hierarchy and polymorphic dispatch.
- Pluggable scanners and verifiers. These remain non-pluggable in v9. Parsers (parse-tree-generators) are pluggable; see §13. Verifiers may become pluggable in a later version if demand emerges.
- Bit-exact compatibility with v8's generated Java output. See §17.
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

```text
             ┌────────────────────────────────────────────────────┐
             │                     Level 2                        │
             │     plcc-make   plcc-scan   plcc-parse   plcc-rep  │
             └──────────────────────────┬─────────────────────────┘
                                        │ orchestrates
                                        ▼
   ┌──────────┬──────────┬──────────────┬──────────────┬──────────┐
   │plcc-spec │plcc-ll1  │ plcc-tokens  │  plcc-tree   │plcc-model│
   │          │          │              │ (dispatcher) │          │
   │ grammar  │spec JSON │ text stream  │ tokens JSONL │spec JSON │
   │    ↓     │    ↓     │      ↓       │      ↓       │    ↓     │
   │spec JSON │ ll1 JSON │ token JSONL  │  tree JSON   │model JSON│
   └──────────┴──────────┴──────────────┴──────┬───────┴─────┬────┘
                                               │             │
                                               ▼             ▼
                                    ┌──────────────────┐ ┌──────────────┐
                                    │ plcc-parser-*    │ │plcc-lang-emit│
                                    │  (PATH plugin)   │ │ (dispatcher) │
                                    └──────────────────┘ └──────┬───────┘
                                                                ▼
                                                     ┌────────────────────┐
                                                     │  plcc-<lang>-emit  │
                                                     │   (PATH plugin)    │
                                                     └────────────────────┘
```

## 5. Level 0 Primitives

Each primitive is a pip console-script entry point provided by the `plcc` package. Every primitive accepts the cross-cutting `--verbose`/`-v` and `--verbose-format=text|json` flags defined in §9.

| Command | Input | Output | Role |
| --- | --- | --- | --- |
| `plcc-spec` | `.plcc` grammar file (path or stdin) | spec JSON (stdout) | Faithful translation of the grammar file into JSON. Does **not** perform LL(1) analysis. One-shot; single JSON document. |
| `plcc-ll1` | spec JSON (stdin or path) | LL(1) analysis JSON (stdout) | Compute FIRST, FOLLOW, predict sets; build the parsing table; detect conflicts and left-recursion cycles. One-shot; single JSON document. Exits 0 on any grammar that parses as spec JSON; result is signalled by the top-level `is_ll1` field. Nonzero exit reserved for tool failures (missing input, malformed spec JSON). |
| `plcc-tokens` | text stream (stdin), `--spec <path>` | token JSONL (stdout) | Tokenize a character stream into a line-delimited JSON stream of tokens. Streaming; stateless; runs until EOF. |
| `plcc-tree` | token JSONL (stdin), `--ll1 <path>` (required), `--parser=<kind>` (optional, default `table`) | parse tree as a single newline-terminated JSON document (stdout) | Dispatcher. Reads token JSONL to EOF, execs `plcc-parser-<kind>` forwarding `--ll1`, exits when the dispatched plugin exits. One parse tree per invocation. No long-running mode, no multi-program mode. Output is also a valid one-line JSONL stream so it composes directly with the long-lived interpreter (§10). |
| `plcc-model` | spec JSON (stdin or path) | model JSON (stdout) | Transform a language spec into a language-neutral OO code model: classes, inheritance, attributes, constructors, method slots, and opaque semantic blocks. One-shot; single JSON document. |
| `plcc-lang-emit` | model JSON (stdin), `--target=<lang>`, `--output=<dir>` | source files in `<dir>` | Dispatcher: constructs `plcc-<lang>-emit` and execs it via PATH. The plugin writes generated source files and copies its bundled runtime into `<dir>`. |
| `plcc-lang-build` | `--target=<lang>`, `--output=<dir>` | compiled artifacts in `<dir>` | Dispatcher: constructs `plcc-<lang>-build` and execs it via PATH if present. Exits 0 silently if no build command is installed for that language. |
| `plcc-lang-list` | — | language names (stdout) | Scans PATH for commands matching `plcc-*-emit`; prints one language name per line. |
| `plcc-parser-list` | — | parser-kind names (stdout) | Scans PATH for commands matching `plcc-parser-*`; prints one kind per line. |

Naming rationale: the pure filters (`spec`, `ll1`, `tokens`, `tree`, `model`) are named after their output. The `plcc-lang-*` and `plcc-parser-*` commands are named after the layer they manage — they form the boundary between the core pipeline and the plugin ecosystem. `tree` is preferred over `ast` because it is approachable without jargon; `tokens` is preferred over `lex` or `tokenize` because it is a noun and matches the output. `model` is preferred over `code-model` for brevity.

## 6. Level 2 Commands

Level 2 commands are Python modules published as pip console-script entry points. They orchestrate Level 0 primitives using `subprocess.Popen`, wire stdin/stdout between stages, handle tty detection and prompting, and present errors to the user. Every Level 2 command accepts `--verbose`/`-v` and `--verbose-format=text|json` (§9) and a `--parser=<kind>` flag that plumbs through to `plcc-tree`. Phase 2 Part 1 ships only `plcc-parser-table` and `plcc-tree`'s dispatcher; the Level 2 `--parser` passthroughs land in Part 2 and Phase 4.

| Command | Role | Replaces |
| --- | --- | --- |
| `plcc-make` | Build the project from a grammar file. Always cleans `build/` before rebuilding. See §11 for phase sequence. | `plccmk` |
| `plcc-scan` | Pedagogical scanner view. Reads source input, runs it through `plcc-tokens`, prints tokens in a human-readable format. | `scan` |
| `plcc-parse` | Pedagogical parser view. Reads source input, runs it through `plcc-tokens` then `plcc-tree`, prints parse trees in a human-readable format. | (new; previously part of `rep`) |
| `plcc-rep` | REPL. Reads source input (files then stdin if interactive), runs it through `plcc-tokens` then `plcc-tree` then the interpreter, prints evaluation results. Handles prompting in tty mode. | `rep` |

All Level 2 commands take the same input model: zero or more file arguments followed by stdin. Files are concatenated in order, then stdin is appended. In interactive mode (`sys.stdin.isatty()`), the orchestrator emits prompts to stderr before each read.

**No shell dependency.** Level 2 orchestrators do not invoke `cat`, `sh`, or any external shell. They open files through `pathlib`, read stdin through `sys.stdin`, and write bytes to the first subprocess's stdin pipe. This works identically on Linux, macOS, and Windows without platform branching.

Students or instructors who want to run the primitives by hand from a Unix shell can do so. That usage is documented as a teaching aid but is not the path any installed Level 2 command takes.

## 7. JSON Contracts

This section describes the shape of data flowing between stages at a high level. Exact schemas are the implementation plan's responsibility; this spec establishes only the contract.

**One-shot vs. streaming.** One primitive runs as a streaming pipeline stage and uses JSONL (one JSON document per line) so it can emit output incrementally as input arrives:

- `plcc-tokens` — token JSONL.

The remaining primitives run once per invocation and produce a single JSON document (or, for `plcc-lang-emit`, files on disk):

- `plcc-spec` — spec JSON.
- `plcc-ll1` — LL(1) analysis JSON.
- `plcc-tree` — a single newline-terminated JSON document (also a valid one-line JSONL stream).
- `plcc-model` — model JSON.
- `plcc-lang-emit` — files.

### 7.1 Spec JSON

Output of `plcc-spec`. Contains lexical rules, syntactic rules, semantic sections (one per `% <tool> <language>` divider), and metadata needed by downstream primitives. Already produced by plcc-ng's existing `spec` command; the shape of the v9 spec JSON starts from whatever plcc-ng emits today and is refined as downstream primitives require.

### 7.2 LL(1) Analysis JSON

Output of `plcc-ll1`. A single JSON document with top-level fields:

- `is_ll1` — boolean result.
- `first`, `follow`, `predict` — set representations per nonterminal.
- `parse_table` — the LL(1) parse table.
- `conflicts` — array; empty when `is_ll1` is true.
- `left_recursion` — array of cycle reports; empty when the grammar has no left recursion.

A `--format=human` flag renders the same content human-readably for direct inspection. Downstream stages (currently `plcc-parser-table`) consume this JSON directly and do not recompute analysis at runtime.

All of the fields above — FIRST, FOLLOW, predict, parse table, conflicts, and the left-recursion cycle report — are first-class outputs of `plcc-ll1` from Phase 1 onward, not deferred features. Left-factoring candidate detection is the one analysis deferred to a later phase because it requires new logic beyond what the plcc-ng validator currently computes.

**LL(1) analysis is separated from `plcc-spec` on purpose.** It is a derived artifact, not a translation of the grammar file, so embedding it in `spec.json` would violate the philosophy that `spec.json` is a faithful parse of the `.plcc` file. Extracting the analysis into its own stage (a) preserves that philosophy, (b) exposes the analysis data as a first-class pedagogical artifact — the very thing PLCC exists to teach, (c) gives downstream consumers (`plcc-tree` today, future parse-tree-generator generators tomorrow) a stable JSON contract, and (d) factors the one-JSON-stage-per-responsibility architecture honestly.

**`plcc-model` does not depend on `ll1.json`.** Model construction is a translation of the spec into the canonical model representation; LL(1) analysis is a separate concern that flows to `plcc-tree` and parser plugins, not to `plcc-model`. The two stages consume `spec.json` independently of each other.

### 7.3 Token JSONL

Output of `plcc-tokens`. One JSON object per line, each describing a single token: kind, lexeme, source position. Streaming: tokens are emitted as they are scanned. Lexical errors terminate the stage with a structured error on stderr and a nonzero exit per §8.

### 7.4 Tree JSON

Output of `plcc-tree` (and, transitively, of any `plcc-parser-<kind>` plugin). A single newline-terminated JSON document describing an abstract syntax tree rooted at the grammar's start symbol for one program. One-shot: the stage reads token JSONL to EOF, parses exactly one program, emits the tree, and exits. Batch use parses multiple programs by spawning `plcc-tree` per program.

The output is also a valid one-line JSONL stream, so it composes directly with downstream consumers that expect JSONL (notably the long-lived interpreter — see §10). No adapter is needed between `plcc-tree`'s output and the interpreter's input.

### 7.5 Model JSON

Output of `plcc-model`. A single JSON document — a language-neutral description of the OO class hierarchy that an emitter will realize in its target language:

- **Classes** with inheritance relationships.
- **Attributes** with types described abstractly (primitive, reference, optional, list-of).
- **Constructors** with parameter lists and field bindings.
- **Method slots** — named methods with parameter lists and opaque bodies.
- **Semantic blocks** — opaque strings carrying target-language code from the grammar's `%%%` sections, tagged with the source language.

The code model is the retargeting pivot. Every emitter consumes this format; adding a new target language means writing an emitter that reads model JSON and produces source files. The code model does not know anything about any specific target language.

## 8. Error Handling

Every Level 0 stage follows the Unix `stderr + nonzero exit` convention:

- **Success:** valid output on stdout, exit 0.
- **Failure:** error on stderr, exit nonzero, stdout undefined.

There are no in-band error records in the pipeline. Errors always terminate the stage that emits them.

Error rendering uses the verbose infrastructure (§9): GNU-style text on stderr under `--verbose-format=text`, a JSONL record with `"event": "error"` under `--verbose-format=json`. Errors are emitted regardless of `--verbose` level — `--verbose=0` suppresses informational output, never error output.

Orchestrators detect failures by checking child returncodes in pipeline order (upstream first), capture the structured JSONL stderr their children produce (children are always spawned with `--verbose-format=json` — see §9.3), and report the first failing stage's error. In interpreter sessions (§10), per-chunk subpipeline failures do not kill the long-lived interpreter; the orchestrator reports the error and the session continues.

**`plcc-ll1` is a pure filter.** A non-LL(1) grammar is a result, not a failure. `plcc-ll1` always exits 0 on any grammar that parses as spec JSON; the result is signalled by its `is_ll1` output field. Nonzero exit is reserved for tool failures (missing input, malformed spec JSON). `plcc-make` decides whether to continue by reading `build/ll1.json` back after writing it (see §11). `grep` exits 1 on no matches, which is widely considered a design mistake that makes scripting harder; `jq` exits 0 on `null` results, which is preferred. `plcc-ll1` joins the latter camp.

**Parser plugins terminate on the first syntax error.** No error recovery, no partial trees, no Error nodes. A syntax error in the token stream is a structured error on stderr plus a nonzero exit. If a future amendment reintroduces recovery, it will specify the contract.

**Interpreter runtime errors** are the interpreter's own stdout schema, not a revival of in-band errors. Because the interpreter is long-lived (§10), runtime errors in student code are emitted as one kind of evaluation record on stdout; exit stays 0. Stderr is reserved for interpreter-level tool failures. The exact record shape is a Phase 2 Part 2 design-doc decision.

## 9. Verbose Diagnostics

Every pipeline stage — Level 0 and Level 2 — accepts two cross-cutting flags that give the pipeline a uniform diagnostic surface:

- `--verbose` (`-v`) — **how much** to emit on stderr. Level dial 0–3.
- `--verbose-format=text|json` — **how** to render. Default `text`.

Both flags are part of the walking-skeleton baseline from Phase 1 onward. Retrofitting diagnostic output across an already-shipped pipeline is exactly the cross-cutting change most disruptive to do after the fact, so every stage accepts and propagates both flags from day one. What varies across phases is how much each stage has to say, not whether it participates. Concretely:

- **Accept-and-propagate** is mandatory for every stage from day one. The cost of adding two flags to an argparse/Click definition plus a subprocess-argv pass-through is negligible; the cost of retrofitting it later is high because every stage's contract, every test that invokes a stage, and every subprocess-spawning call site would need to change at once.
- **Both renderers** (text and JSON) must be implemented for every event a stage emits. This is enforced by test parity checks (§9.5). A stage that has no events yet has no renderers to implement — the null case costs nothing.
- **Emit** is expected for every stage that has meaningful milestones or events, as soon as it has them. "We'll add verbose output later" is rejected as a valid plan item. The protocol itself must be present from day one; only the content fills in over time.

Diagnostic visibility is the single most-requested PLCC v8 feature among faculty using PLCC for teaching: "what is the parser doing, what is the scanner doing, why did this program behave that way." v8 offers a handful of ad-hoc `-t` flags on individual tools; the result is inconsistent, undiscoverable, and does not compose across a pipeline. A single cross-cutting flag pair with uniform semantics fixes all three problems.

**Two flags, not one, because the pipeline has two audiences.** A student running `plcc-parser-table -vv` at the command line wants human-readable narration — present tense, one event per line, GNU-style positions. A Level 2 orchestrator consuming `plcc-parser-table -vv` as a subprocess wants structured JSONL it can reliably parse, aggregate, and reformat into a higher-level view (e.g. `plcc-parse -vv` producing a v8-style indented parse trace). Making the stage responsible for both renderings — text for humans, JSON for machines — keeps the boundary between "what events happened" (the stage's responsibility) and "how to present them" (the consumer's responsibility) clean. `--verbose-format` selects which rendering the consumer wants; `--verbose` selects how much.

### 9.1 `--verbose`: level dial

- `--verbose=0` or flag absent — silent. **Default.**
- `--verbose=1`, `--verbose`, `-v` — milestones. One line per major phase boundary.
- `--verbose=2`, `-vv` — per-event narration. Every shift, expand, token, evaluation step, etc.
- `--verbose=3`, `-vvv` — internal detail. Predict-set lookups, table entries consulted, recovery decisions, DFA transitions.

Higher levels are strictly supersets of lower ones. Shorthand `-vv` means two `-v` flags counted by the argument parser (e.g. Click's `count` action or argparse's `"count"` action), not a literal string. Levels higher than a stage supports collapse silently — asking for `-vvv` from a stage that only defines `-v` and `-vv` is not an error, it just gets `-vv`. A stage that has nothing interesting to say at a given level emits nothing, which is a valid forward-compatible null case.

The specific events emitted at each level are stage-specific and specified in the relevant phase design doc. Examples:

- `plcc-parser-table`: `-v` emits start/finish milestones and summary stats; `-vv` emits shift/expand/complete per token; `-vvv` adds predict-set lookup detail and recovery decisions.
- `plcc-tokens`: `-v` emits start/finish and token count; `-vv` emits each token as it is scanned; `-vvv` adds DFA-state transitions.
- Level 2 commands: `-v` emits orchestration milestones and aggregated statistics (possibly derived from higher-detail Level 0 output); `-vv` emits the v8-style formatted view appropriate to the command (e.g. indented parse trace for `plcc-parse`, token-by-token narration for `plcc-scan`); `-vvv` adds internal orchestration detail.

A single level dial was chosen over per-stage selection because the primary consumer of verbose output is a human looking at a terminal. Per-stage selection is a solution to noise in structured-log grep results, which is a machine concern, not a human concern. If one stage is overwhelmingly chatty at a given level, the correct fix is to recalibrate which events that stage emits at which level.

### 9.2 `--verbose-format`: output format

- `--verbose-format=text` (default) — human-readable narrative on stderr per §9.4. Intended for direct human consumption when a student or developer runs a stage at the command line.
- `--verbose-format=json` — JSONL on stderr, one record per line per §9.5. Intended for machine consumption by Level 2 orchestrators that need to parse, aggregate, and reformat diagnostic events from their children.

Both formats emit the same underlying events at the same level; the flag selects rendering, not content. Tests enforce parity: the set of events and their counts must match under both formats for identical input.

### 9.3 Propagation rules

Propagation is asymmetric between Level 0 and Level 2. Level 2's job is to consume Level 0's diagnostic output and present it in a form appropriate to its own task, so Level 2 needs machine-readable input from children regardless of what the user asked for, and may need more detail than the user's requested level.

**Level 0 stages and dispatchers** (e.g. `plcc-tree` forwarding to `plcc-parser-<kind>`):

1. **Self-emit.** Honour `--verbose` and `--verbose-format` as received. Emit events on stderr accordingly.
2. **Forward unchanged.** Pass both flags to any child subprocess exactly as received. Dispatchers are pass-throughs, not reformatters.

**Level 2 orchestrators** (e.g. `plcc-parse`, `plcc-rep`, `plcc-scan`, `plcc-make`):

1. **Self-emit.** Emit the command's own diagnostic output on stderr in the format the **user** requested (default `text`). Level 2's output includes both its own orchestration events (chunk boundaries, subprocess lifecycles) and reformatted events from Level 0 children.
2. **Override children's flags.** When spawning Level 0 children:
   - **Always** pass `--verbose-format=json`, regardless of the user's `--verbose-format`. This makes children's stderr reliably parseable.
   - Set `--verbose` to whatever the orchestrator needs internally, which may be higher than the user's requested level. For example, `plcc-parse -v` (user wants milestones) may need `plcc-parser-table -vvv` to compute summary statistics like parse-table size. Each Level 2 command's phase design doc specifies this mapping.
3. **Capture and reformat.** Level 2 captures children's JSONL stderr, parses the records, and re-renders them into its own output format. This is how `plcc-parse -vv` produces a v8-style indented parse trace from `plcc-parser-table`'s flat JSONL event stream.

**Why Level 2 overrides both axes.** Level 2 orchestrators need structured input (JSON, not text) from children to do reliable reformatting — text parsing is fragile and drifts with formatting changes. They also need sufficient detail from children to present their own output — a Level 2 summary at `-v` may require Level 0 detail at `-vvv`. The user's flags express what the user wants to *see* from Level 2; they do not constrain what Level 2 needs *internally* from its children. The asymmetry is the same pattern that every compiler driver uses: `gcc -v` shows the user a summary while internally passing whatever flags each subprocess needs.

**Long-lived subprocesses (§10 interpreter).** The interpreter is long-lived for the session. `--verbose` and `--verbose-format` are set at spawn time and are immutable for the session — there is no mid-session mechanism to change them. If a future phase needs dynamic verbosity (e.g. a REPL user toggling `-vv` for a single chunk), the mechanism will be specified as an amendment at that time.

**Level 2 nesting** is not designed for. If that topology arises in a future phase, propagation rules will be amended.

### 9.4 Text output standards

When a stage emits text-format verbose output:

- **Stage-name prefix.** Every line begins with the stage's executable name, a colon, and a space: `plcc-tree: expanding Expression -> left:Term op:Op right:Term`. The prefix is how a reader tells who said what when stderr from several stages interleaves.
- **GNU-style source positions where relevant.** When a line corresponds to a source location, include the position as `file:line:col:` after the stage prefix: `plcc-tree: program.txt:4:12: shift IDENT 'foo'`. Editors and IDEs already parse this convention, so verbose lines become click-through.
- **Present tense, active voice, one event per line.** "expanding Expression", not "Expression was expanded." "shift IDENT 'foo'", not "a shift occurred."
- **Line-atomic writes.** A stage buffers an entire line before writing. Under POSIX, writes smaller than `PIPE_BUF` (4096 bytes on Linux) are atomic to pipes; to files and ptys, atomicity is best-effort. One line per write minimises interleaving in all cases.
- **No ANSI colors by default.** Colors break when stderr is redirected or captured. A future `--color=auto|always|never` flag can add colors opt-in.
- **No timestamps by default.** Timestamps add noise for human consumption. If a future phase needs them, they can be added behind an opt-in flag.
- **Errors remain distinguishable.** Real errors use a distinct marker (`plcc-tree: error: ...`) and are emitted regardless of verbose level (§8).

### 9.5 JSON output standards

When `--verbose-format=json` is active, every verbose event is a single JSONL line on stderr. Minimum shape:

```json
{"stage": "<executable-name>", "time": <monotonic-ns>, "event": "<kind>", ...payload}
```

- `stage` — emitting executable's name (same as the text-format prefix).
- `time` — monotonic nanosecond timestamp for **intra-stage** ordering. Monotonic clocks are per-process; timestamps from different stages are not directly comparable. Level 2 orchestrators that need cross-stage ordering stamp ingestion time when capturing children's stderr.
- `event` — a stable event-kind identifier (e.g. `shift`, `expand`, `predict-lookup`, `error-recovery`, `milestone`, `error`). Event kinds and payloads are stage-specific and defined in each phase design doc.

## 10. Pipeline Lifetimes

In any session-scoped Level 2 command that includes an interpreter (primarily `plcc-rep`):

- The **interpreter** subprocess is **long-lived** for the duration of the session. It accepts parse-tree JSONL on stdin continuously, evaluates each tree as it arrives, and emits one evaluation record (also JSONL) per tree on stdout. Line-delimited JSON frames both directions; no out-of-band delimiter is needed.
- `plcc-tokens` and `plcc-tree` (and any parser plugin dispatched from `plcc-tree`) are **one-shot per input chunk**. For each chunk — a library file, the main program file, or an interactive REPL entry — the orchestrator spawns a fresh `plcc-tokens | plcc-tree` subpipeline, feeds the chunk through, reads the resulting parse-tree JSON, and pipes it into the long-lived interpreter's stdin. The orchestrator waits for the interpreter's evaluation output before accepting the next chunk.
- **One evaluation record per parse tree.** The exact schema of evaluation records (how they represent printed output, errors, and multiple results per program) is a Phase 2 Part 2 design-doc decision.

`plcc-rep` invocation forms compose cleanly under this model:

- `plcc-rep grammar.plcc` — interactive; prompts, reads chunks from tty, evaluates each.
- `plcc-rep grammar.plcc < program.txt` — batch; feeds the file as a single chunk.
- `plcc-rep grammar.plcc lib1.txt lib2.txt` — loads libraries as sequential chunks into the interpreter, then enters interactive mode. State from the libraries is visible to subsequent chunks because the interpreter is long-lived.
- `plcc-rep grammar.plcc lib1.txt lib2.txt < program.txt` — loads libraries, then runs program.txt as the final chunk, then exits.

**Rationale.** Only stages that hold state need to be long-lived. The interpreter holds state (loaded library definitions, runtime environment) and must persist for the session. `plcc-tokens` and `plcc-tree` hold no state; spawning them per chunk is simpler than coordinating program-boundary framing across long-running streaming stages. Fork/exec/JSON-load cost per chunk is imperceptible in interactive use and negligible in batch use.

## 11. Build Output Layout

`plcc-make` produces all generated artifacts under a single top-level `build/` directory:

```text
build/
├── spec.json         # output of plcc-spec
├── ll1.json          # output of plcc-ll1
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

- **Single directory to clean.** `plcc-make` always runs `rm -rf build/` before rebuilding. There is no `-c` flag in v9; clean-and-rebuild is the default and only behaviour. (A future option to skip cleaning can be added if a concrete need arises.)
- **Single `.gitignore` line.** `build/` in the project's `.gitignore` excludes every generated artifact.
- **Intermediate files are visible.** `spec.json`, `ll1.json`, and `model.json` live at the top of `build/` where students can `cat` them. The pipeline is inspectable, not magical.
- **One output subdirectory per semantic section.** Each `% <tool> <language>` divider in the grammar produces one subdirectory named `<tool>`, emitted by the plugin for `<language>`. The name is taken verbatim from the grammar; `plcc-make` does not normalize casing. A divider written as `% Java Java` produces `build/Java/`; one written as `% java Java` produces `build/java/`. Learning materials should standardize on a casing convention.
- **Generated output is disposable.** Students regenerate frequently. Source (the grammar file) persists; `build/` is ephemeral.

`plcc-make` phase sequence:

1. **Clean:** `rm -rf build/`
2. **Spec:** `plcc-spec grammar.plcc > build/spec.json`
3. **LL(1):** `plcc-ll1 build/spec.json > build/ll1.json`
4. **Model:** `plcc-model build/spec.json > build/model.json`
5. **Emit:** for each semantic section, `plcc-lang-emit --target=<lang> --output=build/<tool>/ < build/model.json`
6. **Build:** for each semantic section, `plcc-lang-build --target=<lang> --output=build/<tool>/` (silently skipped if no build command is installed for that language)

After step 3, `plcc-make` reads `build/ll1.json` back. If `is_ll1` is false, it prints a human-readable summary of `conflicts` and `left_recursion` on stderr and exits nonzero; subsequent phases do not run. If any other phase exits nonzero, `plcc-make` reports the error and stops; subsequent phases do not run.

## 12. Language Plugin System

Language plugins are discovered via PATH. A plugin is any executable named `plcc-<lang>-emit` present on the user's PATH. No entry point group, no registry, no Python packaging machinery is required beyond `pip install` placing the command on PATH.

### 12.1 Contract

A language plugin consists of one required command and one optional command:

**`plcc-<lang>-emit` (required)**

- Reads model JSON from stdin.
- Accepts `--output=<dir>` (required) and `--semantics=hide|note|comment|body` (optional, default `body`).
- Accepts and forwards `--verbose` and `--verbose-format` per §9.
- Writes generated source files into `<dir>`.
- Copies its bundled runtime into `<dir>/runtime/`.
- Exits 0 on success; exits nonzero and writes to stderr on failure.
- A malformed model is a tool failure: stderr + nonzero exit per §8.

**`plcc-<lang>-build` (optional)**

- Accepts `--output=<dir>` (required).
- Accepts and forwards `--verbose` and `--verbose-format` per §9.
- Compiles or prepares files already in `<dir>` (e.g. runs `javac`).
- Exits 0 on success; exits nonzero and writes to stderr on failure.
- Absence from PATH means no build step for that language — not an error.

The `--semantics` flag controls how semantic `%%%` blocks appear in emitted output. PlantUML and similar diagram emitters use `--semantics=note` or `--semantics=hide`; interpreter emitters use `--semantics=body`. How the user specifies `--semantics` (as a flag to `plcc-make` or embedded in the grammar file) is left to the Phase 1 design document.

Because the contract is stdin/stdout/exit codes, a plugin need not be a Python package. `pip install` is the conventional delivery mechanism, but the runtime contract has no Python dependency.

### 12.2 Package layout

Each language plugin package bundles its own runtime library. A reference layout for a third-party plugin (e.g. `plcc-rust`):

```text
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
- **Output is self-contained.** The bundled runtime in `build/<tool>/runtime/` has no per-language external dependencies: no separate runtime package on PyPI, no Maven Central lookup, no crates.io. The generated interpreter is a pipeline stage (§14) that composes with `plcc-tokens` and `plcc-tree` from the main `plcc` install, and needs nothing else beyond the target language's interpreter itself.
- **One install per language.** `pip install plcc-rust` brings in emission logic, templates, and runtime in a single unit. Runtime bugs are fixed by releasing a new version of the plugin package.
- **Regeneration is cheap.** Students regenerate frequently, so "runtime is copied into every rebuild" is not a cost.

### 12.3 Discovery

`plcc-lang-emit --target=<lang>` constructs `plcc-<lang>-emit` and execs it as a subprocess. Discovery is PATH-based: if the command exists on PATH, the plugin is installed; if not, `plcc-lang-emit` exits nonzero with:

```text
No emitter found for '<lang>'. Is plcc-<lang>-emit installed?
Run plcc-lang-list to see what is available.
```

`plcc-lang-list` scans PATH for executables matching `plcc-*-emit`, strips the prefix and suffix, and prints one language name per line.

### 12.4 Built-in emitters

The `plcc` core package ships with three built-in language plugins, declared as console scripts in `plcc`'s own `pyproject.toml`:

```toml
[project.scripts]
plcc-plantuml-emit = "plcc.lang.plantuml:emit_main"
plcc-python-emit   = "plcc.lang.python:emit_main"
plcc-java-emit     = "plcc.lang.java:emit_main"
plcc-java-build    = "plcc.lang.java:build_main"
```

`pip install plcc` installs all three out of the box. No separate packages, no entry point groups.

Third-party plugins (`plcc-rust`, `plcc-typescript`, etc.) are published as independent PyPI packages following the naming convention `plcc-<lang>`. Installing one places `plcc-<lang>-emit` (and optionally `plcc-<lang>-build`) on PATH, making the language immediately available to `plcc-lang-emit`.

## 13. Parser Plugin System

Parser plugins follow the same PATH-based discovery as language plugins. A parser plugin is any executable named `plcc-parser-<kind>` on PATH.

### 13.1 Contract

- Reads token JSONL on stdin.
- Accepts `--ll1 <path>` (required).
- Accepts `--verbose` and `--verbose-format` per §9.
- Emits a single newline-terminated parse-tree JSON document on stdout (also a valid one-line JSONL stream).
- Exits 0 on success; exits nonzero and writes to stderr on tool failure.
- Terminates on the first syntax error; no error recovery, no partial trees, no Error nodes (§8).

One-shot, like `plcc-tree` itself: a parser plugin reads token JSONL to EOF, parses one program, emits one tree, and exits. No long-running mode, no multi-tree-per-invocation mode. Error-recovery strategy (panic-mode, phrase-level, etc.) is plugin-defined beyond the one-error-terminates rule; the Phase 2 Part 1 design doc commits `plcc-parser-table` to a specific strategy.

### 13.2 Dispatcher (`plcc-tree`)

`plcc-tree` is a dispatcher. It constructs `plcc-parser-<kind>` from its `--parser=<kind>` flag (default `table`), execs it forwarding `--ll1`, `--verbose`, and `--verbose-format` unchanged, and exits when the dispatched plugin exits. If `plcc-parser-<kind>` is not on PATH, `plcc-tree` exits nonzero with a message naming the missing command and pointing at `plcc-parser-list`.

### 13.3 Built-in parser

The `plcc` package ships with one built-in parser plugin:

```toml
[project.scripts]
plcc-parser-table = "plcc.parser.table:main"
```

`plcc-parser-table` is the table-driven LL(1) parser that consumes `ll1.json` and produces parse-tree JSON. It is the default parser, so `plcc-tree` (and `plcc-rep`, `plcc-parse`, `plcc-scan`, `plcc-make`) work out of the box with `pip install plcc`.

### 13.4 Discovery

`plcc-parser-list` scans PATH for executables matching `plcc-parser-*`, strips prefix and suffix, and prints one parser-kind name per line (symmetric with `plcc-lang-list`).

### 13.5 Recursive-descent parser generation (forward-looking)

A future Level 0 stage, working name `plcc-gen-parser` (named outside the `plcc-parser-*` glob to avoid being mistaken for a parser plugin by `plcc-tree` or `plcc-parser-list`), will generate parser source code in a target language from `ll1.json`. A built-in invocation always generates Python source, producing a parser plugin that can be installed alongside `plcc-parser-table` and selected via `--parser=`. Language plugins may optionally provide their own target-language parser generators (e.g. a Java parser generator emitted into `build/Java/`). The generated parser is itself a pipeline-stage parse-tree-generator under §14: token JSONL in, parse-tree JSON out, no scanner. Recursive-descent generation is not Phase 2 Part 1 scope; the Part 1 design doc describes the intended shape as a forward-looking note so the later phase slides in without reshaping.

### 13.6 Rationale

The parse-tree-generator is already one pipeline stage regardless of whether it is the built-in Python table-driven parser, a generated Python recursive-descent parser, or a parser generated in a different target language — every variant reads token JSONL and emits parse-tree JSON. The question is only how that stage is discovered and dispatched. PATH-based discovery reuses infrastructure from the language-plugin system, composes with `pip install`, and matches the Unix-idiomatic pattern the architecture already uses.

PLCC's pedagogical context is programming languages courses, in which parser implementation strategies are part of the curriculum even when parsers are not student-written. Making parse-tree-generators visibly pluggable lets faculty show students a table-driven parser, a recursive-descent parser, and any other strategy side-by-side against the same grammar — the same pluggability axis that makes language-level retargeting work. Scanner and verifier pluggability remain out of scope because (a) lexical analysis in PLCC's context is a DFA-driven data problem rather than an algorithmic variation, and (b) verifiers in v9 consist of exactly one implementation (`plcc-ll1`); pluggability is meaningless without multiple implementations. These constraints may loosen post-v9.

## 14. Generated Components

Every generated component is a **pipeline stage** that communicates via JSON on stdin/stdout, not a standalone program:

- A **generated interpreter** reads parse-tree JSONL on stdin, deserializes each tree into an object tree whose classes are generated from the grammar, calls the root entry-point method, and writes evaluation records on stdout. **It has no scanner and no parser.** To deserialize trees, it uses whatever off-the-shelf JSON library ships with its target language.
- A **generated parse-tree-generator** (future, via §13.5) reads token JSONL on stdin, deserializes each token, runs its parsing algorithm, and emits parse-tree JSON on stdout. **It has no scanner.**
- A **generated tokenizer** is out of scope in v9.

To invoke a generated interpreter standalone, a student composes the upstream stages:

```sh
plcc-tokens --spec build/spec.json < program.txt \
  | plcc-tree --ll1 build/ll1.json \
  | python build/py/main.py
```

`plcc-rep` automates this orchestration and is the primary way students interact with generated interpreters.

### 14.1 Runtime contents

The runtime a language plugin bundles into `<dir>/runtime/` consists of:

1. Base classes for the generated grammar classes (one base per nonterminal kind, plus token base classes).
2. Parse-tree JSON deserialization helpers that reconstruct an object tree from parse-tree JSONL on stdin.
3. Optional token JSON deserialization helpers, included only if the plugin also emits a parse-tree-generator.
4. An entry-point harness that reads parse-tree JSONL from stdin, deserializes one tree per line, calls the root entry-point method on each, and writes evaluation records to stdout.
5. Error-record rendering helpers per §8.

The runtime explicitly does **not** include a tokenizer, a parser, or any code for reading raw program source. Generated components rely on upstream pipeline stages for tokenization and parsing.

Generated components are pipeline stages and inherit the full verbose-diagnostics contract from §9: they accept `--verbose` and `--verbose-format`, forward them to any subprocess they spawn, and emit diagnostic output under their own executable name on stderr in the requested format. The runtime bundles whatever rendering helpers the emitter needs to satisfy this contract in its target language.

### 14.2 Entry-point method name

`$run()` (the name used by v8) is not portable: Python, C#, Rust, Go, and Swift all reject `$` in identifiers. The portable name is deferred to the Phase 2 Part 2 brainstorm, which is the first phase that emits an interpreter and thus must commit to a name.

### 14.3 Rationale

Treating generated components as pipeline stages eliminates a two-layer mental model where the "parser inside `plcc-rep`" and the "parser inside the generated interpreter" appear to be different things. Under the pipeline-stage framing, there is one parse-tree-generator in use at a time, and it serves both the interactive Level 2 commands and the composition used when invoking generated interpreters. Students see one pipeline and one JSON contract. The generated artifact's responsibility narrows to "take trees, run trees," which is the pedagogical essence of an interpreter and eliminates the need for every emitter to independently reinvent tokenization and parsing in its target language.

## 15. First Non-Java Target: Python

The primary proof point for the retargeting architecture in v9 is `plcc-python-emit`. Python is chosen because:

- It is the highest-leverage adoption win. Many institutions teach Python as their primary language; their faculty cannot currently adopt PLCC.
- Its dynamic typing puts pressure on the code model abstraction. A code model that survives emission to Python without Java-ism leaks is much more likely to also survive emission to TypeScript, C#, or Rust later.
- Students in most CS curricula already know some Python, so the emitted interpreter is immediately readable to them.

`plcc-python-emit` must round-trip through the `languages` test repository (§17) in both its emitted code and its embedded runtime. "Round-trip" here means the generated Python interpreter pipeline stage correctly evaluates parse trees the upstream pipeline produces — not that the generated artifact runs programs end-to-end standalone.

## 16. Distribution and Packaging

PLCC v9 is distributed through PyPI as `plcc`. All Level 0 primitives and Level 2 commands are console-script entry points declared in `pyproject.toml`. Installing the package provides every command on the user's `PATH`.

```sh
pip install plcc
```

Cross-platform by construction. No shell scripts, no environment variable setup, no OS-specific installers. The command a student or instructor runs to get a working PLCC is the same on Windows, macOS, and Linux.

Third-party language plugins are separate PyPI packages following the naming convention `plcc-<lang>`. Installing one places `plcc-<lang>-emit` (and optionally `plcc-<lang>-build`) on PATH.

```sh
pip install plcc plcc-rust
```

This distribution model replaces the v8 model, which required cloning the repo and configuring environment variables — an adoption barrier that disproportionately affects students on Windows and instructors supporting multiple operating systems.

## 17. Backwards Compatibility

v9 provides **semantic backwards compatibility** for v8 grammar files, not bit-exact compatibility. A grammar file written against v8 passed to v9's `plcc-make` produces a working Java interpreter with the same runtime behaviour. Generated class names, method signatures, and file layout may differ from v8's output; faculty tests of student programs continue to pass; faculty who inspected generated Java source may see differences.

### The `languages` test oracle

Backwards compatibility is not an aspiration. It is a runnable, concrete signal. The `languages` repository contains the example languages referenced in PLCC's learning materials, along with tests that verify each language can be parsed by PLCC, have Java code generated, compiled, and run against example programs.

**v9 is considered backwards compatible when the full `languages` test suite passes against it.**

This test suite is part of v9's acceptance criteria. It runs in CI throughout development to catch regressions early rather than at the end. The Java language plugin (`plcc-java-emit`) is designed and tested against this suite.

The suite is not comprehensive — its coverage of runtime behaviour is shallow — but it is concrete, already written, and exercises the full pipeline end to end against realistic grammars.

## 18. Deferred and Out of Scope

- **Pluggable verifiers.** Future extension; no work in v9.
- **Pluggable scanners.** The Level 0 primitive `plcc-tokens` remains the only implementation in v9.
- **Level 1 intermediate compositions.** Deferred until a pedagogical use case emerges.
- **Non-OO target languages.** Retargeting in v9 is limited to modern OO languages.
- **Exact JSON schemas.** This spec establishes contracts and the error model (§8); schema details are the implementation plan's responsibility.
- **Migration of existing PLCC users to v9 on a timeline.** The cutover strategy supports parallel operation; the decision of when individual faculty migrate is their own.
- **Integration of plcc-ng into the plcc repository.** Deferred until v9 is complete and has demonstrated buy-in. Development of v9 happens entirely within the plcc-ng repository.
- **Recursive-descent parser generation** (`plcc-gen-parser`). Forward-looking design sketched in §13.5; not Phase 2 Part 1 scope.
- **Left-factoring candidate detection in `plcc-ll1`.** Deferred to a later phase; requires new logic beyond what the plcc-ng validator currently computes.
- **Dynamic verbosity in long-lived subprocesses.** `--verbose` and `--verbose-format` are immutable for the interpreter session.
- **Interpreter evaluation record schema.** Phase 2 Part 2 design-doc decision.
- **Entry-point method name for generated interpreters.** Phase 2 Part 2 design-doc decision.

## 19. Open Risks

- **Code model generality.** The code model is the retargeting pivot. If it accidentally encodes Java-isms, emission to Python will surface them, but late-discovered abstraction leaks could require rework of every emitter. Mitigation: emit to Python as early in the implementation plan as possible, before investing in the Java emitter's polish.
- **Runtime library drift across languages.** Each emitter plugin owns its runtime, so different languages' interpreters can drift in behaviour. Mitigation: the `languages` test suite exercises Java runtime behaviour; a parallel language-agnostic test suite should exercise Python runtime behaviour as the Python emitter matures.
- **plcc-ng code that does not fit the pipeline shape.** plcc-ng's 282 commits include spec parsing and a scanner, but its internal structure shares dataclasses across package boundaries. Re-homing that code into Level 0 primitives with JSON contracts may reveal coupling that requires restructuring, not just relocation. Mitigation: the implementation plan begins with extracting `plcc-spec` as a standalone primitive to surface these issues early.
- **Learning materials lag.** Learning materials need to be updated to match v9's commands and behaviour before v9 can be widely adopted. Mitigation: name a specific maintainer responsible for the learning materials update, with a review checkpoint after the Python emitter lands.
