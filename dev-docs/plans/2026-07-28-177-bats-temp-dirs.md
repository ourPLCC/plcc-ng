# bats temp directories via `BATS_TEST_TMPDIR` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace every `mktemp` call in the bats suite with a path under
`BATS_TEST_TMPDIR`, so the bats runner owns temporary-file cleanup and no test
carries cleanup code.

**Architecture:** Bats exports `BATS_TEST_TMPDIR` per test and removes it when
the test ends, pass or fail. Tests therefore name paths inside it instead of
allocating with `mktemp`, and the four hand-rolled cleanup mechanisms in use
today (`teardown()`, `trap … EXIT`, `trap … RETURN`, and a trailing `rm`) are
deleted. A lint test keeps `mktemp` from coming back.

**Tech Stack:** bash, bats-core 1.11.0 (pinned by `bin/install/bats.bash`).

**Spec:** [2026-07-28-177-bats-temp-dirs-design.md](../specs/2026-07-28-177-bats-temp-dirs-design.md)

## Global Constraints

- Work in the `arbno-mid-body-terminal` worktree at
  `/workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal`, on branch
  `arbno-mid-body-terminal`. Always `cd` there explicitly; a bare shell may
  reset to the main checkout.
- Every converted file must declare `bats_require_minimum_version 1.5.0`. Three
  lack it: `happy-path.bats`, `spec-tokens.bats`, `model-lang-emit.bats`.
- Directory replacements need an explicit `mkdir -p`. `mktemp -d` created the
  directory; a bare path does not.
- File replacements need no `mkdir`; every such path in this suite is written
  with `>` or `cat >`, which creates it.
- Do not touch `mktemp` calls under `bin/`. Those are not bats tests and the
  runner does not clean up after them.
- Conversions are behaviour-preserving. A converted file must pass exactly as it
  did before. Never change an assertion to make a converted file pass.
- Naming: replace the random suffix with a descriptive basename — `work`,
  `spec.json`, `model.json`, `ll1.json`, `output`, and so on, as given per file
  below.
- Commit messages follow conventional commits, scope `test`.

---

### Task 1: Canary test for the bats cleanup guarantee

The whole design rests on bats removing `BATS_TEST_TMPDIR`. This task pins that
property so a future change to the version pin fails loudly.

**Files:**
- Create: `tests/bats/commands/bats-temp-dirs.bats`

**Interfaces:**
- Consumes: nothing.
- Produces: `tests/bats/commands/bats-temp-dirs.bats`, which Task 9 extends
  with the lint test.

- [ ] **Step 1: Record the current violation count as RED evidence**

Run:
```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
grep -rln mktemp tests/bats --include='*.bats' | wc -l
grep -rn  mktemp tests/bats --include='*.bats' | wc -l
```
Expected: `42` files and `102` call sites. This is the state Task 9's lint will
reject. Record the numbers; do not commit anything in this step.

- [ ] **Step 2: Write the canary test**

Create `tests/bats/commands/bats-temp-dirs.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "bats removes BATS_TEST_TMPDIR after a test" {
    local probe="${BATS_TEST_TMPDIR}/inner.bats"
    local record="${BATS_TEST_TMPDIR}/recorded"

    cat > "${probe}" << EOF
@test "inner records its tmpdir" {
    printf '%s' "\${BATS_TEST_TMPDIR}" > "${record}"
}
EOF

    # 3>&- closes bats' TAP pass-through fd. Without it the nested run
    # writes its own TAP to fd 3 and corrupts this run's test count.
    run bats "${probe}" 3>&-
    [ "$status" -eq 0 ]
    [ -s "${record}" ]

    local inner
    inner="$(cat "${record}")"
    [ ! -e "${inner}" ]
}
```

- [ ] **Step 3: Run the canary**

Run: `bin/test/functional.bash tests/bats/commands/bats-temp-dirs.bats`
Expected: PASS, exactly 1 test, exit 0. An exit code of 1 with
`bats warning: Executed 2 instead of expected 1 tests` means the `3>&-` is
missing.

- [ ] **Step 4: Commit**

```bash
git add tests/bats/commands/bats-temp-dirs.bats
git commit -m "test: pin the bats BATS_TEST_TMPDIR cleanup guarantee"
```

---

### Task 2: Convert the straightforward `commands/` files

Twenty-two files whose temporaries are all allocated in `setup()` and removed by
a `teardown()` that does nothing else. For each: rewrite the assignments, add
`mkdir -p` for directories, and delete `teardown()` entirely.

