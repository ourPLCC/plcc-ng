# Doc example drift: fix the stale `_run()` examples and make the class of error testable

**Issues:** #181 (docs), #182 (test)
**Date:** 2026-08-03

## Problem

Every `=== "Python"` tabbed example in `docs/` implements `_run()` by printing
rather than returning. Under the 2.0.0 contract that is a
`specification_error`, so all three exit 1. Verified against the installed CLI:

```
$ echo "42 36 2" | plcc-rep          # docs/quick-start.md, Python tab
80
Specification error: TypeError: _run() must return a string, got NoneType
Fix the errors in your specification and re-run.
$ echo $?
1
```

The `80` is the leaked `print` reaching the terminal. That is why three broken
examples shipped in 2.0.0 and survived a release: the page appears to work
before it fails.

### Root cause

Not carelessness — scope. The 2.0.0 design doc
(`2026-07-23-issues-162-165-run-contract-design.md`) enumerated affected
documentation by hand, and scoped `docs/quick-start.md` to "update the Java
example." Java's `void _run()` could not compile, so it announced itself;
`language-guide/index.md` and `language-guide/examples.md` were never listed at
all. Statically-typed targets partly defend themselves. Python and JavaScript
examples fail only at runtime, and only if something runs them.

Nothing runs them. `grep -rl 'docs/' tests/` matches only the issue-tooling
tests. And `.github/workflows/ci.yml` sets `paths-ignore` on `docs/**`,
`*.md`, and `mkdocs.yml`, so docs-only PRs skip CI entirely — a doc test placed
in the normal suite would not run on the PRs most likely to break an example.

Hand-enumeration of affected docs is the failure mode. The fix has to remove
the need for it.

## Audit results

Broken, each reproduced with exit 1:

| Location | Code | Failure |
|---|---|---|
| `docs/quick-start.md:44` | `print(sum(...))` | `got NoneType` |
| `docs/language-guide/index.md:24` | `print("Hello")` | `got NoneType` |
| `docs/language-guide/examples.md:43` | `print(self.exp.eval())` | `got NoneType` |

Plus one prose error: `docs/language-guide/semantic.md:46` states the default
`_run` implementation "prints a string representation of the parse tree root."
It returns it — `src/plcc/lang/ext/python/emit.py` defines
`def _run(self): return str(self)`. That page is the language guide's
conceptual home for `_run` and never states the return-a-string contract.

Verified correct, no change needed: all three Java tabs, each run through
`plcc-rep` at exit 0. Reviewed and correct, not executed: the four
`docs/language-guide/languages/*.md` reference pages, `docs/migration.md`,
`docs/whats-new.md`, and `docs/cli/guide/language-extensions.md`.

All six tabs covered by Part 2 have therefore been run by hand — three Java as
they stand, three Python with the Part 1 corrections applied — so every
`expected-*` file in the fixtures is transcribed from observed output rather
than from the page's claim.

## Part 1 — Doc corrections

| File | Change | Verified output |
|---|---|---|
| `docs/quick-start.md` | `return str(sum(int(str(num)) for num in self.numList))` | `80`, exit 0 |
| `docs/language-guide/index.md` | `return "Hello"` | `Hello`, exit 0 |
| `docs/language-guide/examples.md` | `return str(self.exp.eval())` | `3/1/2`, exit 0 |
| `docs/language-guide/semantic.md` | Rewrite the `_run` section to state the contract | prose |

`examples.md` needs more than a mechanical `print(x)` → `return x` edit.
`self.exp.eval()` returns an `int`, so the naive fix trades one
`specification_error` for another (`got int`) — confirmed by running it. It
needs `str(...)`, mirroring the Java tab's `String.valueOf(...)`. This is
precisely the kind of thing a blocklist-style lint would miss.

The `semantic.md` rewrite states that `_run` returns a string, that the default
implementation returns `str(root)` rather than printing it, and that writing to
stdout from inside `_run` bypasses `plcc-rep`'s JSON envelope. It defers exact
signatures to the per-language pages, which already have them right.

