"""Assert every runnable spec in docs/ is byte-identical to its fixture.

Behaviour of these examples is covered by tests/bats/docs/, which runs the
fixtures through the real CLI. This file covers the other half: that what a
reader copies out of the documentation is exactly what those tests ran — both
the specification the reader writes and the output the page promises they will
see.

This lives here rather than co-located in src/ because it tests documentation
rather than a src module, and must not ship in the wheel. See CONTRIBUTING.md.
"""

import difflib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS = PROJECT_ROOT / "docs"
FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "docs"

# Four spaces of indentation nest a fenced block inside a `=== "Tab"` block.
TAB_INDENT = "    "

# Every fixture directory, and what on its page each of its files is pinned to.
#
#   spec     -> (page, relative to docs/; the `=== "Tab"` label holding it)
#   outputs  -> expected-* file -> (page; the heading of the section that
#               documents the command producing it)
#   unpinned -> expected-* files the page does not show, with the reason
#
# Two fixtures deliberately map to the same headings (the Python and Java tabs
# of one page document a single set of outputs); asserting both against it is
# the point.
MANIFEST = {
    "quick-start-python": {
        "spec": ("quick-start.md", "Python"),
        "outputs": {
            "expected-scan": ("quick-start.md", "### 2. Scan source text"),
            "expected-parse": ("quick-start.md", "### 3. Parse source text"),
            "expected-rep": ("quick-start.md", "### 4. Run the program"),
        },
    },
    "quick-start-java": {
        "spec": ("quick-start.md", "Java"),
        "outputs": {
            "expected-scan": ("quick-start.md", "### 2. Scan source text"),
            "expected-parse": ("quick-start.md", "### 3. Parse source text"),
            "expected-rep": ("quick-start.md", "### 4. Run the program"),
        },
    },
    "lang-guide-index-python": {
        "spec": ("language-guide/index.md", "Python"),
        "outputs": {},
        # The page shows a specification but documents no commands and no
        # output, so there is nothing on it to pin expected-rep to. The
        # fixture's input and expected-rep are authored rather than
        # transcribed, which makes the tier stronger than the page.
        "unpinned": ("expected-rep",),
    },
    "lang-guide-index-java": {
        "spec": ("language-guide/index.md", "Java"),
        "outputs": {},
        "unpinned": ("expected-rep",),
    },
    "lang-guide-examples-python": {
        "spec": ("language-guide/examples.md", "Python"),
        "outputs": {
            "expected-scan": ("language-guide/examples.md", "### Scanner"),
            "expected-parse": ("language-guide/examples.md", "### Parser"),
            "expected-rep": ("language-guide/examples.md", "### Interpreter"),
        },
    },
    "lang-guide-examples-java": {
        "spec": ("language-guide/examples.md", "Java"),
        "outputs": {
            "expected-scan": ("language-guide/examples.md", "### Scanner"),
            "expected-parse": ("language-guide/examples.md", "### Parser"),
            "expected-rep": ("language-guide/examples.md", "### Interpreter"),
        },
    },
}

# Pages holding a runnable specification that the tier does not cover yet.
# MANIFEST is a hand-enumeration, and hand-enumeration of affected docs is the
# root cause this tier exists to remove, so every uncovered specification is
# named here with a reason rather than being silently absent.
# Pages whose `%%%` fences the tier does not cover, mapped to how many such
# fences each holds today. The count is what makes this allowlist a guard rather
# than a blanket exemption: adding a fence to a listed page changes its count and
# fails `test_every_runnable_spec_is_covered_or_allowlisted`, so a new example
# cannot ride in on an existing entry. Whoever adds one has to either fixture it
# or bump the count deliberately.
UNCOVERED = {
    # Complete, copy-and-run quick-reference specifications that work today but
    # are unguarded, plus the illustrative `%%%` fragments on the same pages.
    # Extending the tier to them is deliberately out of scope (see
    # dev-docs/specs/2026-08-03-doc-example-drift-design.md, "Out of scope"):
    # they need fixtures of their own, and the Haskell one needs a `cabal
    # build`, so it belongs with the slow tests rather than in this tier.
    "language-guide/languages/haskell.md": 4,
    "language-guide/languages/java.md": 3,
    "language-guide/languages/javascript.md": 4,
    "language-guide/languages/python.md": 4,
    # Illustrative fragments rather than specifications: semantic.md shows the
    # `ClassName` / `%%%` code-block syntax in isolation, and migration.md
    # shows PLCC-versus-plcc-ng snippets. Neither is runnable, so there is
    # nothing for the behavior tier to execute.
    "language-guide/semantic.md": 2,
    "migration.md": 2,
}


