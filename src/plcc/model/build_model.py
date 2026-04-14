"""Transform spec JSON into a language-neutral code model."""


def build_model(spec):
    """
    Given a parsed spec dict (output of plcc-spec deserialized),
    return a model dict ready for JSON serialization.
    """
    classes = _build_classes(spec)
    semantic_sections = _build_semantic_sections(spec)
    start = _find_start(spec)
    return {
        'start': start,
        'classes': classes,
        'semantic_sections': semantic_sections,
    }


def _find_start(spec):
    rules = spec.get('syntax', {}).get('rules', [])
    if not rules:
        return None
    return rules[0]['lhs']['name']


def _build_classes(spec):
    classes = []
    for rule in spec.get('syntax', {}).get('rules', []):
        lhs_name = rule['lhs']['name']
        # Use [:1].upper() + [1:] rather than capitalize() to preserve camelCase names
        # (e.g. 'addExpr' -> 'AddExpr', not 'Addexpr').
        class_name = lhs_name[:1].upper() + lhs_name[1:]
        fields = _extract_fields(rule.get('rhsSymbolList', []))
        classes.append({
            'name': class_name,
            'extends': None,
            'fields': fields,
            'methods': [],
        })
    return classes


def _extract_fields(rhs_symbol_list):
    # rhsSymbolList symbols are serialized by plcc-spec via dataclasses.asdict().
    # The real shape uses isCapturing/isTerminal flags.
    # Capturing symbols also have an optional altName field.
    fields = []
    for symbol in rhs_symbol_list:
        if not symbol.get('isCapturing'):
            continue
        field_name = symbol.get('altName') or symbol.get('name', '').lower()
        if symbol.get('isTerminal'):
            field_type = 'Token'
        else:
            name = symbol.get('name', 'Object')
            field_type = name[:1].upper() + name[1:]
        fields.append({'name': field_name, 'type': field_type})
    return fields


def _build_semantic_sections(spec):
    return [
        {'tool': s['tool'], 'language': s['language']}
        for s in spec.get('semantics', [])
    ]
