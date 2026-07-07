# 095 — Semantic Section Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the semantic section format so the divider is a bare `%`, the language name moves into the section body as its first non-blank non-comment line, and the tool concept is removed entirely.

**Architecture:** Work bottom-up through the parsing stack: (1) rough parser Divider + semantic parser, (2) single-section enforcement + Spec type, (3) JSON schema + model builder, (4) plcc-make, (5) plcc-rep. Each task leaves all tests green.

**Tech Stack:** Python 3.14, pytest (`bin/test/units.bash`), dataclasses, docopt.

## Global Constraints

- No backward compatibility. Old `% Language` and `% tool Language` divider syntax → parse error.
- Only one semantic section allowed per spec file.
- `semantics` in `spec.json` is now a nullable object, not an array.
- `semantic_sections` in `model.json` remains an array (0 or 1 items), but `tool` is removed.
- Language name validation (canonical casing) is implicit at build time via `plcc-lang-emit`.
- Build output dir: `build/<language>/` (e.g., `build/Python`).
- Run tests with: `bin/test/units.bash` from the worktree root.
- Commit from the worktree root (branch `095-redesign-semantic-section-format`).

---

## File Map

**Create:**
- `src/plcc/spec/rough/UnexpectedTokensOnDividerError.py`
- `src/plcc/spec/semantics/LanguageDeclaration.py`
- `src/plcc/spec/semantics/MissingLanguageDeclarationError.py`
- `src/plcc/spec/MultipleSemanticsError.py`

**Delete:**
- `src/plcc/spec/rough/TooManyDividerTokensError.py`

**Modify:**
- `src/plcc/spec/rough/Divider.py` — remove `tool`, `language`
- `src/plcc/spec/rough/parse_dividers.py` — bare `%` only, raise on tokens
- `src/plcc/spec/rough/__init__.py` — swap exported error
- `src/plcc/spec/semantics/SemanticSpec.py` — remove `tool`
- `src/plcc/spec/semantics/parse_semantic_spec.py` — extract language from body
- `src/plcc/spec/semantics/__init__.py` — export new types
- `src/plcc/spec/Spec.py` — `semantics: SemanticSpec | None`
- `src/plcc/spec/parseSpec.py` — enforce single section, catch MissingLanguageDeclarationError
- `src/plcc/schemas/spec.schema.json` — semantics → nullable object, no tool
- `src/plcc/schemas/model.schema.json` — remove `tool` from semantic_sections items
- `src/plcc/model/build_model.py` — handle nullable semantics, drop tool
- `src/plcc/cmd/make.py` — language as output dir, remove validate_tool_name
- `src/plcc/cmd/rep.py` — remove --tool, simplify language resolution
- `src/plcc/cmd/output.py` — simplify print_banner signature

**Test files modified:**
- `src/plcc/spec/rough/parse_dividers_test.py`
- `src/plcc/spec/semantics/parse_semantic_spec_test.py`
- `src/plcc/spec/parseSpec_test.py`
- `src/plcc/spec/plcc_spec_cli_test.py`
- `src/plcc/model/build_model_test.py`
- `src/plcc/lang/ext/python/emit_test.py`
- `src/plcc/lang/ext/java/emit_test.py`
- `src/plcc/cmd/make_test.py`
- `src/plcc/cmd/rep_test.py`

---

## Task 1: Core parsing pipeline — Divider simplification and language extraction from body

Rewrites the path from raw `%` line through `SemanticSpec`. After this task, `Divider` has no metadata, `parse_dividers` rejects tokens after `%`, and `parse_semantic_spec` reads the language from the first non-blank/non-comment body line.

**Files:**
- Create: `src/plcc/spec/rough/UnexpectedTokensOnDividerError.py`
- Modify: `src/plcc/spec/rough/Divider.py`
- Modify: `src/plcc/spec/rough/parse_dividers.py`
- Modify: `src/plcc/spec/rough/__init__.py`
- Delete: `src/plcc/spec/rough/TooManyDividerTokensError.py`
- Create: `src/plcc/spec/semantics/LanguageDeclaration.py`
- Create: `src/plcc/spec/semantics/MissingLanguageDeclarationError.py`
- Modify: `src/plcc/spec/semantics/SemanticSpec.py`
- Modify: `src/plcc/spec/semantics/parse_semantic_spec.py`
- Modify: `src/plcc/spec/semantics/__init__.py`
- Test: `src/plcc/spec/rough/parse_dividers_test.py`
- Test: `src/plcc/spec/semantics/parse_semantic_spec_test.py`

