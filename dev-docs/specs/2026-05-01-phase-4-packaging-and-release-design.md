# Phase 4: Packaging and First Release — Design

**Date:** 2026-05-01
**Status:** Draft — pending review
**Companion architectural spec:** `dev-docs/specs/2026-04-12-multi-lang-pipeline.md`
**Roadmap reference:** `dev-docs/specs/2026-04-12-multi-lang-implementation-plan.md` §7

---

## 1. Goal

Take the working v9 pipeline produced by Phases 1–3 and make it installable, releasable, and pedagogically presentable. Deliver the project's first public release on PyPI under the name `plcc-ng`, starting at version `0.0.0` semantics — experimental, with a separate identity from the original `plcc` package, and with no implicit claim of being PLCC's successor.

The decision about whether `plcc-ng` becomes the next major version of `plcc` is deliberately deferred. Phase 4 produces an artifact that can be installed, tried, and evaluated; it does not pre-commit to the eventual outcome.

---

## 2. Phase Structure

| Phase | Scope | Status |
| ----- | ----- | ------ |
| Phase 1 | Walking skeleton — trivial grammar, PlantUML emitter | Complete |
| Phase 2 | Python emitter, LL(1) parser, `plcc-rep`, arbno support | Complete |
| Phase 3 | Java emitter, Java runtime, `languages` corpus tests | Complete (pending retro) |
| **Phase 4** | **Visualizer polish, packaging, CI/release workflow, first release** | **This design** |
| Phase 5 | Field validation, learning-materials updates, stable release | Pending |

---

## 3. Scope

### 3.1 In scope

- Polish `plcc-scan` and `plcc-parse`: location-aware output and human-first error formatting
- Rename the package: `plcc` → `plcc-ng` in `pyproject.toml` (console scripts unchanged)
- Fix license inconsistency: AGPL-3.0-or-later in both `pyproject.toml` and `README.md`
- Polish `pyproject.toml` metadata for PyPI presentation
- Polish `README.md` for PyPI rendering and onboarding
- Replace existing CI workflow (`ci.yml`): full test suite (units, integration, e2e, languages corpus, packaging) on every PR
- Replace existing release workflow (`pypi.yaml`): `python-semantic-release` on merge to `main`, then TestPyPI → PyPI publish via Trusted Publishing
- Add branch protection on `main`
- Pin the `languages` repo for CI corpus runs
- Append a Phase 3 retro to the Phase 3 design doc
- Cut and ship the first `plcc-ng` release

### 3.2 Out of scope

| Item | Reason |
| ---- | ------ |
| Stable `1.0.0` release | Field validation gates 1.0; Phase 5 |
| Migration to the `plcc` PyPI namespace | Group decision pending; separate cutover later |
| Learning materials updates | Phase 5 |
| Pilot user evaluation | Phase 5 |
| `CHANGELOG.md` file | GitHub auto-generated release notes are sufficient for 0.x |
| Versioning the visualizer output format as part of a public contract | Output is explicitly unstable in 0.x |
| Cross-platform CI matrix (Windows, macOS) | Ubuntu only for now; expand if it becomes load-bearing |
| Modifying or coordinating with the original `plcc` package | Out-of-band conversation; Phase 4 does not touch the original |
| Adding more grammars to the languages corpus | Ongoing maintenance, not Phase 4 work |

---

## 4. Phase 4 Entry Conditions

All of the following must be true before Phase 4 implementation begins:

1. Phase 3 corpus is closed: every grammar in the Phase 3 target list is either in `tests/fixtures/languages-corpus.txt` or explicitly deferred (with a note in the Phase 3 retro).
2. `bin/test/functional.bash` (units, commands, integration, e2e) passes locally with `LANGUAGES_REPO_PATH` set.
3. Phase 3 retro is appended to `dev-docs/specs/2026-04-29-phase-3-java-emitter-design.md` (see §9 of this document for content guidance).
4. This Phase 4 design doc is approved and committed.

The Phase 4 implementation plan (produced by the writing-plans skill after this design is approved) will gate task 1 on these conditions.

---

## 5. Visualizer Output Format

### 5.1 `plcc-scan`

One token per line. Format:

```
<file>:<line>:<col> <NAME> '<lexeme>'
```

When `source.file` is `null` (stdin without a filename), the `<file>:` prefix is omitted:

```
<line>:<col> <NAME> '<lexeme>'
```

Single space between fields. No column alignment.

The `source` object is already part of the `TokenRecord` schema (`src/plcc/schemas/token.schema.json`) and carries `file`, `line`, `column`. No schema changes are required.

### 5.2 `plcc-parse`

