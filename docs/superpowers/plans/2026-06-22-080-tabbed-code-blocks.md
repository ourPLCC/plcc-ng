# Tabbed Code Blocks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Python/Java content tabs to every page with a semantic section example so users can view only the language they care about.

**Architecture:** Enable MkDocs Material's native content tabs feature (`content.tabs` + `content.tabs.link`) and the required `pymdownx.tabbed` Markdown extension; then convert or augment code blocks on four pages. Tab labels are exactly `"Python"` and `"Java"` so that cross-page tab linking works automatically.

**Tech Stack:** MkDocs Material 9.x, pymdownx.tabbed (bundled with mkdocs-material), Markdown

## Global Constraints

- Python tab always appears first (works out of the box; Java requires a separate JDK install)
- Tab labels are exactly the strings `Python` and `Java` — no variation — so `content.tabs.link` syncs them across pages
- Commits on this branch: conventional-commit style; all commits affecting `docs/` or `mkdocs.yml` must NOT append `[skip ci]` — the docs deployment workflow must run
- Build command for verification: `PATH=/workspaces/plcc-ng/.venv/bin:$PATH mkdocs build --strict`
- Working directory for all commands: `/workspaces/plcc-ng/.worktrees/issue-080-tabbed-code-blocks`
- pymdownx.tabbed requires `alternate_style: true` for MkDocs Material v9+

---

### Task 1: Enable content tabs in mkdocs.yml

**Files:**
- Modify: `mkdocs.yml`

**Interfaces:**
- Produces: `content.tabs` and `content.tabs.link` features active; `pymdownx.tabbed` extension registered. All subsequent tasks depend on this.

- [ ] **Step 1: Add features and markdown_extensions to mkdocs.yml**

Open `mkdocs.yml`. Make two edits:

1. In `theme.features`, add the two new entries after `search.suggest`:

```yaml
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - toc.integrate
    - search.suggest
    - content.tabs
    - content.tabs.link
```

2. Append a new top-level `markdown_extensions` block at the end of the file (after the `extra:` block):

```yaml
markdown_extensions:
  - pymdownx.tabbed:
      alternate_style: true
```

The complete final `mkdocs.yml` looks like this:

```yaml
site_name: plcc-ng
site_url: https://ourplcc.github.io/plcc-ng/
repo_url: https://github.com/ourPLCC/plcc-ng
repo_name: ourPLCC/plcc-ng

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - toc.integrate
    - search.suggest
    - content.tabs
    - content.tabs.link
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      toggle:
        icon: material/weather-night
        name: Switch to dark mode
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      toggle:
        icon: material/weather-sunny
        name: Switch to light mode

plugins:
  - search
  - include-markdown
  - mike
  - kroki:
      fence_prefix: ''
      tag_format: svg

nav:
  - Home: index.md
  - Quick Start: quick-start.md
  - Installation: installation.md
  - Migration from PLCC: migration.md
  - Language Guide:
    - Overview: language-guide/index.md
    - Lexical Section: language-guide/lexical.md
    - Syntactic Section: language-guide/syntactic.md
    - Semantic Section: language-guide/semantic.md
    - Examples: language-guide/examples.md
  - CLI:
    - Overview: cli/index.md
    - Guide:
      - Author-facing commands: cli/guide/author-commands.md
      - Under the hood: cli/guide/under-the-hood.md
      - Language extensions: cli/guide/language-extensions.md
      - Parser extensions: cli/guide/parser-extensions.md
      - Diagram extensions: cli/guide/diagram-extensions.md
    - All Commands:
      - plcc-diagram: cli/commands/plcc-diagram.md
      - plcc-diagram-build: cli/commands/plcc-diagram-build.md
      - plcc-diagram-emit: cli/commands/plcc-diagram-emit.md
      - plcc-diagram-list: cli/commands/plcc-diagram-list.md
      - plcc-diagram-run: cli/commands/plcc-diagram-run.md
      - plcc-java-build: cli/commands/plcc-java-build.md
      - plcc-java-emit: cli/commands/plcc-java-emit.md
      - plcc-java-run: cli/commands/plcc-java-run.md
      - plcc-lang-build: cli/commands/plcc-lang-build.md
      - plcc-lang-emit: cli/commands/plcc-lang-emit.md
      - plcc-lang-list: cli/commands/plcc-lang-list.md
      - plcc-lang-run: cli/commands/plcc-lang-run.md
      - plcc-ll1: cli/commands/plcc-ll1.md
      - plcc-make: cli/commands/plcc-make.md
      - plcc-mermaid-diagram-build: cli/commands/plcc-mermaid-diagram-build.md
      - plcc-mermaid-diagram-emit: cli/commands/plcc-mermaid-diagram-emit.md
      - plcc-mermaid-diagram-run: cli/commands/plcc-mermaid-diagram-run.md
      - plcc-model: cli/commands/plcc-model.md
      - plcc-parse: cli/commands/plcc-parse.md
      - plcc-parser-list: cli/commands/plcc-parser-list.md
      - plcc-parser-table: cli/commands/plcc-parser-table.md
      - plcc-plantuml-diagram-build: cli/commands/plcc-plantuml-diagram-build.md
      - plcc-plantuml-diagram-emit: cli/commands/plcc-plantuml-diagram-emit.md
      - plcc-plantuml-diagram-run: cli/commands/plcc-plantuml-diagram-run.md
      - plcc-python-emit: cli/commands/plcc-python-emit.md
      - plcc-python-run: cli/commands/plcc-python-run.md
      - plcc-rep: cli/commands/plcc-rep.md
      - plcc-scan: cli/commands/plcc-scan.md
      - plcc-spec: cli/commands/plcc-spec.md
      - plcc-tokens: cli/commands/plcc-tokens.md
      - plcc-trees: cli/commands/plcc-trees.md
      - plcc-version: cli/commands/plcc-version.md
  - Instructor Guide:
    - Overview: instructor-guide/index.md
    - Evaluating plcc-ng: instructor-guide/evaluating.md
    - Adopting plcc-ng: instructor-guide/adopting.md
  - Changelog: changelog.md

extra:
  version:
    provider: mike

markdown_extensions:
  - pymdownx.tabbed:
      alternate_style: true
```

