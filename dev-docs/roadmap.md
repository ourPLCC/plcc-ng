# Roadmap

6 open issues as of 2026-06-30.

## Open Issues

### Docs

- **[#128](issues/128-docs-help-options-output-diagnostics.md) — Update command reference pages for Options/Output/Diagnostics help restructuring**
  Issue 115 reorganized `--help` output; command reference pages may be stale.

- **[#129](issues/129-docs-parser-eof-message-example.md) — Update docs for "end of file" parser error message change**
  Example error output in docs may still show the old `eof` wording.

- **[#130](issues/130-release-sop.md) — Write the release SOP**
  `dev-docs/release-sop.md` is empty; needed before v1.0.

### Features

- **[#131](issues/131-haskell-language-error-not-accessible-from-user-code.md) — Make `LanguageError` accessible from Haskell user code**
  `LanguageError` is defined in generated `Main.hs` but unreachable from user semantics modules; needs a dedicated runtime module.

- **[#132](issues/132-language-error-in-scope-by-default.md) — Make `LanguageError` in scope by default in user semantics code**
  Users must manually import `LanguageError` in each class file; it should be auto-injected by the emitter.

- **[#112](issues/112-first-major-release.md) — Prepare for first major release (v1.0.0)**
  Define v1.0 criteria and coordinate the remaining pre-1.0 work (docs 128–130, features 131–132).
