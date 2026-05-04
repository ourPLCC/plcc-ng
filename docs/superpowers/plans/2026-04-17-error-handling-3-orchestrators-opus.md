# Error Handling Redesign — Part 3: Orchestrator Pipefail (Opus)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Model:** Opus. Cross-cutting orchestration code touching three Level 2 commands with subtle semantics (upstream-first attribution, cascade suppression, structured error re-rendering). Small implementation surface, but judgment-heavy — get this wrong and every pipeline error surface regresses.

**Goal:** Wire §17.9's pipeline-failure model into the Level 2 orchestrators that drive actual subprocess pipelines (`plcc-scan`, `plcc-parse`, `plcc-rep`). After Part 3, when a pipeline child fails, the user sees the first failing stage's error (not its downstream cascade), rendered with position and context, and the orchestrator exits nonzero with the offending stage's code.

**Design reference:** `docs/design/2026-04-12-multi-lang-pipeline.md` §17.9 (landed by Part 1).

**Predecessors:** Parts 1 and 2 must be merged. This plan depends on `VerboseContext.emit_error` (Part 2, Task 2) and on stages emitting `"event": "error"` records on their JSONL stderr (Part 2, Task 3).

**Tech stack:** Python 3.12+, pdm, pytest, docopt-ng, BATS.

---

## Design summary

### What's already right

`plcc-parse` and `plcc-rep` already:

- Force `--verbose-format=json` on children (via `VerboseContext.child_flags_for_orchestrator`).
- Check child returncodes in the order that happens to be upstream-first.
- Capture each child's stderr and re-render it through `VerboseContext.reformat_child_events`.

### What's missing

1. **Explicit upstream-first attribution.** The current code's ordering is correct by accident; there is no abstraction that encodes "walk the pipeline from the head and report the first failing stage." If someone reorders the checks, attribution silently regresses.

2. **Cascade suppression.** When upstream (`plcc-tokens`) fails, downstream (`plcc-tree`) also fails with a cascading error (EOF in the middle of a token stream). The orchestrator currently reformats both stages' stderr and prints both errors — the user sees two errors where the root cause is one.

3. **Structured error rendering.** `VerboseContext.reformat_child_events` renders every event uniformly as `{stage}: {event}: {message}`. It does not consume the `pos` field from `event: "error"` records. The user sees `plcc-tokens: error: unrecognized character` without a position, even though the child emitted a full structured record.

4. **Dead code for legacy in-band errors.** `plcc-scan`'s output formatter has a branch for `kind: "error"` token records that Part 2 eliminated. `plcc-parse`'s `_print_tree` has a branch for `kind: "error"` tree children that Part 1 eliminated from the schema. Both branches are unreachable and should be removed.

### Solution

- **New helper `reap_pipeline(procs, labels)` in `plcc.verbose`** (or a new `plcc.pipefail` module). Given a list of `(Popen, label)` pairs in upstream-to-downstream order, waits for all to finish, parses each stage's stderr into JSONL events, finds the first failing stage (lowest index with nonzero returncode), and returns a structured result describing what to render and what exit code to propagate.
- **Extend `VerboseContext.reformat_child_events`** to recognize `event: "error"` records and render them with position in text mode (`{stage}: {file}:{line}:{col}: error: {message}`).
- **Cascade suppression:** when `reap_pipeline` finds a failing stage, it emits that stage's error events only; events from downstream stages are discarded (they were cascades). Upstream stages that succeeded still have their milestone events reformatted normally.
- **Dead code removal:** delete the `kind: "error"` branches in `plcc-scan`'s formatter and `plcc-parse`'s `_print_tree`.
- **Deferred:** long-lived interpreter resilience (per-chunk parser failure must not kill the session) is a Phase 2 Part 2 concern. Part 3 handles only one-shot pipeline invocations.

---

## Task 1 — Verify green bar (post-Part 2)

**Files:**
- Run only: `bin/test/all.bash`

- [ ] **Step 1: Confirm Parts 1 and 2 are merged**

```bash
git log --oneline | head
```

Look for the commits from Parts 1 and 2 (doc amendment, `VerboseContext.emit_error`, token-error stderr routing, `plcc-ll1` `is_ll1`, `plcc-make` `is_ll1` check). If any are missing, stop and resolve.

- [ ] **Step 2: Run the full test suite**

