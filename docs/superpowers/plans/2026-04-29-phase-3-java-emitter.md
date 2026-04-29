# Phase 3: Java Emitter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a complete `plcc-java-emit` that produces a working Java interpreter for all 33 in-scope grammars in the `languages` test corpus.

**Architecture:** Replace the stub Java emitter with a Jinja2-based emitter that mirrors the Python emitter structure. Add a Java runtime library (Node, Token, Registry, Deserializer + bundled org.json jar) that is copied verbatim into the build output. Update `plcc-java-build` and `plcc-java-run` for the org.json classpath. Validate with unit tests, integration tests, and an e2e corpus loop over all 33 grammars.

**Tech Stack:** Python/Jinja2 (emitter), Java (runtime + generated code), org.json (bundled jar), Bats (integration + e2e tests), pytest (unit tests)

---

## File Map

| File | Action | Purpose |
| ---- | ------ | ------- |
| `src/plcc/model/build_model.py` | Modify | Fix `_extract_body` `\n` bug |
| `src/plcc/model/build_model_test.py` | Modify | Add failing test before fix |
| `src/plcc/lang/ext/java/runtime/Node.java` | Create | Abstract base for all generated classes |
| `src/plcc/lang/ext/java/runtime/Token.java` | Create | Wraps a terminal; `toString()` returns lexeme |
| `src/plcc/lang/ext/java/runtime/Registry.java` | Create | Maps (ruleName, fieldSet) → Class |
| `src/plcc/lang/ext/java/runtime/Deserializer.java` | Create | Reads tree JSON; reconstructs object trees |
| `src/plcc/lang/ext/java/runtime/org.json-20250107.jar` | Add | Bundled JSON library (download once, commit) |
| `src/plcc/lang/ext/java/templates/class_file.java.jinja` | Create | Template for one generated class file |
| `src/plcc/lang/ext/java/templates/Main.java.jinja` | Create | Template for entry-point harness |
| `src/plcc/lang/ext/java/emit.py` | Replace | Full Jinja2 emitter (replaces stub) |
| `src/plcc/lang/ext/java/emit_test.py` | Replace | Full unit tests (replaces stub tests) |
| `src/plcc/lang/ext/java/build.py` | Modify | Add org.json classpath + runtime/*.java |
| `src/plcc/lang/ext/java/build_test.py` | Modify | Update for new classpath |
| `src/plcc/lang/ext/java/run.py` | Modify | Add org.json classpath |
| `src/plcc/lang/ext/java/run_test.py` | Modify | Update for new classpath (if exists) |
| `tests/fixtures/trivial-java.plcc` | Modify | Add `$run` Java semantics for real end-to-end test |
| `tests/bats/commands/plcc-java-emit.bats` | Modify | Test real emitter (one file per class, runtime copied) |
| `tests/bats/commands/plcc-java-build.bats` | Modify | Test with org.json classpath |
| `tests/bats/commands/plcc-java-run.bats` | Modify | Test real output (JSON result record) |
| `tests/bats/integration/java-emit.bats` | Create | End-to-end emit→build→run for trivial-java |
| `tests/fixtures/languages-corpus.txt` | Create | Phase progress board (one grammar path per line) |
| `tests/bats/e2e/languages-java.bats` | Create | Corpus loop test |
| `bin/test/e2e.bash` | Modify | Run languages-java.bats when LANGUAGES_REPO_PATH set |

---

## Task 1: Failing test for `_extract_body` bug

**Files:**
- Modify: `src/plcc/model/build_model_test.py`

- [ ] **Step 1: Open `src/plcc/model/build_model_test.py` and add this test at the end:**

```python
def test_extract_body_strips_percent_markers_with_trailing_newlines():
    from .build_model import _extract_body
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

- [ ] **Step 2: Run the test to confirm it fails**

```bash
cd .worktrees/multi-lang
bin/test/unit.bash -k test_extract_body_strips_percent_markers_with_trailing_newlines
```

Expected: FAIL — `AssertionError: assert '%%%' not in '%%%\n    public void $run() {\n    }\n%%%'` (or similar).

- [ ] **Step 3: Commit the failing test**

```bash
git add src/plcc/model/build_model_test.py
git commit -m "test(model): add failing test for _extract_body trailing newline bug"
```

---

## Task 2: Fix `_extract_body` bug

**Files:**
- Modify: `src/plcc/model/build_model.py:149-155`

- [ ] **Step 1: Replace `_extract_body` in `src/plcc/model/build_model.py`**

Current (lines 149–155):
```python
def _extract_body(lines):
    strings = [line['string'] for line in lines]
    if strings and strings[0] == '%%%':
        strings = strings[1:]
    if strings and strings[-1] == '%%%':
        strings = strings[:-1]
    return '\n'.join(strings)
```

New:
```python
def _extract_body(lines):
    strings = [line['string'].rstrip('\n') for line in lines]
    if strings and strings[0] == '%%%':
        strings = strings[1:]
    if strings and strings[-1] == '%%%':
        strings = strings[:-1]
    return '\n'.join(strings)
```

- [ ] **Step 2: Run the new test and all build_model tests**

```bash
cd .worktrees/multi-lang
bin/test/unit.bash src/plcc/model/build_model_test.py
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add src/plcc/model/build_model.py
git commit -m "fix(model): strip trailing newline before %%% delimiter comparison"
```

---

## Task 3: Download and add org.json jar

**Files:**
- Create: `src/plcc/lang/ext/java/runtime/org.json-20250107.jar`

- [ ] **Step 1: Download the jar**

```bash
cd .worktrees/multi-lang/src/plcc/lang/ext/java/runtime
curl -L -o org.json-20250107.jar \
  "https://search.maven.org/remotecontent?filepath=org/json/json/20250107/json-20250107.jar"
```

- [ ] **Step 2: Verify the jar is valid**

```bash
jar tf org.json-20250107.jar | head -5
```

Expected: shows class file names like `org/json/JSONObject.class`.

- [ ] **Step 3: Commit**

```bash
git add src/plcc/lang/ext/java/runtime/org.json-20250107.jar
git commit -m "feat(java-runtime): add bundled org.json-20250107.jar"
```

---

## Task 4: Write Node.java and Token.java

**Files:**
- Create: `src/plcc/lang/ext/java/runtime/Node.java`
- Create: `src/plcc/lang/ext/java/runtime/Token.java`

- [ ] **Step 1: Create `src/plcc/lang/ext/java/runtime/Node.java`**

```java
package runtime;

public abstract class Node {
}
```

- [ ] **Step 2: Create `src/plcc/lang/ext/java/runtime/Token.java`**

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

- [ ] **Step 3: Commit**

```bash
git add src/plcc/lang/ext/java/runtime/Node.java \
        src/plcc/lang/ext/java/runtime/Token.java
git commit -m "feat(java-runtime): add Node and Token base classes"
```

---

## Task 5: Write Registry.java

**Files:**
- Create: `src/plcc/lang/ext/java/runtime/Registry.java`

The Registry reads static `_RULE_NAME` and `_FIELDS` from each registered class (populated by the generated code template in Task 7).

- [ ] **Step 1: Create `src/plcc/lang/ext/java/runtime/Registry.java`**

```java
package runtime;

import java.util.*;

public class Registry {
    private final Map<String, Map<Set<String>, Class<? extends Node>>> byRule = new HashMap<>();

    public void register(Class<?>... classes) throws Exception {
        for (Class<?> cls : classes) {
            String ruleName = (String) cls.getField("_RULE_NAME").get(null);
            String[] fieldsArr = (String[]) cls.getField("_FIELDS").get(null);
            Set<String> fieldSet = new HashSet<>(Arrays.asList(fieldsArr));
            byRule.computeIfAbsent(ruleName, k -> new HashMap<>())
                  .put(fieldSet, cls.asSubclass(Node.class));
        }
    }

    public Class<? extends Node> lookup(String ruleName, Set<String> fieldNames) {
        Map<Set<String>, Class<? extends Node>> candidates = byRule.get(ruleName);
        if (candidates == null)
            throw new RuntimeException("No class registered for rule '" + ruleName + "'");
        Class<? extends Node> cls = candidates.get(fieldNames);
        if (cls == null)
            throw new RuntimeException(
                "No class for rule '" + ruleName + "' with fields " + fieldNames);
        return cls;
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add src/plcc/lang/ext/java/runtime/Registry.java
git commit -m "feat(java-runtime): add Registry class"
```

---

## Task 6: Write Deserializer.java

**Files:**
- Create: `src/plcc/lang/ext/java/runtime/Deserializer.java`

The Deserializer reads tree JSON (one `JSONObject` per line) and recursively reconstructs object trees using the Registry.

- [ ] **Step 1: Create `src/plcc/lang/ext/java/runtime/Deserializer.java`**

```java
package runtime;

import org.json.*;
import java.lang.reflect.*;
import java.util.*;

public class Deserializer {
    private final Registry registry;

    public Deserializer(Registry registry) {
        this.registry = registry;
    }

    public Node deserialize(JSONObject tree) throws Exception {
        String kind = tree.getString("kind");
        if ("token".equals(kind)) {
            return new Token(tree.getString("name"), tree.getString("lexeme"));
        }
        String rule = tree.getString("rule");
        JSONArray children = tree.getJSONArray("children");
        Map<String, Object> fields = new LinkedHashMap<>();
        for (int i = 0; i < children.length(); i++) {
            JSONArray pair = children.getJSONArray(i);
            String name = pair.getString(0);
            fields.put(name, deserializeValue(pair.get(1)));
        }
        Class<? extends Node> cls = registry.lookup(rule, fields.keySet());
        Constructor<? extends Node> ctor = cls.getConstructor(Map.class);
        return ctor.newInstance(fields);
    }

    private Object deserializeValue(Object val) throws Exception {
        if (val instanceof JSONObject) {
            return deserialize((JSONObject) val);
        }
        if (val instanceof JSONArray) {
            JSONArray arr = (JSONArray) val;
            List<Object> list = new ArrayList<>();
            for (int i = 0; i < arr.length(); i++) {
                list.add(deserializeValue(arr.get(i)));
            }
            return list;
        }
        return val;
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add src/plcc/lang/ext/java/runtime/Deserializer.java
git commit -m "feat(java-runtime): add Deserializer class"
```

---

## Task 7: Write class_file.java.jinja template

**Files:**
- Create: `src/plcc/lang/ext/java/templates/class_file.java.jinja`

Note: The template adds `_RULE_NAME` and `_FIELDS` static fields so `Registry.register()` can read them via reflection. This mirrors Python's `_rule_name` and `_fields` class attributes.

- [ ] **Step 1: Create the templates directory and template file**

Create `src/plcc/lang/ext/java/templates/class_file.java.jinja`:

````jinja2
{% for frag in import_fragments %}{{ frag.body }}
{% endfor %}
import java.util.List;
import java.util.Map;

{% if cls.abstract %}
public abstract class {{ cls.name }}{% if cls.extends %} extends {{ cls.extends }}{% else %} extends runtime.Node{% endif %} {
}
{% else %}
public class {{ cls.name }}{% if cls.extends %} extends {{ cls.extends }}{% else %} extends runtime.Node{% endif %} {

    public static final String _RULE_NAME = {{ cls.rule_name | tojson }};
    public static final String[] _FIELDS = { {% for field in cls.fields %}{{ field.name | tojson }}{% if not loop.last %}, {% endif %}{% endfor %} };

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
````

- [ ] **Step 2: Commit**

```bash
git add src/plcc/lang/ext/java/templates/class_file.java.jinja
git commit -m "feat(java-emit): add class_file.java.jinja template"
```

---

## Task 8: Write Main.java.jinja template

**Files:**
- Create: `src/plcc/lang/ext/java/templates/Main.java.jinja`

`Main.java` reads tree-JSON lines from stdin, deserializes each, invokes the entry point via reflection (handles both `void $run()` and non-void), and outputs a JSON result record. Direct `System.out.println` calls from `$run()` are NOT suppressed — they appear before the JSON record line.

- [ ] **Step 1: Create `src/plcc/lang/ext/java/templates/Main.java.jinja`**

````jinja2
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
````

- [ ] **Step 2: Commit**

```bash
git add src/plcc/lang/ext/java/templates/Main.java.jinja
git commit -m "feat(java-emit): add Main.java.jinja template"
```

---

## Task 9: Implement full emit.py and emit_test.py

**Files:**
- Replace: `src/plcc/lang/ext/java/emit.py`
- Replace: `src/plcc/lang/ext/java/emit_test.py`

- [ ] **Step 1: Replace `src/plcc/lang/ext/java/emit.py` with the full implementation**

```python
"""plcc-java-emit
    Emit a Java interpreter from model JSON.

Usage:
    plcc-java-emit --output=DIR [options]

Options:
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
"""

import enum
import json
import shutil
import sys
from pathlib import Path

import jinja2
from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS

_DEFAULT_ENTRY_POINT = '$run'


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-java-emit", Events, args)
    output_dir = Path(args['--output'])
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')

    model = json.load(sys.stdin)
    output_dir.mkdir(parents=True, exist_ok=True)

    _copy_runtime(output_dir)

    classes = model['classes']
    section = _find_java_section(model)
    entry_point = (section.get('entry_point') if section else None) or _DEFAULT_ENTRY_POINT
    fragments_by_class = _group_fragments(section.get('fragments', []) if section else [])

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(Path(__file__).parent / 'templates')),
        keep_trailing_newline=True,
    )
    class_template = env.get_template('class_file.java.jinja')
    main_template = env.get_template('Main.java.jinja')

    for cls in classes:
        frags = fragments_by_class.get(cls['name'], [])
        content = class_template.render(
            cls=cls,
            import_fragments=[f for f in frags if f['kind'] == 'import'],
            init_fragments=[f for f in frags if f['kind'] == 'init'],
            body_fragments=[f for f in frags if f['kind'] == 'body'],
        )
        (output_dir / f"{cls['name']}.java").write_text(content)

    all_frags = section.get('fragments', []) if section else []
    for frag in all_frags:
        if frag['kind'] == 'file':
            (output_dir / f"{frag['class_name']}.java").write_text(frag['body'])

    concrete_classes = [c for c in classes if not c['abstract']]
    start_class = model['start'][0].upper() + model['start'][1:]
    main_content = main_template.render(
        concrete_classes=concrete_classes,
        start_class=start_class,
        entry_point=entry_point,
    )
    (output_dir / 'Main.java').write_text(main_content)

    verbose.emit(Events.FINISHED, message='done')


def _copy_runtime(output_dir):
    src = Path(__file__).parent / 'runtime'
    dst = output_dir / 'runtime'
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*_test.py'))


def _find_java_section(model):
    for s in model.get('semantic_sections', []):
        if s.get('language') == 'Java':
            return s
    return None


def _group_fragments(fragments):
    groups = {}
    for frag in fragments:
        if frag['class_name'].startswith('#'):
            continue
        groups.setdefault(frag['class_name'], []).append(frag)
    return groups
```

- [ ] **Step 2: Replace `src/plcc/lang/ext/java/emit_test.py` with the full test suite**

```python
import io
import json

import pytest
from docopt import DocoptExit

from .emit import main as run_main


def _trivial_model():
    return {
        "start": "program",
        "classes": [
            {"name": "Program", "abstract": False, "extends": None, "rule_name": "program",
             "fields": [{"name": "expr", "type": "Expr", "is_list": False}]},
            {"name": "Expr", "abstract": True, "extends": None, "rule_name": "expr",
             "fields": []},
            {"name": "NumExpr", "abstract": False, "extends": "Expr", "rule_name": "expr",
             "fields": [{"name": "num", "type": "runtime.Token", "is_list": False}]},
        ],
        "semantic_sections": [
            {
                "language": "Java",
                "tool": "Java",
                "entry_point": "$run",
                "fragments": [
                    {"class_name": "Program", "kind": "body",
                     "body": "    public void $run() {\n        System.out.println(expr.toString());\n    }"},
                ]
            }
        ]
    }


def test_no_args_prints_usage():
    with pytest.raises((DocoptExit, SystemExit)):
        run_main([])


def test_emit_produces_one_java_file_per_class(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    for name in ["Program", "Expr", "NumExpr"]:
        assert (tmp_path / f'{name}.java').exists(), f"{name}.java missing"


def test_emit_produces_main_java(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'Main.java').exists()


def test_emit_copies_runtime_directory(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'runtime' / 'Node.java').exists()
    assert (tmp_path / 'runtime' / 'Token.java').exists()
    assert (tmp_path / 'runtime' / 'Registry.java').exists()
    assert (tmp_path / 'runtime' / 'Deserializer.java').exists()
    assert list((tmp_path / 'runtime').glob('org.json*.jar'))


def test_abstract_class_generates_no_constructor(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    expr_java = (tmp_path / 'Expr.java').read_text()
    assert 'abstract' in expr_java
    assert 'public Expr(' not in expr_java


def test_concrete_class_has_map_constructor(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'public Program(java.util.Map<String, Object> fields)' in program_java
    assert 'this.expr = (Expr) fields.get("expr")' in program_java


def test_concrete_class_has_rule_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert '_RULE_NAME' in program_java
    assert '_FIELDS' in program_java


def test_list_field_generates_list_type(tmp_path, monkeypatch):
    model = _trivial_model()
    model['classes'].append({
        "name": "Rands", "abstract": False, "extends": None, "rule_name": "rands",
        "fields": [{"name": "exprList", "type": "Expr", "is_list": True}]
    })
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    rands_java = (tmp_path / 'Rands.java').read_text()
    assert 'java.util.List<Expr>' in rands_java
    assert 'this.exprList = (java.util.List<Expr>) fields.get("exprList")' in rands_java


def test_body_fragment_pasted_into_class(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'System.out.println(expr.toString())' in program_java


def test_import_fragment_appears_at_top(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Program", "kind": "import", "body": "import java.util.ArrayList;"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'import java.util.ArrayList;' in program_java


def test_init_fragment_appears_inside_constructor(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Program", "kind": "init", "body": "System.out.println(\"init\");"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    ctor_pos = program_java.index('public Program(')
    init_pos = program_java.index('System.out.println("init")')
    assert init_pos > ctor_pos, "init fragment must be inside constructor"


def test_file_fragment_written_as_standalone_java_file(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Env", "kind": "file", "body": "public class Env {}\n"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'Env.java').exists()
    assert 'public class Env {}' in (tmp_path / 'Env.java').read_text()


def test_hash_comment_class_name_is_skipped(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "# a comment", "kind": "body", "body": "// ignored"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    assert not (tmp_path / '# a comment.java').exists()


def test_entry_point_defaults_to_dollar_run_when_null(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['entry_point'] = None
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    main_java = (tmp_path / 'Main.java').read_text()
    assert '"$run"' in main_java


def test_declared_entry_point_is_used(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['entry_point'] = 'eval'
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    main_java = (tmp_path / 'Main.java').read_text()
    assert '"eval"' in main_java


def test_main_java_references_start_class(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    main_java = (tmp_path / 'Main.java').read_text()
    assert 'Program root' in main_java


def test_verbose_flag_accepted(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}', '--verbose=1'])
```

- [ ] **Step 3: Run the unit tests**

```bash
cd .worktrees/multi-lang
bin/test/unit.bash src/plcc/lang/ext/java/emit_test.py
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/lang/ext/java/emit.py src/plcc/lang/ext/java/emit_test.py
git commit -m "feat(java-emit): replace stub with full Jinja2-based emitter"
```

---

## Task 10: Update plcc-java-build for org.json classpath

**Files:**
- Modify: `src/plcc/lang/ext/java/build.py`
- Modify: `tests/bats/commands/plcc-java-build.bats`

- [ ] **Step 1: Replace `main()` in `src/plcc/lang/ext/java/build.py`**

```python
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-java-build", Events, args)
    output_dir = Path(args['--output']).resolve()
    verbose.emit(Events.STARTED, message=f'compiling in {output_dir}')
    java_files = list(output_dir.glob('*.java'))
    runtime_java_files = list((output_dir / 'runtime').glob('*.java'))
    if not java_files and not runtime_java_files:
        verbose.emit(Events.FINISHED, message='no .java files found')
        return
    json_jars = list((output_dir / 'runtime').glob('org.json*.jar'))
    if not json_jars:
        print('plcc-java-build: org.json jar not found in runtime/', file=sys.stderr)
        sys.exit(1)
    json_jar = str(json_jars[0])
    result = subprocess.run(
        ['javac', '-cp', json_jar] + [str(f) for f in java_files + runtime_java_files],
        cwd=str(output_dir),
    )
    if result.returncode != 0:
        print('plcc-java-build: javac failed', file=sys.stderr)
        sys.exit(result.returncode)
    verbose.emit(Events.FINISHED, message='done')
```

Also add `from pathlib import Path` to the imports at the top of `build.py` (remove `import glob` and `import os`, add `from pathlib import Path`).

Full updated `src/plcc/lang/ext/java/build.py`:

```python
"""plcc-java-build
    Compile generated Java source files.

Usage:
    plcc-java-build --output=DIR [options]

Options:
    --output=DIR    Directory containing generated Java files.
    -h --help       Show this message.
"""

import enum
import subprocess
import sys
from pathlib import Path

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-java-build", Events, args)
    output_dir = Path(args['--output']).resolve()
    verbose.emit(Events.STARTED, message=f'compiling in {output_dir}')
    java_files = list(output_dir.glob('*.java'))
    runtime_java_files = list((output_dir / 'runtime').glob('*.java'))
    if not java_files and not runtime_java_files:
        verbose.emit(Events.FINISHED, message='no .java files found')
        return
    json_jars = list((output_dir / 'runtime').glob('org.json*.jar'))
    if not json_jars:
        print('plcc-java-build: org.json jar not found in runtime/', file=sys.stderr)
        sys.exit(1)
    json_jar = str(json_jars[0])
    result = subprocess.run(
        ['javac', '-cp', json_jar] + [str(f) for f in java_files + runtime_java_files],
        cwd=str(output_dir),
    )
    if result.returncode != 0:
        print('plcc-java-build: javac failed', file=sys.stderr)
        sys.exit(result.returncode)
    verbose.emit(Events.FINISHED, message='done')
```

- [ ] **Step 2: Update `tests/bats/commands/plcc-java-build.bats` to verify `.class` files for non-stub classes**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    if ! command -v javac &>/dev/null; then skip "JDK not available"; fi
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial-java.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
    plcc-java-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
}

teardown() { rm -rf "${WORK_DIR}" "${SPEC_JSON}" "${MODEL_JSON}"; }

@test "plcc-java-build is on PATH" { command -v plcc-java-build; }

@test "plcc-java-build compiles Main.java" {
    run plcc-java-build --output="${WORK_DIR}"
    [ "$status" -eq 0 ]
    [ -f "${WORK_DIR}/Main.class" ]
}

@test "plcc-java-build compiles Program.class" {
    run plcc-java-build --output="${WORK_DIR}"
    [ "$status" -eq 0 ]
    [ -f "${WORK_DIR}/Program.class" ]
}
```

- [ ] **Step 3: Run the updated command test**

```bash
cd .worktrees/multi-lang
bin/test/command.bash tests/bats/commands/plcc-java-build.bats
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/lang/ext/java/build.py tests/bats/commands/plcc-java-build.bats
git commit -m "feat(java-build): add org.json classpath and runtime/*.java compilation"
```

---

## Task 11: Update plcc-java-run for org.json classpath

**Files:**
- Modify: `src/plcc/lang/ext/java/run.py`

- [ ] **Step 1: Replace `src/plcc/lang/ext/java/run.py`**

```python
"""plcc-java-run
    Run a compiled Java interpreter.

Usage:
    plcc-java-run --output=DIR [options]

Options:
    --output=DIR    Directory containing compiled Java class files.
    -h --help       Show this message.
"""

import enum
import os
import subprocess
import sys
from pathlib import Path

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-java-run", Events, args)
    output_dir = Path(args['--output']).resolve()
    verbose.emit(Events.STARTED, message=f'running Main in {output_dir}')
    json_jars = list((output_dir / 'runtime').glob('org.json*.jar'))
    if not json_jars:
        print('plcc-java-run: org.json jar not found in runtime/', file=sys.stderr)
        sys.exit(1)
    json_jar = str(json_jars[0])
    classpath = f"{output_dir}{os.pathsep}{json_jar}"
    result = subprocess.run(
        ['java', '-cp', classpath, 'Main'],
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    verbose.emit(Events.FINISHED, message=f'exit {result.returncode}')
    sys.exit(result.returncode)
```

- [ ] **Step 2: Run the existing command tests to check nothing obviously broken**

```bash
cd .worktrees/multi-lang
bin/test/command.bash tests/bats/commands/plcc-java-run.bats
```

Note: the run test currently expects `"evaluated: program (tree)"` from the old stub. It will fail until Task 12 updates the fixture and test. That failure is expected at this point.

- [ ] **Step 3: Commit**

```bash
git add src/plcc/lang/ext/java/run.py
git commit -m "feat(java-run): add org.json classpath"
```

---

## Task 12: Update trivial-java.plcc fixture and command bats tests

**Files:**
- Modify: `tests/fixtures/trivial-java.plcc`
- Modify: `tests/bats/commands/plcc-java-emit.bats`
- Modify: `tests/bats/commands/plcc-java-run.bats`

The current `trivial-java.plcc` has no Java semantics. Add a `$run` method that prints the token lexeme. The run test will then verify a JSON result record with `"value":null` (void return) and that stdout from `$run()` appears.

- [ ] **Step 1: Replace `tests/fixtures/trivial-java.plcc`**

```
token NUM '\d+'
skip SPACE '\s+'
%
<program> ::= <NUM>num
% Java Java
Program
%%%
    public void $run() {
        System.out.println(num.toString());
    }
%%%
```

- [ ] **Step 2: Replace `tests/bats/commands/plcc-java-emit.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial-java.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
}

teardown() { rm -rf "${WORK_DIR}" "${SPEC_JSON}" "${MODEL_JSON}"; }

@test "plcc-java-emit is on PATH" { command -v plcc-java-emit; }

@test "plcc-java-emit produces Program.java" {
    plcc-java-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
    [ -f "${WORK_DIR}/Program.java" ]
}

@test "plcc-java-emit produces Main.java" {
    plcc-java-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
    [ -f "${WORK_DIR}/Main.java" ]
}

@test "plcc-java-emit copies runtime directory" {
    plcc-java-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
    [ -f "${WORK_DIR}/runtime/Node.java" ]
    [ -f "${WORK_DIR}/runtime/Token.java" ]
    [ -f "${WORK_DIR}/runtime/Registry.java" ]
    [ -f "${WORK_DIR}/runtime/Deserializer.java" ]
    ls "${WORK_DIR}/runtime/org.json"*.jar
}

@test "plcc-java-emit accepts --verbose" {
    run bash -c "plcc-java-emit --output='${WORK_DIR}' --verbose=1 < '${MODEL_JSON}'"
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 3: Replace `tests/bats/commands/plcc-java-run.bats`**

We feed a real parse tree JSON for `program(num=Token("NUM","42"))` and check:
1. Exit code 0
2. Direct `$run()` output (`42`) appears on stdout before the JSON record
3. A `{"kind":"result",...}` record appears

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    if ! command -v javac &>/dev/null; then skip "JDK not available"; fi
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial-java.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
    plcc-java-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
    plcc-java-build --output="${WORK_DIR}"
}

teardown() { rm -rf "${WORK_DIR}" "${SPEC_JSON}" "${MODEL_JSON}"; }

@test "plcc-java-run is on PATH" { command -v plcc-java-run; }

@test "plcc-java-run evaluates parse-tree JSONL" {
    TREE='{"kind":"tree","rule":"program","children":[["num",{"kind":"token","name":"NUM","lexeme":"42"}]]}'
    run bash -c "echo '${TREE}' | plcc-java-run --output='${WORK_DIR}'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *'"kind"'* ]]
    [[ "$output" == *'"result"'* ]]
}
```

- [ ] **Step 4: Run all three command tests**

```bash
cd .worktrees/multi-lang
bin/test/command.bash tests/bats/commands/plcc-java-emit.bats
bin/test/command.bash tests/bats/commands/plcc-java-build.bats
bin/test/command.bash tests/bats/commands/plcc-java-run.bats
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/trivial-java.plcc \
        tests/bats/commands/plcc-java-emit.bats \
        tests/bats/commands/plcc-java-build.bats \
        tests/bats/commands/plcc-java-run.bats
git commit -m "test(java): update trivial-java fixture and command tests for real emitter"
```

---

## Task 13: Write integration bats tests

**Files:**
- Create: `tests/bats/integration/java-emit.bats`

This test runs the full emit → build → run pipeline end-to-end on the trivial-java fixture with a real parse tree.

- [ ] **Step 1: Create `tests/bats/integration/java-emit.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    if ! command -v javac &>/dev/null; then skip "JDK not available"; fi
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/trivial-java.plcc" \
        | plcc-model \
        | plcc-java-emit --output="${WORK_DIR}"
    plcc-java-build --output="${WORK_DIR}"
}

teardown() { rm -rf "${WORK_DIR}"; }

@test "emit produces one .java file per class" {
    [ -f "${WORK_DIR}/Program.java" ]
}

@test "emit produces Main.java" {
    [ -f "${WORK_DIR}/Main.java" ]
}

@test "emit copies runtime directory" {
    [ -f "${WORK_DIR}/runtime/Node.java" ]
    [ -f "${WORK_DIR}/runtime/Deserializer.java" ]
    ls "${WORK_DIR}/runtime/org.json"*.jar
}

@test "build produces .class files" {
    [ -f "${WORK_DIR}/Program.class" ]
    [ -f "${WORK_DIR}/Main.class" ]
}

@test "run exits 0 on valid tree JSON" {
    TREE='{"kind":"tree","rule":"program","children":[["num",{"kind":"token","name":"NUM","lexeme":"99"}]]}'
    run bash -c "echo '${TREE}' | plcc-java-run --output='${WORK_DIR}'"
    [ "$status" -eq 0 ]
}

@test "run outputs token lexeme from void \$run()" {
    TREE='{"kind":"tree","rule":"program","children":[["num",{"kind":"token","name":"NUM","lexeme":"99"}]]}'
    run bash -c "echo '${TREE}' | plcc-java-run --output='${WORK_DIR}'"
    [[ "$output" == *"99"* ]]
}

@test "run outputs JSON result record" {
    TREE='{"kind":"tree","rule":"program","children":[["num",{"kind":"token","name":"NUM","lexeme":"99"}]]}'
    run bash -c "echo '${TREE}' | plcc-java-run --output='${WORK_DIR}'"
    [[ "$output" == *'"kind"'* ]]
    [[ "$output" == *'"result"'* ]]
}

@test "full pipeline: plcc-tokens | plcc-tree | plcc-java-run" {
    LL1_JSON="$(mktemp)"
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    plcc-spec "${FIXTURES}/trivial-java.plcc" | plcc-ll1 > "${LL1_JSON}"
    run bash -c "echo '42' | plcc-tokens '${FIXTURES}/trivial-java.plcc' | plcc-tree --ll1='${LL1_JSON}' | plcc-java-run --output='${WORK_DIR}'"
    rm -f "${LL1_JSON}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
}
```

- [ ] **Step 2: Run the integration tests**

```bash
cd .worktrees/multi-lang
bin/test/integration.bash tests/bats/integration/java-emit.bats
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/bats/integration/java-emit.bats
git commit -m "test(java-emit): add integration tests for full emit→build→run pipeline"
```

---

## Task 14: Write corpus infrastructure

**Files:**
- Create: `tests/fixtures/languages-corpus.txt`
- Create: `tests/bats/e2e/languages-java.bats`
- Modify: `bin/test/e2e.bash`

The corpus test compares Java program output to `.expected` files. Since v8 grammars use `void $run()` with direct `System.out.println`, the test filters out JSON result/error lines (which start with `{"kind":`) before comparing.

- [ ] **Step 1: Create `tests/fixtures/languages-corpus.txt`**

Start empty (grammars are added as they pass in later tasks):

```
# languages corpus — grammars that pass end-to-end
# One path per line, relative to $LANGUAGES_REPO_PATH
# Format: src/<Name>/grammar
```

- [ ] **Step 2: Create `tests/bats/e2e/languages-java.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    if ! command -v javac &>/dev/null; then skip "JDK not available"; fi
    if [ -z "${LANGUAGES_REPO_PATH:-}" ]; then skip "LANGUAGES_REPO_PATH not set"; fi
    CORPUS="$(git rev-parse --show-toplevel)/tests/fixtures/languages-corpus.txt"
}

# Helper: run one grammar test case
# Usage: run_test_case <grammar_dir> <test_dir>
run_test_case() {
    local grammar_dir="$1"
    local test_dir="$2"
    local input_file expected_file build_dir ll1_json

    input_file=$(ls "${test_dir}"/*.input 2>/dev/null | head -1)
    expected_file=$(ls "${test_dir}"/*.expected 2>/dev/null | head -1)

    [ -n "${input_file}" ] || return 0
    [ -n "${expected_file}" ] || return 0

    build_dir="$(mktemp -d)"
    ll1_json="$(mktemp)"
    trap "rm -rf '${build_dir}' '${ll1_json}'" RETURN

    plcc-spec "${grammar_dir}" | plcc-ll1 > "${ll1_json}"
    plcc-spec "${grammar_dir}" | plcc-model | plcc-java-emit --output="${build_dir}"
    plcc-java-build --output="${build_dir}"

    actual=$(
        cat "${input_file}" \
        | plcc-tokens "${grammar_dir}" \
        | plcc-tree --ll1="${ll1_json}" \
        | plcc-java-run --output="${build_dir}" \
        | grep -v '^{"kind":'
    )
    expected=$(cat "${expected_file}")

    [ "${actual}" = "${expected}" ]
}

@test "corpus grammars pass" {
    while IFS= read -r line || [ -n "$line" ]; do
        # skip blank lines and comments
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue

        grammar_dir="${LANGUAGES_REPO_PATH}/${line}"
        [ -d "${grammar_dir}" ] || { echo "SKIP: ${grammar_dir} not found"; continue; }

        for test_dir in "${grammar_dir%/grammar}/tests"/*/; do
            [ -d "${test_dir}" ] || continue
            run_test_case "${grammar_dir}" "${test_dir}"
        done
    done < "${CORPUS}"
}
```

- [ ] **Step 3: Update `bin/test/e2e.bash` to run corpus tests when LANGUAGES_REPO_PATH is set**

Replace the contents of `bin/test/e2e.bash`:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/e2e.bash"
echo "-----------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

"${PROJECT_ROOT}/bin/install/bats.bash"
pdm install
export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"

bats tests/bats/e2e/

if command -v javac &>/dev/null && [ -n "${LANGUAGES_REPO_PATH:-}" ]; then
    echo ""
    echo "Running Java corpus tests (LANGUAGES_REPO_PATH=${LANGUAGES_REPO_PATH})"
    bats tests/bats/e2e/languages-java.bats
fi
```