- [ ] **Step 2: Verify the build succeeds**

```bash
PATH=/workspaces/plcc-ng/.venv/bin:$PATH mkdocs build --strict 2>&1
```

Expected: exits 0, last line is `INFO    -  Documentation built in X.XX seconds`.

- [ ] **Step 3: Commit**

```bash
git add mkdocs.yml
git commit -m "docs(mkdocs): enable content tabs feature and pymdownx.tabbed extension"
```

---

### Task 2: Tab the quick-start grammar

**Files:**
- Modify: `docs/quick-start.md`

**Interfaces:**
- Consumes: `content.tabs` + `pymdownx.tabbed` from Task 1
- Produces: `spec.plcc` shown in two tabs, Python and Java, both copy-pasteable

- [ ] **Step 1: Replace the single grammar block with a tabbed block**

Find this block in `docs/quick-start.md` (the entire fenced code block beginning with `# Define the tokens`):

`````markdown
```text
# Define the tokens of the language.
skip  WHITESPACE '\s+'
token NUM '\d+'

%

# Define the structure of the language.
# A program consists of a sequence of numbers.
<Program> **= <NUM:num>

%

# Define what happens when a program is run.
Python

Program
%%%
def _run(self):
  print(sum(int(str(num)) for num in self.numList))
%%%
```
`````

Replace it with:

`````markdown
=== "Python"
    ```text
    # Define the tokens of the language.
    skip  WHITESPACE '\s+'
    token NUM '\d+'

    %

    # Define the structure of the language.
    # A program consists of a sequence of numbers.
    <Program> **= <NUM:num>

    %

    # Define what happens when a program is run.
    Python

    Program
    %%%
    def _run(self):
      print(sum(int(str(num)) for num in self.numList))
    %%%
    ```

=== "Java"
    ```text
    # Define the tokens of the language.
    skip  WHITESPACE '\s+'
    token NUM '\d+'

    %

    # Define the structure of the language.
    # A program consists of a sequence of numbers.
    <Program> **= <NUM:num>

    %

    # Define what happens when a program is run.
    Java

    Program
    %%%
    public void _run() {
        int sum = 0;
        for (NUM num : numList) {
            sum += Integer.parseInt(num.lexeme);
        }
        System.out.println(sum);
    }
    %%%
    ```
`````

