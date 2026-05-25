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
    assert "grammar file not found" in err


def test_calls_plcc_make_with_through_diagram(tmp_path, monkeypatch):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    make_calls = []

    def fake_run(cmd, **kwargs):
        make_calls.append(cmd)
        m = MagicMock()
        m.returncode = 1  # fail so we stop after first call
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main([])

    assert any('plcc-make' in str(c) for c in make_calls)
    assert any('--through=diagram' in str(c) for c in make_calls[0])


def test_default_format_is_plantuml(tmp_path, monkeypatch):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    make_calls = []

    def fake_run(cmd, **kwargs):
        make_calls.append(cmd)
        m = MagicMock()
        m.returncode = 1  # fail so we stop after first call
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main([])

    assert any('--diagram-format=plantuml' in str(c) for c in make_calls[0])
