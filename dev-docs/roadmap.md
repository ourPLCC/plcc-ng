# Roadmap

4 open issues as of 2026-06-28.

## Open Issues

### Fixes

- **[#115](issues/115-scan-trace-vs-verbose-inconsistency.md) — `plcc-scan --trace` vs `plcc-parse --verbose` inconsistency**
  Diagnostic flag names differ across commands; pick one term and apply it consistently.

### Features

- **[#112](issues/112-first-major-release.md) — Prepare for first major release (v1.0.0)**
  Define v1.0 criteria, decide emitter support tiers, and write the release SOP.

- **[#124](issues/124-drop-mermaid-support.md) — Drop Mermaid diagram support**
  Remove the broken Mermaid extension; PlantUML covers all current diagram needs.

### Performance

- **[#110](issues/110-e2e-haskell-build-test-performance.md) — E2e Haskell build roundtrip is too slow**
  `cabal build` in the e2e suite takes 4–5 minutes; cache the cabal store or split into fast/slow tiers.
