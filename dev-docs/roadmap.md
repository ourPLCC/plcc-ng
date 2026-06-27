# Roadmap

7 open issues as of 2026-06-27.

## Open Issues

### Fixes

- **[#115](issues/115-scan-trace-vs-verbose-inconsistency.md) — `plcc-scan --trace` vs `plcc-parse --verbose` inconsistency**
  Diagnostic flag names differ across commands; pick one term and apply it consistently.

- **[#121](issues/121-rep-python-syntax-error-continues.md) — `plcc-rep` continues after Python syntax errors in semantics**
  Build failures from syntax errors should abort the REPL rather than drop into the input loop.

- **[#122](issues/122-rep-python-wrong-output.md) — `plcc-rep` with Python emitter returns object repr instead of value**
  Evaluated expressions show raw object repr; Python semantics are not wired up correctly.

### Features

- **[#111](issues/111-mermaid-extension-redesign.md) — Redesign the Mermaid diagram extension**
  Replace broken CLI renderer with VS Code Markdown preview path using fenced ` ```mermaid ` blocks.

- **[#114](issues/114-lexical-ebnf-diagram.md) — PlantUML EBNF diagram from lexical section**
  Add `plcc-diagram-lexical` command, the lexical counterpart to the existing syntactic diagram.

- **[#112](issues/112-first-major-release.md) — Prepare for first major release (v1.0.0)**
  Define v1.0 criteria, decide emitter support tiers, and write the release SOP.

### Performance

- **[#110](issues/110-e2e-haskell-build-test-performance.md) — E2e Haskell build roundtrip is too slow**
  `cabal build` in the e2e suite takes 4–5 minutes; cache the cabal store or split into fast/slow tiers.
