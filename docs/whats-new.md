# What's new

Curated highlights of what's changed in PLCC-ng and why it matters
to you. For the full commit-level history, see
[GitHub Releases](https://github.com/ourPLCC/plcc-ng/releases).

<!-- last-covered: v2.0.1 -->

## 2026-07-XX — PLCC-ng v2.0.1

A patch release fixing one parsing bug in repetition rules.

### Repetition rules keep their uncaptured tokens

A repetition rule (`**=`) whose body contains a token you don't capture —
the `EQUALS` in `<Decls> **= <SYMBOL> EQUALS <Exp>` — used to drop that
token silently. The grammar passed LL(1) analysis, and then parsing failed
at the first uncaptured token with a confusing "no production for" error.
PLCC-ng now matches every symbol in a repetition body on every repetition,
building lists only from the ones you captured. See
[Repetition rules](language-guide/syntactic.md#repetition-rules).

## 2026-07-26 — PLCC-ng v2.0.0

The first release since 1.0 tightens the language runtime and fixes
several ways generated code could surprise you. One change is breaking:
if you have specs written against v1.0.0, update your `_run()` methods
before upgrading — see below and the migration guide's
[breaking behavior changes](migration.md#breaking-behavior-changes).

### `_run()` now returns a string

Your semantics' entry point, `_run()`, now **returns** its output as a
string and lets the runtime print it — the same contract in all four
languages. Java's `_run()` changes from `void` to `String`; Python and
JavaScript's `_run()` must return an actual `str`/`string` rather than an
`int`, list, or other value. A non-string return is now reported as a
`specification_error` instead of silently producing quoted or malformed
output, and no language's `_run()` may print to stdout directly. This is
the one breaking change in this release: existing v1.0.0 specs need
updating, and the
[migration guide](migration.md#breaking-behavior-changes) shows the
before/after for each language.

### Field names can't collide with reserved words

A captured field whose name is a reserved word in your target language —
for example a field auto-named `var` in JavaScript — used to slip through
and fail later with a confusing error from the generated code. PLCC-ng
now detects this and reports it against your spec, in Python, Java,
Haskell, and JavaScript. Because the check is per target language, it
fires when you emit or run for that language, not during language-neutral
grammar validation. See
[Reserved words](language-guide/syntactic.md#reserved-words).

### More predictable auto-generated field names

Two bugs in how PLCC-ng derives captured-field names are fixed. An
alternative name (`:name`) now keeps its original case, so a camelCase
alt-name no longer produces a mismatched field. And a bare multi-word
nonterminal capture now decapitalizes only its first letter
(`<OneMore>` → field `oneMore`) instead of lowercasing the whole name
(`onemore`), matching the naming rule in the
[migration guide](migration.md#7-update-captured-field-syntax). A v1.0.0
spec that relied on the old full-lowercasing will see its generated field
names change.

### More correct LL(1) grammar analysis

PLCC-ng's LL(1) analysis now recognizes a nullable production no matter
when it is registered, so FOLLOW sets are computed correctly (including
end-of-input) for grammars whose nullable productions appear late.
Grammars that were previously mis-analyzed are now handled correctly.

### Documentation examples that actually run

Every language's quick-reference example grammar is now genuinely LL(1),
and its generated code compiles and runs exactly as shown — so copying an
example straight from the docs works the first time. See the per-language
guides for [Python](language-guide/languages/python.md),
[Java](language-guide/languages/java.md),
[Haskell](language-guide/languages/haskell.md), and
[JavaScript](language-guide/languages/javascript.md).

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