**Indentation note:** The `=== "Python"` and `=== "Java"` lines are at column 0. Everything inside each tab block is indented exactly 4 spaces (including the opening and closing ` ``` ` fence markers).

- [ ] **Step 2: Verify the build succeeds**

```bash
PATH=/workspaces/plcc-ng/.venv/bin:$PATH mkdocs build --strict 2>&1
```

Expected: exits 0.

- [ ] **Step 3: Commit**

```bash
git add docs/quick-start.md
git commit -m "docs(quick-start): add Java tab to semantic section example"
```

---

### Task 3: Tab the language-guide overview grammar

**Files:**
- Modify: `docs/language-guide/index.md`

**Interfaces:**
- Consumes: `content.tabs` + `pymdownx.tabbed` from Task 1
- Produces: introductory grammar example shown in two tabs

- [ ] **Step 1: Replace the single grammar block with a tabbed block**

Find this block in `docs/language-guide/index.md`:

`````markdown
```text
# Lexical section
skip WHITESPACE /\s+/
token NUM /\d+/

%

# Syntactic section
<Exp> ::= <NUM>

%

# Semantic section
Python

Exp
%%%
def __run__(self):
    print("Hello")
%%%
```
`````

Replace it with:

`````markdown
=== "Python"
    ```text
    # Lexical section
    skip WHITESPACE /\s+/
    token NUM /\d+/

    %

    # Syntactic section
    <Exp> ::= <NUM>

    %

    # Semantic section
    Python

    Exp
    %%%
    def __run__(self):
        print("Hello")
    %%%
    ```

=== "Java"
    ```text
    # Lexical section
    skip WHITESPACE /\s+/
    token NUM /\d+/

    %

    # Syntactic section
    <Exp> ::= <NUM>

    %

    # Semantic section
    Java

    Exp
    %%%
    public void __run__() {
        System.out.println("Hello");
    }
    %%%
    ```
`````

- [ ] **Step 2: Verify the build succeeds**

```bash
PATH=/workspaces/plcc-ng/.venv/bin:$PATH mkdocs build --strict 2>&1
```

Expected: exits 0.

- [ ] **Step 3: Commit**

```bash
git add docs/language-guide/index.md
git commit -m "docs(language-guide): add Java tab to overview grammar example"
```

---

### Task 4: Tab the semantic section page

**Files:**
- Modify: `docs/language-guide/semantic.md`

**Interfaces:**
- Consumes: `content.tabs` + `pymdownx.tabbed` from Task 1
- Produces: three code block groups on semantic.md converted to tabs

There are three places to change on this page. Make all three edits before running the build.

- [ ] **Step 1: Tab the basic code injection example**

Find this content (two consecutive fenced blocks starting after "use the following construct"):

`````markdown
```text
%
Python

Exp
%%%
def _run(self):
    print("Hello")
%%%
```

```text
%
Java

Exp
%%%
public void _run() {
    System.out.println("Hello");
}
%%%
```
`````

Replace with:

`````markdown
=== "Python"
    ```text
    %
    Python

    Exp
    %%%
    def _run(self):
        print("Hello")
    %%%
    ```

=== "Java"
    ```text
    %
    Java

    Exp
    %%%
    public void _run() {
        System.out.println("Hello");
    }
    %%%
    ```
`````

- [ ] **Step 2: Tab the hooks example**

Find this block (under the `### Example` heading in the Hooks section):

`````markdown
```text
WholeExp:import
%%%
import sys
%%%

WholeExp
%%%
def eval(self):
    x = int(self.whole.lexeme)
    sys.stderr.write(f"eval: {x}\n")
    return x
%%%
```
`````

Replace with:

`````markdown
=== "Python"
    ```text
    WholeExp:import
    %%%
    import sys
    %%%

    WholeExp
    %%%
    def eval(self):
        x = int(self.whole.lexeme)
        sys.stderr.write(f"eval: {x}\n")
        return x
    %%%
    ```

=== "Java"
    ```text
    WholeExp:import
    %%%
    import java.io.*;
    %%%

    WholeExp
    %%%
    public int eval() {
        int x = Integer.parseInt(whole.lexeme);
        System.err.println("eval: " + x);
        return x;
    }
    %%%
    ```
`````

- [ ] **Step 3: Tab the standalone classes example**

Find this block (under "## Adding standalone classes"):

`````markdown
```text
Helper      # Creates a file named Helper.py
%%%
class Helper:
    @staticmethod
    def double(x):
        return x * 2
%%%
```
`````

Replace with:

`````markdown
=== "Python"
    ```text
    Helper      # Creates a file named Helper.py
    %%%
    class Helper:
        @staticmethod
        def double(x):
            return x * 2
    %%%
    ```

=== "Java"
    ```text
    Helper      # Creates a file named Helper.java
    %%%
    public class Helper {
        public static int doubled(int x) {
            return x * 2;
        }
    }
    %%%
    ```
`````

Note: the Java method name is `doubled` (not `double`) because `double` is a reserved keyword in Java.

- [ ] **Step 4: Verify the build succeeds**

```bash
PATH=/workspaces/plcc-ng/.venv/bin:$PATH mkdocs build --strict 2>&1
```

Expected: exits 0.

- [ ] **Step 5: Commit**

```bash
git add docs/language-guide/semantic.md
git commit -m "docs(language-guide): add Java tabs to semantic section examples"
```

---

### Task 5: Tab the examples page

**Files:**
- Modify: `docs/language-guide/examples.md`

**Interfaces:**
- Consumes: `content.tabs` + `pymdownx.tabbed` from Task 1
- Produces: `subtract.plcc` shown as two complete, copy-pasteable grammar files

- [ ] **Step 1: Replace the single grammar block with a tabbed block**

Find this block in `docs/language-guide/examples.md` (the fenced block under "### Grammar file"):

`````markdown
```text
# Subtraction language
skip WHITESPACE '\s+'
token WHOLE     '\d+'
token MINUS     '\-'
token LP        '\('
token RP        '\)'
token COMMA     ','
%
<Prog>         ::= <Exp:exp>
<Exp:WholeExp> ::= <WHOLE:whole>
<Exp:SubExp>   ::= MINUS LP <Exp:exp1> COMMA <Exp:exp2> RP
%
Python

Prog
%%%
def _run(self):
    print(self.exp.eval())
%%%

WholeExp
%%%
def eval(self):
    return int(self.whole.lexeme)
%%%

SubExp
%%%
def eval(self):
    return self.exp1.eval() - self.exp2.eval()
%%%
```
`````

Replace with:

`````markdown
=== "Python"
    ```text
    # Subtraction language
    skip WHITESPACE '\s+'
    token WHOLE     '\d+'
    token MINUS     '\-'
    token LP        '\('
    token RP        '\)'
    token COMMA     ','
    %
    <Prog>         ::= <Exp:exp>
    <Exp:WholeExp> ::= <WHOLE:whole>
    <Exp:SubExp>   ::= MINUS LP <Exp:exp1> COMMA <Exp:exp2> RP
    %
    Python

    Prog
    %%%
    def _run(self):
        print(self.exp.eval())
    %%%

    WholeExp
    %%%
    def eval(self):
        return int(self.whole.lexeme)
    %%%

    SubExp
    %%%
    def eval(self):
        return self.exp1.eval() - self.exp2.eval()
    %%%
    ```

=== "Java"
    ```text
    # Subtraction language
    skip WHITESPACE '\s+'
    token WHOLE     '\d+'
    token MINUS     '\-'
    token LP        '\('
    token RP        '\)'
    token COMMA     ','
    %
    <Prog>         ::= <Exp:exp>
    <Exp:WholeExp> ::= <WHOLE:whole>
    <Exp:SubExp>   ::= MINUS LP <Exp:exp1> COMMA <Exp:exp2> RP
    %
    Java

    Prog
    %%%
    public void _run() {
        System.out.println(exp.eval());
    }
    %%%

    WholeExp
    %%%
    public int eval() {
        return Integer.parseInt(whole.lexeme);
    }
    %%%

    SubExp
    %%%
    public int eval() {
        return exp1.eval() - exp2.eval();
    }
    %%%
    ```
`````

The sections after the grammar file (Build, Scanner, Parser, Interpreter) use the same `plcc-make`, `plcc-scan`, `plcc-parse`, and `plcc-rep` commands for both languages — leave them unchanged.

- [ ] **Step 2: Verify the build succeeds**

```bash
PATH=/workspaces/plcc-ng/.venv/bin:$PATH mkdocs build --strict 2>&1
```

Expected: exits 0.

- [ ] **Step 3: Commit**

```bash
git add docs/language-guide/examples.md
git commit -m "docs(language-guide): add Java tab to subtract.plcc example"
```