**Files (modify):** `tests/bats/commands/` — `cache-stats.bats`,
`issues-close.bats`, `plcc-diagram-class-plantuml-emit.bats`,
`plcc-lang-build.bats`, `plcc-lang-emit.bats`, `plcc-java-emit.bats`,
`plcc-lang-run.bats`, `plcc-java-build.bats`, `plcc-java-run.bats`,
`plcc-parse.bats`, `plcc-make.bats`, `plcc-python-emit.bats`,
`plcc-parser-table.bats`, `plcc-ll1.bats`, `plcc-model.bats`, `plcc-spec.bats`,
`plcc-rep.bats`, `plcc-trees.bats`, `plcc-python-run.bats`, `plcc-scan.bats`,
`release-extract-changelog.bats`, `release-verify.bats`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: no symbols. Later tasks depend only on the convention.

- [ ] **Step 1: Apply the conversion, file by file**

The pattern, using `plcc-java-emit.bats` as the worked example. Before:

```bash
setup() {
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    ...
}

teardown() { rm -rf "${WORK_DIR}" "${SPEC_JSON}" "${MODEL_JSON}"; }
```

After:

```bash
setup() {
    WORK_DIR="${BATS_TEST_TMPDIR}/work"
    mkdir -p "${WORK_DIR}"
    SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"
    MODEL_JSON="${BATS_TEST_TMPDIR}/model.json"
    ...
}
```

The `teardown()` is removed, blank line included.

Per-file replacements:

| File | Replace | With |
| --- | --- | --- |
| `cache-stats.bats:9` | `STATS_DIR="$(mktemp -d)"` | `STATS_DIR="${BATS_TEST_TMPDIR}/stats"` + `mkdir -p` |
| `issues-close.bats:11` | `REPO="$(mktemp -d)"` | `REPO="${BATS_TEST_TMPDIR}/repo"` + `mkdir -p` |
| `plcc-diagram-class-plantuml-emit.bats:7` | `MODEL_JSON="$(mktemp)"` | `MODEL_JSON="${BATS_TEST_TMPDIR}/model.json"` |
| `plcc-diagram-class-plantuml-emit.bats:8` | `OUTPUT_DIR="$(mktemp -d)"` | `OUTPUT_DIR="${BATS_TEST_TMPDIR}/output"` + `mkdir -p` |
| `plcc-lang-build.bats:6` | `OUTPUT_DIR="$(mktemp -d)"` | `OUTPUT_DIR="${BATS_TEST_TMPDIR}/output"` + `mkdir -p` |
| `plcc-lang-emit.bats:7-9` | `SPEC_JSON`, `MODEL_JSON`, `OUTPUT_DIR` | `spec.json`, `model.json`, `output` + `mkdir -p` |
| `plcc-java-emit.bats:7-9` | `WORK_DIR`, `SPEC_JSON`, `MODEL_JSON` | `work` + `mkdir -p`, `spec.json`, `model.json` |
| `plcc-lang-run.bats:7-9` | `WORK_DIR`, `SPEC_JSON`, `MODEL_JSON` | `work` + `mkdir -p`, `spec.json`, `model.json` |
| `plcc-java-build.bats:8-10` | `WORK_DIR`, `SPEC_JSON`, `MODEL_JSON` | `work` + `mkdir -p`, `spec.json`, `model.json` |
| `plcc-java-run.bats:8-10` | `WORK_DIR`, `SPEC_JSON`, `MODEL_JSON` | `work` + `mkdir -p`, `spec.json`, `model.json` |
| `plcc-parse.bats:7` | `WORK_DIR="$(mktemp -d)"` | `WORK_DIR="${BATS_TEST_TMPDIR}/work"` + `mkdir -p` |
| `plcc-make.bats:7` | `WORK_DIR="$(mktemp -d)"` | `WORK_DIR="${BATS_TEST_TMPDIR}/work"` + `mkdir -p` |
| `plcc-python-emit.bats:7-9` | `WORK_DIR`, `SPEC_JSON`, `MODEL_JSON` | `work` + `mkdir -p`, `spec.json`, `model.json` |
| `plcc-parser-table.bats:8-9` | `SPEC_JSON`, `LL1_JSON` | `spec.json`, `ll1.json` |
| `plcc-ll1.bats:8` | `SPEC_JSON="$(mktemp)"` | `SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"` |
| `plcc-model.bats:8` | `SPEC_JSON="$(mktemp)"` | `SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"` |
| `plcc-spec.bats:8` | `BAD_SPEC="$(mktemp --suffix=.plcc)"` | `BAD_SPEC="${BATS_TEST_TMPDIR}/bad.plcc"` |
| `plcc-rep.bats:7` | `WORK_DIR="$(mktemp -d)"` | `WORK_DIR="${BATS_TEST_TMPDIR}/work"` + `mkdir -p` |
| `plcc-trees.bats:8-9` | `SPEC_JSON`, `LL1_JSON` | `spec.json`, `ll1.json` |
| `plcc-python-run.bats:7-9` | `WORK_DIR`, `SPEC_JSON`, `MODEL_JSON` | `work` + `mkdir -p`, `spec.json`, `model.json` |
| `plcc-scan.bats:7` | `WORK_DIR="$(mktemp -d)"` | `WORK_DIR="${BATS_TEST_TMPDIR}/work"` + `mkdir -p` |
| `release-extract-changelog.bats:9` | `WORK_DIR="$(mktemp -d)"` | `WORK_DIR="${BATS_TEST_TMPDIR}/work"` + `mkdir -p` |
| `release-verify.bats:16` | `STUB_DIR="$(mktemp -d)"` | `STUB_DIR="${BATS_TEST_TMPDIR}/stub"` + `mkdir -p` |