Indented tree, two spaces per level. Internal nodes show only the rule name. Token leaves show name, lexeme, and bracketed location:

```
Program
  Expr
    NUM '42' [trivial.txt:1:1]
    PLUS '+' [trivial.txt:1:4]
    NUM '17' [trivial.txt:1:6]
```

When file is null, drop it from the bracketed location: `[1:1]`.

### 5.3 Error presentation (both commands)

Single-line, compiler-style:

```
<file>:<line>:<col>: error: <message>
```

When file is null:

```
<line>:<col>: error: <message>
```

The `<message>` is extracted from the human-readable field of the error record. Raw JSON is never shown to the user.

### 5.4 Exit codes

Both commands exit `0` when the pipeline completes — even if it produced in-band error records. They exit non-zero only on tool-level failures (missing file, unreadable input, malformed grammar at the spec level, etc.). This matches the architectural spec's distinction between in-band error records and tool failures.

### 5.5 Format stability

The visualizer output is **explicitly unstable in 0.x**. It will likely evolve as we get feedback from classroom use. The format becomes part of the public contract no earlier than 1.0.

A `--no-locations` flag is **not** added in Phase 4 (YAGNI). It can be added later if students or teachers report the locations are noisy.

---

## 6. Packaging and Metadata

### 6.1 `pyproject.toml` changes

| Field | Change |
| ----- | ------ |
| `name` | `plcc` → `plcc-ng` |
| `license` | `GPL-3.0-or-later` → `AGPL-3.0-or-later` |
| `description` | Add: a single-sentence pitch (e.g. "Programming Languages Compiler Compiler — experimental rewrite of PLCC") |
| `keywords` | Add: `["compiler", "parser", "education", "plcc", "teaching", "programming-languages"]` |
| `[project.urls]` | Add: `Homepage`, `Repository`, `Issues` |
| `[project.classifiers]` | Add: PEP 301 trove classifiers — Development Status (Alpha), Intended Audience (Education / Developers), License (AGPL-3.0-or-later), Programming Language (Python 3.12+), Topic (Compilers / Education) |
| `dynamic = ["version"]` | **Preserve** (with `[tool.pdm.version] source = "scm"`) |

The `dynamic = ["version"]` + `source = "scm"` arrangement is preserved deliberately. `python-semantic-release` runs in tag-only mode (see §7.2): it determines the next version, creates the git tag, and creates the GitHub Release without writing back into `pyproject.toml`. `pdm-backend` reads the version from the tag at build time. This avoids requiring CI to push a commit back to `main` (which would otherwise need a bot PAT or a branch-protection bypass).

### 6.2 README polish

- Verify Markdown renders correctly on PyPI (no exotic extensions; `twine check` validates this in CI).
- Fix typo: "Licnesing" → "Licensing".
- Add an install section pointing at `pip install plcc-ng`.
- Add a "what this is and isn't" paragraph: experimental project, not (yet) the successor to PLCC, no compatibility guarantees with the original `plcc` package.

The README is otherwise unchanged — this is polish, not a rewrite.

### 6.3 Built-in plugin inventory

The packaging story for built-in plugins is split across two parallel subsystems:

- **Language emitters** (`src/plcc/lang/ext/...`): `plcc-python-emit`, `plcc-python-run`, `plcc-java-emit`, `plcc-java-build`, `plcc-java-run`. Discovery via `plcc-lang-list` (PATH scan for `plcc-*-emit`).
- **Diagram emitters** (`src/plcc/diagram/...`): `plcc-plantuml-diagram`. Discovery via `plcc-diagram-list`.

All are submodules of `plcc-ng` and exposed as console scripts in this same `pyproject.toml`. A plain `pip install plcc-ng` installs all of them with no additional packages or entry-point group registration.

### 6.4 Cleanup

- Delete the empty `src/plcc/lang/ext/plantuml/` directory. PlantUML lives in `plcc.diagram.plantuml` now; the `lang/ext/plantuml/` stub is residue from the architectural shift and should not survive into the released package.

### 6.5 Package data

The wheel must include non-Python data that the runtime needs:

- `src/plcc/lang/ext/java/runtime/org.json-20250107.jar` (and any other runtime files)
- `src/plcc/lang/ext/java/templates/*.jinja`
- `src/plcc/lang/ext/python/runtime/*` and templates
- `src/plcc/diagram/plantuml/templates/*` (if any)
- `src/plcc/schemas/*.schema.json`

Inclusion is configured via `pyproject.toml` (`[tool.pdm.build]` / `package-data`). The packaging smoke test (§7.3) catches missing files because emitter and discovery commands fail if data is absent.

---

