# Design: Suppress KeyboardInterrupt stack trace in generated Python interpreter

**Issue:** 085
**Date:** 2026-06-15

## Problem

Pressing ^C in `plcc-rep` causes the generated `main.py` subprocess to crash with a full Python stack trace. `KeyboardInterrupt` inherits from `BaseException`, not `Exception`, so the inner `except Exception` block in `main.py.jinja` does not catch it. The exception propagates to the top level and Python prints a traceback before exiting.

## Scope

Python only. Java's JVM intercepts SIGINT at the runtime level and exits cleanly with code 130 — no stack trace, no change needed. Only `main.py.jinja` requires a fix.

## Change

### `src/plcc/lang/ext/python/templates/main.py.jinja`

Wrap the outer `for` loop in `try/except KeyboardInterrupt`. On interrupt, print a user-facing message to stdout, then exit with code 130.

```python
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

The message is printed to stdout (the pipe to `plcc-rep`) so that `_read_response` in `rep.py` receives and displays it when the interpreter is mid-evaluation. When ^C fires at the idle `>>>` prompt, `plcc-rep` exits first via `SourceRunner._clear_buffer_or_exit` before reading the message — nothing is printed, which is the correct behaviour (no computation was interrupted).

## Propagation chain (no changes needed)

The exit-130 chain is already correct end-to-end:

1. `main.py` exits 130 (new handler)
2. `plcc-python-run` (`run.py`) passes `result.returncode` through via `sys.exit(result.returncode)`
3. `plcc-rep`'s `_read_response` (line 179): `if rc is not None and (rc < 0 or rc == 130): sys.exit(130)`
4. `SourceRunner._evaluate` (line 139): catches any `KeyboardInterrupt` from `plcc-rep`'s own side and calls `sys.exit(130)`

## Testing

One new unit test in `src/plcc/lang/ext/python/emit_test.py`, alongside `test_emit_generated_main_is_runnable`:

- Generate `main.py` using `run_main([f'--output={tmp_path}'])`
- Launch it as a subprocess via `subprocess.Popen`
- Send SIGINT (`process.send_signal(signal.SIGINT)`)
- Wait for process to exit
- Assert exit code is 130
- Assert stderr is empty (no traceback)
- Assert stdout contains `"User interrupted execution by ^C."`
