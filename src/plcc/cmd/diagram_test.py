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


def test_calls_plcc_make_with_through_model(tmp_path, monkeypatch, capsys):
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
    assert not any('--through=diagram' in arg for arg in calls[0])


def test_calls_emit_build_run_after_make(tmp_path, monkeypatch):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'build'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    (build_dir / '.grammar').write_text(str(grammar))
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
    assert '--format=plantuml' in calls[1]   # emit
    assert '--format=plantuml' in calls[2]   # build
    assert '--format=plantuml' in calls[3]   # run


def test_diagram_main_version_line_appears_even_when_make_fails(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("plcc.cmd.diagram.get_version", lambda: "1.2.3")

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 1
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main([])

    out, _ = capsys.readouterr()
    assert "plcc-ng 1.2.3" in out


def test_diagram_main_no_banner_suppresses_version_line(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'build'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    (build_dir / '.grammar').write_text(str(grammar))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("plcc.cmd.diagram.get_version", lambda: "1.2.3")

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main(["--no-banner"])

    out, _ = capsys.readouterr()
    assert "plcc-ng" not in out


def test_diagram_main_no_banner_suppresses_grammar_line(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'build'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    (build_dir / '.grammar').write_text(str(grammar))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("plcc.cmd.diagram.get_version", lambda: "1.2.3")

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main(["--no-banner"])

    out, _ = capsys.readouterr()
    assert "grammar:" not in out


def test_diagram_main_make_call_includes_no_banner(tmp_path, monkeypatch):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'build'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    (build_dir / '.grammar').write_text(str(grammar))
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

    make_calls = [c for c in calls if c and c[0] == 'plcc-make']
    assert make_calls, "plcc-make was not called"
    assert any('--no-banner' in c for c in make_calls)


def test_make_plain_text_stderr_forwarded(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 1
        m.stderr = b'plcc-make: something went wrong\n'
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main(['--no-banner'])

    _, err = capsys.readouterr()
    assert 'plcc-make: something went wrong' in err