**Interfaces:**
- Produces: `Divider(line: Line)` — no tool, no language
- Produces: `LanguageDeclaration(language: str, line: Line)`
- Produces: `MissingLanguageDeclarationError(SpecError)` — raised when body has no language line
- Produces: `UnexpectedTokensOnDividerError(SpecError)` — raised when `%` has tokens
- Produces: `SemanticSpec(language: str, codeFragmentList: list[CodeFragment])` — no tool
- Consumes: `SpecError(line, column)` from `src/plcc/spec/SpecError.py`

- [ ] **Step 1: Replace parse_dividers_test.py**

Replace the full contents of `src/plcc/spec/rough/parse_dividers_test.py`:

```python
from pytest import raises
from ... import lines
from .Block import Block
from .Divider import Divider
from .UnexpectedTokensOnDividerError import UnexpectedTokensOnDividerError
from .parse_blocks import parse_blocks
from .parse_dividers import parse_dividers


def test_None_yields_nothing():
    assert list(parse_dividers(None)) == []


def test_empty_yields_nothing():
    assert list(parse_dividers([])) == []


def test_non_dividers_pass_through():
    lines_ = list(parse_blocks(lines.parseLines('''\
one
%%%
two
%%%
three
''')))
    assert list(parse_dividers(lines_)) == lines_


def test_bare_percent_yields_divider():
    lines_ = list(lines.parseLines('%'))
    result = list(parse_dividers(lines_))
    assert result == [Divider(line=lines_[0])]


def test_percent_with_trailing_whitespace_yields_divider():
    lines_ = list(lines.parseLines('%  '))
    result = list(parse_dividers(lines_))
    assert result == [Divider(line=lines_[0])]


def test_percent_with_token_raises_error():
    with raises(UnexpectedTokensOnDividerError):
        list(parse_dividers(list(lines.parseLines('% Java'))))


def test_percent_with_two_tokens_raises_error():
    with raises(UnexpectedTokensOnDividerError):
        list(parse_dividers(list(lines.parseLines('% tool Java'))))


def test_percent_with_three_tokens_raises_error():
    with raises(UnexpectedTokensOnDividerError):
        list(parse_dividers(list(lines.parseLines('% a b c'))))


def test_double_percent_does_not_match():
    lines_ = list(lines.parseLines('%%'))
    assert list(parse_dividers(lines_)) == [lines.Line('%%', 1, None)]


def test_blocks_mask_dividers():
    lines_ = list(parse_blocks(lines.parseLines('%%%\n%\n%%%')))
    assert list(parse_dividers(lines_)) == [
        Block([
            lines_[0].lines[0],
            lines_[0].lines[1],
            lines_[0].lines[2]
        ])
    ]
```

- [ ] **Step 2: Run tests, confirm failures**

```
bin/test/units.bash src/plcc/spec/rough/parse_dividers_test.py -v
```

Expected: multiple failures — `UnexpectedTokensOnDividerError` not importable, `Divider` constructor mismatch.

- [ ] **Step 3: Create `UnexpectedTokensOnDividerError.py`**

Create `src/plcc/spec/rough/UnexpectedTokensOnDividerError.py`:

```python
from ..SpecError import SpecError


class UnexpectedTokensOnDividerError(SpecError):
    ...
```

- [ ] **Step 4: Update `Divider.py`**

Replace `src/plcc/spec/rough/Divider.py`:

```python
from dataclasses import dataclass

from ...lines import Line


@dataclass
class Divider:
    line: Line
```

- [ ] **Step 5: Update `parse_dividers.py`**

Replace `src/plcc/spec/rough/parse_dividers.py`:

```python
import re

from ...lines import Line
from .Divider import Divider
from .UnexpectedTokensOnDividerError import UnexpectedTokensOnDividerError

_BARE_PERCENT = re.compile(r'^%\s*$')
_PERCENT_PREFIX = re.compile(r'^%')
_FIRST_TOKEN = re.compile(r'^%\s*(\S)')


def parse_dividers(lines):
    if not lines:
        return
    for line in lines:
        if isinstance(line, Line) and _PERCENT_PREFIX.match(line.string):
            if _BARE_PERCENT.match(line.string):
                yield Divider(line=line)
            else:
                match = _FIRST_TOKEN.match(line.string)
                col = match.start(1) + 1
                raise UnexpectedTokensOnDividerError(line=line, column=col)
        else:
            yield line
```

