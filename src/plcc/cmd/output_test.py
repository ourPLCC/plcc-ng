from .output import print_user_error, print_startup_banner


def test_print_user_error_writes_to_stdout(capsys):
    print_user_error("scan error: bad token")
    out, err = capsys.readouterr()
    assert "scan error: bad token" in out
    assert err == ""


def test_print_user_error_does_not_write_to_stderr(capsys):
    print_user_error("any message")
    _, err = capsys.readouterr()
    assert err == ""


def test_print_startup_banner_contains_version(capsys):
    print_startup_banner("/abs/path/grammar.plcc", "1.2.3")
    out, _ = capsys.readouterr()
    assert "plcc-ng 1.2.3" in out


def test_print_startup_banner_contains_grammar_path(capsys):
    print_startup_banner("/abs/path/grammar.plcc", "1.2.3")
    out, _ = capsys.readouterr()
    assert "/abs/path/grammar.plcc" in out


def test_print_startup_banner_goes_to_stdout(capsys):
    print_startup_banner("/abs/path/grammar.plcc", "1.2.3")
    _, err = capsys.readouterr()
    assert err == ""


def test_print_startup_banner_no_tool_prints_one_line(capsys):
    print_startup_banner("/abs/path/grammar.plcc", "1.2.3")
    out, _ = capsys.readouterr()
    assert out.count("\n") == 1


def test_print_startup_banner_with_tool_prints_running_line(capsys):
    print_startup_banner("/abs/path/grammar.plcc", "1.2.3", tool="calc", language="python")
    out, _ = capsys.readouterr()
    assert "Running calc with python." in out


def test_print_startup_banner_tool_line_goes_to_stdout(capsys):
    print_startup_banner("/abs/path/grammar.plcc", "1.2.3", tool="calc", language="python")
    _, err = capsys.readouterr()
    assert err == ""


def test_print_startup_banner_with_tool_prints_two_lines(capsys):
    print_startup_banner("/abs/path/grammar.plcc", "1.2.3", tool="calc", language="python")
    out, _ = capsys.readouterr()
    assert out.count("\n") == 2
