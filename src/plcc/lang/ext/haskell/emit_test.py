import io
import json

import pytest

from .emit import main as run_main


def _run_emit(monkeypatch, tmp_path, model):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])


def _minimal_model():
    return {
        "start": "prog",
        "classes": [
            {
                "name": "Prog",
                "extends": None,
                "abstract": False,
                "rule_name": "prog",
                "fields": [{"name": "expr", "type": "Expr", "is_list": False}],
            },
            {
                "name": "Expr",
                "extends": None,
                "abstract": True,
                "rule_name": "expr",
                "fields": [],
            },
            {
                "name": "NumExpr",
                "extends": "Expr",
                "abstract": False,
                "rule_name": "expr",
                "fields": [{"name": "num", "type": "Token", "is_list": False}],
            },
        ],
        "semantic_sections": [],
    }


def test_emit_writes_cabal_file(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    assert (tmp_path / 'interpreter.cabal').exists()


def test_cabal_file_contains_executable(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'interpreter.cabal').read_text()
    assert 'executable interpreter' in text


def test_cabal_file_contains_aeson_dep(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'interpreter.cabal').read_text()
    assert 'aeson' in text


def test_cabal_file_lists_token_module(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'interpreter.cabal').read_text()
    assert 'Token' in text


def test_emit_copies_token_hs(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    assert (tmp_path / 'Token.hs').exists()


def test_token_hs_contains_token_module(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Token.hs').read_text()
    assert 'module Token' in text


def test_emit_writes_module_for_abstract_rule(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    assert (tmp_path / 'Expr.hs').exists()


def test_abstract_module_contains_data_declaration(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'data Expr' in text


def test_abstract_module_contains_concrete_constructor(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'NumExpr' in text


def test_concrete_constructor_has_token_field(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'num :: Token' in text


def test_emit_writes_module_for_lone_concrete(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    assert (tmp_path / 'Prog.hs').exists()


def test_lone_concrete_module_contains_data_declaration(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Prog.hs').read_text()
    assert 'data Prog' in text


def test_lone_concrete_field_uses_class_type(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Prog.hs').read_text()
    assert 'expr :: Expr' in text


def test_all_types_derive_show_and_eq(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    for path in [tmp_path / 'Expr.hs', tmp_path / 'Prog.hs']:
        text = path.read_text()
        assert 'deriving (Show, Eq)' in text


def test_abstract_module_has_from_json_instance(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'instance FromJSON Expr' in text


def test_from_json_matches_on_rule_name(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert '"expr"' in text


def test_from_json_matches_constructor_by_sorted_field_names(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert '["num"]' in text
    assert 'NumExpr' in text


def test_lone_concrete_has_from_json_instance(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Prog.hs').read_text()
    assert 'instance FromJSON Prog' in text


def test_from_json_uses_parse_field(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'parseField' in text


def test_from_json_parses_children_as_pairs(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'parseChildren' in text


def test_list_field_uses_bracket_type(monkeypatch, tmp_path):
    model = {
        "start": "stmts",
        "classes": [
            {
                "name": "Stmts",
                "extends": None,
                "abstract": False,
                "rule_name": "stmts",
                "fields": [{"name": "items", "type": "Token", "is_list": True}],
            }
        ],
        "semantic_sections": [],
    }
    _run_emit(monkeypatch, tmp_path, model)
    text = (tmp_path / 'Stmts.hs').read_text()
    assert 'items :: [Token]' in text


def _model_with_fragments(fragment_list):
    model = _minimal_model()
    model['semantic_sections'] = [{'language': 'haskell', 'fragments': fragment_list}]
    return model


def test_top_fragment_appears_before_module_declaration(monkeypatch, tmp_path):
    model = _model_with_fragments([
        {'class_name': 'Expr', 'kind': 'top', 'body': '{-# LANGUAGE OverloadedStrings #-}'}
    ])
    _run_emit(monkeypatch, tmp_path, model)
    text = (tmp_path / 'Expr.hs').read_text()
    top_pos = text.index('{-# LANGUAGE')
    module_pos = text.index('module Expr')
    assert top_pos < module_pos


def test_import_fragment_appears_after_generated_imports(monkeypatch, tmp_path):
    model = _model_with_fragments([
        {'class_name': 'Expr', 'kind': 'import', 'body': 'import Data.Map (Map)'}
    ])
    _run_emit(monkeypatch, tmp_path, model)
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'import Data.Map (Map)' in text
    token_pos = text.index('import Token')
    map_pos = text.index('import Data.Map (Map)')
    assert token_pos < map_pos


def test_body_fragment_appears_after_from_json(monkeypatch, tmp_path):
    model = _model_with_fragments([
        {'class_name': 'Expr', 'kind': 'body',
         'body': '_run :: Expr -> String\n_run (NumExpr t) = lexeme t'}
    ])
    _run_emit(monkeypatch, tmp_path, model)
    text = (tmp_path / 'Expr.hs').read_text()
    assert '_run :: Expr -> String' in text
    from_json_pos = text.index('instance FromJSON Expr')
    body_pos = text.index('_run :: Expr -> String')
    assert from_json_pos < body_pos


def test_file_fragment_replaces_entire_module(monkeypatch, tmp_path):
    model = _model_with_fragments([
        {'class_name': 'Expr', 'kind': 'file', 'body': '-- custom Expr module\nmodule Expr where\n'}
    ])
    _run_emit(monkeypatch, tmp_path, model)
    text = (tmp_path / 'Expr.hs').read_text()
    assert '-- custom Expr module' in text
    assert 'instance FromJSON Expr' not in text


def test_default_run_generated_when_start_has_no_body_fragment(monkeypatch, tmp_path):
    # _minimal_model() start is 'prog' → start module is 'Prog'
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Prog.hs').read_text()
    assert '_run :: Prog -> String' in text
    assert '_run = show' in text


def test_default_run_not_generated_when_user_provides_it(monkeypatch, tmp_path):
    model = _model_with_fragments([
        {'class_name': 'Prog', 'kind': 'body',
         'body': '_run :: Prog -> String\n_run (Prog e) = show e'}
    ])
    _run_emit(monkeypatch, tmp_path, model)
    text = (tmp_path / 'Prog.hs').read_text()
    # User's _run is present; default '_run = show' must not be added
    assert text.count('_run') >= 1
    assert '_run = show' not in text


def test_default_run_not_added_to_non_start_modules(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert '_run = show' not in text