```bash
cd /workspaces/plcc-ng/.worktrees/multi-lang
bin/test/all.bash
```

Expected: green. Record test counts.

---

## Task 2 — Add `reap_pipeline` helper

**Files:**
- Edit: `src/plcc/verbose.py`
- Edit: `src/plcc/verbose_test.py`

Context: the helper encapsulates upstream-first attribution, cascade suppression, and JSONL event collection. Putting it next to `VerboseContext` keeps all cross-cutting pipeline primitives in one module. An alternative is a new `plcc.pipefail` module; choose that instead if `verbose.py` grows awkwardly large.

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/verbose_test.py`:

```python
import subprocess

from plcc.verbose import reap_pipeline, VerboseContext


def _dummy_proc(stderr_bytes, returncode):
    """Build a minimal Popen-like object for unit testing reap_pipeline."""
    class P:
        pass
    p = P()
    p.returncode = returncode
    p.stderr_captured = stderr_bytes
    return p


def test_reap_pipeline_all_success():
    tokens_stderr = b'{"stage":"plcc-tokens","event":"started"}\n'
    tree_stderr = b'{"stage":"plcc-tree","event":"started"}\n'
    stages = [
        (_dummy_proc(tokens_stderr, 0), "plcc-tokens"),
        (_dummy_proc(tree_stderr, 0), "plcc-tree"),
    ]
    result = reap_pipeline(stages)
    assert result.failed_stage is None
    assert result.exit_code == 0
    # All non-error events are kept for reformatting
    assert len(result.events_to_render) == 2


def test_reap_pipeline_upstream_failure_suppresses_downstream():
    tokens_err = (
        b'{"stage":"plcc-tokens","event":"error","severity":"error",'
        b'"pos":{"file":"p.txt","line":1,"column":3},'
        b'"message":"unrecognized character"}\n'
    )
    tree_err = (
        b'{"stage":"plcc-tree","event":"error","severity":"error",'
        b'"pos":{"file":"p.txt","line":1,"column":0},'
        b'"message":"unexpected end of input"}\n'
    )
    stages = [
        (_dummy_proc(tokens_err, 1), "plcc-tokens"),
        (_dummy_proc(tree_err, 1), "plcc-tree"),
    ]
    result = reap_pipeline(stages)
    assert result.failed_stage == "plcc-tokens"
    assert result.exit_code == 1
    # Only the upstream-failing stage's error events render
    rendered_stages = {ev["stage"] for ev in result.events_to_render}
    assert rendered_stages == {"plcc-tokens"}


def test_reap_pipeline_downstream_failure_reports_downstream():
    # Upstream succeeded; downstream failed (e.g. parser hit a syntax error)
    tokens_ok = b'{"stage":"plcc-tokens","event":"finished"}\n'
    parser_err = (
        b'{"stage":"plcc-parser-table","event":"error","severity":"error",'
        b'"pos":{"file":"p.txt","line":4,"column":12},'
        b'"message":"expected IDENT"}\n'
    )
    stages = [
        (_dummy_proc(tokens_ok, 0), "plcc-tokens"),
        (_dummy_proc(parser_err, 2), "plcc-tree"),
    ]
    result = reap_pipeline(stages)
    assert result.failed_stage == "plcc-tree"
    assert result.exit_code == 2
```

- [ ] **Step 2: Run tests, confirm failure**

```bash
bin/test/units.bash src/plcc/verbose_test.py
```

Expected: the three new tests fail (helper missing).

- [ ] **Step 3: Implement `reap_pipeline`**

In `src/plcc/verbose.py`, add:

```python
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PipelineResult:
    failed_stage: Optional[str]   # label of first failing stage, or None
    exit_code: int                # returncode of first failing stage, or 0
    events_to_render: List[dict] = field(default_factory=list)


