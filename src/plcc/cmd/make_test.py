import pytest
import docopt
from types import SimpleNamespace

from .make import main as run_main, validate_language_name, _report_ll1_failure
from plcc.build.spec import read_spec, write_spec


def test_help(capsys):
    with pytest.raises(SystemExit):
        run_main(['--help'])
    out, err = capsys.readouterr()
    assert 'Usage' in out


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


def test_spec_flag_not_found_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main(['--spec=nonexistent.plcc'])
    assert exc.value.code != 0


def test_short_spec_flag_not_found_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main(['-s', 'nonexistent.plcc'])
    assert exc.value.code != 0


def test_invalid_through_value_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main(['--through=typo'])
    assert exc.value.code != 0


def test_invalid_through_value_prints_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main(['--through=typo'])
    _, err = capsys.readouterr()
    assert "invalid --through" in err



def test_report_ll1_failure_prints_error_and_conflicts(capsys):
    ll1 = {
        "is_ll1": False,
        "conflicts": [
            {
                "nonterminal": "expr",
                "lookahead": "ID",
                "conflict_type": "first_first",
                "productions": [
                    {"alt": None, "production": [
                        {"symbol": "ID", "field": None},
                        {"symbol": "PLUS", "field": None},
                    ]},
                    {"alt": None, "production": [
                        {"symbol": "ID", "field": None},
                        {"symbol": "MINUS", "field": None},
                    ]},
                ],
            }
        ],
        "left_recursion": [],
    }
    _report_ll1_failure(ll1)
    _, err = capsys.readouterr()
    assert "plcc-make: error:" in err
    assert "LL(1) conflict: <expr> on lookahead ID" in err
    assert "FIRST/FIRST" in err


def test_report_left_recursion_cycle(capsys):
    ll1 = {
        "conflicts": [],
        "left_recursion": [{"cycle": ["A", "B", "A"]}],
    }
    _report_ll1_failure(ll1)
    _, err = capsys.readouterr()
    assert "A -> B -> A" in err


def test_report_ll1_failure_no_path_in_header(capsys):
    ll1 = {"conflicts": [], "left_recursion": []}
    _report_ll1_failure(ll1)
    _, err = capsys.readouterr()
    assert "see" not in err
    assert "ll1.json" not in err


