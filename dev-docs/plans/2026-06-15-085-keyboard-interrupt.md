# 085 KeyboardInterrupt Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Suppress the Python stack trace printed when the user presses ^C in `plcc-rep`, and instead print `User interrupted execution by ^C.` and exit with code 130.

**Architecture:** Wrap the outer `for line in sys.stdin:` loop in `main.py.jinja` with `try/except KeyboardInterrupt`. The rest of the exit-130 propagation chain (`plcc-python-run`, `_read_response`, `SourceRunner`) is already correct and requires no changes.

**Tech Stack:** Python, Jinja2 template, pytest

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `src/plcc/lang/ext/python/templates/main.py.jinja` | Modify | Add `try/except KeyboardInterrupt` around the stdin loop |
| `src/plcc/lang/ext/python/emit_test.py` | Modify | Add test verifying generated `main.py` exits 130 silently on SIGINT |

---

### Task 1: Write the failing test

**Files:**
- Modify: `src/plcc/lang/ext/python/emit_test.py`

- [ ] **Step 1: Add the test**

Open `src/plcc/lang/ext/python/emit_test.py`. Add this test after `test_emit_generated_main_is_runnable` (around line 164):

```python
def test_emit_generated_main_exits_130_on_sigint(tmp_path, monkeypatch):
    import signal
    import time
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    proc = subprocess.Popen(
        [sys.executable, str(tmp_path / 'main.py')],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(0.1)  # ensure subprocess has entered the stdin loop
    proc.send_signal(signal.SIGINT)
    stdout, stderr = proc.communicate(timeout=5)
    assert proc.returncode == 130
    assert stderr == b''
    assert b'User interrupted execution by ^C.' in stdout
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
bin/test/units.bash src/plcc/lang/ext/python/emit_test.py::test_emit_generated_main_exits_130_on_sigint -v
```

Expected: FAIL. The generated `main.py` will crash with a `KeyboardInterrupt` traceback on stderr and a non-130 exit code.

---

### Task 2: Implement the fix

**Files:**
- Modify: `src/plcc/lang/ext/python/templates/main.py.jinja`

- [ ] **Step 1: Wrap the stdin loop**

Replace the entire content of `src/plcc/lang/ext/python/templates/main.py.jinja` with:

```jinja
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runtime.registry import Registry
{% for cls in classes %}from {{ cls.name }} import {{ cls.name }}
{% endfor %}
registry = Registry()
registry.register({% for cls in classes if not cls.abstract %}{{ cls.name }}{% if not loop.last %}, {% endif %}{% endfor %})

try:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            tree = registry.deserialize(json.loads(line))
            result = tree.{{ entry_point }}()
            print(json.dumps({"kind": "result", "value": repr(result) if result is not None else None}), flush=True)
        except Exception as e:
            print(json.dumps({"kind": "error", "type": type(e).__name__, "message": str(e)}), flush=True)
except KeyboardInterrupt:
    print("User interrupted execution by ^C.")
    sys.exit(130)
```

- [ ] **Step 2: Run the new test to verify it passes**

```bash
bin/test/units.bash src/plcc/lang/ext/python/emit_test.py::test_emit_generated_main_exits_130_on_sigint -v
```

Expected: PASS

- [ ] **Step 3: Run the full unit suite to check for regressions**

```bash
bin/test/units.bash
```

Expected: all 981+ tests pass, 0 failures.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/lang/ext/python/templates/main.py.jinja \
        src/plcc/lang/ext/python/emit_test.py
git commit -m "fix(rep): suppress KeyboardInterrupt stack trace in generated main.py

On ^C, generated Python interpreters now print 'User interrupted
execution by ^C.' and exit 130 instead of crashing with a traceback.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```