def reap_pipeline(stages):
    """Wait for all pipeline stages, attribute failure upstream-first,
    and suppress downstream cascades.

    Arguments:
        stages: list of (Popen-or-dummy, label) pairs in upstream-to-downstream
                order. Each proc must have .returncode set and either
                .stderr_captured (bytes) already set, or a .stderr attribute
                that can be .read().

    Returns:
        PipelineResult with:
          - failed_stage: label of first failing stage, or None
          - exit_code: returncode of the first failing stage, or 0
          - events_to_render: JSONL events to be reformatted.
            If any stage failed, events from downstream-of-failure are dropped.
    """
    # Collect stderr bytes for every stage, parse JSONL.
    per_stage_events = []
    for proc, label in stages:
        stderr_bytes = getattr(proc, "stderr_captured", None)
        if stderr_bytes is None and getattr(proc, "stderr", None) is not None:
            stderr_bytes = proc.stderr.read()
        text = (stderr_bytes or b"").decode("utf-8", errors="replace")
        events = _parse_jsonl_events(text)
        per_stage_events.append(events)

    # Find first failing stage.
    failed_index = None
    for i, (proc, _label) in enumerate(stages):
        if proc.returncode != 0:
            failed_index = i
            break

    if failed_index is None:
        all_events = [e for stage_events in per_stage_events for e in stage_events]
        return PipelineResult(failed_stage=None, exit_code=0, events_to_render=all_events)

    # Keep events from stages 0..failed_index inclusive; drop everything downstream.
    kept = []
    for events in per_stage_events[: failed_index + 1]:
        kept.extend(events)

    return PipelineResult(
        failed_stage=stages[failed_index][1],
        exit_code=stages[failed_index][0].returncode,
        events_to_render=kept,
    )


def _parse_jsonl_events(text):
    events = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            # Non-JSON line (e.g. a child that wrote text to stderr despite
            # --verbose-format=json). Preserve it as an opaque record.
            events.append({"stage": "unknown", "event": "raw", "message": line})
    return events
```

- [ ] **Step 4: Run, confirm pass**

```bash
bin/test/units.bash src/plcc/verbose_test.py
```

Expected: all new tests pass; existing tests still pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/verbose.py src/plcc/verbose_test.py
git commit -m "feat(verbose): add reap_pipeline for upstream-first attribution + cascade suppression per §17.9"
```

---

## Task 3 — Extend `reformat_child_events` to render errors with position

**Files:**
- Edit: `src/plcc/verbose.py`
- Edit: `src/plcc/verbose_test.py`

Context: children now emit `{"event": "error", "pos": {...}, "message": ...}` records under `--verbose-format=json`. The orchestrator must render these as GNU-style errors (text mode) or pass-through (json mode), matching the `VerboseContext.emit_error` format introduced in Part 2.

- [ ] **Step 1: Write the failing tests**

Add to `verbose_test.py`:

```python
def test_reformat_child_events_renders_error_with_position_text(capsys):
    ctx = VerboseContext("plcc-parse", SampleEvents, level=0, fmt="text")
    ctx.reformat_child_events([{
        "stage": "plcc-tokens",
        "event": "error",
        "severity": "error",
        "pos": {"file": "p.txt", "line": 4, "column": 12},
        "message": "unrecognized character '$'",
    }])
    _, err = capsys.readouterr()
    assert err == "plcc-tokens: p.txt:4:12: error: unrecognized character '$'\n"


def test_reformat_child_events_renders_error_json_pass_through(capsys):
    ctx = VerboseContext("plcc-parse", SampleEvents, level=0, fmt="json")
    event = {
        "stage": "plcc-tokens",
        "event": "error",
        "severity": "error",
        "pos": {"file": "p.txt", "line": 4, "column": 12},
        "message": "unrecognized character '$'",
    }
    ctx.reformat_child_events([event])
    _, err = capsys.readouterr()
    records = [json.loads(l) for l in err.strip().splitlines() if l.strip()]
    assert records == [event]


def test_reformat_child_events_non_error_unchanged(capsys):
    # Ensure the error-path does not disturb existing rendering of non-error events.
    ctx = VerboseContext("plcc-parse", SampleEvents, level=0, fmt="text")
    ctx.reformat_child_events([{
        "stage": "plcc-tokens", "event": "started", "message": "go",
    }])
    _, err = capsys.readouterr()
    assert err == "plcc-tokens: started: go\n"
```

- [ ] **Step 2: Run, confirm failure**

```bash
bin/test/units.bash src/plcc/verbose_test.py
```

Expected: first two tests fail (error records rendered uniformly, missing position).

- [ ] **Step 3: Update `reformat_child_events`**

Replace its body with:

```python
def reformat_child_events(self, events):
    for ev in events:
        if self.fmt == "json":
            print(json.dumps(ev), file=sys.stderr, flush=True)
            continue
        if ev.get("event") == "error":
            stage = ev.get("stage", "unknown")
            pos = ev.get("pos", {}) or {}
            file = pos.get("file") or "<stdin>"
            line = pos.get("line", 0)
            col = pos.get("column", 0)
            msg = ev.get("message", "")
            print(f"{stage}: {file}:{line}:{col}: error: {msg}",
                  file=sys.stderr, flush=True)
        else:
            stage = ev.get("stage", "unknown")
            event = ev.get("event", "unknown")
            msg = ev.get("message", "")
            print(f"{stage}: {event}: {msg}", file=sys.stderr, flush=True)
```

- [ ] **Step 4: Run, confirm pass**

```bash
bin/test/units.bash src/plcc/verbose_test.py
```

Expected: green.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/verbose.py src/plcc/verbose_test.py
git commit -m "feat(verbose): render error events with GNU-style position per §17.9"
```

---

## Task 4 — Wire `plcc-parse` to `reap_pipeline`

**Files:**
- Edit: `src/plcc/cmd/parse.py`
- Edit (if coverage exists): `tests/bats/commands/plcc-parse.bats`

- [ ] **Step 1: Replace the pipe-reaping block**

In `plcc-parse`'s main pipeline block (the `plcc-tokens | plcc-tree` section), replace the manual `tokens_proc.wait()` / `tree_proc.communicate()` / returncode-checking code with:

```python
from plcc.verbose import reap_pipeline

# ...after starting tokens_proc and tree_proc, writing input, closing stdin...
tree_out, _ = tree_proc.communicate()
tokens_proc.wait()

# Capture each stage's stderr for reap_pipeline.
tokens_proc.stderr_captured = tokens_proc.stderr.read()
tree_proc.stderr_captured = tree_proc.stderr  # tree_proc.communicate already set this
# Actually: communicate() closes and reads tree_proc.stderr; use the returned tuple:
# tree_out, tree_err = tree_proc.communicate(); tree_proc.stderr_captured = tree_err
```

Restructure the pipeline block so it ends with:

```python
tree_out, tree_err = tree_proc.communicate()
tokens_err = tokens_proc.stderr.read()
tokens_proc.wait()
tokens_proc.stderr_captured = tokens_err
tree_proc.stderr_captured = tree_err

result = reap_pipeline([
    (tokens_proc, "plcc-tokens"),
    (tree_proc, "plcc-tree"),
])
verbose.reformat_child_events(result.events_to_render)
if result.failed_stage:
    sys.exit(result.exit_code)
```

- [ ] **Step 2: Remove the dead `error`-kind branch in `_print_tree`**

Delete:

```python
elif kind == "error":
    print(f"{prefix}ERROR: {node}")
```

With the tree schema no longer allowing `error` children (Part 2, Task 4), this branch is unreachable.

- [ ] **Step 3: Write a failing integration test for attribution**

Create or extend `tests/bats/integration/plcc-parse-errors.bats`:

```bash
@test "plcc-parse: lex error reports plcc-tokens, not plcc-tree cascade" {
    tmp=$(mktemp -d)
    cat > "$tmp/trivial.plcc" <<'EOF'
token NUM '\d+'
%
<program> ::= NUM
EOF
    run bash -c "echo 'abc' | plcc-parse '$tmp/trivial.plcc'"
    [ "$status" -ne 0 ]
    # User-facing error: plcc-tokens is responsible
    echo "$stderr" | grep -q 'plcc-tokens:.*error'
    # plcc-tree's cascading "unexpected end of input" must NOT appear
    ! echo "$stderr" | grep -q 'plcc-tree:.*error.*end of input'
    rm -rf "$tmp"
}
```

(If the repo's BATS style captures stderr differently, adjust; the essential assertion is: upstream error shown, downstream cascade suppressed.)

- [ ] **Step 4: Run, confirm pass**

```bash
bin/test/integration.bash
bin/test/functional.bash
```

Expected: green.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/parse.py tests/bats/integration/plcc-parse-errors.bats
git commit -m "feat(parse): use reap_pipeline for upstream-first attribution + cascade suppression per §17.9"
```

---

## Task 5 — Wire `plcc-scan` to the new error rendering

**Files:**
- Edit: `src/plcc/cmd/scan.py`
- Edit (if coverage exists): `tests/bats/commands/plcc-scan.bats`