- [ ] **Step 4: Run the e2e suite to confirm it still passes (corpus test skips gracefully)**

```bash
cd .worktrees/multi-lang
bin/test/e2e.bash
```

Expected: existing e2e tests pass; corpus test is skipped (LANGUAGES_REPO_PATH not set).

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/languages-corpus.txt \
        tests/bats/e2e/languages-java.bats \
        bin/test/e2e.bash
git commit -m "test(corpus): add languages-java e2e corpus infrastructure"
```

---

## Task 15: Add V0 grammar to corpus

**Files:**
- Modify: `tests/fixtures/languages-corpus.txt`

V0 is the simplest grammar (primitive expressions). This task follows the pattern for all subsequent corpus grammars.

- [ ] **Step 1: Run plcc-make on V0 manually to check for issues**

```bash
export LANGUAGES_REPO_PATH=/path/to/languages   # set once; re-use for all corpus tasks
cd "$(mktemp -d)"
plcc-make "${LANGUAGES_REPO_PATH}/src/V0/grammar"
```

Expected: `build/Java/` contains `.java` files and after `plcc-java-build`, `.class` files.

- [ ] **Step 2: Run one test case manually**

```bash
BUILD_DIR="$(pwd)/build/Java"
LL1_JSON="$(pwd)/build/ll1.json"
echo 'add1(+(2,3))' \
    | plcc-tokens "${LANGUAGES_REPO_PATH}/src/V0/grammar" \
    | plcc-tree --ll1="${LL1_JSON}" \
    | plcc-java-run --output="${BUILD_DIR}" \
    | grep -v '^{"kind":'
