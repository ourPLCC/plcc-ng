"""Transform spec JSON into a language-neutral code model."""


def build_model(spec):
    classes = _build_classes(spec)
    known_class_names = {c['name'] for c in classes}
    semantic_sections = _build_semantic_sections(spec, known_class_names)
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
    rules = spec.get('syntax', {}).get('rules', [])

    groups = {}
    order = []
    for rule in rules:
        name = rule['lhs']['name']
        if name not in groups:
            groups[name] = []
            order.append(name)
        groups[name].append(rule)

    classes = []
    for nt_name in order:
        nt_rules = groups[nt_name]
        class_name = nt_name[:1].upper() + nt_name[1:]
        is_abstract = any(r['lhs'].get('altName') for r in nt_rules)

        if is_abstract:
            classes.append({
                'name': class_name,
                'abstract': True,
                'extends': None,
                'fields': [],
                'rule_name': nt_name,
            })
            for rule in nt_rules:
                alt_name = rule['lhs']['altName']
                fields = _extract_fields_for_rule(rule)
                classes.append({
                    'name': alt_name,
                    'abstract': False,
                    'extends': class_name,
                    'fields': fields,
                    'rule_name': alt_name,
                })
        else:
            rule = nt_rules[0]
            fields = _extract_fields_for_rule(rule)
            classes.append({
                'name': class_name,
                'abstract': False,
                'extends': None,
                'fields': fields,
                'rule_name': nt_name,
            })

    return classes


def _extract_fields_for_rule(rule):
    rhs = rule.get('rhsSymbolList', [])
    if 'separator' in rule:
        return _extract_arbno_fields(rhs)
    return _extract_fields(rhs)


def _extract_arbno_fields(rhs_symbol_list):
    fields = []
    for symbol in rhs_symbol_list:
        if not symbol.get('isCapturing'):
            continue
        alt = symbol.get('altName')
        name = symbol.get('name', '')
        field_name = (alt if alt else name).lower() + 'List'
        if symbol.get('isTerminal'):
            field_type = 'Token'
        else:
            n = symbol.get('name', 'Object')
            field_type = n[:1].upper() + n[1:]
        fields.append({'name': field_name, 'type': field_type, 'is_list': True})
    return fields


def _extract_fields(rhs_symbol_list):
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
        fields.append({'name': field_name, 'type': field_type, 'is_list': False})
    return fields


def _build_semantic_sections(spec, known_class_names):
    sections = []
    for s in spec.get('semantics', []):
        fragments = [
            _build_fragment(frag, known_class_names)
            for frag in s.get('codeFragmentList', [])
        ]
        sections.append({
            'language': s['language'].lower(),
            'tool': s['tool'],
            'entry_point': s.get('entry_point'),
            'fragments': fragments,
        })
    return sections


def _build_fragment(frag, known_class_names):
    locator = frag.get('targetLocator') or {}
    class_name = locator.get('className', '')
    modifier = locator.get('modifier')
    kind = _compute_kind(modifier, class_name, known_class_names)
    body = _extract_body((frag.get('block') or {}).get('lines', []))
    return {
        'class_name': class_name,
        'kind': kind,
        'body': body,
    }


def _compute_kind(modifier, class_name, known_class_names):
    if modifier in ('top', 'import', 'class', 'init'):
        return modifier
    if class_name in known_class_names:
        return 'body'
    return 'file'


def _extract_body(lines):
    strings = [line['string'].rstrip('\n') for line in lines]
    if strings and strings[0].rstrip() == '%%%':
        strings = strings[1:]
    if strings and strings[-1].rstrip() == '%%%':
        strings = strings[:-1]
    return '\n'.join(strings)