Context: `plcc-scan` does not set up a true multi-stage pipe — it runs `plcc-spec` sequentially, then `plcc-tokens` with fully buffered input. No cascade suppression is needed; the failure path is already upstream-first by construction. What `plcc-scan` does need:

1. Remove the dead `kind: "error"` branch in the output-formatting loop (Part 2 eliminated error-kind token records).
2. Rely on `VerboseContext.reformat_child_events` (now error-aware) to render `plcc-tokens`'s error on stderr with a position.
3. Drop the redundant `"plcc-scan: plcc-tokens failed (exit N)"` line — the re-rendered child error already tells the user what happened.

- [ ] **Step 1: Remove the dead branch**

In `plcc-scan`'s token-rendering loop, delete:

```python
elif record.get("kind") == "error":
    print(f"ERROR: {record}")
```

Tokens have only one kind now (`token`), so this branch is unreachable.

- [ ] **Step 2: Drop the redundant "X failed" line**

The existing error path is:

```python
if result.returncode != 0:
    print(f"plcc-scan: plcc-tokens failed (exit {result.returncode})", file=sys.stderr)
    sys.exit(result.returncode)
```

With `reformat_child_events` now rendering the child's full structured error, the `"plcc-tokens failed (exit N)"` line is noise. Replace the block with:

```python
if result.returncode != 0:
    sys.exit(result.returncode)
```

Apply the same simplification to the `plcc-spec` check above.

- [ ] **Step 3: Write a failing integration test**

Add to `tests/bats/integration/plcc-scan-errors.bats` (create if needed):

```bash
@test "plcc-scan: lex error produces GNU-style stderr and nonzero exit" {
    tmp=$(mktemp -d)
    cat > "$tmp/trivial.plcc" <<'EOF'
token NUM '\d+'
%
<program> ::= NUM
EOF
    run bash -c "echo 'abc' | plcc-scan '$tmp/trivial.plcc' 2>&1 >/dev/null"
    [ "$status" -ne 0 ]
    echo "$output" | grep -qE 'plcc-tokens: [^:]+:[0-9]+:[0-9]+: error:'
    rm -rf "$tmp"
}
```

- [ ] **Step 4: Run, confirm pass**

```bash
bin/test/integration.bash
bin/test/functional.bash
```

Expected: green.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/scan.py tests/bats/integration/plcc-scan-errors.bats
git commit -m "feat(scan): drop dead in-band error branch; rely on reformat_child_events for stderr rendering per §17.9"
```

---

## Task 6 — Wire `plcc-rep` to `reap_pipeline`

**Files:**
- Edit: `src/plcc/cmd/rep.py`
- Edit (if coverage exists): `tests/bats/commands/plcc-rep.bats`

Context: `plcc-rep` drives a three-stage pipe: `plcc-tokens | plcc-tree | plcc-lang-run`. Same shape as `plcc-parse` but with an extra stage downstream. Apply the same `reap_pipeline` pattern.

- [ ] **Step 1: Replace the pipe-reaping block**

Restructure the `plcc-tokens | plcc-tree | plcc-lang-run` block so it ends with:

```python
tokens_out, tokens_err = tokens_proc.communicate()
tree_out, tree_err = tree_proc.communicate()
run_out, run_err = run_proc.communicate()
tokens_proc.stderr_captured = tokens_err
tree_proc.stderr_captured = tree_err
run_proc.stderr_captured = run_err

result = reap_pipeline([
    (tokens_proc, "plcc-tokens"),
    (tree_proc, "plcc-tree"),
    (run_proc, "plcc-lang-run"),
])
verbose.reformat_child_events(result.events_to_render)
if result.failed_stage:
    sys.exit(result.exit_code)

