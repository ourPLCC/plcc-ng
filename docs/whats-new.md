# What's New

Curated highlights of what's changed in PLCC-ng and why it matters
to you. For the full commit-level history, see
[GitHub Releases](https://github.com/ourPLCC/plcc-ng/releases).

<!-- last-covered: v1.0.0 -->

## 2026-07-06 — PLCC-ng v1.0.0

PLCC-ng reaches 1.0: the next generation of
[PLCC](https://github.com/ourPLCC/plcc) is ready for classroom use.
If you're coming from PLCC, here's a tour of what's changed and why
it matters. Migrating a course? Start with the
[migration guide](migration.md).

### Write semantics in four languages

PLCC generated Java, and only Java. PLCC-ng generates scanners,
parsers, and interpreters in Python, Java, Haskell, or JavaScript —
pick the language your course teaches and write your semantics in
it. Start with the [Language Guide](language-guide/index.md), then
see the per-language pages for
[Python](language-guide/languages/python.md),
[Java](language-guide/languages/java.md),
[Haskell](language-guide/languages/haskell.md), and
[JavaScript](language-guide/languages/javascript.md).

### Simpler native installation

Installing PLCC-ng natively is now a single `pip install plcc-ng` —
no shell-script installer to fetch and configure. See
[Installation](installation.md) for upgrade, pinning, and uninstall
instructions.

### Three commands to run your language

Day-to-day work needs just three commands, with no separate compile
step: [`plcc-scan`](cli/commands/plcc-scan.md) tokenizes input,
[`plcc-parse`](cli/commands/plcc-parse.md) shows the parse tree, and
[`plcc-rep`](cli/commands/plcc-rep.md) runs your full language in a
read-eval-print loop. Each one orchestrates smaller composable
commands underneath — emitting generated code, building it, feeding
it input — that you can run directly to explore each stage of the
pipeline and how the pieces fit together. See
[Author-facing commands](cli/guide/author-commands.md) and
[Under the hood](cli/guide/under-the-hood.md).

### Diagrams from your spec

The `plcc-diagram` add-on package draws diagrams straight from your
spec file: class diagrams of the object model your semantics program
against, and syntax (EBNF) diagrams of your grammar. See
[plcc-diagram](cli/commands/plcc-diagram.md) and
[plcc-diagram-syntax](cli/commands/plcc-diagram-syntax.md).

### Built to extend

The pipeline is open: language extensions add new target languages,
parser extensions add new parsing algorithms, and diagram extensions
add new visualizations — all discovered and dispatched through the
same CLI conventions. See the
[language](cli/guide/language-extensions.md),
[parser](cli/guide/parser-extensions.md), and
[diagram](cli/guide/diagram-extensions.md) extension guides.

### A real documentation site

You're reading it. The [Language Guide](language-guide/index.md)
covers every section of a spec file with worked examples, and the
[CLI reference](cli/index.md) documents every command and flag.

### Spec syntax has changed

PLCC-ng is not backwards compatible with PLCC: spec files need
updating. Regular expressions switch from Java to Python flavor,
nonterminals become PascalCase, subclass and captured-field syntax
change, and more. The [migration guide](migration.md) walks through
every change step by step, and its
[features not yet in PLCC-ng](migration.md#features-not-yet-in-plcc-ng)
section lists what hasn't made the jump, so you know both sides of
the trade before switching.
