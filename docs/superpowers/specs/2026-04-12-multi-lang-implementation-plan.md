# PLCC v9.0.0 — High-Level Implementation Plan

**Date:** 2026-04-12
**Status:** Draft — pending review
**Companion architectural spec:** [2026-04-12-multi-lang-pipeline.md](2026-04-12-multi-lang-pipeline.md)
**Target branch:** `multi-lang` (to be created)
**Target release:** PLCC v9.0.0

## 1. Purpose

This document is the **roadmap** for implementing PLCC v9.0.0, not a detailed task list. It sequences the work into phases, names the strategy behind each phase, states the acceptance criteria that mark a phase as complete, and describes how phase-level design documents and detailed implementation plans are produced iteratively.

It does not contain code, TDD task steps, or exhaustive enumerations of files to touch. Those live in each phase's own implementation plan, which is written when that phase is about to begin — not now.

The companion architectural spec (`2026-04-12-multi-lang-pipeline.md`) describes *what* is being built. This document describes *how and in what order* it gets built.

## 2. Process Model

Each phase is executed through a small, full cycle of the brainstorming and planning skills. The steps of that cycle are:

1. **Phase brainstorm.** Revisit the architectural spec's relevant sections. Surface open questions specific to this phase. Resolve them through dialogue. The scope is narrow: only what this phase needs to decide.
2. **Phase design document.** Capture the decisions that emerged from the brainstorm as a short design doc dedicated to the phase. Saved to `docs/design/YYYY-MM-DD-phase-<n>-<name>.md`. This document is additive to the architectural spec, not a replacement — it fills in details the architectural spec intentionally left open.
3. **Phase implementation plan.** Produced by the writing-plans skill. A detailed TDD task list with exact files, steps, commands, and commits. Saved to `docs/plans/YYYY-MM-DD-phase-<n>-<name>.md`.
4. **Execution.** The phase plan is executed task by task, with tests at every step. Work happens on the `multi-lang` branch.
5. **Phase review.** At phase completion, a short retrospective captures what was learned, what surprised us, and whether any decisions in the architectural spec need revisiting. This feedback informs the next phase's brainstorm.

This cycle exists because implementation details for later phases cannot be honestly designed up front — they depend on what we learn from earlier phases. The architectural spec is stable; phase-level details are just-in-time.

### 2.1 The architectural spec is frozen

During v9 development, the architectural spec (`2026-04-12-multi-lang-pipeline.md`) is treated as frozen. Phase work does not edit it. If a phase reveals that an architectural decision is wrong, the response is a deliberate **architectural amendment**: a new dated section added to the spec (or a superseding spec) with a clear "amends §X because of lesson learned in Phase Y" header. This is rare and intentional. Routine phase work never touches the spec.

### 2.2 Documents produced by this plan

By the time v9.0.0 ships, the following documents exist:

- `docs/design/2026-04-12-multi-lang-pipeline.md` — architectural spec (already exists)
- `docs/design/2026-04-12-multi-lang-implementation-plan.md` — this document
- `docs/design/YYYY-MM-DD-phase-1-walking-skeleton.md` — Phase 1 design doc (later)
- `docs/plans/YYYY-MM-DD-phase-1-walking-skeleton.md` — Phase 1 detailed plan (later)
- …and similarly for Phases 2–5.

Phase-level retros are appended to each phase's design doc rather than given separate files.

## 3. Phase Overview

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
 Walking   Python     Java     Polish &   Release
 skeleton  emitter    emitter  prerelease
