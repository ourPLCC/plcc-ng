# 178 — enforce `bats_require_minimum_version` in bats files

**Date:** 2026-07-29
**Issue:** [178](../issues/done/178-bats-version-declaration-unenforced.md)

## Problem

Bats tests name temporary paths under `BATS_TEST_TMPDIR` and let the runner
clean them up. That variable exists only on bats 1.4.0 and later. Each file
guards against an older runner by declaring `bats_require_minimum_version
1.5.0`, which turns a too-old bats into a clear startup failure instead of a
silent one.

Nothing enforces the declaration.
[bats-temp-dirs.bats](../../tests/bats/commands/bats-temp-dirs.bats) lints the
other half of the convention — that no bats file calls `mktemp` — but a new file
can use `BATS_TEST_TMPDIR` with no version floor and the lint stays green. On an
older runner the variable is unset, so `"${BATS_TEST_TMPDIR}/work"` becomes
`/work`: the test writes outside the sandbox, or fails somewhere far from the
cause. Preventing exactly that silent degradation is what the declaration is
for.

The gap is real rather than hypothetical.
[tests/bats/integration/spec-model.bats](../../tests/bats/integration/spec-model.bats)
is the one file of 58 without the declaration. It allocates no temporaries and
never mentions `BATS_TEST_TMPDIR`, so it is harmless today — but it is the
proof that a file can be added without the line and nothing notices.

## Approach

Add a second lint to `bats-temp-dirs.bats`, beside the `mktemp` one. Same file,
same scan-and-report shape, same failure-message style. The two rules are two
halves of one convention — "use `BATS_TEST_TMPDIR`, and declare the version that
provides it" — and the file already carries the first.

The design question the issue leaves open is how wide the rule should be:

- **Every file, exact line 3** (chosen). All 57 declaring files carry
  `bats_require_minimum_version 1.5.0` as line 3, byte for byte, after the
  shebang and a blank line. The strict form therefore costs nothing today, and
  it produces the sharpest possible failure message: the fix is a single literal
  line at a known position, not a rule the reader has to interpret. It requires
  adding the line to `spec-model.bats`.
- **Every file, declaration anywhere, version unpinned.** Tolerates future
  reformatting, but accepts a declaration buried mid-file where no reader would
  look for it, and accepts a version floor below 1.4.0 that would not actually
  guarantee `BATS_TEST_TMPDIR`. Rejected: it is looser without buying anything
  the repository needs.
- **Only files that reference `BATS_TEST_TMPDIR`.** Ties the requirement to the
  concrete hazard, and exempts `spec-model.bats`. Rejected: it introduces an
  exception to maintain, and the exemption is unstable — the moment a
  maintenance edit adds a temporary path to an exempt file, the file needs the
  declaration and the reason why is no longer visible at the top of it. A
  uniform rule has no such edge.

Uniformity is also what makes the check cheap to read. "Line 3 of every bats
file is this exact line" needs no qualification, and the failure message can
quote the fix verbatim.

## Design

### The lint

One new test in
[tests/bats/commands/bats-temp-dirs.bats](../../tests/bats/commands/bats-temp-dirs.bats),
after the `mktemp` lint:

```bash
@test "every bats test file declares the required bats version" {
    local required='bats_require_minimum_version 1.5.0'
    local bats_dir
    bats_dir="$(git rev-parse --show-toplevel)/tests/bats"

    if [ ! -d "${bats_dir}" ] || [ ! -r "${bats_dir}" ]; then
        printf 'Expected a readable bats test directory at %s but found none.\n' "${bats_dir}" >&2
        return 1
    fi

    local offenders='' scanned=0 file
    while IFS= read -r -d '' file; do
        scanned=$(( scanned + 1 ))
        if [ "$(sed -n '3p' -- "${file}")" != "${required}" ]; then
            offenders+="${file}"$'\n'
        fi
    done < <(find "${bats_dir}" -name '*.bats' -type f -print0 | sort -z)

    if [ "${scanned}" -eq 0 ]; then
        printf 'Found no .bats files under %s. This lint checked nothing.\n' "${bats_dir}" >&2
        return 1
    fi

    if [ -n "${offenders}" ]; then
        printf 'Every bats test file must declare the bats version floor, as\n' >&2
        printf 'line 3, exactly:\n\n    %s\n\n' "${required}" >&2
        printf 'BATS_TEST_TMPDIR requires bats 1.4.0 or later. Without the\n' >&2
        printf 'declaration an older runner leaves it unset, and paths under it\n' >&2
        printf 'silently resolve outside the sandbox instead of failing.\n\n' >&2
        printf 'Missing the declaration:\n\n%s' "${offenders}" >&2
        return 1
    fi
}
```