def _locate_tabbed_block(lines, tab_label):
    """Return the (open, close) indices of the fence nested inside the tab."""
    header = f'=== "{tab_label}"'

    for start, line in enumerate(lines):
        if line.strip() == header:
            break
    else:
        raise LookupError(f"no {header} tab found")

    i = start + 1
    while i < len(lines) and not lines[i].strip().startswith("```"):
        if lines[i].strip():
            raise LookupError(f"{header} is not followed by a fenced block")
        i += 1
    if i == len(lines):
        raise LookupError(f"{header} is not followed by a fenced block")
    opening = i

    i += 1
    while i < len(lines) and not lines[i].strip().startswith("```"):
        i += 1
    if i == len(lines):
        raise LookupError(f"{header} block is never closed")

    return opening, i


def extract_tabbed_block(md_text, tab_label):
    """Return the first fenced code block inside the `=== "<tab_label>"` tab.

    The four spaces that nest the block inside the tab are stripped, so the
    result is directly comparable to a standalone file. Indentation relative
    to the block is preserved.
    """
    lines = md_text.split("\n")
    opening, closing = _locate_tabbed_block(lines, tab_label)
    header = f'=== "{tab_label}"'

    body = []
    for line in lines[opening + 1:closing]:
        if line.startswith(TAB_INDENT):
            line = line[len(TAB_INDENT):]
        elif line.strip():
            raise LookupError(f"{header} block has an under-indented line: {line!r}")
        body.append(line)

    return "\n".join(body) + "\n"


def extract_output_block(md_text, heading):
    """Return the first unindented ```text block in the `<heading>` section.

    The section runs from the heading line to the next line starting with `#`.
    Fences opened at column zero are skipped over as units, so a `#` inside a
    fenced block never ends the search early.

    Being unindented is the discriminator: a fence nested inside a
    `=== "Tab"` block is indented four spaces, so this can never return a
    specification tab. Fences with any other info string (the ```bash block
    showing the command) are skipped.
    """
    lines = md_text.split("\n")

    for start, line in enumerate(lines):
        if line.strip() == heading:
            break
    else:
        raise LookupError(f"no {heading!r} heading found")

    i = start + 1
    while i < len(lines) and not lines[i].startswith("#"):
        if not lines[i].startswith("```"):
            i += 1
            continue
        is_text = lines[i][3:].strip() == "text"
        body = []
        i += 1
        while i < len(lines) and lines[i].rstrip() != "```":
            body.append(lines[i])
            i += 1
        if i == len(lines):
            raise LookupError(f"{heading!r} has an unclosed fenced block")
        i += 1
        if is_text:
            return "\n".join(body) + "\n"

    raise LookupError(f"{heading!r} is not followed by an unindented ```text block")


def find_spec_fences(md_text):
    """Return the 1-based opening-fence line of every `%%%`-bearing block.

    A fenced block containing `%%%` is a semantic section, so the block is a
    runnable specification rather than a fragment of prose.
    """
    lines = md_text.split("\n")
    found = []

    i = 0
    while i < len(lines):
        if not lines[i].strip().startswith("```"):
            i += 1
            continue
        opening = i
        body = []
        i += 1
        while i < len(lines) and lines[i].strip() != "```":
            body.append(lines[i])
            i += 1
        i += 1
        if any("%%%" in line for line in body):
            found.append(opening + 1)

    return found


def _read(path):
    return path.read_text(encoding="utf-8")


def test_extract_selects_the_named_tab():
    md = (
        '=== "Python"\n    ```text\n    py\n    ```\n'
        '\n'
        '=== "Java"\n    ```text\n    java\n    ```\n'
    )
    assert extract_tabbed_block(md, "Java") == "java\n"


