import pytest
from .list import find_languages, extract_language_name


def test_extract_language_name():
    assert extract_language_name('plcc-plantuml-emit') == 'plantuml'
    assert extract_language_name('plcc-java-emit') == 'java'


def test_extract_ignores_non_matching():
    assert extract_language_name('plcc-lang-emit') is None
    assert extract_language_name('python') is None


def test_find_languages_returns_list(monkeypatch):
    monkeypatch.setenv('PATH', '/fake/bin')
    import os, pathlib
    # Not testing actual PATH scan here — just that function is callable
    result = find_languages()
    assert isinstance(result, list)
