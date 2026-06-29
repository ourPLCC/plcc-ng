from .list import extract_type_format, find_plugins, main


def test_extract_type_format_plantuml():
    assert extract_type_format('plcc-diagram-class-plantuml-emit') == ('class', 'plantuml')


def test_extract_ignores_dispatcher():
    assert extract_type_format('plcc-diagram-emit') is None


def test_extract_ignores_old_pattern():
    assert extract_type_format('plcc-plantuml-diagram-emit') is None


def test_extract_ignores_non_matching():
    assert extract_type_format('plcc-diagram-list') is None
    assert extract_type_format('python') is None


def test_main_prints_type_slash_format(capsys, monkeypatch):
    monkeypatch.setattr(
        'plcc.diagram.list.find_plugins',
        lambda: [('class', 'plantuml')]
    )
    main([])
    out, _ = capsys.readouterr()
    assert out.splitlines() == ['class/plantuml']