def test_extract_strips_the_tab_indent_but_keeps_relative_indentation():
    md = '=== "Python"\n    ```text\n    def _run(self):\n      return "x"\n    ```\n'
    assert extract_tabbed_block(md, "Python") == 'def _run(self):\n  return "x"\n'


def test_extract_keeps_blank_lines_inside_the_block():
    md = '=== "Python"\n    ```text\n    a\n\n    b\n    ```\n'
    assert extract_tabbed_block(md, "Python") == "a\n\nb\n"


def test_extract_raises_for_a_missing_tab():
    md = '=== "Python"\n    ```text\n    a\n    ```\n'
    with pytest.raises(LookupError, match="Haskell"):
        extract_tabbed_block(md, "Haskell")


def test_extract_raises_for_an_unclosed_block():
    md = '=== "Python"\n    ```text\n    a\n'
    with pytest.raises(LookupError, match="never closed"):
        extract_tabbed_block(md, "Python")


def test_extract_output_skips_the_command_fence_before_it():
    md = (
        "### Scanner\n\n```bash\nplcc-scan samples\n```\n\n"
        "Output:\n\n```text\nsamples:1:1 WHOLE '3'\n```\n"
    )
    assert extract_output_block(md, "### Scanner") == "samples:1:1 WHOLE '3'\n"


def test_extract_output_prefers_an_unindented_fence_over_an_indented_one():
    md = (
        "### Scanner\n\n"
        '=== "Python"\n    ```text\n    spec\n    ```\n\n'
        "```text\nreal output\n```\n"
    )
    assert extract_output_block(md, "### Scanner") == "real output\n"


def test_extract_output_stops_at_the_next_heading():
    md = "### Scanner\n\nNo output shown here.\n\n### Parser\n\n```text\nlater\n```\n"
    with pytest.raises(LookupError, match="### Scanner"):
        extract_output_block(md, "### Scanner")


def test_extract_output_raises_for_a_missing_heading():
    md = "### Scanner\n\n```text\nout\n```\n"
    with pytest.raises(LookupError, match="### Parser"):
        extract_output_block(md, "### Parser")


def test_extract_output_ignores_a_hash_inside_a_fenced_block():
    md = "### Scanner\n\n```bash\n# a comment\nplcc-scan\n```\n\n```text\nout\n```\n"
    assert extract_output_block(md, "### Scanner") == "out\n"


def test_find_spec_fences_reports_only_blocks_containing_a_semantic_section():
    md = "```text\nno semantics\n```\n\n```text\nProg\n%%%\ncode\n%%%\n```\n"
    assert find_spec_fences(md) == [5]


def test_find_spec_fences_sees_blocks_nested_in_tabs():
    md = '=== "Python"\n    ```text\n    Prog\n    %%%\n    code\n    %%%\n    ```\n'
    assert find_spec_fences(md) == [2]


@pytest.mark.parametrize("fixture", sorted(MANIFEST))
def test_documented_block_matches_its_fixture(fixture):
    page, tab = MANIFEST[fixture]["spec"]
    documented = extract_tabbed_block(_read(DOCS / page), tab)
    tested = _read(FIXTURES / fixture / "spec.plcc")
    if documented != tested:
        diff = "".join(
            difflib.unified_diff(
                tested.splitlines(keepends=True),
                documented.splitlines(keepends=True),
                fromfile=f"tests/fixtures/docs/{fixture}/spec.plcc",
                tofile=f'docs/{page}  === "{tab}"',
            )
        )
        pytest.fail(
            f'docs/{page} tab "{tab}" has drifted from its fixture.\n'
            f"tests/bats/docs/ runs the fixture, so the documentation is no "
            f"longer what was tested. Edit both or neither.\n\n{diff}"
        )


OUTPUT_CASES = sorted(
    (fixture, expected)
    for fixture, entry in MANIFEST.items()
    for expected in entry.get("outputs", {})
)


