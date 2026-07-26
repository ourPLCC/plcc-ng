import sys


def check_reserved_field_names(classes, language, reserved_words):
    """Return one message per field whose name collides with reserved_words."""
    errors = []
    for cls in classes:
        for field in cls['fields']:
            name = field['name']
            if name in reserved_words:
                errors.append(
                    f"class '{cls['name']}' field '{name}' collides with "
                    f"the {language} reserved word '{name}' — give the "
                    f"capture an explicit ':fieldname'"
                )
    return errors


def reject_reserved_field_names(classes, language, reserved_words, stage):
    """Print each collision to stderr and exit(1) if any are found."""
    errors = check_reserved_field_names(classes, language, reserved_words)
    if errors:
        for error in errors:
            print(f"{stage}: error: {error}", file=sys.stderr)
        sys.exit(1)
