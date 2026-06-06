from .class_name import is_valid_class_name


def test_single_uppercase_letter_is_valid():
    assert is_valid_class_name("E")

def test_pascal_case_is_valid():
    assert is_valid_class_name("Expr")

def test_pascal_case_with_digits_is_valid():
    assert is_valid_class_name("ExprRest123")

def test_pascal_case_with_underscore_is_valid():
    assert is_valid_class_name("Expr_Rest")

def test_lowercase_is_invalid():
    assert not is_valid_class_name("expr")

def test_starts_with_underscore_is_invalid():
    assert not is_valid_class_name("_Expr")

def test_starts_with_digit_is_invalid():
    assert not is_valid_class_name("1Expr")

def test_contains_colon_is_invalid():
    assert not is_valid_class_name("E:name")

def test_empty_string_is_invalid():
    assert not is_valid_class_name("")
