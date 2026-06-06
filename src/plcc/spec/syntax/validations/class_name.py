import re

CLASS_NAME_RE = re.compile(r"^[A-Z][a-zA-Z0-9_]*$")


def is_valid_class_name(name: str) -> bool:
    return bool(CLASS_NAME_RE.match(name))