```

Each arrow is a phase boundary. At every boundary there is a phase retro that informs the next phase's brainstorm. Phases do not overlap; each one completes and is reviewed before the next begins.

## 4. Phase 1: Walking Skeleton

### 4.1 Goal

Build a thin, end-to-end pipeline that drives a trivial grammar file all the way through to a rendered PlantUML class diagram, proving every JSON contract and the plugin discovery mechanism in one pass.

### 4.2 Strategy

This is a **walking skeleton** in the Alistair Cockburn sense: every part of the pipeline exists but is only as thick as it needs to be to process a minimal grammar. The value is not in what the skeleton can do (very little) but in what its existence proves (every contract is honored, every boundary is crossed, the plugin discovery works).

Five Level 0 primitives get stubs:

- `plcc-spec` — wrap plcc-ng's existing spec parser; emit spec JSON
- `plcc-tokens` — wrap plcc-ng's existing scanner; emit token JSONL
- `plcc-tree` — hand-rolled minimum viable parser, enough to handle the trivial grammar
- `plcc-model` — minimal spec → model transform, enough to describe the trivial grammar's class hierarchy
- `plcc-lang-emit` — dispatcher: constructs `plcc-<lang>-emit` and execs it via PATH
- `plcc-lang-build` — dispatcher: constructs `plcc-<lang>-build` and execs it via PATH if present; exits 0 silently if absent
- `plcc-lang-list` — scans PATH for `plcc-*-emit` commands and prints language names

One language plugin gets built:

- `plcc-plantuml-emit` — smallest possible plugin. Reads model JSON from stdin, writes a `.puml` file to `--output`. No build command. No runtime library. Declared as a console script in `plcc`'s `pyproject.toml`.

One Level 2 command gets built:

- `plcc-make` — orchestrates the phase sequence in §9 of the architectural spec. Cleans `build/`, runs the pipeline, calls the plugin.

The trivial grammar is chosen to exercise the shape of every contract without needing any feature richness. Something like a grammar for a single expression language with one lexical rule, one syntactic rule, and one semantic section emitting PlantUML.

### 4.3 Why PlantUML first

PlantUML is the simplest possible language plugin. It has no runtime library, no build step, and its output is a single text file that can be visually verified by rendering it in a browser or local tool. It proves the PATH-based plugin discovery mechanism, the command contract, and the end-to-end pipeline without the complexity of a runnable interpreter. It is "hello world" for the plugin system.

### 4.4 Acceptance criteria

- `plcc-make trivial.plcc` produces `build/spec.json`, `build/model.json`, and `build/diagram/<something>.puml`.
- Running the generated `.puml` through PlantUML renders a valid class diagram.
- The diagram correctly represents the trivial grammar's class hierarchy (manually verified).
- `plcc-plantuml-emit` is discovered via PATH; `plcc-lang-list` finds it.
- `plcc-make -h` describes the tool correctly.
- CI runs the skeleton end-to-end against the trivial grammar and asserts the expected output exists.

### 4.5 Explicitly deferred to later phases

- Handling any grammar more complex than the trivial one (Phases 2, 3)
- Runnable interpreters (Phase 2)
- Backwards compatibility with v8 grammars (Phase 3)
- Error records and error rendering (Phase 2 at the earliest)
- `plcc-scan`, `plcc-parse`, `plcc-rep` orchestrators (Phase 4)
- PyPI publication (Phase 4)

### 4.6 Phase 1 design document scope

The phase design doc will decide: the exact shape of the trivial grammar; the exact JSON schemas for spec, token, tree, and model (minimum viable versions); the internal module layout within the `plcc` package for the Level 0 primitives; how `pyproject.toml` declares console scripts for the dispatchers and built-in language plugins; the plugin package's directory layout; how `plcc-make` locates the grammar file and `build/` directory relative to the current working directory; how `--semantics` is passed from `plcc-make` through the dispatcher to the plugin; and the testing strategy for the skeleton (unit tests per primitive plus an end-to-end smoke test).

## 5. Phase 2: Python Emitter Thickening

### 5.1 Goal

Grow the skeleton into a pipeline that produces a runnable Python interpreter for a simple arithmetic grammar. `plcc-rep` lands in this phase, and the first interactive REPL session becomes possible.

### 5.2 Strategy

This phase is where the code model earns its keep as a retargeting pivot. The Python emitter is the first emitter that produces code capable of actually running, which means the model must describe enough structure for an emitter to generate:

- Class definitions with inheritance
- Constructors with field initialization
- Method slots with opaque semantic bodies
- Token references and tree-walking
- A top-level entry point that drives the parse → evaluate loop

The parser runtime (`plcc-tree`) thickens from hand-rolled to a real LL(1) parser table driver, consuming the grammar structure that plcc-ng has already validated. Given the scope of Phase 2, the Phase 2 implementation plan should treat the LL(1) parser as a discrete sub-milestone with its own acceptance criteria, so that delays in parser development do not block progress on emitter and REPL work. `plcc-model` thickens to describe a realistic class hierarchy instead of the trivial skeleton. `plcc-python-emit` gets built out with templates, a bundled runtime library, and enough emission logic to handle the simple arithmetic grammar end-to-end. `plcc-rep` orchestrates the runtime pipeline and handles tty prompting.

Error records (§8 of the architectural spec) are introduced in this phase because the REPL needs them: a malformed program in the REPL must produce an error record that the interpreter renders without tearing down the pipeline.

The test grammar for this phase is a simple expression-evaluator language: numeric literals, addition, subtraction, multiplication, division, parenthesization. Enough to have a real tree, real semantic methods, real evaluation, and a meaningful REPL interaction.

### 5.3 Why Python before Java

Per the architectural spec §16 (open risks): the code model is the retargeting pivot, and building Python before Java forces the model to be language-neutral by construction. If Java were built first, the model would quietly accumulate Java-isms that only surface when a second target is attempted. Python is the stress test that prevents that accumulation.

### 5.4 Acceptance criteria

- `plcc-make arith.plcc` produces `build/py/` containing a runnable Python interpreter for the test grammar.
- The generated Python interpreter includes the bundled `runtime/` directory (per spec §9).
- `plcc-rep arith.plcc` starts a REPL. Typing `1 + 2 * 3` produces `7`. Typing a malformed expression produces an error message and the REPL continues.
- `plcc-rep arith.plcc program.txt` evaluates the program and exits.
- `cd build/py && python main.py < program.txt` works as a way to invoke the generated interpreter without `plcc-rep`.
- Error records flow through the pipeline as in-band JSON; they are never confused with tool failures (which still use stderr and nonzero exit codes).
- `plcc-tree` is a real parser, not a hand-rolled stub.
- `plcc-model` describes the test grammar's class hierarchy accurately enough for Python emission.

### 5.5 Explicitly deferred to later phases

- Java emission (Phase 3)
- Passing the `languages` backwards-compat test suite (Phase 3)
- `plcc-scan` and `plcc-parse` visualizer commands (Phase 4)
- PyPI publication (Phase 4)

### 5.6 Phase 2 design document scope

The phase design doc will decide: the exact shape of the code model JSON beyond the skeleton (inheritance, method slots, semantic blocks, type representation); the LL(1) parser table format and runtime algorithm; the template strategy for Python code emission (Jinja, string templates, or ad-hoc construction); the layout and content of the bundled Python runtime library; the error record schema; the `plcc-rep` tty detection and prompting behavior; the test grammar's exact shape; and the test strategy for generated interpreter correctness.

## 6. Phase 3: Java Emitter and Backwards Compatibility

### 6.1 Goal

Port v8's Java generation logic into a `plcc-java-emit` plugin, and iterate until the `languages` test repository's full suite passes in CI.

### 6.2 Strategy

This is the phase that makes v9 a drop-in replacement for v8 for existing users. By this point, the code model is stable (Phase 2 stress-tested it), `plcc-make` works end-to-end (Phase 1), and the plugin contract is proven (Phase 1). What's new in this phase is:

- A `plcc-java-emit` command with emission logic ported from v8's Java generator
- A bundled Java runtime library inside the plugin, distilled from v8's runtime support classes
- A `build()` hook on the Java emitter that runs `javac`
- Whatever additions to the code model are needed to describe language constructs that v8 grammars use but the Python test grammar did not
- CI integration for the `languages` test suite as a continuous backwards-compat signal

The port is not a rewrite of v8's Java generator. Wherever possible, v8's existing logic is adapted rather than reinvented — the goal is semantic equivalence of output, not improvement. Any improvement happens only when v8's approach cannot be expressed as a code-model-consuming emitter without Java-isms leaking upward.

The `languages` suite runs continuously throughout the phase. It starts red (the Java emitter doesn't exist at phase start) and iteratively turns green grammar by grammar as the emitter handles more features. A phase progress board tracks which of the `languages` grammars have passed.

### 6.3 The red CI bet

This phase is where the strategic bet from Axis 2 pays off — or costs us. The `languages` CI job has been red since the start of v9 development, and only now does it turn green. The bet is that a code model stress-tested by Python before Java is more language-neutral than one that was Java-first, and therefore the port goes faster than it would have without Phase 2's pressure.

If the bet is wrong and the code model turns out to be Python-biased instead of language-neutral, this phase will reveal it, and the response will be an architectural amendment per §2.1 followed by rework. The phase retro is especially important here.

### 6.4 Acceptance criteria

- `plcc-java-emit` exists on PATH and is discovered by `plcc-lang-list`.
- `plcc-make <grammar>` for any grammar in the `languages` repo produces working Java code in `build/Java/` with a compiled class hierarchy after `plcc-java-build` runs.
- The full `languages` test suite passes in CI on `multi-lang`.
- The Java runtime library is bundled inside the `plcc-java-emit` package per spec §10.2.
- Semantic compatibility (spec §13) is achieved: generated Java may differ from v8's output in names and layout, but runtime behavior is equivalent as measured by the `languages` suite.

### 6.5 Explicitly deferred to later phases

- `plcc-scan` and `plcc-parse` visualizer commands (Phase 4)
- PyPI publication (Phase 4)
- Learning materials updates (Phase 5)
- Stable release (Phase 5)

### 6.6 Phase 3 design document scope

The phase design doc will decide: the exact mapping from v8's code generator to the `emit()` callable; the bundled Java runtime library's content and internal API; the `javac` invocation strategy for the `build()` hook; the CI configuration that runs the `languages` suite; the strategy for handling any grammar in `languages` that reveals a code model gap (architectural amendment vs. emitter workaround); and the process for tracking phase progress against the full grammar list.

## 7. Phase 4: Polish and Prerelease

### 7.1 Goal

Finish the pedagogical visualizer commands (`plcc-scan`, `plcc-parse`), ready the package for PyPI, and publish `plcc==9.0.0a1` as the first prerelease for early adopters.

### 7.2 Strategy

By the start of this phase, the hard architectural work is done: the pipeline runs end-to-end, both Python and Java emitters work, and the `languages` suite is green. What remains is user-facing polish and the plumbing to get v9 into pip users' hands.

`plcc-scan` and `plcc-parse` are the visualizer commands that let students watch the pipeline's intermediate outputs: tokens and parse trees in human-readable form. They reuse the Level 0 primitives directly, format the output for terminals, and handle the same file+stdin input model as `plcc-rep`. They are small additions on top of infrastructure that already exists.

PyPI publication requires `pyproject.toml` polish: correct metadata, classifiers, console-script entry points for every Level 0 and Level 2 command and every built-in language plugin (`plcc-plantuml-emit`, `plcc-python-emit`, `plcc-java-emit`, `plcc-java-build`), README rendering on PyPI, and a release workflow. No entry-point group is needed — discovery is PATH-based (see architectural spec §17.2).

**Built-in plugin packaging:** the three built-in language plugins (Java, Python, PlantUML) are bundled inside the `plcc` package itself as submodules (`plcc.lang.java`, `plcc.lang.python`, `plcc.lang.plantuml`) and exposed via console scripts in `plcc`'s own `pyproject.toml`. A plain `pip install plcc` installs all three with no additional packages or entry-point group registration.

**Plugin consolidation in this phase:** Phases 1–3 each build a language plugin that is already a console script in `plcc`'s `pyproject.toml` (since the built-in plugins live inside `plcc` from Phase 1). No separate packages to consolidate — the PATH-based contract means the plugins are ready for PyPI publication as part of `plcc` with no restructuring needed. The Phase 4 implementation plan should verify that the `plcc-lang-*` dispatchers and all three built-in plugins install and are discoverable after a clean `pip install`.

The first prerelease is tagged `9.0.0a1` and published. The prerelease tag signals that v9 is not yet considered stable and that API changes are possible. Early adopters install with `pip install --pre plcc` and provide feedback.

### 7.3 Acceptance criteria

- `plcc-scan <grammar> <program>` prints the token stream in a human-readable format.
- `plcc-parse <grammar> <program>` prints the parse tree in a human-readable format.
- Both visualizer commands handle file and stdin input per spec §6.
- `pip install plcc` on a fresh environment (Linux, macOS, Windows) installs v9 and all three built-in emitters with no additional steps.
- `plcc-make --help` (and every other Level 2 command's `--help`) produces useful output.
- `plcc==9.0.0a1` is published to PyPI.
- The `languages` suite still passes after the packaging polish (no regressions from PyPI publication).

### 7.4 Explicitly deferred to later phases

- Stable 9.0.0 release (Phase 5)
- Learning materials updates (Phase 5)
- Deprecation timeline for v8 (Phase 5)

### 7.5 Phase 4 design document scope

The phase design doc will decide: the exact terminal output format for `plcc-scan` and `plcc-parse`; how they present error records from the pipeline; the full `pyproject.toml` layout; the release workflow and publishing credentials; the GitHub Actions or equivalent CI configuration for tagged releases; whether built-in emitters are installed as true dependencies or as part of the `plcc` package itself.

## 8. Phase 5: Stable Release

### 8.1 Goal

Iterate on prereleases based on early-adopter feedback, coordinate the update of learning materials, and publish `plcc==9.0.0` stable.

### 8.2 Strategy

Phase 5 is the least mechanical of the phases. It is about iteration, coordination, and release timing. The work is:

- **Prerelease iteration.** Additional alphas (`9.0.0a2`, `9.0.0a3`, …) and betas (`9.0.0b1`, …) respond to feedback from the two pilot faculty. Each prerelease is cut from `multi-lang` with a version bump and a PyPI publish.
- **Pilot evaluation with the two faculty users.** The known PLCC user population consists of two faculty: the project maintainer and one colleague who meets with the maintainer weekly. Prereleases are evaluated through those weekly conversations and any ad-hoc testing either faculty chooses to do against their own course materials. The exact test cadence and criteria are decided during the Phase 5 brainstorm — which may be as informal as "does it work for the next semester's course?" — but the small user population means pilot testing is a deliberate conversation, not a public beta program.
- **Learning materials update.** The parallel effort to update course materials, example grammars, and documentation to match v9's commands and output. The maintainer owns this directly. The stable release is gated on this work being sufficiently complete for at least one of the two faculty's courses.
- **Deprecation timeline.** A public announcement names the dates on which (a) v8 transitions to security-fix-only support, (b) v8 is frozen. These dates give existing users a known runway.
- **Stable release.** Merge `multi-lang` into `main` of the plcc-ng repository. Publish `plcc==9.0.0` stable to PyPI from the merged `main`.

Integration of plcc-ng into the plcc repository is explicitly out of scope for this phase. That decision is revisited once v9 is complete and has demonstrated buy-in from its user community.

### 8.3 Acceptance criteria

- At least one of the two pilot faculty has run v9 against their own course workflow (or an approximation of it) and reported no blocking issues.
- Learning materials are updated to match v9 commands and behavior.
- `multi-lang` has been merged into `main` of the plcc-ng repository.
- `plcc==9.0.0` is published to PyPI as a stable release.
- A deprecation timeline for v8 has been published in a public location.

### 8.4 Phase 5 design document scope

The phase design doc will decide: the exact sequence of prerelease versions; the pilot user list and feedback collection mechanism; the learning materials update checklist; the deprecation timeline dates; the cutover procedure (PR-reviewed merge vs direct merge); and the exact wording of the deprecation announcement.

## 9. Cross-Phase Concerns

### 9.1 TDD discipline

Every primitive, every plugin, and every orchestrator is built test-first. plcc-ng already uses TDD; the existing test suite is the starting point and is extended, not replaced. The writing-plans skill's task granularity (write failing test → run to confirm failure → write minimal code → run to confirm pass → commit) applies to every task in every phase-level plan.

### 9.2 CI strategy

CI runs on every push to `multi-lang` throughout development. The CI job set grows phase by phase:

- **After Phase 1:** plcc-ng's existing tests run, plus the skeleton smoke test (trivial grammar → PlantUML). The Phase 1 implementation plan should inventory which existing plcc-ng tests remain valid as-is, which need to be migrated to the new pipeline shape (e.g. tests for the `spec` and `scan` CLIs that are being renamed), and which can be deleted. Tests should not be skipped indefinitely; any test that is temporarily broken by Phase 1 work is either migrated or deleted in that same phase.
- **During Phase 2:** Python emitter tests and the REPL integration tests are added.
- **During Phase 3:** the `languages` suite is added and runs continuously — starting red and turning green grammar by grammar.
- **Phase 4:** packaging smoke test (install from built wheel and run a smoke test grammar).
- **Phase 5:** release workflow testing on prerelease tags.

Tests that are expected to be red (the `languages` suite during Phase 3 before grammars are ported) are marked as such in CI so the overall pipeline status remains meaningful. They flip to required once their grammar passes locally.

### 9.3 Prerelease cadence

Prereleases are cut from `multi-lang` at natural milestones:

- `9.0.0a1` — at the end of Phase 4 (first PyPI publication; pipeline complete through Java and packaged)
- `9.0.0a2`, `a3`, … — during Phase 5 as iteration warrants
- `9.0.0b1` — when most known issues are addressed and the release is feature-complete
- `9.0.0rc1` — when ready for stable release, pending final learning materials sync
- `9.0.0` — the stable release, published from `main` after the cutover merge

Nothing before Phase 4 is published. Earlier phases don't produce usable artifacts for end users.

### 9.4 Phase retros feeding back into the architectural spec

Section 2.1 notes that architectural amendments to the spec are rare and intentional. When a phase retro surfaces a decision that needs to be amended, the amendment takes the form of a new dated section appended to `2026-04-12-multi-lang-pipeline.md`, clearly labeled "Amendment from Phase N retro: …". The original sections are not edited. This keeps the history of architectural thinking visible and preserves the context in which later decisions were made.

Routine phase learnings (things that worked, things that didn't, surprises that didn't warrant spec changes) are captured in each phase design doc's retro section, not the architectural spec.

## 10. What Each Phase Owes the Next

Each phase leaves behind artifacts that the next phase builds on. Enumerating those artifacts explicitly helps surface design debt (when a phase accepts an artifact that isn't ready) and helps each phase brainstorm start with a clear picture of what's already fixed.

**Phase 1 → Phase 2:**
- All five Level 0 primitives exist as console-script entry points
- Minimum viable JSON schemas for spec, token, tree, model are defined
- Plugin discovery mechanism works
- `plcc-make` orchestrator works
- End-to-end CI smoke test exists and is green
- A known-working trivial grammar and its expected `build/` output

**Phase 2 → Phase 3:**
- Code model is rich enough to describe a realistic class hierarchy (inheritance, method slots, semantic blocks, type representation)
- `plcc-tree` is a real LL(1) parser runtime
- `plcc-rep` orchestrator works end-to-end
- Error record schema is defined and flowing in-band
- Python emitter provides a working reference for what an emitter plugin looks like in practice
- Bundled runtime library pattern is established

**Phase 3 → Phase 4:**
- Java emitter plugin works
- `languages` test suite passes in CI
- Code model is stable across two target languages (no more expected churn)
- A known-good baseline for backwards compatibility
- All three built-in language plugins (`plcc-plantuml-emit`, `plcc-python-emit`, `plcc-java-emit`, `plcc-java-build`) are console scripts in `plcc`'s `pyproject.toml` and discoverable via `plcc-lang-list`

**Phase 4 → Phase 5:**
- Pipeline is installable via `pip install --pre plcc` on every supported OS
- `plcc-scan` and `plcc-parse` visualizers work
- First prerelease is published and at least internally validated
- Release workflow exists and is repeatable

**Phase 5 → post-release:**
- v9.0.0 stable on PyPI
- `main` of the plcc-ng repository is v9
- A published deprecation timeline for v8

## 11. What This Plan Does Not Decide

- Exact file paths, module names, or class hierarchies inside `plcc` core (Phase 1 design doc)
- The exact schema of any JSON format (Phase 1 and Phase 2 design docs)
- The LL(1) parser algorithm and runtime (Phase 2 design doc)
- How semantic `%%%` blocks are lexed and attached to methods (Phase 2 design doc)
- The emitter template strategy for any language (per-phase design docs)
- The bundled runtime library's internal API for any language (per-phase design docs)
- The error record schema (Phase 2 design doc)
- The `languages` suite integration mechanics (Phase 3 design doc)
- The PyPI release workflow mechanics (Phase 4 design doc)
- The exact deprecation timeline dates (Phase 5 design doc)

These are deliberately deferred. Forcing them now would either produce speculative designs that don't survive first contact with the code or lock in choices before we've earned the right to make them.

## 12. Open Questions for Review

- **Maintainer capacity.** This plan assumes single-developer bandwidth with AI assistance. If additional maintainers join any phase, their onboarding is the responsibility of the phase-level design doc, not this roadmap.

### 12.1 Questions resolved during roadmap review

- **Phase 3 red CI duration.** Resolved: deferred to the Phase 3 brainstorm. The Phase 3 brainstorm will decide whether to mark the `languages` CI job as advisory (non-blocking) for the duration of Phase 3, or to use a separate CI configuration, or to accept a red required job. §9.2 already specifies the mechanism (expected-red jobs are marked as such); the exact CI configuration choice is a Phase 3 brainstorm decision.
- **Phase 3 conflict resolution policy.** Resolved: the conflict policy is decided during the Phase 3 brainstorm, not pre-decided in this roadmap. §6.2 now reflects this.
- **Language plugin command contract.** Resolved: the plugin contract is defined as CLI commands (`plcc-<lang>-emit`, `plcc-<lang>-build`), not Python callables. Discovery is PATH-based. `plcc-emit` is retired; the dispatchers are `plcc-lang-emit`, `plcc-lang-build`, `plcc-lang-list`. `plcc-make` calls `plcc-lang-emit` and `plcc-lang-build` as subprocesses. The `plcc.emitters` entry-point group is eliminated. See architectural spec §17.2 and `docs/superpowers/specs/2026-04-12-language-plugin-command-contract-design.md`.
- **Built-in plugin packaging.** Resolved: the three built-in language plugins are bundled inside `plcc` as submodules (`plcc.lang.java`, `plcc.lang.python`, `plcc.lang.plantuml`) and exposed as console scripts in `plcc`'s `pyproject.toml`. No separate PyPI packages, no entry-point group. §7.2 captures this.
- **Phase 5 pilot user identification.** Resolved: the known PLCC user population is the maintainer and one colleague who meets with the maintainer weekly. Pilot evaluation happens through that existing conversation cadence; the exact mechanics are decided during the Phase 5 brainstorm. §8.2 captures this.
- **Integration with the plcc repository.** Resolved: integration of plcc-ng into the plcc repository is out of scope for v9.0.0. Development happens entirely within the plcc-ng repository. Integration is reconsidered once v9 is complete and has demonstrated buy-in.
