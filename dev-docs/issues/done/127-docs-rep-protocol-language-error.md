# 127 - Document `plcc-rep` startup handshake, `specification_error`, and `LanguageError`

**Type:** docs
**Date:** 2026-06-30

## Description

`plcc-rep` gained a startup handshake (ready signal) and structured `specification_error` handling, and each language runtime gained a `LanguageError` mechanism for signaling errors from generated code. None of this is documented in `docs/cli/commands/plcc-rep.md` or the per-language extension pages.

## Notes

- `docs/cli/commands/plcc-rep.md` should describe the JSONL protocol: the ready record emitted on startup, and the `specification_error` record emitted when the generated code fails to load.
- Each language extension page (`docs/language-guide/languages/python.md`, `java.md`, `javascript.md`, `haskell.md`) should explain how to raise a `LanguageError` from semantics blocks and what effect it has at runtime (e.g. `plcc-rep` reports it as a `specification_error`).
- `LanguageError` is the intended way for user-written semantics code to signal domain errors; it should be discoverable from the language extension pages, not just the source code.
