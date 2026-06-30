import pytest
from unittest.mock import patch, MagicMock

from .diagram import main as run_main


def test_spec_file_not_found_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main([])
    assert exc.value.code != 0


def test_spec_file_not_found_prints_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main([])
    _, err = capsys.readouterr()
    assert "spec file not found" in err


def test_calls_plcc_spec(tmp_path, monkeypatch):
    spec = tmp_path / "spec.plcc"
    spec.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        m = MagicMock()
        m.returncode = 1
        m.stderr = b''
        m.stdout = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main([])

    assert calls[0][0] == 'plcc-spec'
    assert str(spec) in calls[0]


def test_calls_emit_build_run_in_order(tmp_path, monkeypatch):
    spec = tmp_path / "spec.plcc"
    spec.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        m.stdout = b'{}'
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main([])

    cmds = [c[0] for c in calls]
    assert cmds == ['plcc-spec', 'plcc-diagram-emit', 'plcc-diagram-build', 'plcc-diagram-run']


def test_emit_called_with_type_syntax(tmp_path, monkeypatch):
    spec = tmp_path / "spec.plcc"
    spec.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        m.stdout = b'{}'
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main([])

    emit_call = calls[1]
    assert '--type=syntax' in emit_call
    assert '--format=plantuml' in emit_call


def test_build_uses_syntax_paths(tmp_path, monkeypatch):
    spec = tmp_path / "spec.plcc"
    spec.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        m.stdout = b'{}'
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main([])

    build_call = calls[2]
    assert '--input=plcc-ng/diagram/syntax.puml' in build_call
    assert '--output=plcc-ng/diagram/syntax.png' in build_call
