# Issue 028 — Baseclass Body Injection Design

**Date:** 2026-05-19
**Status:** APPROVED
**Issue:** `docs/issues/028-plcc-rep-baseclass-semantics-block-injection.md`

---

## 1. Problem

When a grammar uses named alternative rules (`:AltName` syntax), `plcc-java-emit`
generates an abstract baseclass for the non-terminal. If a semantics block targets
that baseclass, the code is silently discarded.

Root cause: `class_file.java.jinja` has two branches. The concrete class branch injects
all fragment kinds; the abstract class branch generates a hard-coded empty body:

```jinja
{% if cls.abstract %}
public abstract class {{ cls.name }} ... {
}
{% else %}
...concrete class with fragments...
{% endif %}
```

The Python emitter is unaffected — its template has no abstract/concrete split, so
fragment injection into abstract classes already works.

The model layer (`build_model.py`) is also correct: it includes abstract baseclasses
in `known_class_names`, so `_compute_kind` returns `'body'` for plain fragments
targeting a baseclass, and the emitter passes those fragments to the template. The
fragments arrive at the template correctly; the template discards them.

---

## 2. Design

### 2.1 Approach

Unify the Java template into a single class path. The `abstract` keyword, the
constructor, and the metadata constants are conditionally emitted within one class
body instead of in two separate branches. This closes the divergence that caused the
bug and prevents future modifiers from needing to be wired into two places.

### 2.2 Template change — `class_file.java.jinja`

Replace the current two-branch `{% if cls.abstract %}...{% else %}...{% endif %}`
structure with a single class declaration. Concrete-only content (metadata constants,
field declarations, map-constructor) is wrapped in `{% if not cls.abstract %}`.
`body_fragments` are rendered unconditionally at the end of the class body.

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

### 2.3 Modifier support for abstract baseclasses

| Modifier | Placement | Works after fix? |
|----------|-----------|-----------------|
| *(none)* | Inside class body | Yes — `body_fragments` rendered unconditionally |
| `:import` | Top of file | Yes — already above the class declaration in template |
| `:file`   | Replaces entire file | Yes — handled in emitter, not template |
| `:init`   | Inside constructor | No — by design. Abstract baseclasses have no generated constructor. Grammar authors who need one write it as a `body` fragment, retaining full control over the signature. |
| `:top`, `:class` | Python-only | N/A |

### 2.4 No changes to model or emitter

`build_model.py` and `emit.py` are correct and require no changes. The fix is
entirely in the Jinja template.

### 2.5 No changes to Python emitter

`class_file.py.jinja` already injects all fragment kinds for both abstract and
concrete classes.

---

## 3. Tests

Two new tests in `src/plcc/lang/ext/java/emit_test.py`, both using the existing
`_trivial_model()` fixture (which already contains an `Expr` abstract class):

**Test 1 — body fragment injected into abstract class:**

Appends a body fragment targeting `Expr` and asserts the fragment content appears
in the generated `Expr.java`. This is the primary regression guard for the fix.

**Test 2 — import fragment appears in abstract class file:**

Appends an import fragment targeting `Expr` and asserts it appears in `Expr.java`.
Import fragments already work, but the test documents this invariant and guards
against future regressions if the template is restructured again.

---

## 4. Acceptance criteria

1. A `body` fragment targeting an abstract baseclass appears in the generated
   `.java` file for that class.
2. An `import` fragment targeting an abstract baseclass appears at the top of the
   generated `.java` file.
3. Concrete class output is byte-for-byte identical to the current output
   (the template unification must not change the concrete class format).
4. All existing `emit_test.py` tests pass without modification.
5. The `test_abstract_class_generates_no_constructor` test continues to pass —
   abstract classes still have no generated constructor.
