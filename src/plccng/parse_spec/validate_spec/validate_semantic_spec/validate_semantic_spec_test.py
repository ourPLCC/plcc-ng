from ...errors import InvalidClassNameError, UndefinedBlockError, UndefinedTargetLocatorError
from .validate_semantic_spec import validate_semantic_spec

from ...parse_spec import parse_semantic_spec
from ...parse_rough import parse_rough


def test_no_code_fragments_no_errors():
    spec = parse('%')
    errors = validate_semantic_spec(spec)
    assert len(errors) == 0

def test_valid_and_invalid_names():
    spec = parse('''\
%
Valid
%%%
%%%
invalid
%%%
%%%
''')
    errors = validate_semantic_spec(spec)
    assert isinstance(errors[0], InvalidClassNameError)

def test_invalid_undefined_target_locator():
    spec = parse('''\
%
%%%
%%%
''')
    errors = validate_semantic_spec(spec)
    assert isinstance(errors[0], UndefinedTargetLocatorError)

def test_invalid_block_and_target_locator_order():
    spec = parse('''\
%
%%%
%%%
Class
''')
    errors = validate_semantic_spec(spec)
    assert isinstance(errors[0], UndefinedTargetLocatorError)
    assert isinstance(errors[1], UndefinedBlockError)

def test_undefined_block_error_multiple_code_fragments():
    spec = parse('''\
%
Class
AnotherClass
%%%
%%%
''')
    errors = validate_semantic_spec(spec)
    assert isinstance(errors[0], UndefinedBlockError)

def test_undefined_block_error_single_code_fragment():
    spec = parse('''\
%
Class
''')
    errors = validate_semantic_spec(spec)
    assert isinstance(errors[0], UndefinedBlockError)

def test_valid_names_no_errors():
    assertValidClassNames(["Class","CLASS","C_lass_","C123","C", "ClaSs", "C_la55"])

def test_multiple_errors_all_counted():
    assertInvalidClassNames([
        "123StartsWithNumbers", "notuppercase", "InvalidChar`", "Invalid space",
        "White Space", "12MustStartUppercase", "startsLowerCase"])

def assertValidClassNames(names: list[str]):
    for name in names:
        assertValidClassName(name)

def assertValidClassName(name: str):
    spec = parse(f'''\
%
{name}
%%%
%%%
''')
    errors = validate_semantic_spec(spec)
    assert len(errors) == 0

def assertInvalidClassNames(names: list[str]):
    for name in names:
        assertInvalidClassName(name)

def assertInvalidClassName(name: str):
    spec = parse(f'''\
%
{name}
%%%
%%%
''')
    errors = validate_semantic_spec(spec)
    assert isinstance(errors[0], InvalidClassNameError)

def parse(string):
    rough = list(parse_rough.from_string(string))
    spec =  parse_semantic_spec(rough)
    return spec