```

Expected: `add1(+(2,3))` (matches `src/V0/tests/nested-prims/V0.expected`).

- [ ] **Step 3: Add V0 to the corpus file**

Append to `tests/fixtures/languages-corpus.txt`:
```
src/V0/grammar
```

- [ ] **Step 4: Run the corpus test against V0**

```bash
cd .worktrees/multi-lang
LANGUAGES_REPO_PATH=/path/to/languages bats tests/bats/e2e/languages-java.bats
```

Expected: V0 passes.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/languages-corpus.txt
git commit -m "test(corpus): add V0 grammar to Java corpus"
```

---

## Task 16: Add V1–V6 grammars to corpus

**Files:**
- Modify: `tests/fixtures/languages-corpus.txt`

Repeat the pattern from Task 15 for each grammar. For each:

1. Run `plcc-make ${LANGUAGES_REPO_PATH}/src/<Name>/grammar` in a temp directory
2. Run each test case manually, compare to `.expected`
3. Fix any issues (template bugs, missing fragment kinds, etc.) with a separate commit
4. Add the grammar path to `languages-corpus.txt`
5. Confirm `bats tests/bats/e2e/languages-java.bats` passes
6. Commit with message `test(corpus): add <Name> grammar to Java corpus`

Grammar paths to add:
```
src/V1/grammar
src/V2/grammar
src/V3/grammar
src/V4/grammar
src/V5/grammar
src/V6/grammar
```