Delete the `teardown()` from all twenty-two.

`plcc-spec.bats` note: `BAD_SPEC` keeps a `.plcc` extension because
`plcc-spec` dispatches on it. Do not rename it to `bad`.

- [ ] **Step 2: Verify no `teardown()` or `mktemp` remains in these files**

Run:
```bash
grep -n 'mktemp\|teardown' tests/bats/commands/{cache-stats,issues-close,plcc-diagram-class-plantuml-emit,plcc-lang-build,plcc-lang-emit,plcc-java-emit,plcc-lang-run,plcc-java-build,plcc-java-run,plcc-parse,plcc-make,plcc-python-emit,plcc-parser-table,plcc-ll1,plcc-model,plcc-spec,plcc-rep,plcc-trees,plcc-python-run,plcc-scan,release-extract-changelog,release-verify}.bats
```
Expected: no output.

- [ ] **Step 3: Run the commands tier**

Run: `bin/test/commands.bash`
Expected: PASS, same test count as before the change.

- [ ] **Step 4: Commit**

```bash
git add tests/bats/commands
git commit -m "test(commands): use BATS_TEST_TMPDIR in setup-only test files"
```

---

### Task 3: Convert the remaining `commands/` files

Six files that allocate inside test bodies, use traps, or have a `teardown()`
doing work unrelated to temporaries.

**Files (modify):** `tests/bats/commands/` — `cache.bats`,
`plcc-haskell-emit.bats`, `plcc-tokens.bats`, `plcc-validate-semantic.bats`,
`plcc-validate-syntactic.bats`, `test-scripts-path-filter.bats`

- [ ] **Step 1: Convert `cache.bats`**

- L9: `CACHE_DIR="$(mktemp -d)"` → `CACHE_DIR="${BATS_TEST_TMPDIR}/cache"`,
  followed by `mkdir -p "${CACHE_DIR}"`. Leave `CACHE_FILE` and
  `PLCC_TEST_STATS_LOG`, which derive from it.
- L124: `fake_bin=$(mktemp -d)` → `fake_bin="${BATS_TEST_TMPDIR}/fake-bin"`,
  followed by `mkdir -p "${fake_bin}"`. Keep the `local fake_bin` declaration.
- L135: delete `rm -rf "${fake_bin}"`.
- `teardown()`: delete `rm -rf "${CACHE_DIR}"`, **keep**
  `rm -f "${DIRTY_FILE}"`. `DIRTY_FILE` is created in the repository root, not
  in a temporary directory, so bats will not clean it up. The resulting
  teardown is:

```bash
teardown() {
    rm -f "${DIRTY_FILE}"
}
```

- [ ] **Step 2: Convert `plcc-haskell-emit.bats`**

Three tests each do `out=$(mktemp -d)` (L19, L28, L37) and end with
`rm -rf "$out"` (L23, L32, L41). In each: replace the allocation with

```bash
    local out="${BATS_TEST_TMPDIR}/out"
    mkdir -p "$out"
```

and delete the trailing `rm -rf "$out"`. Each test gets its own
`BATS_TEST_TMPDIR`, so the shared basename `out` cannot collide.

This file has no `teardown()` and gains none.

- [ ] **Step 3: Convert `plcc-tokens.bats`**

- L8: `SPEC_JSON="$(mktemp)"` → `SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"`.
- L13: delete the `teardown()` containing `rm -f "${SPEC_JSON}"`.
- L55 and L111: `tmp=$(mktemp)` → `tmp="${BATS_TEST_TMPDIR}/out.jsonl"`.
- L60 and L115: delete `rm -f "$tmp"`.
- L85 and L101: `VERBOSITY_SPEC_JSON="$(mktemp)"` →
  `VERBOSITY_SPEC_JSON="${BATS_TEST_TMPDIR}/verbosity-spec.json"`.
