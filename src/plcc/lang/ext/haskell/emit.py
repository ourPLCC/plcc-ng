"""plcc-haskell-emit
    Emit a Haskell interpreter from model JSON.

Usage:
    plcc-haskell-emit --output=DIR [-v ...] [options]

Options:
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
"""

import enum
import json
import shutil
import sys
from pathlib import Path

from plcc.cli import parse_args

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from .validate import validate_fragments

__doc__ = __doc__ + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-haskell-emit", Events, args)
    output_dir = Path(args['--output'])
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')
    model = json.load(sys.stdin)
    emit(model, output_dir)
    verbose.emit(Events.FINISHED, message='done')


def emit(model, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    modules = _group_modules(model['classes'])
    _write_cabal(modules, output_dir)
    _copy_token(output_dir)
    section = _find_haskell_section(model)
    all_frags = section.get('fragments', []) if section else []
    fragments_by_class = _group_fragments(all_frags)
    validate_fragments(all_frags, model['classes'])
    start_module = model['start'][0].upper() + model['start'][1:]
    for module_name, module_info in modules.items():
        is_start = (module_name == start_module)
        _write_module(module_name, module_info, fragments_by_class, output_dir, is_start)
    for frag in all_frags:
        if frag['kind'] == 'file':
            (output_dir / f'{frag["class_name"]}.hs').write_text(frag['body'])
    _write_main(start_module, modules, output_dir)


def _write_main(start_module, modules, output_dir):
    import_lines = '\n'.join(f'import {name}' for name in sorted(modules))
    content = (
        '{-# LANGUAGE OverloadedStrings, ScopedTypeVariables #-}\n'
        'module Main where\n'
        '\n'
        'import Control.Exception (Exception, SomeException, catch, evaluate)\n'
        'import Data.Aeson (eitherDecode, encode, object, (.=))\n'
        'import qualified Data.ByteString.Lazy.Char8 as BL\n'
        'import System.IO (hSetBuffering, stdout, BufferMode (..))\n'
        f'{import_lines}\n'
        '\n'
        'newtype LanguageError = LanguageError String deriving Show\n'
        'instance Exception LanguageError\n'
        '\n'
        'main :: IO ()\n'
        'main = do\n'
        '    hSetBuffering stdout LineBuffering\n'
        '    BL.putStrLn $ encode $ object ["kind" .= ("ready" :: String)]\n'
        '    contents <- getContents\n'
        '    mapM_ handle (filter (not . null) (lines contents))\n'
        '  where\n'
        '    handle line = case eitherDecode (BL.pack line) of\n'
        '        Left err ->\n'
        '            BL.putStrLn $ encode $ object\n'
        '                [ "kind" .= ("specification_error" :: String)\n'
        '                , "type" .= ("ParseError" :: String)\n'
        '                , "message" .= err\n'
        '                ]\n'
        '        Right tree -> do\n'
        f'            let val = _run (tree :: {start_module})\n'
        '            result <- (evaluate val >>= \\v ->\n'
        '                return (encode $ object\n'
        '                    [ "kind" .= ("result" :: String)\n'
        '                    , "value" .= v\n'
        '                    ]))\n'
        '                `catch` (\\(LanguageError msg) ->\n'
        '                    return (encode $ object\n'
        '                        [ "kind" .= ("error" :: String)\n'
        '                        , "type" .= ("LanguageError" :: String)\n'
        '                        , "message" .= msg\n'
        '                        ]))\n'
        '                `catch` (\\(e :: SomeException) ->\n'
        '                    return (encode $ object\n'
        '                        [ "kind" .= ("specification_error" :: String)\n'
        '                        , "type" .= show e\n'
        '                        , "message" .= show e\n'
        '                        ]))\n'
        '            BL.putStrLn result\n'
    )
    (output_dir / 'Main.hs').write_text(content)


def _group_modules(classes):
    """Return dict mapping module_name -> module_info.

    module_info for an abstract rule:
        {'kind': 'abstract', 'abstract': cls_dict, 'concretes': [cls_dict, ...]}
    module_info for a lone concrete class (no abstract parent):
        {'kind': 'concrete', 'cls': cls_dict}
    """
    modules = {}
    for cls in classes:
        if cls['abstract']:
            modules[cls['name']] = {
                'kind': 'abstract',
                'abstract': cls,
                'concretes': [],
            }
    for cls in classes:
        if cls['abstract']:
            continue
        parent = cls['extends']
        if parent is not None and parent in modules:
            modules[parent]['concretes'].append(cls)
        else:
            modules[cls['name']] = {'kind': 'concrete', 'cls': cls}
    return modules


def _write_cabal(modules, output_dir):
    module_list = ', '.join(['Token'] + sorted(modules))
    content = (
        'cabal-version: 3.0\n'
        'name:          interpreter\n'
        'version:       0.1.0.0\n'
        '\n'
        'executable interpreter\n'
        '  main-is:          Main.hs\n'
        f'  other-modules:    {module_list}\n'
        '  build-depends:    base, aeson, bytestring, text\n'
        '  default-language: Haskell2010\n'
        '  hs-source-dirs:   .\n'
    )
    (output_dir / 'interpreter.cabal').write_text(content)


def _copy_token(output_dir):
    src = Path(__file__).parent / 'runtime' / 'Token.hs'
    shutil.copy(src, output_dir / 'Token.hs')


def _write_module(module_name, module_info, fragments_by_class, output_dir, is_start=False):
    frags = fragments_by_class.get(module_name, [])
    content = _render_module(module_name, module_info, fragments_by_class)
    if is_start:
        body_frags = [f for f in frags if f['kind'] == 'body']
        user_has_run = any('_run' in f['body'] for f in body_frags)
        if not user_has_run:
            content = content.rstrip('\n') + f'\n\n_run :: {module_name} -> String\n_run = show\n'
    (output_dir / f'{module_name}.hs').write_text(content)


def _render_module(module_name, module_info, fragments_by_class):
    frags = fragments_by_class.get(module_name, [])
    top_frags = [f for f in frags if f['kind'] == 'top']
    import_frags = [f for f in frags if f['kind'] == 'import']
    body_frags = [f for f in frags if f['kind'] == 'body']

    lines = []
    lines.append('{-# LANGUAGE DuplicateRecordFields, OverloadedStrings #-}')
    for f in top_frags:
        lines.append(f['body'])
    lines.append(f'module {module_name} where')
    lines.append('')
    lines.append('import Data.Aeson (FromJSON (..), Value (..), withObject, (.:))')
    lines.append('import Data.List (sort)')
    lines.append('import Token')
    for imp in _collect_imports(module_name, module_info):
        lines.append(f'import {imp}')
    for f in import_frags:
        lines.append(f['body'])
    lines.append('')
    lines.extend(_render_data(module_name, module_info))
    lines.append('')
    lines.extend(_render_from_json(module_name, module_info))
    lines.append('')
    for f in body_frags:
        lines.append(f['body'])
    return '\n'.join(lines) + '\n'


def _collect_imports(module_name, module_info):
    """Return sorted list of module names to import (excluding Token and self)."""
    concretes = (module_info['concretes'] if module_info['kind'] == 'abstract'
                 else [module_info['cls']])
    imports = set()
    for cls in concretes:
        for field in cls['fields']:
            ft = field['type']
            if ft != 'Token' and ft != module_name:
                imports.add(ft)
    return sorted(imports)


def _render_data(module_name, module_info):
    lines = []
    if module_info['kind'] == 'abstract':
        concretes = module_info['concretes']
        lines.append(f'data {module_name}')
        for i, cls in enumerate(concretes):
            prefix = '    = ' if i == 0 else '    | '
            fields_str = _render_record_fields(cls['fields'])
            if fields_str:
                lines.append(f'{prefix}{cls["name"]} {{ {fields_str} }}')
            else:
                lines.append(f'{prefix}{cls["name"]}')
    else:
        cls = module_info['cls']
        fields_str = _render_record_fields(cls['fields'])
        if fields_str:
            lines.append(f'data {module_name} = {cls["name"]} {{ {fields_str} }}')
        else:
            lines.append(f'data {module_name} = {cls["name"]}')
    lines.append('    deriving (Show, Eq)')
    return lines


def _render_from_json(module_name, module_info):
    if module_info['kind'] == 'abstract':
        concretes = module_info['concretes']
    else:
        concretes = [module_info['cls']]

    lines = [
        f'instance FromJSON {module_name} where',
        f'    parseJSON = withObject "{module_name}" $ \\o -> do',
        f'        rule        <- o .: "rule"',
        f'        rawChildren <- o .: "children"',
        f'        let children = parseChildren rawChildren',
        f'            fns      = sort (map fst children)',
        f'        case (rule :: String) of',
    ]
    # Group by rule_name so same-named alts share an outer case arm
    seen = {}
    for cls in concretes:
        seen.setdefault(cls['rule_name'], []).append(cls)
    for rule_name, group in seen.items():
        lines.append(f'            "{rule_name}" -> case fns of')
        for cls in group:
            field_names = sorted(f['name'] for f in cls['fields'])
            fns_literal = '[' + ', '.join(f'"{n}"' for n in field_names) + ']'
            if cls['fields']:
                first = cls['fields'][0]['name']
                rest = cls['fields'][1:]
                expr = f'{cls["name"]} <$> parseField children "{first}"'
                for f in rest:
                    expr += f'\n                              <*> parseField children "{f["name"]}"'
            else:
                expr = f'return {cls["name"]}'
            lines.append(f'                {fns_literal} ->')
            lines.append(f'                    {expr}')
        lines.append(f'                fns -> fail ("unknown variant of {rule_name}: " ++ show fns)')
    lines.append(f'            r -> fail ("unexpected rule: " ++ r)')
    return lines


def _render_record_fields(fields):
    parts = [f'{f["name"]} :: {_hs_type(f)}' for f in fields]
    return ', '.join(parts)


def _hs_type(field):
    base = field['type']
    return f'[{base}]' if field['is_list'] else base


def _find_haskell_section(model):
    for s in model.get('semantic_sections', []):
        if s.get('language', '').lower() == 'haskell':
            return s
    return None


def _group_fragments(fragments):
    groups = {}
    for frag in fragments:
        groups.setdefault(frag['class_name'], []).append(frag)
    return groups
