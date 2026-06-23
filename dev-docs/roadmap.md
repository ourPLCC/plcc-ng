# Roadmap

4 open issues as of 2026-06-23. Grouped by theme; within a theme the order reflects dependencies.

## Phase 1 — Fix: emitter correctness

| # | Issue | Notes |
| --- | --- | --- |
| [104](issues/104-java-class-fragment-missing.md) | Add `class` fragment support to Java emitter | Update `class_file.java.jinja` and `emit.py`; Python emitter has prior art |
| [105](issues/105-haskell-fragment-concrete-class-name-silently-ignored.md) | Warn when Haskell fragment uses concrete class name | Fragment silently dropped; should warn or redirect to parent abstract module |

## Phase 2 — Docs: new language extensions

| # | Issue | Notes |
| --- | --- | --- |
| [106](issues/106-docs-javascript-language-extension.md) | Add documentation for the JavaScript language extension | Model on existing Java/Python language guide pages |
| [107](issues/107-docs-haskell-language-extension.md) | Add documentation for the Haskell language extension | Note GHC/cabal requirements; mention issue 105 workaround until fixed |
