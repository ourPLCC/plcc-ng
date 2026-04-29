# Phase 3: Java Emitter and Backwards Compatibility — Design

**Date:** 2026-04-29
**Status:** APPROVED
**Companion architectural spec:** `docs/superpowers/specs/2026-04-12-multi-lang-pipeline.md`
**Roadmap reference:** `docs/superpowers/specs/2026-04-12-multi-lang-implementation-plan.md` §6

---

## 1. Goal

Deliver a complete `plcc-java-emit` implementation that produces a working Java
interpreter for every in-scope grammar in the `languages` test corpus. After Phase 3:

```sh
plcc-make src/V0/grammar
java -cp build/Java:build/Java/runtime/org.json-*.jar Main < input.txt
```

produces the same output as v8 for all 33 in-scope `languages` grammars.

---

## 2. Phase Structure

| Phase | Scope | Status |
| ----- | ----- | ------ |
| Phase 1 | Walking skeleton — trivial grammar, PlantUML emitter | Complete |
| Phase 2 | Python emitter, LL(1) parser, `plcc-rep`, arbno support | Complete |
| **Phase 3** | **Java emitter, Java runtime, `languages` corpus tests** | **This design** |
| Phase 4 | Visualizers, PyPI packaging, first prerelease | Pending |
| Phase 5 | Stable release | Pending |

---

## 3. Scope

### 3.1 In scope

- Fix `plcc-model` `_extract_body` bug (prerequisite)
- `plcc-java-emit` — Jinja2 templates, one `.java` file per class, bundled runtime
- Java runtime library — `Node.java`, `Token.java`, `Registry.java`, `Deserializer.java`, bundled `org.json` jar
- Update `plcc-java-build` and `plcc-java-run` for org.json classpath
- E2e corpus tests using the 33 in-scope `languages` grammars

### 3.2 Out of scope

| Item | Reason |
| ---- | ------ |
| CHAR grammar (`!Parser=`/`!Rep=` flags) | `plcc-spec` errors on `!flag=` syntax; already deferred |
| ABC grammar (`*:import` + `abcdatalog.jar`) | External classpath dependency the emitter cannot bundle |
| Updating the `languages` repo | Strategic question deferred; `languages` repo unchanged |
| `plcc-scan` / `plcc-parse` visualizers | Phase 4 |
| PyPI publication | Phase 4 |

That leaves **33 of 35 grammars** as the Phase 3 target corpus.

---

## 4. Prerequisite: `plcc-model` `_extract_body` Fix

### 4.1 The bug

`build_model.py:_extract_body` strips `%%%` delimiters only when the line string is
exactly `"%%%"`. Grammar files read from disk include a trailing newline on each line,
so `"%%%\n" != "%%%"` and the delimiters survive into the fragment body. Every v8
grammar's semantic bodies arrive in model JSON with raw `%%%` wrappers and
newline-padded content.

### 4.2 Fix

Strip trailing whitespace from each line string before the `%%%` comparison, and from
every line before joining:

```python
def _extract_body(lines):
    strings = [line['string'].rstrip('\n') for line in lines]
    if strings and strings[0] == '%%%':
        strings = strings[1:]
    if strings and strings[-1] == '%%%':
        strings = strings[:-1]
    return '\n'.join(strings)
```

### 4.3 TDD order

1. Add a failing test in `build_model_test.py` that feeds a spec fragment whose
   block lines end with `\n` (v8-style) and asserts the resulting `body` contains no
   `%%%` markers and no leading/trailing blank lines from the delimiters.
2. Confirm the test fails against the current code.
3. Apply the fix above.
4. Confirm the test passes.
5. Confirm all existing `build_model_test.py` tests still pass.

---

## 5. Java Runtime Library

The runtime lives at `src/plcc/lang/ext/java/runtime/` and is copied verbatim into
`build/<tool>/runtime/` by `plcc-java-emit` (mirroring the Python runtime pattern).

### 5.1 Files

