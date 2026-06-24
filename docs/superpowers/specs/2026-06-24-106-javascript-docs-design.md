# JavaScript Language Extension Documentation Design

**Issue:** 106
**Date:** 2026-06-24

## Overview

Add user-facing documentation for the JavaScript language extension introduced in issue 066. At the same time, establish a per-language page structure that can accommodate future language extensions without restructuring.

## Goals

- Students (language authors writing plcc-ng specs) can find everything they need for their chosen language on one page.
- The structure scales cleanly: adding a new language means adding one file.
- Existing Java and Python content is reorganized into the same template rather than left in the old tabbed format.

## Audience

Students implementing new languages using plcc-ng's spec language. Not language extension developers adding new backends.

## File Changes

### New files

```
docs/language-guide/languages/
  javascript.md
  java.md
  python.md
docs/cli/commands/
  plcc-javascript-emit.md
  plcc-javascript-run.md
```

### Modified files

```
docs/language-guide/semantic.md          — slim to concepts, link to per-language pages
docs/cli/guide/language-extensions.md   — add ## plcc-javascript section
mkdocs.yml                               — add Languages sub-nav, add JS command docs
```

### mkdocs.yml nav change

```yaml
- Language Guide:
  - Overview: language-guide/index.md
  - Lexical Section: language-guide/lexical.md
  - Syntactic Section: language-guide/syntactic.md
  - Semantic Section: language-guide/semantic.md
  - Languages:
    - JavaScript: language-guide/languages/javascript.md
    - Java: language-guide/languages/java.md
    - Python: language-guide/languages/python.md
  - Examples: language-guide/examples.md
```

## semantic.md After Slimming

`semantic.md` becomes the *what and why* — the language-agnostic concepts. All language-specific tabbed examples are removed. Sections retained:

- **Section header** — the `%` line and language tag syntax; remove the "supported languages are Java/Python" enumeration.
- **Code blocks** — the `%%%` block syntax; replace the Java/Python tab example with a single generic pseudocode snippet.
- **Field access** — the concept (fields become instance variables); drop language-specific access examples.
- **Entry point `_run`** — what `_run` is and that `_Start` provides a default; drop language-specific examples.
- **Hooks** — the `ClassName:hook` syntax and the concept of placement; keep the hook-name descriptions; drop Java/Python tab examples.
- **Adding standalone classes** — the concept; drop language-specific tabs.
- **Choose your language** — new closing section: one-sentence framing + bulleted links to JavaScript, Java, Python pages.

A student reads `semantic.md` once to understand the model, then lives on their language page.

## Per-Language Page Template

Every language page follows the same section order:

1. **Prerequisites** — minimum runtime version, install command or link to official install docs.
2. **Enabling in a spec** — the exact language tag after `%`, with a two-line snippet.
3. **Quick reference example** — the canonical `.plcc` spec with semantic section in this language, shown complete. Serves as a fast lookup for returning users; all later sections reference snippets from it.
4. **BNF to language constructs** — table or short subsections, one row per grammar construct, referencing the canonical example:
   - Concrete non-terminal rule → class with constructor and fields
   - Abstract non-terminal (has alternatives) → abstract class, no constructor
   - RHS non-terminal reference → instance field (syntax to access it)
   - RHS terminal/token → Token field (syntax to access `.lexeme` or equivalent)
   - Arbno → array/list field
   - Named field (`:name` syntax on RHS) → the field name used in generated code
5. **Fragment kinds** — table: kind | where injected | typical use. Lists only the kinds the language actually supports.
6. **`_run` entry point** — method signature in this language, what it should return, what the default `_Start._run` does.
7. **Referencing other generated classes** — how to call or import a sibling generated class from semantic code (this is language-specific and a common pain point).
8. **Generated output** — what files `plcc-<lang>-emit` writes; which are overwritten on every run vs. safe to edit.
9. **Running the example** — pipeline invocation for the canonical example and expected I/O.
10. **Commands** — two-row table (`plcc-<lang>-emit`, `plcc-<lang>-run`) with one-sentence descriptions and links to command reference docs. Note if there is no build step and why.
11. **Restrictions** — things that work in other supported languages but not this one, or known limitations.
12. **Tips** — short practical notes.

