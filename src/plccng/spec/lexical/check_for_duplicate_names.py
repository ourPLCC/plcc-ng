from .DuplicateName import DuplicateName


def check_for_duplicate_names(rulesOrLines):
    errors = []
    seen = set()
    for thing in rulesOrLines:
        if thing.name in seen:
            errors.append(DuplicateName(thing))
        else:
            seen.add(thing.name)
    return errors
