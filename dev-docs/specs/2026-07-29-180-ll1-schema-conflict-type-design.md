# 180 — describe `conflict_type` in the ll1 output schema

**Date:** 2026-07-29
**Issue:** [180](../issues/done/180-ll1-schema-omits-conflict-type.md)

## Problem

`plcc-ll1` emits a `conflict_type` key on every entry of its `conflicts` array.
`build_ll1_result` in
[ll1_result_builder.py](../../src/plcc/ll1/ll1_result_builder.py) sets it to
`"first_follow"` when any of the conflicting productions is empty and
`"first_first"` otherwise, then appends it to the entry unconditionally —
there is no path that omits it.

The `conflicts` item schema in
[ll1.schema.json](../../src/plcc/schemas/ll1.schema.json) requires and describes
exactly three keys: `nonterminal`, `lookahead`, `productions`. No schema in
`src/plcc/schemas/` sets `additionalProperties: false`, so the fourth key is
silently accepted and validated as "anything goes." A `conflict_type` that went
missing, changed type, or took an unexpected value would pass every
`check-jsonschema` call in the suite.

That key drives user-facing output.
[format_conflict_message.py](../../src/plcc/ll1/format_conflict_message.py)
reads it with `conflict.get("conflict_type", "first_first")` and branches on it
to choose between the FIRST/FOLLOW and FIRST/FIRST diagnostic wording — two
different explanations and two different remediation tips. A dropped value does
not fail loudly; it degrades to the FIRST/FIRST branch and prints a
left-factoring suggestion for a conflict that cannot be left-factored.

The gap is wider than the issue states. **No test in this repository produces a
conflicting grammar.** Every fixture is LL(1)-clean, so every schema check in
the suite validates `"conflicts": []` — an empty array, which `required` never
reaches. The three keys already declared in the conflicts item are as unproven
as the missing fourth.

## Approach

Declare the key the emitter already produces, and build the first test subject
that reaches the `conflicts` section at all.