| File | Role |
| ---- | ---- |
| `Node.java` | Abstract base class for all generated nonterminal classes |
| `Token.java` | Wraps a terminal; fields `kind` (String) and `lexeme` (String); `toString()` returns `lexeme` |
| `Registry.java` | Maps `(ruleName, Set<fieldNames>)` → `Class<? extends Node>`; mirrors Python `Registry` |
| `Deserializer.java` | Reads tree JSON via org.json; reconstructs object trees using `Registry` |
| `org.json-20250107.jar` | Bundled JSON library; pinned version committed to repo |

### 5.2 Constructor contract — `Map<String, Object>` pattern

Every generated concrete class takes a single `Map<String, Object>` constructor.
This avoids Java reflection's parameter-name problem and mirrors Python's `**kwargs`
construction cleanly:

```java
public class Program extends runtime.Node {
    public Expr expr;

    @SuppressWarnings("unchecked")
    public Program(java.util.Map<String, Object> fields) {
        this.expr = (Expr) fields.get("expr");
    }
}
```

Arbno fields arrive as `List<T>` and are cast in the generated constructor without
special handling in the Deserializer:

```java
public List<Exp> expList;

@SuppressWarnings("unchecked")
public Rands(java.util.Map<String, Object> fields) {
    this.expList = (List<Exp>) fields.get("expList");
}
```

Abstract classes are plain abstract Java classes with no constructor and no fields.
They are never registered in the Registry and never directly instantiated.

### 5.3 `Deserializer.java`

Reads a single `JSONObject` representing one parse-tree node and recursively
reconstructs an object tree:

- `kind == "token"` → `new Token(tree.getString("name"), tree.getString("lexeme"))`
- Otherwise: extract `rule` and the `children` array (list of `[name, value]` pairs),
  build a `Map<String, Object>` of field values by deserializing each child
  recursively, look up the class via `registry.lookup(rule, fields.keySet())`, call
  `cls.getConstructor(Map.class).newInstance(fields)`

Arbno values (JSON arrays in the children) are deserialized as `List<Object>` by
recursively deserializing each element.

### 5.4 `Token.java`

```java
package runtime;

public class Token extends Node {
    public final String kind;
    public final String lexeme;

    public Token(String kind, String lexeme) {
        this.kind = kind;
        this.lexeme = lexeme;
    }

    @Override
    public String toString() {
        return lexeme;
    }
}
```

`toString()` returns `lexeme` — this is the v8 contract that semantic methods rely on
(e.g. `return lit.toString()`).

### 5.5 Classpath impact

`plcc-java-build` compiles with `-cp runtime/org.json-*.jar` and includes
`runtime/*.java` alongside `*.java`:

```python
json_jar = next(Path(output_dir, 'runtime').glob('org.json*.jar'))
java_files = list(Path(output_dir).glob('*.java'))
runtime_java_files = list(Path(output_dir, 'runtime').glob('*.java'))
subprocess.run(['javac', '-cp', str(json_jar)] + java_files + runtime_java_files, ...)
```

`plcc-java-run` runs with `output_dir` and the jar on the classpath:

```python
json_jar = next(Path(output_dir, 'runtime').glob('org.json*.jar'))
classpath = f"{output_dir}{os.pathsep}{json_jar}"
subprocess.run(['java', '-cp', classpath, 'Main'], ...)
```

---

## 6. `plcc-java-emit` — Emitter Design

### 6.1 Source layout

```text
src/plcc/lang/ext/java/
├── emit.py
├── emit_test.py
├── build.py          (updated for org.json classpath)
├── build_test.py     (updated)
├── run.py            (updated for org.json classpath)
├── templates/
│   ├── class_file.java.jinja
│   └── Main.java.jinja
└── runtime/
    ├── Node.java
    ├── Token.java
    ├── Registry.java
    ├── Deserializer.java
    └── org.json-20250107.jar
```

### 6.2 `class_file.java.jinja`

Applied once per class in `model.classes`:

```jinja
{% for frag in import_fragments %}{{ frag.body }}
{% endfor %}
import java.util.List;
import java.util.Map;

{% if cls.abstract %}
public abstract class {{ cls.name }}{% if cls.extends %} extends {{ cls.extends }}{% else %} extends runtime.Node{% endif %} {
}
{% else %}
public class {{ cls.name }}{% if cls.extends %} extends {{ cls.extends }}{% else %} extends runtime.Node{% endif %} {

{% for field in cls.fields %}
    public {% if field.is_list %}java.util.List<{{ field.type }}>{% else %}{{ field.type }}{% endif %} {{ field.name }};
{% endfor %}

    @SuppressWarnings("unchecked")
    public {{ cls.name }}(java.util.Map<String, Object> fields) {
{% for field in cls.fields %}
{% if field.is_list %}
        this.{{ field.name }} = (java.util.List<{{ field.type }}>) fields.get("{{ field.name }}");
{% else %}
        this.{{ field.name }} = ({{ field.type }}) fields.get("{{ field.name }}");
{% endif %}
{% endfor %}
{% for frag in init_fragments %}
        {{ frag.body | indent(8) }}
{% endfor %}
    }

{% for frag in body_fragments %}
{{ frag.body }}

{% endfor %}
}
{% endif %}
```

### 6.3 `Main.java.jinja`

Generated once per semantic section. Uses reflection to call the entry point so that
both `void $run()` (v8 convention — side-effects to stdout, returns null from
`invoke()`) and non-void entry points are handled uniformly:

```jinja
import java.io.BufferedReader;
import java.io.InputStreamReader;
import org.json.JSONObject;
import runtime.Deserializer;
import runtime.Registry;
{% for cls in concrete_classes %}
import {{ cls.name }};
{% endfor %}

public class Main {
    public static void main(String[] args) throws Exception {
        Registry registry = new Registry();
        registry.register({% for cls in concrete_classes %}{{ cls.name }}.class{% if not loop.last %}, {% endif %}{% endfor %});
        Deserializer deserializer = new Deserializer(registry);

        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line;
        while ((line = reader.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty()) continue;
            try {
                {{ start_class }} root = ({{ start_class }}) deserializer.deserialize(new JSONObject(line));
                java.lang.reflect.Method m = {{ start_class }}.class.getMethod("{{ entry_point }}");
                Object result = m.invoke(root);
                JSONObject record = new JSONObject();
                record.put("kind", "result");
                record.put("value", result != null ? result.toString() : JSONObject.NULL);
                System.out.println(record.toString());
                System.out.flush();
            } catch (Exception e) {
                JSONObject record = new JSONObject();
                record.put("kind", "error");
                record.put("type", e.getClass().getSimpleName());
                record.put("message", e.getMessage() != null ? e.getMessage() : "");
                System.out.println(record.toString());
                System.out.flush();
            }
        }
    }
}
```

`start_class` is `model.start` with first letter uppercased. `entry_point` is taken
from the first semantic section with `language == "Java"` (same selection logic as the
Python emitter uses for `language == "Python"`); it falls back to `$run` when the
section's `entry_point` field is null.

### 6.4 Fragment handling in `emit.py`

| Fragment kind | Action |
| ------------- | ------ |
| `body` | Pasted verbatim into the class body after the constructor |
| `import` (class-specific) | Added as import lines at the top of that class's file |
| `init` | Added inside the constructor after field assignments |
| `file` | Written as a standalone `.java` file with the fragment body as complete contents |
| Any fragment with `class_name` starting with `#` | Skipped (v8 comment artefacts) |

`emit.py` structure mirrors `plcc/lang/ext/python/emit.py`: read model JSON from
stdin, find the Java semantic section, group fragments by class name, render each
class through `class_file.java.jinja`, write files, render `Main.java.jinja`, copy
runtime directory (excluding `__pycache__`, `*.pyc`, `*_test.py`).

### 6.5 Entry point default

```python
_DEFAULT_ENTRY_POINT = '$run'
```