- [ ] **Step 1: Process V1**

```bash
cd "$(mktemp -d)"
plcc-make "${LANGUAGES_REPO_PATH}/src/V1/grammar"
# Run test cases and compare to expected
# Add to corpus, run bats, commit
```

- [ ] **Step 2: Process V2** (same pattern)

- [ ] **Step 3: Process V3** (same pattern)

- [ ] **Step 4: Process V4** (same pattern)

- [ ] **Step 5: Process V5** (same pattern)

- [ ] **Step 6: Process V6** (same pattern)

---

## Task 17: Add remaining grammars to corpus

**Files:**
- Modify: `tests/fixtures/languages-corpus.txt`

Continue the pattern from Task 16 for these grammars. Process one at a time — each is an independent commit:

```
src/LAMBDA/grammar
src/LAMBDAQ/grammar
src/NAME/grammar
src/NEED/grammar
src/LON/grammar
src/LON2/grammar
src/LONN/grammar
src/LIST/grammar
src/INFIX/grammar
src/Env/grammar
src/ARRAY/grammar
src/BF/grammar
src/OBJ/grammar
src/PROP/grammar
src/SET/grammar
src/TYPE0/grammar
src/TYPE1/grammar
src/CONT/grammar
src/RANDSCONT/grammar
src/REFCONT/grammar
src/THREADCONT/grammar
src/HANDLER/grammar
src/REF/grammar
src/GINGER/grammar
src/Misc/grammar
src/Prog/grammar
src/Examples/grammar
```

