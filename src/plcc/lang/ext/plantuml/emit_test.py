import json
import os
import pytest

from .emit import main as run_main


_TRIVIAL_MODEL = json.dumps({
    'start': 'program',
    'classes': [
        {'name': 'Program', 'extends': None,
         'fields': [{'name': 'num', 'type': 'Token'}],
         'methods': []}
    ],
    'semantic_sections': [{'tool': 'diagram', 'language': 'PlantUML'}]
})


def test_no_args_prints_usage():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_creates_puml_file(tmp_path, monkeypatch):
    import io
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    run_main([f'--output={tmp_path}'])
    puml_files = list(tmp_path.glob('*.puml'))
    assert len(puml_files) == 1


def test_puml_contains_class_name(tmp_path, monkeypatch):
    import io
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    run_main([f'--output={tmp_path}'])
    content = list(tmp_path.glob('*.puml'))[0].read_text()
    assert 'Program' in content


def test_puml_contains_field(tmp_path, monkeypatch):
    import io
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    run_main([f'--output={tmp_path}'])
    content = list(tmp_path.glob('*.puml'))[0].read_text()
    assert 'num' in content


def test_exits_zero_on_success(tmp_path, monkeypatch):
    import io
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    # Should not raise SystemExit
    run_main([f'--output={tmp_path}'])
