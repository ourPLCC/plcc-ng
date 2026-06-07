# Issue 028 — Baseclass Body Injection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Inject semantics block fragments (body, import) into generated Java abstract baseclass files.

**Architecture:** The bug is entirely in `class_file.java.jinja`. The template's abstract-class branch generates a static empty body, discarding all fragments. The fix unifies the template into a single class path: concrete-only content (metadata constants, field declarations, constructor) is wrapped in `{% if not cls.abstract %}`; `body_fragments` are rendered unconditionally. No changes to `build_model.py` or `emit.py` — they are already correct.

**Tech Stack:** Jinja2 (template), pytest (unit tests), `bin/test/units.bash` (TDD runner)

---

### Task 1: Add failing tests for fragment injection into abstract classes

**Files:**
- Modify: `src/plcc/lang/ext/java/emit_test.py`

- [ ] **Step 1: Add two failing tests**

Open `src/plcc/lang/ext/java/emit_test.py`. Add these two tests after the existing `test_body_fragment_pasted_into_class` test:

```python
def test_body_fragment_injected_into_abstract_class(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Expr", "kind": "body",
         "body": "    public abstract int eval();"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    expr_java = (tmp_path / 'Expr.java').read_text()
    assert 'public abstract int eval()' in expr_java


def test_import_fragment_appears_in_abstract_class_file(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Expr", "kind": "import",
         "body": "import java.util.function.Function;"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    expr_java = (tmp_path / 'Expr.java').read_text()
    assert 'import java.util.function.Function;' in expr_java
```

Note: `_trivial_model()` already contains an `Expr` class with `"abstract": True` — no fixture changes needed.

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /workspaces/plcc-ng/.worktrees/test-plcc-rep
bin/test/units.bash src/plcc/lang/ext/java/emit_test.py::test_body_fragment_injected_into_abstract_class src/plcc/lang/ext/java/emit_test.py::test_import_fragment_appears_in_abstract_class_file -v
```

Expected: both FAIL. `test_body_fragment_injected_into_abstract_class` fails because `public abstract int eval()` is not in `Expr.java`. `test_import_fragment_appears_in_abstract_class_file` may pass already (imports are above the if/else in the current template) — if it does, that is fine; it documents an invariant.

- [ ] **Step 3: Commit the failing tests**

```bash
git add src/plcc/lang/ext/java/emit_test.py
git commit -m "test(java-emit): add failing tests for fragment injection into abstract classes"
```

---

### Task 2: Fix the Java template to inject fragments into abstract classes

**Files:**
- Modify: `src/plcc/lang/ext/java/templates/class_file.java.jinja`

- [ ] **Step 1: Replace the template contents**

The current template is:

```jinja
{% for frag in import_fragments %}{{ frag.body }}
{% endfor %}
import java.util.List;
import java.util.Map;
import runtime.Token;

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
```

Replace it entirely with:

```jinja
{% for frag in import_fragments %}{{ frag.body }}
{% endfor %}
import java.util.List;
import java.util.Map;
import runtime.Token;

public {% if cls.abstract %}abstract {% endif %}class {{ cls.name }}{% if cls.extends %} extends {{ cls.extends }}{% else %} extends runtime.Node{% endif %} {
{% if not cls.abstract %}

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

{% endif %}
{% for frag in body_fragments %}
{{ frag.body }}

{% endfor %}
}
```

- [ ] **Step 2: Run the two new tests to confirm they pass**

```bash
cd /workspaces/plcc-ng/.worktrees/test-plcc-rep
bin/test/units.bash src/plcc/lang/ext/java/emit_test.py::test_body_fragment_injected_into_abstract_class src/plcc/lang/ext/java/emit_test.py::test_import_fragment_appears_in_abstract_class_file -v
```

Expected: both PASS.

- [ ] **Step 3: Run the full emit test suite to confirm no regressions**

```bash
bin/test/units.bash src/plcc/lang/ext/java/emit_test.py -v
```

Expected: all tests PASS, including `test_abstract_class_generates_no_constructor`.

- [ ] **Step 4: Run all unit tests**

```bash
bin/test/units.bash
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/lang/ext/java/templates/class_file.java.jinja
git commit -m "fix(java-emit): inject body fragments into abstract baseclass files"
```

---

### Task 3: Move issue 028 to done

**Files:**
- Move: `docs/issues/028-plcc-rep-baseclass-semantics-block-injection.md` → `docs/issues/done/028-plcc-rep-baseclass-semantics-block-injection.md`

- [ ] **Step 1: Move the issue file**

```bash
cd /workspaces/plcc-ng/.worktrees/test-plcc-rep
git mv docs/issues/028-plcc-rep-baseclass-semantics-block-injection.md docs/issues/done/028-plcc-rep-baseclass-semantics-block-injection.md
```

- [ ] **Step 2: Commit**

```bash
git commit -m "docs(issues): move 028 to done [skip ci]"
```