## Canonical Example

The same grammar and semantic implementation is used on every language page, enabling easy cross-language comparison.

**Grammar (language-agnostic):**

```text
%% lexical
NUM \d+
PLUS \+
SKIP \s+

%% syntactic
<Prog>   ::= <Exp>*
<Exp>    ::= <AddExp>
           | <NumExp>
<AddExp> ::= <Exp:left> PLUS <Exp:right>
<NumExp> ::= NUM
```

**Constructs exercised:**

| Construct | Where |
|-----------|-------|
| Arbno (zero or more) | `<Prog> ::= <Exp>*` |
| Abstract non-terminal (alternatives, no constructor) | `<Exp>` |
| Concrete non-terminal with named non-terminal fields | `<AddExp>` (`left`, `right`) |
| Terminal/token field | `<NumExp>` (`num`) |

The semantic section implements `eval()` on each class and overrides `_run()` on `Prog` to print results — just enough to show how every construct is accessed.

No standalone helper classes or every hook kind are demonstrated; those are covered in the relevant sections using targeted snippets.

## JavaScript-Specific Details (for javascript.md)

### Prerequisites

Node.js. Minimum version: the generated code uses ES6 classes, static class fields, and CommonJS modules — Node.js 12 or later.

### Language tag

```text
%
javascript
```

### Fragment kinds

| Kind | Where injected | Typical use |
|------|----------------|-------------|
| `top` | Before `require` lines at top of file | File-level constants, `'use strict'` |
| `import` | After generated `require` lines, before class | Additional `require` calls |
| `init` | Inside constructor, after field assignments | Initialize extra instance state |
| `body` | Inside class body | Methods |
| `file` | Replaces entire file | Standalone helper classes |

No `class` hook. JavaScript has no interfaces and no multiple inheritance, so there is nothing to inject into the class declaration line.

### `_run` entry point

```javascript
_run() {
    // return value is ignored by the runtime
}
```

The default `_Start._run()` prints `String(this)` to stdout.

### Referencing other generated classes

Generated files use CommonJS. To call a sibling class, require it at the top of the file using the `import` or `top` fragment:

```text
MyClass:import
%%%
const { OtherClass } = require('./OtherClass');
%%%
```

### Generated output structure

```
<output>/
  main.js           — entry point; overwritten on every emit
  _Start.js         — default base for the start class; overwritten on every emit
  <ClassName>.js    — one per class; overwritten on every emit
  runtime/
    base.js         — overwritten on every emit
    registry.js     — overwritten on every emit
    deserialize.js  — overwritten on every emit
```

All files are overwritten on every `plcc-javascript-emit` run. Do not edit them directly; put custom code in the spec's semantic section.

### No build step

`plcc-javascript-run` invokes `node main.js` directly. There is no `plcc-javascript-build` — Node.js does not require a compilation step, so `plcc-lang-build` skips silently when no build command is found.

### Restrictions

- No `class` hook (unlike Python).
- Generated code uses CommonJS (`require`/`module.exports`). ESM (`import`/`export`) is not supported.
- All files in the output directory are overwritten on every emit run.

### Tips

- Use `console.error(...)` for debug output. The runtime reads `_run()`'s return value via stdout; writing to stdout from inside `_run()` will corrupt the output.
- `this.num.lexeme` is always a string. Use `parseInt(this.num.lexeme)` or `parseFloat(this.num.lexeme)` to get a numeric value.

## CLI Command Docs

`plcc-javascript-emit.md` and `plcc-javascript-run.md` follow the same structure as the existing `plcc-python-emit.md` and `plcc-java-emit.md`: one-line description, usage block, arguments table, example invocation.

`language-extensions.md` gets a `## plcc-javascript` section matching the style of the existing `## plcc-python` and `## plcc-java` sections: a short paragraph and a two-row command table.
