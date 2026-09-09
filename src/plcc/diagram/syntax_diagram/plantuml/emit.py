import enum
import json
import sys

from plcc.cli import parse_args

from ....verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-syntax-plantuml-emit
    Emit a PlantUML EBNF diagram from spec JSON.

Usage:
    plcc-diagram-syntax-plantuml-emit [-v ...] [options]

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    VerboseContext.from_args("plcc-diagram-syntax-plantuml-emit", Events, args)
    spec = json.load(sys.stdin)
    sys.stdout.write(build_ebnf(spec))


def build_ebnf(spec):
    rules = spec.get('syntax', {}).get('rules', [])
    groups = {}
    order = []
    for rule in rules:
        name = rule['lhs']['name']
        if name not in groups:
            groups[name] = []
            order.append(name)
        groups[name].append(rule)
    lines = ['@startebnf']
    for name in order:
        rhs = _render_alternatives(groups[name])
        lines.append(f'{name} = {rhs} ;')
    lines.append('@endebnf')
    return '\n'.join(lines) + '\n'


def _render_alternatives(rules):
    # PlantUML EBNF has no notation for an empty alternative, so an empty
    # right-hand side cannot be emitted as the empty string: `A = 'X' | ;` is
    # a syntax error and renders as an error image rather than a diagram.
    # Express the same language with optionality instead.
    rendered = [(r, _render_rule(r)) for r in rules]
    nonempty = [(r, text) for r, text in rendered if text]
    if not nonempty:
        # Every alternative is empty, so the rule matches only the empty
        # string. An empty terminal draws as an empty box, which is the
        # picture we want.
        return "''"
    texts = [text for _, text in nonempty]
    if len(nonempty) == len(rendered):
        return ' | '.join(texts)
    if len(nonempty) == 1 and 'separator' in nonempty[0][0]:
        # The sole non-empty alternative is a `{ ... }` repetition, which
        # already matches zero occurrences -- wrapping it in `[ ... ]` would
        # just be a bypass around a bypass.
        return texts[0]
    return '[ ' + ' | '.join(texts) + ' ]'


def _render_rule(rule):
    if 'separator' in rule:
        return _render_repeating(rule)
    return _render_standard(rule)


def _render_standard(rule):
    return ', '.join(_render_symbol(s) for s in rule['rhsSymbolList'])


def _render_repeating(rule):
    body = ', '.join(_render_symbol(s) for s in rule['rhsSymbolList'])
    sep = rule['separator']
    if sep:
        return f'{{ {body}, \'{sep["name"]}\' }}'
    return f'{{ {body} }}'


def _render_symbol(sym):
    if sym['isTerminal']:
        return f'\'{sym["name"]}\''
    return sym['name']