- L97 and L107: delete `rm -f "${VERBOSITY_SPEC_JSON}"`.

- [ ] **Step 4: Convert `plcc-validate-semantic.bats` and `plcc-validate-syntactic.bats`**

Both allocate `SPEC_JSON=$(mktemp)` inside test bodies and guard it with
`trap "rm -f '${SPEC_JSON}'" EXIT` on the following line —
semantic at L30/31, L53/54, L76/77; syntactic at L30/31, L48/49.

In every case replace the pair

```bash
    SPEC_JSON=$(mktemp)
    trap "rm -f '${SPEC_JSON}'" EXIT
```

with

```bash
    SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"
```

Neither file has a `teardown()`, and neither gains one.

- [ ] **Step 5: Convert `test-scripts-path-filter.bats`**

- L8: `FAKE_BIN="$(mktemp -d)"` → `FAKE_BIN="${BATS_TEST_TMPDIR}/fake-bin"` +
  `mkdir -p "${FAKE_BIN}"`.
- L61: `STUB_ROOT="$(mktemp -d)"` → `STUB_ROOT="${BATS_TEST_TMPDIR}/stub-root"` +
  `mkdir -p "${STUB_ROOT}"`.
- L80: `FAKE_PDM_BIN="$(mktemp -d)"` →
  `FAKE_PDM_BIN="${BATS_TEST_TMPDIR}/fake-pdm-bin"` + `mkdir -p "${FAKE_PDM_BIN}"`.
- `teardown()`: drop the `rm -rf` line, **keep** both `unset` lines:

```bash
teardown() {
    unset SKIP_SETUP
    unset PLCC_NO_TEST_CACHE
}
```

- [ ] **Step 6: Verify and run the tier**

Run:
```bash
grep -n 'mktemp' tests/bats/commands/*.bats | grep -v bats-temp-dirs.bats
bin/test/commands.bash
```
Expected: the grep prints nothing; the tier passes with an unchanged test count.

- [ ] **Step 7: Commit**

```bash
git add tests/bats/commands
git commit -m "test(commands): use BATS_TEST_TMPDIR for in-body temporaries"
```

---

### Task 4: Convert the straightforward `integration/` files

**Files (modify):** `tests/bats/integration/` — `ll1-tree.bats`,
`model-lang-emit.bats`, `spec-tokens.bats`, `tokens-tree.bats`

- [ ] **Step 1: Apply the conversions**

| File | Replace | With |
| --- | --- | --- |
| `ll1-tree.bats:8-9` | `SPEC_JSON`, `LL1_JSON` | `spec.json`, `ll1.json` |
| `model-lang-emit.bats:5` | `SPEC_JSON="$(mktemp)"` | `SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"` |
| `model-lang-emit.bats:6` | `OUTPUT_DIR="$(mktemp -d)"` | `OUTPUT_DIR="${BATS_TEST_TMPDIR}/output"` + `mkdir -p` |
| `spec-tokens.bats:6` | `SPEC_JSON="$(mktemp)"` | `SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"` |
| `tokens-tree.bats:8-9` | `SPEC_JSON`, `LL1_JSON` | `spec.json`, `ll1.json` |

Delete the `teardown()` from all four.

- [ ] **Step 2: Add the version declaration where missing**