**For each grammar:**

- [ ] Run `plcc-make` in a temp dir
- [ ] Run test cases, compare to `.expected`
- [ ] Fix any emitter bugs (separate commit per bug fix)
- [ ] Add to `languages-corpus.txt`
- [ ] Run `LANGUAGES_REPO_PATH=... bats tests/bats/e2e/languages-java.bats` — must pass
- [ ] Commit: `test(corpus): add <Name> grammar to Java corpus`

**Common issues to watch for and fix:**

| Symptom | Likely cause | Fix |
| ------- | ------------ | --- |
| `NoSuchMethodException: $run` | Grammar has no Java semantics section, or entry_point lookup fails | Check `_find_java_section` logic; confirm model has `language:"Java"` |
| `ClassCastException` | Field type mismatch in generated cast | Check model field types vs cast in template |
| `NoSuchFieldException: _RULE_NAME` | Class registered without static metadata | Confirm template emits `_RULE_NAME`/`_FIELDS` for concrete classes |
| `KeyError: No class registered for rule` | Grammar uses `#` comment prefix fragments or file fragments that aren't actual classes | Check `_group_fragments` skips `#`; check model class names match grammar |
| Compilation error in generated code | Fragment body includes text that doesn't compile | Debug by examining generated `.java` file |

---

## Running the full test suite

After all grammars pass, run the complete suite to confirm no regressions:

```bash
cd .worktrees/multi-lang
bin/test/unit.bash
bin/test/command.bash
bin/test/integration.bash
LANGUAGES_REPO_PATH=/path/to/languages bin/test/e2e.bash
```

All tests should pass.
