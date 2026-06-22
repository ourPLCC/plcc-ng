# Design: Tabbed Code Blocks for Language-Specific Alternatives (Issue 080)

**Date:** 2026-06-22
**Issue:** [080](../../../../dev-docs/issues/080-tabbed-code-blocks.md)

## Problem

Pages with semantic section examples show Python and Java variants sequentially.
Users who only care about one language must visually skip the other throughout the docs.

## Solution

Use MkDocs Material's native content tabs to present Python and Java variants side by side.
Tab selection syncs across all tab groups on the page and persists across pages for the session.

## Configuration

Add two feature flags to `mkdocs.yml`:

```yaml
features:
  - content.tabs        # enables === "Label" tab syntax
  - content.tabs.link   # syncs matching tab labels across pages
```

No other configuration changes are needed.

## Tab Structure

Tab labels are exactly `"Python"` and `"Java"`. Python always appears first because it works
out of the box — users only need Python to install plcc-ng and run their spec. Java requires
a separate JDK install.

```markdown
=== "Python"
    ```text
    <python content>
    ```

=== "Java"
    ```text
    <java content>
    ```
```

Because `content.tabs.link` is enabled, any tab group using these same labels on any page
will stay in sync. Selecting "Java" on the quick-start page pre-selects "Java" on the
semantic section and examples pages.

## Pages Changed

### `docs/quick-start.md`

The `spec.plcc` code block currently shows a Python-only grammar. Replace it with a
two-tab block containing the complete grammar in both languages:

- **Python tab**: current content unchanged
- **Java tab**: identical lexical and syntactic sections; semantic section uses `Java`
  as the language declaration and Java method syntax in `%%%` blocks

Both tabs are complete, copy-pasteable grammar files.

### `docs/language-guide/index.md`

The introductory grammar example currently shows a Python-only semantic section. Replace
with a two-tab block using the same pattern as quick-start.

### `docs/language-guide/semantic.md`

Contains a mix of: existing Python/Java pairs shown sequentially, and Python-only examples
that need a Java variant added. Prose is unchanged throughout.

Four code block groups require tab treatment:

1. **Basic code injection** (`Exp`/`_run`) — existing Python and Java blocks shown
   sequentially; merge into a single tabbed block
2. **Hooks example** (`WholeExp:import` + `WholeExp`) — Python-only; add a Java tab
   (Java uses `import` statements in the `:import` hook and Java method syntax in the body)
3. **Standalone classes** (`Helper`) — Python-only; add a Java tab with an equivalent
   Java class declaration
4. **Packages and imports** — prose only, no code block; no tabs needed

### `docs/language-guide/examples.md`

The `subtract.plcc` grammar currently ends with a Python semantic section. Replace
with a two-tab block:

- **Python tab**: full grammar unchanged
- **Java tab**: full grammar with `Java` replacing `Python` and Java method syntax
  (`public <ReturnType> methodName()`) in the `%%%` blocks

Both tabs are complete, copy-pasteable grammar files.

## Tab Content — Java Equivalents

The Java semantic section declares `Java` as the language name and uses Java method syntax.
For each Python method, the Java equivalent is:

| Python | Java |
| --- | --- |
| `def _run(self):` | `public void _run() {` |
| `def eval(self):` | `public <Type> eval() {` |
| `return int(self.whole.lexeme)` | `return Integer.parseInt(whole.lexeme);` |
| `return self.exp1.eval() - self.exp2.eval()` | `return exp1.eval() - exp2.eval();` |
| `print(self.exp.eval())` | `System.out.println(exp.eval());` |

Field access drops `self.` in Java (fields are accessed directly).

## Scope

Only pages with semantic section examples are changed. Lexical and syntactic section pages
(`lexical.md`, `syntactic.md`) have no language-specific examples and are not changed.
The CLI reference pages are not changed.
