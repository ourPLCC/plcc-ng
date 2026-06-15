from .output import print_user_error, print_banner


def test_print_user_error_writes_to_stdout(capsys):
    print_user_error("scan error: bad token")
    out, err = capsys.readouterr()
    assert "scan error: bad token" in out
    assert err == ""


def test_print_user_error_does_not_write_to_stderr(capsys):
    print_user_error("any message")
    _, err = capsys.readouterr()
    assert err == ""


def test_print_banner_version_goes_to_stderr(capsys):
    print_banner("1.2.3", "/abs/grammar.plcc")
    _, err = capsys.readouterr()
    assert "plcc-ng 1.2.3" in err


def test_print_banner_grammar_goes_to_stderr(capsys):
    print_banner("1.2.3", "/abs/grammar.plcc")
    _, err = capsys.readouterr()
    assert "grammar: /abs/grammar.plcc" in err


def test_print_banner_nothing_on_stdout(capsys):
    print_banner("1.2.3", "/abs/grammar.plcc")
    out, _ = capsys.readouterr()
    assert out == ""


def test_print_banner_with_tool_running_line_on_stderr(capsys):
    print_banner("1.2.3", "/abs/grammar.plcc", tool="calc", language="python")
    _, err = capsys.readouterr()
    assert "Running calc with python." in err


def test_print_banner_without_tool_no_running_line(capsys):
    print_banner("1.2.3", "/abs/grammar.plcc")
    _, err = capsys.readouterr()
    assert "Running" not in err