sys.stdout.buffer.write(run_out)
sys.stdout.flush()
```

Note: `plcc-tokens` in this pipeline has its stdout piped to `plcc-tree`. `tokens_proc.communicate()` is not the right call if `stdin` is still being written — the code currently writes `input_data` to `tokens_proc.stdin` and then closes it before calling `communicate()` on downstream procs. The restructuring must preserve that sequencing; use `tokens_proc.wait()` + manual `tokens_proc.stderr.read()` if `communicate()` conflicts with the stdin-write ordering.

- [ ] **Step 2: Drop the redundant "X failed" lines**

Replace the three per-stage `if ... != 0: print(...); sys.exit(...)` blocks with the single `reap_pipeline` call above. The new `reformat_child_events` call renders each stage's structured error.

Apply the same simplification to the sequential stages (`plcc-spec`, `plcc-ll1`, `plcc-model`, `plcc-lang-emit`, `plcc-lang-build`) — delete the redundant `plcc-rep: X failed (exit N)` lines; child error rendering now tells the user what failed.

- [ ] **Step 3: Write a failing integration test**

Add `tests/bats/integration/plcc-rep-errors.bats`:

```bash
@test "plcc-rep: lex error suppresses plcc-tree and plcc-lang-run cascades" {
    tmp=$(mktemp -d)
    cat > "$tmp/trivial.plcc" <<'EOF'
token NUM '\d+'
%
<program> ::= NUM
% Java Java
EOF
    run bash -c "echo 'abc' | plcc-rep '$tmp/trivial.plcc' 2>&1 >/dev/null"
    [ "$status" -ne 0 ]
    echo "$output" | grep -q 'plcc-tokens:.*error'
    ! echo "$output" | grep -q 'plcc-tree:.*error'
    ! echo "$output" | grep -q 'plcc-lang-run:.*error'
    rm -rf "$tmp"
}
```

- [ ] **Step 4: Run, confirm pass**

```bash
bin/test/integration.bash
bin/test/functional.bash
```

Expected: green.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/rep.py tests/bats/integration/plcc-rep-errors.bats
git commit -m "feat(rep): use reap_pipeline for 3-stage pipe attribution + cascade suppression per §17.9"
```

---

## Task 7 — End-to-end verification

- [ ] **Step 1: Full suite**

```bash
bin/test/all.bash
```

Expected: green. Unit count grew (new `reap_pipeline` and `reformat_child_events` tests); BATS count grew (new integration error tests).

- [ ] **Step 2: Manual smoke test — `plcc-parse` upstream error**

```bash
echo 'abc' | plcc-parse tests/fixtures/trivial-java.plcc
echo "exit: $?"
```

Expected: exit nonzero; stderr contains one `plcc-tokens: ...: error: ...` line; **no** `plcc-tree: ...: error: ...` cascade line.

- [ ] **Step 3: Manual smoke test — `plcc-rep` upstream error**

```bash
echo 'abc' | plcc-rep tests/fixtures/trivial-java.plcc
echo "exit: $?"
```

Expected: exit nonzero; stderr contains one `plcc-tokens: ...: error: ...` line; **no** downstream cascade.

- [ ] **Step 4: Manual smoke test — error format in json mode**

```bash
echo 'abc' | plcc-parse --verbose-format=json tests/fixtures/trivial-java.plcc 2>&1 >/dev/null | head -20
```

Expected: JSONL on stderr; among the records, at least one `{"stage": "plcc-tokens", "event": "error", ...}` with a `pos` field; no such record from `plcc-tree` (cascade).

- [ ] **Step 5: Packaging check**

```bash
bin/test/packaging.bash
```

Expected: green. Ensures the new orchestration paths survive a fresh-venv install.

---

## Deferred and out of scope

- **Long-lived interpreter resilience** (§17.7): per-chunk parser failure must not kill the session. This requires the orchestrator to spawn a fresh per-chunk `plcc-tokens | plcc-tree` subpipeline for each chunk while keeping a long-lived interpreter subprocess alive. It is tracked as a Phase 2 Part 2 concern and is explicitly *out of scope* for this plan because no interpreter exists yet. When the interpreter lands, a follow-up amendment to `plcc-rep` will reuse `reap_pipeline` per-chunk without killing the session.

- **Error-code taxonomy.** §17.9 does not yet specify a stable catalog of error codes (e.g. `PLCC-TOK-001` for unrecognized character). The current plan uses human-readable messages only. A taxonomy can be layered on later without breaking the transport contract — add a `code` field to error records.

- **`--color=auto`** for error rendering (per §17.8.4's deferred color discussion). Out of scope.

## Completion

When this plan is complete:

- §17.9 is fully enforced across the pipeline's one-shot invocations.
- Users see the first failing stage's error, not its cascade.
- The token and tree schemas, the `plcc-ll1` output contract, and the orchestrator error paths all agree with the spec.
- The only remaining §17.9 obligation is long-lived-interpreter resilience, deferred to Phase 2 Part 2.
