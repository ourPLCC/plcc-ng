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


def test_diagram_main_default_prints_no_banner_to_stdout(tmp_path, monkeypatch, capsys):
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
    assert "plcc-ng" not in out


def test_diagram_main_banner_prints_version_to_stderr(tmp_path, monkeypatch, capsys):
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
        run_main(["--banner"])

    _, err = capsys.readouterr()
    assert "plcc-ng 1.2.3" in err


def test_diagram_main_banner_prints_grammar_to_stderr(tmp_path, monkeypatch, capsys):
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
        run_main(["--banner"])

    _, err = capsys.readouterr()
    assert "grammar:" in err
    assert str(grammar) in err


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
            run_main([])

    _, err = capsys.readouterr()
    assert 'plcc-make: something went wrong' in err


def test_make_jsonl_stderr_reformatted_as_text(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    event = json.dumps({
        "stage": "plcc-make",
        "time": 0,
        "event": "started",
        "message": "building"
    })

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 1
        m.stderr = (event + '\n').encode()
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main(['-v', '--verbose-format=text'])

    _, err = capsys.readouterr()
    assert 'plcc-make: started: building' in err
    assert event not in err  # raw JSON must NOT appear


def test_empty_child_stderr_produces_no_output(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 1
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main([])

    _, err = capsys.readouterr()
    assert err == ''
