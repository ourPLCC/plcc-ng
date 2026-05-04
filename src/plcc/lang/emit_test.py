import subprocess
import json
import pytest
import docopt

from .emit import main as run_main, resolve_emit_command


def test_no_args_prints_usage():
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_resolve_plantuml():
    cmd = resolve_emit_command('PlantUML')
    assert cmd == 'plcc-plantuml-emit'


def test_resolve_lowercases_lang():
    cmd = resolve_emit_command('Java')
    assert cmd == 'plcc-java-emit'


def test_missing_plugin_exits_nonzero(tmp_path, monkeypatch):
    import io
    monkeypatch.setattr('sys.stdin', io.StringIO('{}'))
    with pytest.raises(SystemExit) as exc:
        run_main([f'--target=NoSuchLang9999', f'--output={tmp_path}'])
    assert exc.value.code != 0