Symmetric with the Python emitter's `_DEFAULT_ENTRY_POINT = '_run'`.

---

## 7. Testing Strategy

### 7.1 Unit tests — `emit_test.py`

One test per concern. Feed minimal model JSON via `monkeypatch`'d `sys.stdin`,
assert the files written to a `tmp_path`:

- Abstract class generates no constructor, no fields
- Concrete class with scalar fields generates correct Map constructor casts
- Arbno list field generates `List<Type>` declaration and cast
- Body fragment is pasted verbatim into class body
- Import fragment appears as import statement at top of file
- Init fragment appears inside constructor after field assignments
- File fragment is written as a standalone `.java` file
- `$run` is used as entry point when `entry_point` is null
- Declared entry point is used when present
- `# comment` class name is skipped (no file written)
- Runtime directory is copied into output

### 7.2 Unit tests — `build_model_test.py` addition

```python
def test_extract_body_strips_percent_markers_with_trailing_newlines():
    # v8-style lines include '\n'
    lines = [
        {'string': '%%%\n'},
        {'string': '    public void $run() {\n'},
        {'string': '    }\n'},
        {'string': '%%%\n'},
    ]
    result = _extract_body(lines)
    assert '%%%' not in result
    assert result == '    public void $run() {\n    }'
```

Written before the fix; must fail first.

### 7.3 Integration tests — `tests/bats/integration/java-emit.bats`

- `plcc-java-emit` produces a `.java` file per model class for `trivial-java.plcc`
- `plcc-java-build` compiles the output without errors (requires JDK)
- `plcc-java-run` exits 0 on valid tree JSON input
- Updated `plcc-java-build` and `plcc-java-run` tests reflect new classpath

### 7.4 E2e corpus tests — `tests/bats/e2e/languages-java.bats`

The `languages` repo is cloned at CI time via an environment variable
`LANGUAGES_REPO_PATH`. The bats test skips gracefully when the variable is unset
(local dev without the clone).

A plain-text corpus file `tests/fixtures/languages-corpus.txt` lists the grammars
currently expected to pass — one relative path per line (e.g.
`src/V0/grammar`). This file starts with the simplest grammars and grows as
Phase 3 progresses. It is the phase progress board: turning a grammar green means
adding it to this file.

For each grammar in the corpus file:

1. `plcc-make <grammar>` succeeds
2. `build/Java/*.class` files exist
3. For each `tests/*/` subdirectory: feed `.input` through
   `plcc-tokens | plcc-tree | java Main` and assert output matches `.expected`

### 7.5 CI

`bin/test/e2e.bash` extended to run `languages-java.bats` when both JDK and
`LANGUAGES_REPO_PATH` are set. A CI step clones `languages` at a pinned commit and
sets the variable before running the test suite. Java availability is already guarded
in existing e2e tests with `if ! command -v javac &>/dev/null; then skip ...; fi`.

---

## 8. Acceptance Criteria

1. `plcc-model` correctly strips `%%%` delimiters from v8-style fragment bodies (lines
   with trailing `\n`)
2. `plcc-java-emit --output=DIR < model.json` produces one `.java` file per class plus
   `Main.java` and `runtime/`
3. `plcc-java-build --output=DIR` compiles all generated `.java` files and runtime
   sources with org.json on the classpath
4. All 33 in-scope `languages` grammars pass: `plcc-make <grammar>` succeeds,
   `.class` files are produced, and feeding each grammar's test inputs through the
   full v9 pipeline produces output matching the `.expected` files
5. All existing Phase 1 and Phase 2 tests pass (no regressions)

---

## 9. Out of Scope for Phase 3

- CHAR grammar (`!flag=` syntax) — deferred
- ABC grammar (external jar dependency) — deferred
- `*:import` global import modifier (only used by ABC) — deferred with ABC
- Updating the `languages` repo with v9-native test scripts — strategic question
  deferred; addressed in Phase 3 retro
- `plcc-scan` / `plcc-parse` visualizers — Phase 4
- PyPI publication — Phase 4