- [ ] **Step 6: Update `rough/__init__.py`**

Replace `src/plcc/spec/rough/__init__.py`:

```python
from .Block import Block
from .CircularIncludeError import CircularIncludeError
from .Divider import Divider
from .parseRough import parseRough
from .Include import Include
from .UnexpectedTokensOnDividerError import UnexpectedTokensOnDividerError
from .UnclosedBlockError import UnclosedBlockError
```

- [ ] **Step 7: Delete `TooManyDividerTokensError.py`**

```bash
git rm src/plcc/spec/rough/TooManyDividerTokensError.py
```

- [ ] **Step 8: Run divider tests, confirm they pass**

```
bin/test/units.bash src/plcc/spec/rough/parse_dividers_test.py -v
```

Expected: all pass.

- [ ] **Step 9: Replace `parse_semantic_spec_test.py`**

Replace `src/plcc/spec/semantics/parse_semantic_spec_test.py`:

```python
import pytest

from ...lines import Line
from .. import rough
from .LanguageDeclaration import LanguageDeclaration
from .MissingLanguageDeclarationError import MissingLanguageDeclarationError
from .parse_semantic_spec import parse_semantic_spec


def test_language_extracted_from_first_non_blank_line():
    section = [make_divider('%'), make_line('Python'), make_block()]
    spec = parse_semantic_spec(section)
    assert spec.language == 'Python'


def test_language_extracted_skips_blank_lines():
    section = [make_divider('%'), make_line(''), make_line('  '), make_line('Java')]
    spec = parse_semantic_spec(section)
    assert spec.language == 'Java'


def test_language_extracted_skips_comment_lines():
    section = [make_divider('%'), make_line('# a comment'), make_line('Python')]
    spec = parse_semantic_spec(section)
    assert spec.language == 'Python'


def test_language_is_stripped():
    section = [make_divider('%'), make_line('  Python  ')]
    spec = parse_semantic_spec(section)
    assert spec.language == 'Python'


def test_code_fragments_follow_language_line():
    section = [make_divider('%'), make_line('Python'), make_line('Program'), make_block()]
    spec = parse_semantic_spec(section)
    assert len(spec.codeFragmentList) == 1
    assert spec.codeFragmentList[0].targetLocator.className == 'Program'


def test_no_code_fragments_is_valid():
    section = [make_divider('%'), make_line('Python')]
    spec = parse_semantic_spec(section)
    assert spec.codeFragmentList == []


def test_no_language_line_raises_error():
    section = [make_divider('%')]
    with pytest.raises(MissingLanguageDeclarationError):
        parse_semantic_spec(section)


def test_only_blank_lines_raises_error():
    section = [make_divider('%'), make_line(''), make_line('  ')]
    with pytest.raises(MissingLanguageDeclarationError):
        parse_semantic_spec(section)


def test_only_comment_lines_raises_error():
    section = [make_divider('%'), make_line('# comment')]
    with pytest.raises(MissingLanguageDeclarationError):
        parse_semantic_spec(section)


def test_spec_has_no_tool_attribute():
    section = [make_divider('%'), make_line('Python')]
    spec = parse_semantic_spec(section)
    assert not hasattr(spec, 'tool')


def make_divider(string, number=1):
    return rough.Divider(line=make_line(string, number))


def make_block():
    rough_, _ = rough.parseRough('%%%\nblock\n%%%\n')
    return rough_[0]


def make_line(string, number=1):
    return Line(string, number, None)
```

- [ ] **Step 10: Run semantic spec tests, confirm failures**

```
bin/test/units.bash src/plcc/spec/semantics/parse_semantic_spec_test.py -v
```

Expected: multiple failures — `LanguageDeclaration`, `MissingLanguageDeclarationError` not importable.

- [ ] **Step 11: Create `LanguageDeclaration.py`**

Create `src/plcc/spec/semantics/LanguageDeclaration.py`:

```python
from dataclasses import dataclass

from ...lines import Line


@dataclass
class LanguageDeclaration:
    language: str
    line: Line
```

- [ ] **Step 12: Create `MissingLanguageDeclarationError.py`**

Create `src/plcc/spec/semantics/MissingLanguageDeclarationError.py`:

```python
from ..SpecError import SpecError


class MissingLanguageDeclarationError(SpecError):
    ...
```

- [ ] **Step 13: Update `SemanticSpec.py`**

Replace `src/plcc/spec/semantics/SemanticSpec.py`:

```python
from dataclasses import dataclass

from .CodeFragment import CodeFragment


@dataclass
class SemanticSpec:
    language: str
    codeFragmentList: list[CodeFragment]
```

- [ ] **Step 14: Update `parse_semantic_spec.py`**

Replace `src/plcc/spec/semantics/parse_semantic_spec.py`:

```python
from ...lines import Line
from ..rough import Block, Divider
from .LanguageDeclaration import LanguageDeclaration
from .MissingLanguageDeclarationError import MissingLanguageDeclarationError
from .parse_code_fragments import parse_code_fragments
from .SemanticSpec import SemanticSpec


def parse_semantic_spec(semantic_spec: list) -> SemanticSpec:
    divider = semantic_spec[0]
    rest = list(semantic_spec[1:])
    language_decl, body_start = _extract_language(rest, divider)
    code_fragments = parse_code_fragments(rest[body_start:])
    return SemanticSpec(language=language_decl.language, codeFragmentList=code_fragments)


def _extract_language(items, divider):
    for i, item in enumerate(items):
        if isinstance(item, Line) and not _is_blank_or_comment(item.string):
            return LanguageDeclaration(language=item.string.strip(), line=item), i + 1
    raise MissingLanguageDeclarationError(line=divider.line, column=1)


def _is_blank_or_comment(s):
    if s is None:
        return True
    stripped = s.strip()
    return stripped == '' or stripped.startswith('#')
```

- [ ] **Step 15: Update `semantics/__init__.py`**

Replace `src/plcc/spec/semantics/__init__.py`:

```python
from .LanguageDeclaration import LanguageDeclaration
from .MissingLanguageDeclarationError import MissingLanguageDeclarationError
from .SemanticSpec import SemanticSpec
from .parse_semantic_spec import parse_semantic_spec
```

- [ ] **Step 16: Run all unit tests, confirm they pass**

```
bin/test/units.bash -v
```

Expected: 977+ pass, 0 failures.

- [ ] **Step 17: Commit**

```bash
git add src/plcc/spec/rough/UnexpectedTokensOnDividerError.py \
        src/plcc/spec/rough/Divider.py \
        src/plcc/spec/rough/parse_dividers.py \
        src/plcc/spec/rough/__init__.py \
        src/plcc/spec/rough/parse_dividers_test.py \
        src/plcc/spec/semantics/LanguageDeclaration.py \
        src/plcc/spec/semantics/MissingLanguageDeclarationError.py \
        src/plcc/spec/semantics/SemanticSpec.py \
        src/plcc/spec/semantics/parse_semantic_spec.py \
        src/plcc/spec/semantics/__init__.py \
        src/plcc/spec/semantics/parse_semantic_spec_test.py
git commit -m "feat(095): simplify Divider and extract language from semantic section body"
```

---

## Task 2: Single-section enforcement and `Spec` type change

Adds `MultipleSemanticsError`, enforces one semantic section in `parseSpec`, changes `Spec.semantics` from `list` to `SemanticSpec | None`.

**Files:**
- Create: `src/plcc/spec/MultipleSemanticsError.py`
- Modify: `src/plcc/spec/Spec.py`
- Modify: `src/plcc/spec/parseSpec.py`
- Test: `src/plcc/spec/parseSpec_test.py`
- Test: `src/plcc/spec/plcc_spec_cli_test.py`

**Interfaces:**
- Consumes: `MissingLanguageDeclarationError` from Task 1
- Consumes: `Divider.line` (bare `Line`) from Task 1
- Produces: `MultipleSemanticsError(SpecError)` — raised when spec has 2+ semantic sections
- Produces: `Spec.semantics: SemanticSpec | None` — single optional section

- [ ] **Step 1: Replace `parseSpec_test.py`**

Replace `src/plcc/spec/parseSpec_test.py`:

