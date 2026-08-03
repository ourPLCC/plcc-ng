"""Assert every runnable spec in docs/ is byte-identical to its fixture.

Behaviour of these examples is covered by tests/bats/docs/, which runs the
fixtures through the real CLI. This file covers the other half: that what a
reader copies out of the documentation is exactly what those tests ran.

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

# fixture directory -> (page, relative to docs/; tab label)
MANIFEST = {
    "quick-start-python": ("quick-start.md", "Python"),
    "quick-start-java": ("quick-start.md", "Java"),
    "lang-guide-index-python": ("language-guide/index.md", "Python"),
    "lang-guide-index-java": ("language-guide/index.md", "Java"),
    "lang-guide-examples-python": ("language-guide/examples.md", "Python"),
    "lang-guide-examples-java": ("language-guide/examples.md", "Java"),
}


def extract_tabbed_block(md_text, tab_label):
    """Return the first fenced code block inside the `=== "<tab_label>"` tab.

    The four spaces that nest the block inside the tab are stripped, so the
    result is directly comparable to a standalone file. Indentation relative
    to the block is preserved.
    """
    lines = md_text.split("\n")
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

    body = []
    i += 1
    while i < len(lines) and not lines[i].strip().startswith("```"):
        line = lines[i]
        if line.startswith(TAB_INDENT):
            line = line[len(TAB_INDENT):]
        elif line.strip():
            raise LookupError(f"{header} block has an under-indented line: {line!r}")
        body.append(line)
        i += 1
    if i == len(lines):
        raise LookupError(f"{header} block is never closed")

    return "\n".join(body) + "\n"


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


@pytest.mark.parametrize("fixture", sorted(MANIFEST))
def test_documented_block_matches_its_fixture(fixture):
    page, tab = MANIFEST[fixture]
    documented = extract_tabbed_block((DOCS / page).read_text(), tab)
    tested = (FIXTURES / fixture / "spec.plcc").read_text()
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
