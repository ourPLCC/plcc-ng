import sys


def validate_fragments(fragments, classes):
    """Raise SystemExit if any fragment has an invalid class_name for Haskell.

    fragments: list of fragment dicts with 'class_name' and 'kind' keys.
    classes:   list of class dicts with 'name', 'abstract', and 'extends' keys.
    """
    modules = _build_modules(classes)
    concrete_to_abstract = _build_concrete_to_abstract(classes)

    for frag in fragments:
        class_name = frag['class_name']
        kind = frag['kind']

        if class_name in modules:
            continue

        if class_name in concrete_to_abstract:
            parent = concrete_to_abstract[class_name]
            print(
                f"plcc-haskell-emit: fragment tagged '{class_name}': "
                f"{class_name} is a concrete alternative of {parent}.\n"
                f"In Haskell, concrete alternatives are constructors inside "
                f"their abstract rule's module.\n"
                f"Use '{parent}' as the fragment class name instead.",
                file=sys.stderr,
            )
            sys.exit(1)

        if kind != 'file':
            valid = ', '.join(sorted(modules))
            print(
                f"plcc-haskell-emit: fragment tagged '{class_name}': "
                f"no Haskell module for '{class_name}'.\n"
                f"Valid module names are: {valid}",
                file=sys.stderr,
            )
            sys.exit(1)


def _build_modules(classes):
    """Return the set of valid Haskell module names.

    Includes abstract rules and lone concretes (concretes whose extends is
    not an abstract rule, including extends=None).
    """
    abstract_names = {cls['name'] for cls in classes if cls['abstract']}
    modules = set(abstract_names)
    for cls in classes:
        if not cls['abstract'] and cls['extends'] not in abstract_names:
            modules.add(cls['name'])
    return modules


def _build_concrete_to_abstract(classes):
    """Return dict mapping concrete-alternative names to their abstract parent name."""
    abstract_names = {cls['name'] for cls in classes if cls['abstract']}
    return {
        cls['name']: cls['extends']
        for cls in classes
        if not cls['abstract'] and cls['extends'] in abstract_names
    }