`spec-tokens.bats` and `model-lang-emit.bats` have no
`bats_require_minimum_version`. Add it directly under the shebang, matching the
other files:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0
```

Confirm with:
```bash
grep -L 'bats_require_minimum_version' tests/bats/integration/*.bats
```
Expected: no output.

- [ ] **Step 3: Run the tier**

Run: `bin/test/integration.bash`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/bats/integration
git commit -m "test(integration): use BATS_TEST_TMPDIR in setup-only test files"
```

---

### Task 5: Convert the remaining `integration/` files

**Files (modify):** `tests/bats/integration/` — `java-emit.bats`,
`python-emit.bats`, `plcc-parse-errors.bats`

- [ ] **Step 1: Convert `java-emit.bats`**

- L8: `WORK_DIR="$(mktemp -d)"` → `WORK_DIR="${BATS_TEST_TMPDIR}/work"` +
  `mkdir -p "${WORK_DIR}"`.
- L15: delete `teardown() { rm -rf "${WORK_DIR}"; }`.
- L56/57: replace the allocation and its trap with
  `NULL_DIR="${BATS_TEST_TMPDIR}/null"` + `mkdir -p "${NULL_DIR}"`; delete
  `trap "rm -rf '${NULL_DIR}'" EXIT`.
- L82-83: `SPEC_JSON`, `LL1_JSON` → `${BATS_TEST_TMPDIR}/spec.json`,
  `${BATS_TEST_TMPDIR}/ll1.json`.
- L88: delete `rm -f "${SPEC_JSON}" "${LL1_JSON}"`.
- L94/95, L101/102, L108/109: three tests each allocate `NO_SEM_DIR` and set an
  EXIT trap. Replace each allocation with
  `NO_SEM_DIR="${BATS_TEST_TMPDIR}/no-sem"` + `mkdir -p "${NO_SEM_DIR}"` and
  delete each trap.

- [ ] **Step 2: Convert `python-emit.bats`**

- L7-9: `SPEC_JSON`, `MODEL_JSON` → `spec.json`, `model.json`; `WORK_DIR` →
  `${BATS_TEST_TMPDIR}/work` + `mkdir -p`.
- L15-18: delete the whole `teardown()`.
- L37-38: `LL1_JSON` → `${BATS_TEST_TMPDIR}/ll1.json`, `TREE_FILE` →
  `${BATS_TEST_TMPDIR}/tree.jsonl`.
- L39: delete `trap "rm -f '${LL1_JSON}' '${TREE_FILE}'" EXIT`.
- L53/54, L60/61, L67/68: replace each `NO_SEM_DIR` allocation with
  `NO_SEM_DIR="${BATS_TEST_TMPDIR}/no-sem"` + `mkdir -p "${NO_SEM_DIR}"` and
  delete each EXIT trap.

- [ ] **Step 3: Convert `plcc-parse-errors.bats`**

- L6: `tmp=$(mktemp -d)` → `tmp="${BATS_TEST_TMPDIR}/parse"` +
  `mkdir -p "${tmp}"`.
- L21: delete `rm -rf "$tmp"`.

- [ ] **Step 4: Verify and run the tier**

Run:
```bash
grep -n 'mktemp\|trap' tests/bats/integration/*.bats
bin/test/integration.bash
```
Expected: the grep prints nothing; the tier passes.

- [ ] **Step 5: Commit**

```bash
git add tests/bats/integration
git commit -m "test(integration): use BATS_TEST_TMPDIR for in-body temporaries"
```

---

### Task 6: Convert the runnable `e2e/` files

This task fixes the unconditional leak that issue 177 was filed for.

**Files (modify):** `tests/bats/e2e/` — `bad_block_delimiters.bats`,
`error-propagation.bats`, `happy-path.bats`, `plcc-rep.bats`

- [ ] **Step 1: Reproduce the leak before fixing it**

Run:
```bash
before=$(ls -d /tmp/tmp.* 2>/dev/null | wc -l)
bin/test/e2e.bash tests/bats/e2e/plcc-rep.bats
after=$(ls -d /tmp/tmp.* 2>/dev/null | wc -l)
echo "before=${before} after=${after} leaked=$((after - before))"
```
Expected: `leaked=6` — three from `setup_arbno_build` and three from
`setup_mid_body_arbno_build`. Record the number. If the tier is cached, prefix
with `PLCC_NO_TEST_CACHE=1`.

- [ ] **Step 2: Convert `bad_block_delimiters.bats` and `error-propagation.bats`**

- `bad_block_delimiters.bats:7`: `WORK_DIR` → `${BATS_TEST_TMPDIR}/work` +
  `mkdir -p`; delete its `teardown()`.
- `error-propagation.bats:9-10`: `SPEC_JSON` → `${BATS_TEST_TMPDIR}/spec.json`,
  `LL1_JSON` → `${BATS_TEST_TMPDIR}/ll1.json`; delete its `teardown()`.

- [ ] **Step 3: Convert `happy-path.bats`**

- L7: `WORK_DIR` → `${BATS_TEST_TMPDIR}/work` + `mkdir -p`.
- L12-14: delete the `teardown()`.
- L46/47 and L53/54: `DIAGRAM_DIR="${BATS_TEST_TMPDIR}/diagram"` + `mkdir -p`;
  delete both `trap "rm -rf '${DIAGRAM_DIR}'" EXIT` lines.
- L66: `FULL_DIR="${BATS_TEST_TMPDIR}/full"` + `mkdir -p`.
- L73: delete `rm -rf "${FULL_DIR}"`.
- Add `bats_require_minimum_version 1.5.0` under the shebang.

- [ ] **Step 4: Convert `plcc-rep.bats`**

- L7: `WORK_DIR` → `${BATS_TEST_TMPDIR}/work` + `mkdir -p`.
- L15-17: delete the `teardown()`.
- L64/65: `EMPTY_DIR="${BATS_TEST_TMPDIR}/empty"` + `mkdir -p`; delete
  `trap "rm -rf '${EMPTY_DIR}'" EXIT`.
- L79: in `setup_arbno_build`, `ARBNO_DIR="${BATS_TEST_TMPDIR}/arbno"`. The
  existing `mkdir -p "${ARBNO_DIR}/plcc-ng"` on the next line already creates
  the parent, so no extra `mkdir` is needed here.
- L145: in `setup_mid_body_arbno_build`,
  `MID_BODY_DIR="${BATS_TEST_TMPDIR}/mid-body"`. Same reasoning — the following
  `mkdir -p "${MID_BODY_DIR}/plcc-ng"` covers it.

Both helpers end with `cd` into their directory. Leave that alone; bats removes
the directory afterwards regardless of the shell's working directory.

- [ ] **Step 5: Confirm the leak is gone**

Run:
```bash
before=$(ls -d /tmp/tmp.* 2>/dev/null | wc -l)
PLCC_NO_TEST_CACHE=1 bin/test/e2e.bash tests/bats/e2e/plcc-rep.bats
after=$(ls -d /tmp/tmp.* 2>/dev/null | wc -l)
echo "before=${before} after=${after} leaked=$((after - before))"
```
Expected: `leaked=0`, tests passing. Compare against the `6` from Step 1.

- [ ] **Step 6: Run the tier**

Run: `bin/test/e2e.bash`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add tests/bats/e2e
git commit -m "test(e2e): use BATS_TEST_TMPDIR, fixing leaked arbno build dirs"
```

---

### Task 7: Convert the `e2e/` files that cannot run here

`haskell.bats` and `haskell_roundtrip.bats` skip without `cabal`;
`languages-java.bats` runs only with `LANGUAGES_REPO_PATH` set. Convert them
and verify by inspection. **Do not report these as passing.**

**Files (modify):** `tests/bats/e2e/` — `haskell.bats`,
`haskell_roundtrip.bats`, `languages-java.bats`

- [ ] **Step 1: Convert `haskell.bats`**

- L6-7: `SPEC_DIR="${BATS_TEST_TMPDIR}/spec"` and
  `OUT_DIR="${BATS_TEST_TMPDIR}/out"`, each followed by `mkdir -p`.
- L44-46: delete the `teardown()`.
- L49-50: `SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"`,
  `MODEL_JSON="${BATS_TEST_TMPDIR}/model.json"`.
- L51: delete `trap "rm -f '$SPEC_JSON' '$MODEL_JSON'" RETURN`.

- [ ] **Step 2: Convert `haskell_roundtrip.bats`**

- L8: `SPEC_DIR="${BATS_TEST_TMPDIR}/spec"` + `mkdir -p`.
- L9: `OUT_DIR="${HASKELL_ROUNDTRIP_OUT_DIR:-${BATS_TEST_TMPDIR}/out}"` +
  `mkdir -p "$OUT_DIR"`. The environment override is a documented feature and
  must survive.
- L46-51: delete the whole `teardown()`. Its conditional existed only to avoid
  deleting a caller-supplied `OUT_DIR`; bats removes the fallback and never
  touches an overridden path, so the guard is no longer needed.
- L54-56: `SPEC_JSON`, `MODEL_JSON`, `LL1_JSON` → `${BATS_TEST_TMPDIR}/spec.json`,
  `/model.json`, `/ll1.json`.
- L57: delete the RETURN trap.

- [ ] **Step 3: Convert `languages-java.bats`**

L24-26 sit inside a helper function called per corpus case:

```bash
    build_dir="$(mktemp -d)"
    ll1_json="$(mktemp)"
    trap "rm -rf '${build_dir}' '${ll1_json}'" RETURN
```

becomes

```bash
    build_dir="${BATS_TEST_TMPDIR}/build"
    mkdir -p "${build_dir}"
    ll1_json="${BATS_TEST_TMPDIR}/ll1.json"
```

Keep the `local` declaration on L16. Note this helper may run more than once per
test across corpus cases; the fixed basenames are reused deliberately, matching
the existing behaviour where each case rebuilds from scratch. Confirm by reading
the loop that the helper does not need two cases' outputs alive at once.

- [ ] **Step 4: Verify by inspection and syntax-check**

Run:
```bash
grep -n 'mktemp\|trap\|teardown' tests/bats/e2e/haskell.bats tests/bats/e2e/haskell_roundtrip.bats tests/bats/e2e/languages-java.bats
for f in haskell haskell_roundtrip languages-java; do bash -n "tests/bats/e2e/$f.bats" && echo "$f: syntax OK"; done
```
Expected: the grep prints nothing; all three report `syntax OK`.

- [ ] **Step 5: Confirm the skip path still works**

Run: `bin/test/e2e.bash tests/bats/e2e/haskell.bats`
Expected: tests report as skipped (`cabal not available`), exit 0. This
exercises `setup()` up to the skip, which is where the converted assignments
live.

- [ ] **Step 6: Commit**

```bash
git add tests/bats/e2e
git commit -m "test(e2e): use BATS_TEST_TMPDIR in haskell and java corpus tests"
```

---

### Task 8: Add the lint

With all 42 files converted, the lint can go green on the first run.

**Files:**
- Modify: `tests/bats/commands/bats-temp-dirs.bats`

**Interfaces:**
- Consumes: the file created in Task 1.
- Produces: nothing.

- [ ] **Step 1: Add the lint test**

Append to `tests/bats/commands/bats-temp-dirs.bats`:

```bash
@test "no bats test file calls mktemp" {
    local bats_dir
    bats_dir="$(git rev-parse --show-toplevel)/tests/bats"

    local offenders
    offenders="$(grep -rn 'mktemp' "${bats_dir}" --include='*.bats' \
        | grep -v "^${BATS_TEST_FILENAME}:" || true)"

    if [ -n "${offenders}" ]; then
        printf 'Do not call mktemp in bats tests. Name a path under\n' >&2
        printf 'BATS_TEST_TMPDIR instead; bats removes it after the test.\n\n' >&2
        printf '%s\n' "${offenders}" >&2
        return 1
    fi
}
```

The `grep -v` on `$BATS_TEST_FILENAME` keeps this file — which necessarily
contains the string — from reporting itself. The `|| true` is required because
`grep` exits 1 when it matches nothing, which is the passing case.

- [ ] **Step 2: Run it and confirm it passes**

Run: `bin/test/functional.bash tests/bats/commands/bats-temp-dirs.bats`
Expected: PASS, 2 tests.

- [ ] **Step 3: Confirm the lint actually fails on a violation**

A lint that cannot fail is worthless. Introduce a violation, observe the
failure, then revert:

```bash
printf '\n@test "temporary violation" {\n    d=$(mktemp -d)\n    [ -d "$d" ]\n}\n' >> tests/bats/commands/plcc-ll1.bats
bin/test/functional.bash tests/bats/commands/bats-temp-dirs.bats  # expect FAIL naming plcc-ll1.bats
git checkout tests/bats/commands/plcc-ll1.bats
bin/test/functional.bash tests/bats/commands/bats-temp-dirs.bats  # expect PASS
```
Expected: the middle run fails and its message names
`tests/bats/commands/plcc-ll1.bats`; the last run passes.

- [ ] **Step 4: Commit**

```bash
git add tests/bats/commands/bats-temp-dirs.bats
git commit -m "test: lint against mktemp in bats tests"
```

---

### Task 9: Document the convention

**Files:**
- Modify: `CONTRIBUTING.md`

- [ ] **Step 1: Read the testing section**

Run: `grep -n 'bats\|test tier' CONTRIBUTING.md | head -40`

Find where the bats tiers are described; the new paragraph goes at the end of
that discussion.

- [ ] **Step 2: Add the paragraph**

Match the surrounding heading depth and prose style:

```markdown
### Temporary files in bats tests

Bats tests never call `mktemp`. Name paths under `BATS_TEST_TMPDIR` instead:

```bash
setup() {
    WORK_DIR="${BATS_TEST_TMPDIR}/work"
    mkdir -p "${WORK_DIR}"
    SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"
}
```

Bats creates that directory for each test and removes it afterwards, whether the
test passes or fails, so tests need no cleanup code — no `teardown()`, no
`trap`, no trailing `rm`. Use `bats --no-tempdir-cleanup` to keep the files
while debugging. `tests/bats/commands/bats-temp-dirs.bats` enforces this.
```

- [ ] **Step 3: Verify the lint reference is accurate**

Run: `ls tests/bats/commands/bats-temp-dirs.bats`
Expected: the file exists, so the link in the prose is not stale.

- [ ] **Step 4: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs(contributing): document BATS_TEST_TMPDIR for bats tests"
```

---

### Task 10: Rewrite issue 177 and close it

Issue 177 describes only the `plcc-rep.bats` symptom and proposes a one-line
`teardown()` fix that this branch does not implement. Rewrite it to match the
work before closing, so `issues/done/` records what was actually done.

**Files:**
- Modify: `dev-docs/issues/177-bats-helpers-leak-temp-dirs.md`
- Modify: `dev-docs/roadmap.md`

- [ ] **Step 1: Rewrite the issue body**

Keep the `# 177 - …` heading line, `**Type:** test`, and `**Date:**` as they
are — `bin/issues/check.bash` parses them. Replace Description, Steps to
Reproduce, and Notes with the corrected account:

- Description: bats tests hand-roll temporary cleanup four different ways
  (`teardown()`, `trap … EXIT`, `trap … RETURN`, a trailing `rm`) across 42
  files and 102 call sites. `setup_arbno_build` and
  `setup_mid_body_arbno_build` in `tests/bats/e2e/plcc-rep.bats` are covered by
  none of them and leak six build directories per run. Six further files clean
  up on the last line of the test body, so they leak whenever a test fails.
- Steps to Reproduce: the `ls -d /tmp/tmp.* | wc -l` before/after measurement
  from Task 6 Step 1, with the expected `leaked=6`.
- Notes: bats supplies `BATS_TEST_TMPDIR` and removes it per test, so the fix
  is to delete the hand-rolled cleanup rather than extend it. Link the design
  at `dev-docs/specs/2026-07-28-177-bats-temp-dirs-design.md`.

- [ ] **Step 2: Update the roadmap entry to match**

The Open Issues entry must stay in the exact two-line format
`bin/issues/check.bash` parses. Update only the summary line so it describes the
broader change:

```markdown
- **[#177](issues/177-bats-helpers-leak-temp-dirs.md) — bats tests hand-roll temp cleanup**
  Replace mktemp and four cleanup mechanisms with BATS_TEST_TMPDIR across the suite.
```

If the title on the first line changes, it must match the issue file's `#`
heading.

- [ ] **Step 3: Check consistency and commit the rewrite**

Run: `bin/issues/check.bash`
Expected: exit 0.

```bash
git add dev-docs/issues/177-bats-helpers-leak-temp-dirs.md dev-docs/roadmap.md
git commit -m "docs(issues): rewrite 177 to cover the whole bats temp-dir sweep"
```

- [ ] **Step 4: Run the full functional suite one last time**

Run: `bin/test/functional.bash`
Expected: PASS across units, commands, integration, and e2e.

Then confirm the suite leaks nothing:
```bash
before=$(ls -d /tmp/tmp.* 2>/dev/null | wc -l)
PLCC_NO_TEST_CACHE=1 bin/test/functional.bash
after=$(ls -d /tmp/tmp.* 2>/dev/null | wc -l)
echo "before=${before} after=${after} leaked=$((after - before))"
```
Expected: `leaked=0`. A non-zero count here means a `mktemp` under `bin/`
ran during the suite — check `bin/install/bats.bash` and `bin/test/smoke.bash`,
which are out of scope for this branch, and report the number rather than
silently accepting it.

- [ ] **Step 5: Close the issue as the final commit**

```bash
bin/issues/close.bash 177
git status   # review what close.bash staged, especially roadmap.md
git commit -m "docs(issues): close issue 177 (bats temp-dir sweep), update roadmap"
```

---

## Self-Review

**Spec coverage.** Conversion of all 42 files: Tasks 2-7. Version declarations:
Task 4 Step 2 (`spec-tokens`, `model-lang-emit`), Task 6 Step 3 (`happy-path`) —
the three the spec names. Guard test, both parts: Tasks 1 and 8.
`CONTRIBUTING.md`: Task 9. Issue and roadmap bookkeeping: Task 10. The spec's
two "call sites needing care" are handled at Task 7 Step 2
(`haskell_roundtrip` override) and the Global Constraints (`bin/` excluded).
The spec's note that two `teardown()` bodies survive is implemented at Task 3
Steps 1 and 5.

**Placeholder scan.** No TBDs. Every code step carries the code. Task 7 Step 3
asks the implementer to confirm a loop's behaviour by reading it, which is a
genuine verification rather than deferred work.

**Type consistency.** `BATS_TEST_TMPDIR` is spelled identically throughout.
Basenames are fixed per variable in the Task 2 table and reused consistently
in Tasks 4-7 (`spec.json`, `model.json`, `ll1.json`, `work`, `output`,
`no-sem`). The guard file is `tests/bats/commands/bats-temp-dirs.bats` in Tasks
1, 8, and 9.

**Ordering.** The lint lands in Task 8, after every conversion, so the branch is
never committed in a knowingly red state. Task 1 Step 1 records the pre-fix
violation count as the RED evidence instead.