## 7. CI and Release Workflows

### 7.1 `ci.yml` — runs on every PR to `main`

```yaml
on:
  pull_request:
    branches: [main]
```

This replaces the existing `ci.yml`. Required to pass before merge (enforced via branch protection, §7.4).

**Jobs:**

1. **`unit-and-integration`** — runs `bin/test/units.bash`, `bin/test/commands.bash`, `bin/test/integration.bash` on Ubuntu with Python 3.12+. Provides fast feedback first.

2. **`languages-corpus`** — needs `unit-and-integration`. Steps:
   - Read pinned commit hash from `tests/fixtures/languages-pin.txt` (a new file containing exactly one line: the SHA).
   - `git clone https://github.com/<owner>/languages.git` and `git checkout <pin>`.
   - Set `LANGUAGES_REPO_PATH` env var to the clone path.
   - Install JDK.
   - Run `bin/test/e2e.bash` (which already conditionally runs `languages-java.bats` when both JDK and `LANGUAGES_REPO_PATH` are present).

3. **`packaging`** — needs `unit-and-integration`. Steps:
   - `bin/build/package.bash` (builds the wheel via PDM).
   - `twine check dist/*` (validates metadata + README rendering the way TestPyPI/PyPI would).
   - `bin/test/packaging.bash` extended to:
     - Install the wheel into a fresh venv.
     - Verify all console scripts are on PATH.
     - Run `plcc-lang-list` and assert `python` and `java` appear.
     - Run `plcc-diagram-list` and assert `plantuml` appears.
     - Run `plcc-make` against the trivial fixture and assert expected outputs exist.

### 7.2 `release.yml` — runs on push to `main` and on workflow_dispatch

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:
```

This replaces the existing `pypi.yaml`. The `workflow_dispatch` trigger supports manual TestPyPI-only validation runs from any branch (used rarely — once during initial setup, then only when the publish workflow itself changes).

**Jobs:**

1. **`semantic-release`** — runs `python-semantic-release version`:
   - Configured in tag-only mode (no commits back to `pyproject.toml`).
   - Determines the next version from conventional commits since the last tag.
   - If there are no releasable commits, exits cleanly with no release. The `publish` job is skipped.
   - Pushes the new tag (`v<X>.<Y>.<Z>`) and creates a GitHub Release with auto-generated notes (`gh release create --generate-notes`).

2. **`publish`** — needs `semantic-release` and only runs when a new release was cut. Steps:
   - Checkout at the tag (so `pdm-backend` reads the right version).
   - `bin/build/package.bash` to build the wheel.
   - Publish to **TestPyPI** via Trusted Publishing (OIDC).
   - Smoke test: install from TestPyPI in a fresh venv (`pip install --extra-index-url https://pypi.org/simple/ --index-url https://test.pypi.org/simple/ plcc-ng==<version>`), then run `plcc-make` against the trivial fixture.
   - Publish to **real PyPI** via Trusted Publishing (OIDC).

   When triggered via `workflow_dispatch`, the `publish` job stops after the TestPyPI smoke test — the real PyPI step is skipped. This makes manual runs a safe rehearsal of the OIDC pipeline.

### 7.3 Versioning

The first release version is determined by `python-semantic-release` from conventional commits since project inception. With no prior tags, semantic-release starts at `0.0.0`. The actual first release version (likely `0.1.0` or `0.0.1`) is whatever conventional commits warrant. We do not pre-tag a seed.

This deliberately abandons the roadmap's `9.0.0a1 / a2 / b1 / rc1` prerelease scheme. That scheme was tied to the assumption that the package would be published under the `plcc` name as a continuation of v8. With `plcc-ng` as a separate package starting at 0.x, the prerelease ladder is unnecessary — every 0.x release is implicitly experimental.

### 7.4 Branch protection on `main`

Configured in repository settings (not a workflow file):

- Require pull request before merging
- Require all `ci.yml` status checks to pass
- Require linear history (recommended; keeps `git log` clean)
- Disallow direct pushes to `main`

### 7.5 Trusted Publishing setup (one-time, manual)

- **TestPyPI**: configure trusted publisher pointing at the `plcc-ng` GitHub repo, `release.yml`, `publish` job, environment `test-pypi`.
- **Real PyPI**: same, environment `pypi`.
- No API tokens stored anywhere.

This is documented in the Phase 4 implementation plan as a manual setup task gated before the first release attempt.

---

## 8. Languages Corpus Pinning

The `languages` corpus is an external repo; CI must clone it deterministically. Phase 4 introduces:

- **`tests/fixtures/languages-pin.txt`** — a single line containing the SHA of the `languages` commit that the corpus tests run against. Initial value: the SHA of `languages`'s `main` at the time Phase 4 begins.

