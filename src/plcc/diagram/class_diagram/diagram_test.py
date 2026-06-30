import json
import pytest
from unittest.mock import patch, MagicMock

from .diagram import main as run_main


def test_grammar_file_not_found_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main([])
    assert exc.value.code != 0


def test_grammar_file_not_found_prints_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main([])
    _, err = capsys.readouterr()
    assert "spec file not found" in err


def test_calls_plcc_make_with_through_model(tmp_path, monkeypatch):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        m = MagicMock()
        m.returncode = 1
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main([])

    assert calls[0][0] == 'plcc-make'
    assert '--through=model' in calls[0]


def test_calls_emit_with_type_class(tmp_path, monkeypatch):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'plcc-ng'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    (build_dir / '.spec').write_text(str(grammar))
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main([])

    cmds = [c[0] for c in calls]
    assert cmds == ['plcc-make', 'plcc-diagram-emit', 'plcc-diagram-build', 'plcc-diagram-run']
    emit_call = calls[1]
    assert '--type=class' in emit_call
    assert '--format=plantuml' in emit_call


def test_build_uses_class_puml_path(tmp_path, monkeypatch):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'plcc-ng'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    (build_dir / '.spec').write_text(str(grammar))
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main([])

    build_call = calls[2]  # plcc-diagram-build is the 3rd call
    assert '--input=plcc-ng/diagram/class.puml' in build_call
    assert '--output=plcc-ng/diagram/class.png' in build_call


def test_banner_prints_version_to_stderr(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'plcc-ng'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    (build_dir / '.spec').write_text(str(grammar))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "plcc.diagram.class_diagram.diagram.get_version", lambda: "1.2.3"
    )

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main(["--banner"])

    _, err = capsys.readouterr()
    assert "plcc-ng 1.2.3" in err