The schema addition is descriptive, not prescriptive: no production code
changes and no output changes. It follows
[#179](../issues/done/179-ll1-schema-omits-arbno-section.md), which described
the `arbno` section and established the negative-schema-test pattern this spec
reuses.

Two decisions carry the design.

**`enum`, not `type: string`.** `build_ll1_result` computes the value from a
single boolean — `has_empty` — so `first_first` and `first_follow` are the only
values reachable, and `ll1_result_builder_test.py` asserts both. A bare
`string` declaration would accept `"banana"`, which is precisely the failure
mode `format_conflict_message` cannot detect: an unrecognized value falls
through to the FIRST/FIRST branch and renders plausible-looking but wrong
advice. The enum is also what makes the negative test meaningful — without it,
no test could distinguish the new clause from `type: string`.

**A fixture that emits both types at once.** The alternative — one minimal
fixture per conflict type — costs two `setup()` lines and two positive controls
to prove the same two enum values, and yields two files that differ by three
grammar lines. A single grammar with an ambiguous nullable nonterminal and an
unfactored alternation produces a two-entry `conflicts` array covering both
enum values in one validation.

Two alternatives were considered and rejected:

- **Delete-only mutation, mirroring #179's loop exactly.** Simplest, but leaves
  the enum unproven: dropping `enum` back to `type: string` would keep the test
  green. The tighter declaration is the whole point of the change.
- **Extend the mutation loop over the whole `conflicts` item** — `nonterminal`,
  `lookahead`, `productions`, and the nested production keys. Those are already
  `required`, so those cases pass before the schema edit and after it. They
  would be characterization, not red proof, and mixing them into the loop
  weakens the signal that the loop reds on `conflict_type` specifically. The
  positive control covers the section's accepting direction; that is enough.

## Design

### Schema

In the `conflicts` item, add `"conflict_type"` to `required` and one line to
`properties`:

```json
"conflicts": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["nonterminal", "lookahead", "conflict_type", "productions"],
    "properties": {
      "nonterminal":   { "type": "string" },
      "lookahead":     { "type": "string" },
      "conflict_type": { "enum": ["first_first", "first_follow"] },
      "productions":   { ... unchanged ... }
    }
  }
}
```

Three decisions embedded there:

- **Required, not optional.** The emitter appends the key on every entry; there
  is no conditional path.
- **`enum` with no `type`.** JSON Schema's `enum` already constrains both value
  and type; adding `"type": "string"` alongside it would be redundant. The file
  has no existing enum to match, so this establishes the idiom.
- **No `additionalProperties: false`.** Per the issue and per #179: none of the
  five schemas in `src/plcc/schemas/` use it, and adding it here would be an
  unrelated tightening with its own blast radius.

Nothing else in the schema changes. The `productions` sub-schema, the
`parse_table` items it mirrors, and the `arbno` clause added by #179 are
untouched.

### Fixture

New file `tests/fixtures/ll1-conflicts.plcc` — the first deliberately non-LL(1)
grammar in the repository:

```text
# Deliberately non-LL(1): exercises both conflict_type values.
token X 'x'
token Y 'y'
skip  SPACE '\s+'
%
<Program> ::= <A:a> X <B:b>
<A:Some>  ::= X          # FIRST/FOLLOW: X starts <A> and also follows it
<A:None>  ::=
<B:One>   ::= Y          # FIRST/FIRST: both alternatives start with Y
<B:Two>   ::= Y X
```

`<A>` is nullable and `X` is in both `FIRST(<A>)` and `FOLLOW(<A>)`, so the
parser cannot tell whether to take `<A:Some>` or the empty `<A:None>` — a
FIRST/FOLLOW conflict. `<B>`'s two alternatives both start with `Y` — a
FIRST/FIRST conflict. Verified end to end: `plcc-spec` exits 0, `plcc-ll1`
exits 0, and the output carries `"is_ll1": false` with

```json
"conflicts": [
  { "nonterminal": "A", "lookahead": "X", "conflict_type": "first_follow", ... },
  { "nonterminal": "B", "lookahead": "Y", "conflict_type": "first_first",  ... }
]
```

Entry order is stable across runs — it follows rule declaration order — so
`conflicts.0` is a safe mutation target. `plcc-spec` accepts both whole-line
and trailing `#` comments (confirmed against the fixture text above, verbatim),
so it explains its own purpose inline. No existing fixture uses comments; this
one earns them by being the only fixture that is broken on purpose.

Adding an intentionally broken grammar to the shared fixture directory is inert
for the rest of the suite. Nothing globs `tests/fixtures/` — every reference in
`tests/bats/` and `bin/` names a specific file. The two `bin/` references are
`bin/test/smoke.bash` (`trivial.plcc`) and `bin/test/packaging.bash`
(`arith.plcc`).

The alternative of a heredoc inside the bats file, as
`tests/bats/integration/plcc-parse-errors.bats` and
`tests/bats/integration/java-emit.bats` do, was rejected: this grammar is the
only non-LL(1) subject in the repository, and future work on conflict
diagnostics — `format_conflict_message` has no bats coverage at all — will want
it by name.

### Tests

Both tests go in the existing
[tests/bats/commands/plcc-ll1.bats](../../tests/bats/commands/plcc-ll1.bats),
alongside the `arbno` pair added by #179. That is the narrowest tier that can
produce real output: the schema is `plcc-ll1`'s own output contract, and the
file's `setup()` already builds two spec JSONs with `plcc-spec` before invoking
the command under test. It gains a third.

| # | Test | Assertion |
|---|---|---|
| 1 | Positive control | `plcc-ll1` output for the conflict grammar exits 0 and validates against the schema |
| 2 | Negative, loop-driven | `conflicts.0.conflict_type` deleted, and set to a non-enum value — each mutant is **rejected** |

Test 1 is not redundant with test 2. It is the control: without it, both
mutants could be rejected for a reason unrelated to `conflict_type` and test 2
would pass while proving nothing. It also pins the accepting direction of the
enum — the fixture's two entries carry `first_follow` and `first_first`, and
both must validate. It is the suite's first validation of a non-empty
`conflicts` array.

Test 2 generalizes #179's mutation loop by one axis. That loop carried a dotted
path and always deleted; this one carries a mutation *kind* alongside the path:

```text
delete  conflicts.0.conflict_type
set     conflicts.0.conflict_type = "not_a_conflict_type"
```

`delete` proves `required`; `set` proves the `enum`. Together they are exactly
the two ways the new clause can bite. All four quadrants were confirmed against
real output before this spec was written: the current schema **accepts** both
mutants (the red proof), the candidate schema **rejects** both, and unmutated
output validates clean against the candidate.

The mechanics carry over from #179 unchanged, and for the same reasons:

- Each mutant is written to a file under `BATS_TEST_TMPDIR` and passed to
  `check-jsonschema` **by path**, not piped. No JSON is ever interpolated into
  a shell string.
- The path walker treats an integer segment as a list index and lets a bad path
  raise, so a typo aborts the test with a non-zero `python3` exit rather than
  silently writing out an unmutated document that would then be accepted for
  the wrong reason.
- Per CONTRIBUTING, no `mktemp` and no `teardown` — bats creates and removes
  `BATS_TEST_TMPDIR` per test, and
  `tests/bats/commands/bats-temp-dirs.bats` enforces the rule.
- No `bats-assert` helpers; plain `[ ... ]` tests on `$status`, as every
  existing test in this repository does.

## Testing

Run with `bin/test/commands.bash tests/bats/commands/plcc-ll1.bats`.

**Red proof comes first.** Test 2 is written and run against the *unmodified*
schema, where both mutants must be accepted — so the test must fail, and must
fail on the first case in the loop. A test that goes green only after the
schema lands is the point of the exercise; one that was green before it would
mean the loop is measuring something else. Test 1 passes before and after, as a
control should.

Then `bin/test/integration.bash tests/bats/integration/spec-ll1.bats`. Its
schema-valid assertions all run LL(1)-clean fixtures whose `conflicts` array is
empty, which `required` never reaches, so they are expected to stay green
untouched. Running them confirms the edit did not disturb the surrounding
`productions` sub-schema.

`bin/test/functional.bash` runs before the branch is pushed. No runtime code
loads `src/plcc/schemas/` — the schemas are consumed only by `check-jsonschema`
in the bats tiers — so no packaging or e2e concern follows from editing one.
The new fixture is referenced by exactly one file and is not picked up by any
glob, so no other tier changes behavior.

## Consequences

- The suite gains its first conflicting grammar, and with it the first
  validation of a populated `conflicts` array. The three keys that were already
  declared there — `nonterminal`, `lookahead`, `productions`, and the nested
  production items — start being checked by test 1 for free, having been
  unreachable by every prior schema call.
- A third conflict type added later will fail validation until the enum is
  updated. That is the intended tradeoff. The alternative is worse:
  `format_conflict_message`'s `else` branch would render the new type with
  FIRST/FIRST wording and a left-factoring tip, and no test would notice.
- The schema constrains *which* type appears, not whether it is the *correct*
  type for the conflict. A `first_first` label on a genuine FIRST/FOLLOW
  conflict stays well-formed and validates clean. The unit tests in
  `src/plcc/ll1/ll1_result_builder_test.py` remain the guard for that, and this
  change does not replace them.
- `format_conflict_message`'s `.get("conflict_type", "first_first")` default
  becomes provably unreachable for real `plcc-ll1` output. It is left in place:
  the function is also called with hand-built dicts in its own unit tests, and
  removing the default is a separate change with no test pressure behind it.
- The change touches `src/`, so the issue is typed `fix` and a `fix(schema): …`
  commit bumps the patch version. Its user-visible effect is nil — no runtime
  code reads the schema — so there is no `docs/whats-new.md` entry.