```python
import pytest

from .parseSpec import parseSpec
from .MultipleSemanticsError import MultipleSemanticsError
from .rough.UnclosedBlockError import UnclosedBlockError


def test_rough_errors_are_returned():
    _, errors = parseSpec("token NUM '\\d+'\n%\n<a> ::= NUM\n%\nPython\n%%%\nhi")
    assert any(isinstance(e, UnclosedBlockError) for e in errors)


def test_lex_only():
    spec, errors = parseSpec("token A 'a'\nskip B 'b'\n")
    assert len(spec.lexical) == 2
    assert len(spec.syntax) == 0
    assert spec.semantics is None


def test_lexical_and_syntax_only():
    spec, errors = parseSpec(
        "token A 'a'\nskip B 'b'\n%\n<a> ::= A <b>\n<b> ::= B\n"
    )
    assert len(spec.lexical) == 2
    assert len(spec.syntax) == 2
    assert spec.semantics is None


def test_full_with_single_semantic_section():
    s = '''\
token A 'a'
skip B 'b'
%
<a> ::= A <b>
<b> ::= B
%
Python
A
%%%
Hi
%%%
'''
    spec, errors = parseSpec(s)
    assert errors == []
    assert len(spec.lexical) == 2
    assert len(spec.syntax) == 2
    assert spec.semantics is not None
    assert spec.semantics.language == 'Python'


def test_multiple_semantic_sections_produces_error():
    s = '''\
token A 'a'
%
<a> ::= A
%
Python
%%%
one
%%%
%
Java
%%%
two
%%%
'''
    spec, errors = parseSpec(s)
    assert any(isinstance(e, MultipleSemanticsError) for e in errors)


def test_multiple_semantic_sections_returns_first_section():
    s = '''\
token A 'a'
%
<a> ::= A
%
Python
%
Java
'''
    spec, errors = parseSpec(s)
    assert spec.semantics is not None
    assert spec.semantics.language == 'Python'


def test_missing_language_declaration_produces_error():
    s = "token A 'a'\n%\n<a> ::= A\n%\n"
    spec, errors = parseSpec(s)
    assert len(errors) > 0
    assert spec.semantics is None
```

- [ ] **Step 2: Run tests, confirm failures**

```
bin/test/units.bash src/plcc/spec/parseSpec_test.py -v
```