@pytest.mark.parametrize("fixture,expected", OUTPUT_CASES)
def test_documented_output_matches_its_fixture(fixture, expected):
    page, heading = MANIFEST[fixture]["outputs"][expected]
    documented = extract_output_block(_read(DOCS / page), heading)
    tested = _read(FIXTURES / fixture / expected)
    if documented != tested:
        diff = "".join(
            difflib.unified_diff(
                tested.splitlines(keepends=True),
                documented.splitlines(keepends=True),
                fromfile=f"tests/fixtures/docs/{fixture}/{expected}",
                tofile=f"docs/{page}  {heading}",
            )
        )
        pytest.fail(
            f'docs/{page} section "{heading}" no longer shows what '
            f"tests/fixtures/docs/{fixture}/{expected} contains.\n"
            f"tests/bats/docs/ asserts the command produces the fixture, so the "
            f"page is promising output the tool does not produce. Edit both or "
            f"neither.\n\n{diff}"
        )


@pytest.mark.parametrize("fixture", sorted(MANIFEST))
def test_every_expected_file_is_pinned_to_the_page(fixture):
    entry = MANIFEST[fixture]
    declared = set(entry.get("outputs", {})) | set(entry.get("unpinned", ()))
    present = {p.name for p in (FIXTURES / fixture).glob("expected-*")}
    missing = sorted(present - declared)
    assert not missing, (
        f"tests/fixtures/docs/{fixture}/ holds {', '.join(missing)}, which "
        f"MANIFEST does not account for. A fixture output that is pinned to "
        f"nothing can be updated to match a src/ change while the page keeps "
        f"showing output the tool no longer produces. Add it to this fixture's "
        f'"outputs" with the heading that documents it, or to "unpinned" with '
        f"the reason the page cannot show it."
    )
    stale = sorted(declared - present)
    assert not stale, (
        f"MANIFEST declares {', '.join(stale)} for {fixture}, but "
        f"tests/fixtures/docs/{fixture}/ has no such file."
    )


def test_every_runnable_spec_is_covered_or_allowlisted():
    covered = {}
    for entry in MANIFEST.values():
        page, tab = entry["spec"]
        lines = _read(DOCS / page).split("\n")
        opening, _ = _locate_tabbed_block(lines, tab)
        covered.setdefault(page, set()).add(opening + 1)

    unguarded = []
    miscounted = []
    for md in sorted(DOCS.rglob("*.md")):
        page = md.relative_to(DOCS).as_posix()
        fences = find_spec_fences(_read(md))
        if page in UNCOVERED:
            # Allowlisted, but only for the fences that were there when the
            # exemption was written. A new one changes the count.
            if len(fences) != UNCOVERED[page]:
                miscounted.append(
                    f"docs/{page}: UNCOVERED says {UNCOVERED[page]}, "
                    f"found {len(fences)} at {fences}"
                )
            continue
        for line in fences:
            if line not in covered.get(page, ()):
                unguarded.append(f"docs/{page}:{line}")

    assert not unguarded, (
        "These runnable specifications in docs/ are covered by nothing:\n  "
        + "\n  ".join(unguarded)
        + "\n\nA specification nothing runs can break and ship, which is the "
        "regression this tier exists to prevent. Either add a fixture under "
        "tests/fixtures/docs/ and register it in MANIFEST, or add the page to "
        "UNCOVERED with the count and the reason it is out of scope."
    )

    assert not miscounted, (
        "The number of runnable specifications on these allowlisted pages "
        "changed:\n  "
        + "\n  ".join(miscounted)
        + "\n\nUNCOVERED exempts the fences that existed when the exemption was "
        "written, not the page forever. If you added one, either give it a "
        "fixture under tests/fixtures/docs/ and register it in MANIFEST, or "
        "raise the count here to say deliberately that it is unguarded too. "
        "If you removed one, lower the count."
    )


def test_the_uncovered_allowlist_has_no_stale_entries():
    stale = []
    for page in sorted(UNCOVERED):
        md = DOCS / page
        if not md.is_file():
            stale.append(f"docs/{page} (no such file)")
        elif not find_spec_fences(_read(md)):
            stale.append(f"docs/{page} (no runnable specification)")

    assert not stale, (
        "UNCOVERED lists pages that no longer need allowlisting:\n  "
        + "\n  ".join(stale)
        + "\n\nRemove them, so the allowlist keeps reading as the real list of "
        "gaps."
    )
