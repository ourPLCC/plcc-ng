# Roadmap

4 open issues as of 2026-07-03.

## Open Issues

### Docs

- **[#128](issues/128-docs-help-options-output-diagnostics.md) — Update command reference pages for Options/Output/Diagnostics help restructuring**
  Issue 115 reorganized `--help` output; command reference pages may be stale.

- **[#130](issues/130-release-sop.md) — Write the release SOP**
  `dev-docs/release-sop.md` is empty; needed before v1.0.

### Features

- **[#131](issues/131-haskell-language-error-not-accessible-from-user-code.md) — Make `LanguageError` accessible from Haskell user code**
  `LanguageError` is defined in generated `Main.hs` but unreachable from user semantics modules; needs a dedicated runtime module.

- **[#112](issues/112-first-major-release.md) — Prepare for first major release (v1.0.0)**
  Define v1.0 criteria and coordinate the remaining pre-1.0 work (docs 128, 130, feature 131).