def test_through_model_is_valid(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main(['--through=model'])
    _, err = capsys.readouterr()
    assert "invalid --through" not in err


def test_through_diagram_is_rejected(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main(['--through=diagram'])
    _, err = capsys.readouterr()
    assert "invalid --through" in err


def test_invalid_through_error_message_includes_model(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main(['--through=typo'])
    _, err = capsys.readouterr()
    assert "model" in err


def test_report_ll1_failure_blank_line_before_conflict(capsys):
    ll1 = {
        "conflicts": [
            {
                "nonterminal": "expr",
                "lookahead": "ID",
                "conflict_type": "first_first",
                "productions": [
                    {"alt": None, "production": [
                        {"symbol": "ID", "field": None},
                        {"symbol": "PLUS", "field": None},
                    ]},
                    {"alt": None, "production": [
                        {"symbol": "ID", "field": None},
                        {"symbol": "MINUS", "field": None},
                    ]},
                ],
            }
        ],
        "left_recursion": [],
    }
    _report_ll1_failure(ll1)
    _, err = capsys.readouterr()
    # Header line ends with \n; a blank line means \n\n before the conflict header
    assert "grammar is not LL(1)\n\nLL(1) conflict:" in err


def test_report_ll1_failure_blank_line_between_conflicts(capsys):
    conflict = {
        "nonterminal": "expr",
        "lookahead": "ID",
        "conflict_type": "first_first",
        "productions": [
            {"alt": None, "production": [
                {"symbol": "ID", "field": None},
                {"symbol": "PLUS", "field": None},
            ]},
            {"alt": None, "production": [
                {"symbol": "ID", "field": None},
                {"symbol": "MINUS", "field": None},
            ]},
        ],
    }
    ll1 = {"conflicts": [conflict, conflict], "left_recursion": []}
    _report_ll1_failure(ll1)
    _, err = capsys.readouterr()
    # The second conflict block must be preceded by a blank line.
    # format_conflict_message ends without a trailing newline; print() adds one.
    # A blank separator means the last line of block 1, then \n\n, then LL(1) conflict:.
    blocks = err.split("\n\nLL(1) conflict:")
    assert len(blocks) == 3  # header + conflict1 + conflict2


def test_no_spec_flag_no_stored_falls_back_to_spec_plcc(tmp_path, monkeypatch, capsys):
    # Fresh directory, no spec.plcc → error names spec.plcc
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main([])
    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert "spec.plcc" in err


def test_no_spec_flag_stored_spec_missing_errors_to_stderr(tmp_path, monkeypatch, capsys):
    # build/.spec points to a file that does not exist
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    write_spec(build, "missing.plcc")
    with pytest.raises(SystemExit) as exc:
        run_main([])
    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert "spec file not found" in err
    assert "missing.plcc" in err
    assert "--spec" in err


def test_no_spec_flag_uses_stored_spec_path(tmp_path, monkeypatch, capsys):
    # build/.spec set to a.plcc (missing) — error names a.plcc, not spec.plcc
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    write_spec(build, "a.plcc")
    with pytest.raises(SystemExit):
        run_main([])
    _, err = capsys.readouterr()
    assert "a.plcc" in err
    # Must NOT fall back to spec.plcc
    assert "spec.plcc" not in err


def test_explicit_spec_differs_from_stored_wipes_build(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    (build / "marker.txt").write_text("from old grammar")
    write_spec(build, "old.plcc")
    (tmp_path / "new.plcc").write_text("")  # valid but empty grammar
    run_main(["--spec=new.plcc"])
    # build/ was wiped when grammar changed, marker should not exist
    assert not (build / "marker.txt").exists()


def test_explicit_spec_same_as_stored_does_not_wipe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    (build / "marker.txt").write_text("from current grammar")
    write_spec(build, "same.plcc")
    (tmp_path / "same.plcc").write_text("")  # valid but empty grammar
    run_main(["--spec=same.plcc"])
    # No wipe — marker is still present because grammar didn't change
    assert (build / "marker.txt").exists()


def test_spec_written_before_build_stages_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    (tmp_path / "bad.plcc").write_text("token BAD @@@\n")
    with pytest.raises(SystemExit):
        run_main(["--spec=bad.plcc"])
    assert read_spec(build) == "bad.plcc"


def test_make_main_default_prints_no_banner_to_stdout(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main([])
    out, _ = capsys.readouterr()
    assert "plcc-ng" not in out


def test_make_main_banner_prints_version_to_stderr(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spec.plcc").write_text("")
    monkeypatch.setattr("plcc.cmd.make.get_version", lambda: "1.2.3")
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **kw: SimpleNamespace(returncode=1, stderr=b""))
    with pytest.raises(SystemExit):
        run_main(["--banner"])
    _, err = capsys.readouterr()
    assert "plcc-ng 1.2.3" in err


def test_make_main_banner_prints_spec_to_stderr(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    spec = tmp_path / "spec.plcc"
    spec.write_text("")
    monkeypatch.setattr("plcc.cmd.make.get_version", lambda: "1.2.3")
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **kw: SimpleNamespace(returncode=1, stderr=b""))
    with pytest.raises(SystemExit):
        run_main(["--banner"])
    _, err = capsys.readouterr()
    assert "spec:" in err
    assert str(spec) in err


def test_make_main_banner_short_flag_works(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spec.plcc").write_text("")
    monkeypatch.setattr("plcc.cmd.make.get_version", lambda: "1.2.3")
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **kw: SimpleNamespace(returncode=1, stderr=b""))
    with pytest.raises(SystemExit):
        run_main(["-b"])
    _, err = capsys.readouterr()
    assert "plcc-ng 1.2.3" in err


def test_make_main_banner_is_plain_text_with_json_format(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spec.plcc").write_text("")
    monkeypatch.setattr("plcc.cmd.make.get_version", lambda: "1.2.3")
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **kw: SimpleNamespace(returncode=1, stderr=b""))
    with pytest.raises(SystemExit):
        run_main(["--banner", "--verbose-format=json"])
    _, err = capsys.readouterr()
    assert "plcc-ng 1.2.3" in err  # plain "plcc-ng X.Y.Z", not a JSON object


def test_validate_language_name_accepts_valid():
    validate_language_name('Python')
    validate_language_name('Java')
    validate_language_name('PlantUML')


def test_validate_language_name_rejects_path_traversal():
    with pytest.raises(ValueError):
        validate_language_name('../etc')
    with pytest.raises(ValueError):
        validate_language_name('foo/bar')
    with pytest.raises(ValueError):
        validate_language_name('foo\\bar')


def test_validate_language_name_rejects_empty():
    with pytest.raises(ValueError):
        validate_language_name('')