Expected: failures — `MultipleSemanticsError` not importable, `spec.semantics is None` assertions fail (it's still a list).

- [ ] **Step 3: Create `MultipleSemanticsError.py`**

Create `src/plcc/spec/MultipleSemanticsError.py`:

```python
from .SpecError import SpecError


class MultipleSemanticsError(SpecError):
    ...
```

- [ ] **Step 4: Update `Spec.py`**

Replace `src/plcc/spec/Spec.py`:

```python
from dataclasses import dataclass

from ..spec import lexical, semantics, syntax


@dataclass
class Spec:
    lexical: lexical.LexicalSpec
    syntax: syntax.SyntacticSpec
    semantics: semantics.SemanticSpec | None
```

- [ ] **Step 5: Update `parseSpec.py`**

Replace `src/plcc/spec/parseSpec.py`:

```python
from .MultipleSemanticsError import MultipleSemanticsError
from .Spec import Spec
from .semantics.MissingLanguageDeclarationError import MissingLanguageDeclarationError
from .split_rough import split_rough
from . import lexical, rough, semantics, syntax


def parseSpec(string, file=None, startLineNumber=1):
    rough_, rough_errors = rough.parseRough(string, file, startLineNumber)
    rough_ = iter(rough_)
    rough_lex, rough_syn, rough_sems = split_rough(rough_)
    lex_, lex_errors = lexical.parseLexicalSpec(rough_lex)
    syn_, syn_errors = syntax.parse_syntactic_spec(rough_syn)

    sem_errors = []
    sem_ = None
    if len(rough_sems) > 1:
        second_divider = rough_sems[1][0]
        sem_errors.append(MultipleSemanticsError(line=second_divider.line, column=1))
    if rough_sems:
        try:
            sem_ = semantics.parse_semantic_spec(rough_sems[0])
        except MissingLanguageDeclarationError as e:
            sem_errors.append(e)

    return (
        Spec(lexical=lex_, syntax=syn_, semantics=sem_),
        rough_errors + lex_errors + syn_errors + sem_errors,
    )
```

- [ ] **Step 6: Update `plcc_spec_cli_test.py`**

In `src/plcc/spec/plcc_spec_cli_test.py`, replace `test_outputs_spec_json`:

```python
def test_outputs_spec_json(capsys, fs):
    fs.create_file('/trivial.plcc', contents="""\
token NUM '\\d+'
%
<program> ::= NUM
%
PlantUML
""")
    run_main(['/trivial.plcc'])
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert 'lexical' in data
    assert 'syntax' in data
    assert 'semantics' in data
    assert data['semantics'] is not None
    assert data['semantics']['language'] == 'PlantUML'
```

- [ ] **Step 7: Run all unit tests, confirm they pass**

```
bin/test/units.bash -v
```

Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add src/plcc/spec/MultipleSemanticsError.py \
        src/plcc/spec/Spec.py \
        src/plcc/spec/parseSpec.py \
        src/plcc/spec/parseSpec_test.py \
        src/plcc/spec/plcc_spec_cli_test.py
git commit -m "feat(095): enforce single semantic section; Spec.semantics is now SemanticSpec | None"
```

---

## Task 3: JSON schema and model builder

Updates `spec.schema.json` (semantics → nullable object, no tool), `model.schema.json` (remove tool from semantic_sections items), `build_model.py` (handle nullable semantics), and all affected test fixtures.

**Files:**
- Modify: `src/plcc/schemas/spec.schema.json`
- Modify: `src/plcc/schemas/model.schema.json`
- Modify: `src/plcc/model/build_model.py`
- Test: `src/plcc/model/build_model_test.py`
- Test: `src/plcc/lang/ext/python/emit_test.py`
- Test: `src/plcc/lang/ext/java/emit_test.py`

**Interfaces:**
- Consumes: `spec['semantics']` — now `null | {language, codeFragmentList}` (from Task 2)
- Produces: `model['semantic_sections']` — array of `{language, fragments}`, no tool

- [ ] **Step 1: Update `build_model_test.py` fixture and assertion**

In `src/plcc/model/build_model_test.py`, replace `_TRIVIAL_SPEC` and `test_semantic_sections_present`:

```python
_TRIVIAL_SPEC = {
    "lexical": {
        "ruleList": [
            {
                "name": "NUM",
                "pattern": "\\d+",
                "isSkip": False,
                "line": {"string": "token NUM '\\d+'", "number": 1, "file": None}
            }
        ]
    },
    "syntax": {
        "rules": [
            {
                "line": {"string": "<Program> ::= NUM", "number": 3, "file": None},
                "lhs": {"name": "Program", "isTerminal": False, "altName": None, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "NUM", "isTerminal": True, "isCapturing": True}
                ]
            }
        ]
    },
    "semantics": {"language": "PlantUML", "codeFragmentList": []}
}
```

```python
def test_semantic_sections_present():
    model = build_model(_TRIVIAL_SPEC)
    sections = model['semantic_sections']
    assert len(sections) == 1
    assert sections[0]['language'] == 'plantuml'
    assert 'tool' not in sections[0]
```

- [ ] **Step 2: Run failing test**

```
bin/test/units.bash src/plcc/model/build_model_test.py::test_semantic_sections_present -v
```

Expected: FAIL — `build_model` still reads `spec.get('semantics', [])` as list.

- [ ] **Step 3: Update `build_model.py`**

In `src/plcc/model/build_model.py`, replace `_build_semantic_sections`:

```python
def _build_semantic_sections(spec, known_class_names):
    sem = spec.get('semantics')
    if not sem:
        return []
    fragments = [
        _build_fragment(frag, known_class_names)
        for frag in sem.get('codeFragmentList', [])
    ]
    return [{'language': sem['language'].lower(), 'fragments': fragments}]
