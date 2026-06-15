from .output import print_user_error, print_version_line, print_grammar_line, print_banner


def test_print_user_error_writes_to_stdout(capsys):
    print_user_error("scan error: bad token")
    out, err = capsys.readouterr()
    assert "scan error: bad token" in out
    assert err == ""


def test_print_user_error_does_not_write_to_stderr(capsys):
    print_user_error("any message")
    _, err = capsys.readouterr()
    assert err == ""


def test_print_version_line_contains_version(capsys):
    print_version_line("1.2.3")
    out, _ = capsys.readouterr()
    assert "plcc-ng 1.2.3" in out


def test_print_version_line_goes_to_stdout(capsys):
    print_version_line("1.2.3")
    _, err = capsys.readouterr()
    assert err == ""


def test_print_version_line_prints_one_line(capsys):
    print_version_line("1.2.3")
    out, _ = capsys.readouterr()
    assert out.count("\n") == 1


def test_print_grammar_line_contains_grammar_path(capsys):
    print_grammar_line("/abs/path/grammar.plcc")
    out, _ = capsys.readouterr()
    assert "/abs/path/grammar.plcc" in out


def test_print_grammar_line_goes_to_stdout(capsys):
    print_grammar_line("/abs/path/grammar.plcc")
    _, err = capsys.readouterr()
    assert err == ""


def test_print_grammar_line_no_tool_prints_one_line(capsys):
    print_grammar_line("/abs/path/grammar.plcc")
    out, _ = capsys.readouterr()
    assert out.count("\n") == 1


def test_print_grammar_line_with_tool_prints_running_line(capsys):
    print_grammar_line("/abs/path/grammar.plcc", tool="calc", language="python")
    out, _ = capsys.readouterr()
    assert "Running calc with python." in out


def test_print_grammar_line_tool_line_goes_to_stdout(capsys):
    print_grammar_line("/abs/path/grammar.plcc", tool="calc", language="python")
    _, err = capsys.readouterr()
    assert err == ""


def test_print_grammar_line_with_tool_prints_two_lines(capsys):
    print_grammar_line("/abs/path/grammar.plcc", tool="calc", language="python")
    out, _ = capsys.readouterr()
    assert out.count("\n") == 2


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