## Part 2 — Fixtures

One directory per doc example, under `tests/fixtures/docs/`:

```
tests/fixtures/docs/quick-start-python/
    spec.plcc          # byte-identical to the doc's fenced block
    input              # 42 36 2
    expected-scan      # the page's "Output:" blocks, verbatim
    expected-parse
    expected-rep
```

Six fixtures, matching the tabs that exist today:
`quick-start-{python,java}`, `lang-guide-index-{python,java}`,
`lang-guide-examples-{python,java}`.

`language-guide/index.md` documents no commands and no output, so its `input`
and `expected-rep` are authored here rather than transcribed. The test ends up
stronger than the page.

Existing fixtures in `tests/fixtures/` are flat files; a doc example needs a
spec plus input plus several expected outputs, so it gets a directory. The
`docs/` subdirectory keeps that departure contained and self-explanatory.

## Part 3 — Two independent checks

**Behavior** — new bats tier `tests/bats/docs/`. For each fixture, run the
commands the page documents (`plcc-scan`, `plcc-parse`, `plcc-rep`), assert the
full output equals the `expected-*` file and that exit status is 0. What turns a
leaked `print` from invisible into a failure is the pair. `plcc-rep` writes its
specification error to stdout, not stderr (`src/plcc/cmd/output.py` implements
`print_user_error` as a bare `print`), so the broken example's output is the
documented text *plus* two error lines and exact equality fails on its own. The
exit-status assertion is cheap defense in depth on top of that, and is the only
detector for a nonzero exit whose output happens to match.

