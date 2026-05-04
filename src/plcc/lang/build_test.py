import pytest
import docopt

from .build import main as run_main, resolve_build_command


def test_no_args_prints_usage():
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_resolve_build_command():
    cmd = resolve_build_command('Java')
    assert cmd == 'plcc-java-build'


def test_missing_build_command_exits_zero(tmp_path):
    # plcc-plantuml-build does not exist — should exit 0 silently
    try:
        run_main([f'--target=PlantUML', f'--output={tmp_path}'])
    except SystemExit as e:
        assert e.code == 0
