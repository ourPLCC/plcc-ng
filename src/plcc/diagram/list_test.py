from .list import find_formats, extract_format_name


def test_extract_format_name_plantuml_emit():
    assert extract_format_name('plcc-plantuml-diagram-emit') == 'plantuml'


def test_extract_format_name_mermaid_emit():
    assert extract_format_name('plcc-mermaid-diagram-emit') == 'mermaid'


def test_extract_ignores_old_pattern():
    assert extract_format_name('plcc-plantuml-diagram') is None


def test_extract_ignores_dispatcher():
    assert extract_format_name('plcc-diagram-emit') is None


def test_extract_ignores_non_matching():
    assert extract_format_name('plcc-diagram-list') is None
    assert extract_format_name('python') is None


def test_find_formats_returns_list(monkeypatch):
    monkeypatch.setenv('PATH', '/fake/bin')
    result = find_formats()
    assert isinstance(result, list)


def test_main_prints_sorted_formats(capsys, monkeypatch):
    from .list import main
    monkeypatch.setattr('plcc.diagram.list.find_formats', lambda: ['plantuml', 'mermaid'])
    main([])
    out, _ = capsys.readouterr()
    assert out.splitlines() == ['mermaid', 'plantuml']