Five decisions embedded there:

- **`sed -n '3p'` rather than a `grep` over the whole file.** Position is part
  of the rule, and per-file line extraction is the only way to check it. A file
  shorter than three lines makes `sed` print nothing, which compares unequal to
  `required` and is correctly reported — no special case needed.
- **No self-exclusion.** The `mktemp` lint has to skip its own file, because a
  lint for a string necessarily contains that string; the awk `index()` guard
  above it exists for exactly that. This lint needs no such escape: its own file
  already satisfies the rule it enforces, so it can scan itself like any other.
- **The `scanned` guard.** Without it, a `find` that matches nothing yields an
  empty `offenders` and the test reports a false PASS. This mirrors the
  readable-directory guard already in the `mktemp` lint and the reasoning its
  comment records — fail loudly rather than silently check nothing. The
  directory guard alone does not cover it: a readable directory with no `.bats`
  files inside passes that check.
- **`-print0` with `read -r -d ''`.** Paths come from `git rev-parse`, so they
  carry whatever the checkout directory is named. Null separation costs one
  flag and removes the whole class of whitespace concern.
- **`sort -z`.** Offenders are reported in a stable order, so the same breakage
  produces the same message on every machine.

The message names the rule, quotes the fix as a literal line, explains the
hazard in one sentence, and lists the files — matching the `mktemp` lint, which
does the same four things in the same order.

### Companion changes

- Add `bats_require_minimum_version 1.5.0` as line 3 of
  [tests/bats/integration/spec-model.bats](../../tests/bats/integration/spec-model.bats),
  the one current offender.
- Extend the *Temporary files in bats tests* section of
  [CONTRIBUTING.md](../../CONTRIBUTING.md). It already ends with
  "`tests/bats/commands/bats-temp-dirs.bats` enforces this"; the declaration
  requirement belongs in the same paragraph, since it is the same convention and
  the same enforcing file.

Nothing under `src/` changes. This is test and documentation work only, so the
issue's `test` type stands and there is no `docs/whats-new.md` entry.

## Testing

Run with `bin/test/commands.bash tests/bats/commands/bats-temp-dirs.bats`.

**Red comes from the repository, not from scaffolding.** The lint is written and
run first, against the tree as it stands, where `spec-model.bats` still lacks
the declaration. It must fail, and the failure must name that file — that is the
proof the scan reaches every file and that the reported path is usable. Adding
the declaration to `spec-model.bats` turns it green. No temporary fixture is
created or deleted to manufacture the red.

Two guard behaviours cannot be proven that way, because they only fire on a tree
that does not exist here. Both are checked by hand against a scratch directory,
with `bats_dir` pointed at it, and the checks are not committed:

1. A directory containing no `.bats` files fails on the `scanned` guard rather
   than passing.
2. A two-line `.bats` file is reported as an offender rather than skipped.

Then `bin/test/functional.bash` before pushing. The new lint scans every tier's
files, so a stray edit anywhere under `tests/bats/` surfaces there.

## Consequences

- Adding a bats file without the declaration now fails the commands tier, with a
  message that states the exact line and where it goes.
- The declaration's position is frozen at line 3. Any future reformatting of the
  bats file preamble — a license header, say — has to update this lint in the
  same change. That is the intended cost of the strict form: the rule is
  mechanical and visible, and changing it is a deliberate edit rather than a
  drift nobody notices.
- The lint is structural. It cannot tell that a declared floor is *correct* for
  the features a file uses; it only asserts every file carries the same one. If
  the repository ever needs a higher floor, the constant in the lint and the 58
  files move together.
- `bats-temp-dirs.bats` now holds one behavioural test and two lints. That is
  still one coherent file — everything in it defends the `BATS_TEST_TMPDIR`
  convention — but a third lint would be the point to reconsider the name.