Bumping the pin is a one-line PR. The PR's CI run uses the new pin, so any breakage is caught before merge. This treats corpus drift as ordinary code change, not as a hidden time-bomb.

---

## 9. Phase 3 Retro

Phase 3 retro is appended to `dev-docs/specs/2026-04-29-phase-3-java-emitter-design.md` as a new `## 11. Phase 3 Retro` section, mirroring how Phase 1's retro was captured in its design doc.

Suggested sections (the maintainer fills in actual content):

- **What worked.** Things that should be repeated in future phases.
- **What surprised us.** Things that were not anticipated by the Phase 3 design — e.g. the `_extract_body` `\n` bug (a generic class of bug worth watching for in line-string handling).
- **What was harder than expected.** The corpus iteration loop; fragment-handling edge cases; any specific grammars that exposed subtle bugs.
- **Architectural amendments needed.** Likely none — call this out explicitly so absence is intentional, not oversight.
- **Lessons that should shape Phase 4.** What the corpus loop revealed about test ergonomics, plugin discoverability friction, packaging implications, etc.

The retro is written before Phase 4 implementation begins. It is part of the Phase 4 entry conditions (§4).

---

## 10. Acceptance Criteria

Phase 4 is complete when all of the following hold.

**Visualizers:**

1. `plcc-scan <grammar> <source>` prints one line per token in the format `<file>:<line>:<col> <NAME> '<lexeme>'` (or `<line>:<col> <NAME> '<lexeme>'` when stdin without filename).
2. `plcc-parse <grammar> <source>` prints an indented tree with internal nodes showing rule names and token leaves showing `<NAME> '<lexeme>' [<file>:<line>:<col>]`.
3. Both commands present pipeline error records as single-line compiler-style messages (`<file>:<line>:<col>: error: <message>`), never as raw JSON.
4. Both commands exit 0 when the pipeline completes; non-zero only on tool failures.
5. Bats integration tests cover the formatted output and error formatting for both commands.

**Packaging:**

6. `pyproject.toml` declares `name = "plcc-ng"`, `license = "AGPL-3.0-or-later"`, and complete metadata (description, keywords, URLs, classifiers).
7. `dynamic = ["version"]` with `source = "scm"` is preserved; `python-semantic-release` is configured in tag-only mode.
8. README renders correctly on PyPI (verified via `twine check`); typo `Licnesing` is fixed; install instructions point at `plcc-ng`.
9. The empty `src/plcc/lang/ext/plantuml/` directory is deleted.
10. The built wheel includes the Java runtime jar, Jinja2 templates, Python runtime, and JSON schemas as package data.

**CI and Release:**

11. `.github/workflows/ci.yml` runs on every PR to `main` with three jobs (unit-and-integration, languages-corpus, packaging). All must pass.
12. `.github/workflows/release.yml` runs on push to `main`: `python-semantic-release` determines version, tags, creates GitHub Release; publish job builds wheel, publishes to TestPyPI via OIDC, smoke-tests TestPyPI install, then publishes to real PyPI via OIDC.
13. `release.yml` also supports `workflow_dispatch` for manual TestPyPI-only validation runs.
14. Branch protection on `main` requires PR + all CI checks; direct pushes are disallowed.
15. Trusted Publishing is configured on TestPyPI and PyPI for the `plcc-ng` repo.
16. `tests/fixtures/languages-pin.txt` exists and the languages-corpus job uses it.

**First Release:**

17. The first PR merged to `main` after this work produces a working release: GitHub Release exists, package installs cleanly from PyPI, all console scripts run, `plcc-make` against the trivial fixture succeeds.

**Phase 3 wrap-up:**

18. Phase 3 retro is appended to `dev-docs/specs/2026-04-29-phase-3-java-emitter-design.md`.

---

## 11. What Phase 4 Owes Phase 5

By Phase 4's end, the following artifacts exist for Phase 5 to build on:

- `plcc-ng` is installable from PyPI.
- The release workflow is repeatable: every merge to `main` produces a release if conventional commits warrant one.
- CI gives a continuous backwards-compat signal via the languages corpus.
- The visualizer commands are usable enough for classroom demonstration (format may still evolve).
- A documented manual-rehearsal path exists for the publish workflow (`workflow_dispatch` on `release.yml`).
- Branch protection enforces the PR-based contribution model.

Phase 5 picks up from a state where shipping is mechanical and the open questions are validation, learning materials, and the eventual 1.0 / `plcc`-namespace decision.

---

## 12. Phase 4 Retro

(To be appended at phase completion.)