```

- [ ] **Step 4: Run model tests, confirm they pass**

```
bin/test/units.bash src/plcc/model/build_model_test.py -v
```

Expected: all pass.

- [ ] **Step 5: Remove `tool` from emitter test fixtures**

In `src/plcc/lang/ext/python/emit_test.py`, in `_arith_model()`, remove `"tool": "calculate"` from the semantic section:

```python
"semantic_sections": [
    {
        "language": "Python",
        "fragments": [
            {"class_name": "Program", "kind": "body", "body": "def _run(self):\n    return self.expr.eval()"},
            {"class_name": "AddRest", "kind": "body", "body": "def eval(self, acc):\n    return self.rest.eval(acc + self.term.eval())"},
            {"class_name": "NilRest", "kind": "body", "body": "def eval(self, acc):\n    return acc"},
            {"class_name": "Term", "kind": "body", "body": "def eval(self):\n    return int(self.num.lexeme)"},
            {"class_name": "Expr", "kind": "body", "body": "def eval(self):\n    return self.rest.eval(self.term.eval())"},
        ]
    }
]
```

In `src/plcc/lang/ext/java/emit_test.py`, in `_trivial_model()`, remove `"tool": "Java"`:

```python
"semantic_sections": [
    {
        "language": "Java",
        "fragments": [
            {"class_name": "Program", "kind": "body",
             "body": "    public void _run() {\n        System.out.println(expr.toString());\n    }"},
        ]
    }
]
```

- [ ] **Step 6: Update `spec.schema.json`**

Replace `src/plcc/schemas/spec.schema.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Spec",
  "description": "Output of plcc-spec: a parsed PLCC grammar.",
  "type": "object",
  "required": ["lexical", "syntax", "semantics"],
  "properties": {
    "lexical": {
      "type": "object",
      "required": ["ruleList"],
      "properties": {
        "ruleList": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name", "pattern", "isSkip"],
            "properties": {
              "name":    { "type": "string" },
              "pattern": { "type": "string" },
              "isSkip":  { "type": "boolean" }
            }
          }
        }
      }
    },
    "syntax": {
      "type": "object",
      "required": ["rules"],
      "properties": {
        "rules": { "type": "array" }
      }
    },
    "semantics": {
      "oneOf": [
        {
          "type": "object",
          "required": ["language"],
          "properties": {
            "language": { "type": "string" }
          }
        },
        { "type": "null" }
      ]
    }
  }
}
```

- [ ] **Step 7: Update `model.schema.json`**

In `src/plcc/schemas/model.schema.json`, replace the `semantic_sections` items definition (remove `tool` from `required` and `properties`):

```json
"semantic_sections": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["language", "fragments"],
    "properties": {
      "language":    { "type": "string" },
      "fragments": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["class_name", "kind", "body"],
          "properties": {
            "class_name": { "type": "string" },
            "kind": {
              "type": "string",
              "enum": ["top", "import", "class", "init", "body", "file"]
            },
            "body": { "type": "string" }
          }
        }
      }
    }
  }
}
```

- [ ] **Step 8: Run all unit tests, confirm they pass**

```
bin/test/units.bash -v
```

Expected: all pass.

- [ ] **Step 9: Commit**

```bash
git add src/plcc/schemas/spec.schema.json \
        src/plcc/schemas/model.schema.json \
        src/plcc/model/build_model.py \
        src/plcc/model/build_model_test.py \
        src/plcc/lang/ext/python/emit_test.py \
        src/plcc/lang/ext/java/emit_test.py
git commit -m "feat(095): update spec/model schemas and build_model — semantics is nullable object, no tool"
```

---

## Task 4: Update `plcc-make`

Removes `validate_tool_name`, uses `section['language']` as build output directory, handles nullable semantics.

**Files:**
- Modify: `src/plcc/cmd/make.py`
- Test: `src/plcc/cmd/make_test.py`

**Interfaces:**
- Consumes: `spec_data['semantics']` — `null | {language, ...}` (from Task 3)
- Produces: output in `build/<language>/` (e.g., `build/Python`)

- [ ] **Step 1: Update `make_test.py`**

In `src/plcc/cmd/make_test.py`:

Change the import from:
```python
from .make import main as run_main, validate_tool_name, _report_ll1_failure
```
to:
```python
from .make import main as run_main, _report_ll1_failure
```

Delete the three `validate_tool_name` tests:
- `test_validate_tool_name_accepts_valid`
- `test_validate_tool_name_rejects_path_traversal`
- `test_validate_tool_name_rejects_empty`

- [ ] **Step 2: Run make tests, confirm they pass**

```
bin/test/units.bash src/plcc/cmd/make_test.py -v
```

Expected: all pass (the deleted tests were the only ones importing the deleted function).

- [ ] **Step 3: Update `make.py` — remove `validate_tool_name`, use language as dir**

In `src/plcc/cmd/make.py`:

1. Delete `_TOOL_NAME_RE` and `validate_tool_name`.

2. Replace the `tool_stages` line and `_REQUIRED` dict (around line 136):

```python
sem = spec_data.get('semantics')
lang_stage = {sem['language']} if sem else set()