**Identity** — `tests/docs/example_block_test.py` (pytest). For each fixture,
extract the fenced block from the mapped `.md` inside the mapped `=== "Lang"`
tab, de-indent it, and assert byte-equality with the fixture's `spec.plcc`,
failing with a diff. The same for the other direction of the page: each
`expected-*` file is pinned to the heading of the section that documents the
command producing it, and asserted byte-equal to the first unindented ```` ```text ````
fence in it. Without that half, a `src/` change that altered a command's output
format could be absorbed by updating the fixtures alone, leaving the page
promising output the tool no longer produces with every tier green. Parameterized
over a manifest mapping fixture → (spec tab, documented outputs). Pure file
comparison, no subprocesses, milliseconds.

Together these close both directions. Edit the doc without the fixture and
identity fails. Edit the fixture without the doc and identity fails. Break the
language and behavior fails.

The manifest is still a hand-enumeration, which is the root cause above, so it
gets its own guard: every `%%%`-bearing fence in `docs/**/*.md` must be either
registered in the manifest or named in an `UNCOVERED` allowlist with the reason
it is out of scope. A new example on a new or an already-covered page therefore
cannot land with zero coverage — the worst it can do is force whoever adds it to
write down why it is unguarded.

Bats tests follow the existing conventions: `bats_require_minimum_version
1.5.0` as the third line, paths under `BATS_TEST_TMPDIR`, no `mktemp`, no
cleanup code.

### Two deliberate deviations from convention

The pytest check lives in `tests/docs/` rather than co-located in `src/`.
CONTRIBUTING co-locates unit tests with the module under test; this one tests
documentation, has no `src` module, and should not ship in the wheel. Both
deviations get a note in CONTRIBUTING so the next reader does not have to
reconstruct the reasoning.

Because `pdm test` runs bare `pytest` with no `testpaths` restriction, the
units tier will also collect this test, so it runs twice when the whole suite
runs. Accepted: it is milliseconds, and the upside is that doc drift is caught
by the fastest tier rather than only by a specialized one.

### Rejected alternatives

**Single-source via `include-markdown`.** The plugin is already installed and
unused, and it would give one copy instead of two. Rejected because it breaks
GitHub rendering: `quick-start.md` would show a raw include directive instead
of the spec, and instructors read these pages directly in the repo. The
identity check buys the same guarantee while leaving the markdown plain.

**Extract-and-run from markdown.** Parse the tabs, fences, commands, and
expected output straight out of the `.md`. Best coverage, and it would pick up
new examples with no registration. Rejected as overkill for three pages: it has
to infer which `bash` block pairs with which output block, which is the part
most likely to rot or to fail confusingly.

**Pattern lint.** Grep docs for a `_run` body that prints. Rejected: it is a
blocklist, so it would not have caught the `examples.md` `int` case, and it
never verifies documented output.

## Part 4 — Runner and CI

`bin/test/docs.bash`, matching existing style (`set -euo pipefail`,
`SCRIPT_DIR`/`PROJECT_ROOT`, `run_cached`, `SKIP_SETUP` support): runs the
pytest identity check, then the bats tier. Wired into `bin/test/functional.bash`
in both places — the no-argument tier list, and a `tests/bats/docs*` case in the
path-routing `case` statement. `bin/test/all.bash` needs no change: it calls
`functional.bash`, which now chains the tier.

CI needs the tier reachable from **both** directions, because a doc example can
break in two ways:

1. **A docs-only PR edits an example.** `ci.yml` skips these entirely, so
   `.github/workflows/docs-tests.yml` triggers on `docs/**`, `*.md`,
   `mkdocs.yml`, `tests/fixtures/docs/**`, `tests/bats/docs/**`, `tests/docs/**`,
   and `bin/test/docs.bash`, and runs only `bin/test/docs.bash`.

2. **A `src/` change breaks a working example.** This is the 2.0.0 scenario
   exactly, and `docs-tests.yml` will not fire for it — a change to
   `src/plcc/lang/ext/python/emit.py` touches none of those paths. So `ci.yml`
   also gets a `docs` job running `bin/test/docs.bash`. Without it the whole
   mechanism would miss the very regression that motivated it.

Both use `PLCC_NO_TEST_CACHE=1`, consistent with the other CI steps, and both
need `actions/setup-java@v4` (temurin 17) because half the fixtures are Java.
A PR touching both `src/` and `docs/` runs the tier twice; that is accepted in
exchange for neither direction having a hole.

`ci.yml`'s `paths-ignore` is otherwise left alone. Dropping `docs/**` from it
would make every docs typo run the full suite including the Haskell roundtrip;
the two jobs above cover the gap at a fraction of the cost.

## Part 5 — Documenting the process

CONTRIBUTING gets the docs tier in both the command table and the test-tier
table, plus a short subsection under "Documentation conventions": which runnable
specs in `docs/` have a fixture under `tests/fixtures/docs/` and which do not
yet, that a covered page and its fixture are kept byte-identical by the identity
check in both the spec and the output direction, and that the way to add an
example is to add the fixture first. The subsection names the uncovered pages
rather than claiming the tier covers everything, since claiming coverage that
does not exist is worse than admitting the gap.

## Testing strategy

The doc corrections are already verified by hand against the installed CLI, and
Part 3 converts those manual runs into the permanent regression tests. The
order matters: land the fixtures and tier against the *broken* docs first and
watch all three Python fixtures fail for the documented reason, then apply the
corrections and watch them pass. A prevention mechanism that has never failed
has not been tested.

The identity check gets its own unit coverage for the extraction logic —
correct tab selected among several, de-indentation, and a clear diff on
mismatch — since a silently-passing identity check is worse than none.

## Out of scope

Separate issues, not folded in:

- `quick-start.md`, `language-guide/index.md`, and `language-guide/examples.md`
  show only Python and Java tabs though four targets are supported.
- The four `docs/language-guide/languages/*.md` quick-reference specs are
  correct today but equally able to drift. Once the tier exists, extending it
  is cheap — the Haskell one needs a `cabal build` and belongs behind the same
  slow-test treatment as `e2e_haskell_roundtrip.bash`.