_REQUIRED = {
    'scan':  {'scan'},
    'parse': {'scan', 'parse'},
    'model': {'scan', 'model'},
    'all':   {'scan', 'parse', 'model'} | lang_stage,
}
```

3. Replace the emit loop (the `if through == 'all':` block that iterates `spec_data.get('semantics', [])`):

```python
if through == 'all':
    section = spec_data.get('semantics')
    if section:
        lang = section['language']
        output_dir = str(build_dir / lang)
        os.makedirs(output_dir, exist_ok=True)
        verbose.emit(Events.PHASE, message=f"emit {lang}")
        _run_or_die(
            ['plcc-lang-emit', f'--target={lang}', f'--output={output_dir}'] + child_flags,
            stdin_file=model_json,
            verbose=verbose,
        )
        verbose.emit(Events.PHASE, message=f"build {lang}")
        _run_or_die(
            ['plcc-lang-build', f'--target={lang}', f'--output={output_dir}'] + child_flags,
            verbose=verbose,
        )
```

- [ ] **Step 4: Run all unit tests, confirm they pass**

```
bin/test/units.bash -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
git commit -m "feat(095): plcc-make uses language name as output dir, removes validate_tool_name"
```

---

## Task 5: Update `plcc-rep` and `print_banner`

Removes `--tool` flag from `plcc-rep`, simplifies language resolution to read from nullable `spec['semantics']`, updates `print_banner` to accept only `language`.

**Files:**
- Modify: `src/plcc/cmd/rep.py`
- Modify: `src/plcc/cmd/output.py`
- Test: `src/plcc/cmd/rep_test.py`

**Interfaces:**
- Consumes: `spec['semantics']` — `null | {language}` (from Task 3)

- [ ] **Step 1: Update `rep_test.py` fixtures and assertions**

In `src/plcc/cmd/rep_test.py`:

1. Replace all occurrences of `{"semantics": [{"tool": "calc", "language": "python"}]}` with `{"semantics": {"language": "Python"}}`.

2. Replace `_rep_module.main(["--spec=grammar.plcc", "--tool=calc"])` with `_rep_module.main(["--spec=grammar.plcc"])`.

3. Replace `_rep_module.main(["--tool=calc", "--banner"])` with `_rep_module.main(["--banner"])` (two occurrences in `test_rep_main_banner_prints_version_to_stderr` and `test_rep_main_banner_prints_grammar_to_stderr`).

4. In `test_rep_main_banner_prints_running_line_to_stderr`, replace `_rep_module.main(["--tool=calc", "--banner"])` with `_rep_module.main(["--banner"])` and change the assertion from:
```python
assert "Running calc with python." in err
```
to:
```python
assert "Running Python." in err
```

- [ ] **Step 2: Run rep tests, confirm failures**

```
bin/test/units.bash src/plcc/cmd/rep_test.py -v
```

Expected: failures around `--tool` arg and banner text.

- [ ] **Step 3: Update `output.py`**

Replace `src/plcc/cmd/output.py`:

```python
import sys


def print_user_error(message):
    print(message, flush=True)


def print_banner(version, grammar_path, language=None):
    print(f"plcc-ng {version}", file=sys.stderr, flush=True)
    print(f"spec: {grammar_path}", file=sys.stderr, flush=True)
    if language is not None:
        print(f"Running {language}.", file=sys.stderr, flush=True)
```

- [ ] **Step 4: Update `rep.py`**

In `src/plcc/cmd/rep.py`:

1. Remove `--tool=NAME` from the docstring `__doc__`.

2. Delete `tool_name = args['--tool']` from `main()`.

3. Replace the `_resolve_tool` call and the `tool_dir` / `tool_name` / `language` variables with:

```python
language = _resolve_language(spec)
if banner:
    print_banner(
        get_version(),
        os.path.abspath(read_spec('build')),
        language=language,
    )
output_dir = os.path.join('build', language)

interpreter = subprocess.Popen(
    ['plcc-lang-run', f'--target={language}', f'--output={output_dir}'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=None,
)
```

4. Replace `_resolve_tool` with `_resolve_language`:

```python
def _resolve_language(spec):
    section = spec.get('semantics')
    if not section:
        print("plcc-rep: no semantic section found in spec.", file=sys.stderr)
        sys.exit(1)
    return section['language']
```

- [ ] **Step 5: Run all unit tests, confirm they pass**

```
bin/test/units.bash -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/rep.py src/plcc/cmd/output.py src/plcc/cmd/rep_test.py
git commit -m "feat(095): plcc-rep removes --tool flag, reads language from spec semantics"
```
