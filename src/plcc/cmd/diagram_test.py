from .diagram import _extract_type_name, find_types


class TestExtractTypeName:
    def test_class_type(self):
        assert _extract_type_name('plcc-diagram-class') == 'class'

    def test_ebnf_type(self):
        assert _extract_type_name('plcc-diagram-ebnf') == 'ebnf'

    def test_reserved_emit(self):
        assert _extract_type_name('plcc-diagram-emit') is None

    def test_reserved_build(self):
        assert _extract_type_name('plcc-diagram-build') is None

    def test_reserved_run(self):
        assert _extract_type_name('plcc-diagram-run') is None

    def test_reserved_list(self):
        assert _extract_type_name('plcc-diagram-list') is None

    def test_plugin_name_excluded(self):
        # extra hyphens mean it is a plugin, not a type orchestrator
        assert _extract_type_name('plcc-diagram-class-plantuml-emit') is None

    def test_unrelated_command(self):
        assert _extract_type_name('plcc-make') is None

    def test_wrong_prefix(self):
        assert _extract_type_name('plcc-plantuml-diagram-emit') is None

    def test_empty_string(self):
        assert _extract_type_name('') is None


class TestFindTypes:
    def test_finds_installed_type(self, tmp_path, monkeypatch):
        cmd = tmp_path / 'plcc-diagram-class'
        cmd.write_text('#!/bin/sh\n')
        cmd.chmod(0o755)
        monkeypatch.setenv('PATH', str(tmp_path))
        assert find_types() == ['class']

    def test_excludes_reserved_names(self, tmp_path, monkeypatch):
        for name in ('plcc-diagram-emit', 'plcc-diagram-build',
                     'plcc-diagram-run', 'plcc-diagram-list'):
            f = tmp_path / name
            f.write_text('#!/bin/sh\n')
            f.chmod(0o755)
        monkeypatch.setenv('PATH', str(tmp_path))
        assert find_types() == []

    def test_excludes_non_executable(self, tmp_path, monkeypatch):
        cmd = tmp_path / 'plcc-diagram-class'
        cmd.write_text('#!/bin/sh\n')
        cmd.chmod(0o644)
        monkeypatch.setenv('PATH', str(tmp_path))
        assert find_types() == []

    def test_excludes_plugin_names_with_extra_segments(self, tmp_path, monkeypatch):
        cmd = tmp_path / 'plcc-diagram-class-plantuml-emit'
        cmd.write_text('#!/bin/sh\n')
        cmd.chmod(0o755)
        monkeypatch.setenv('PATH', str(tmp_path))
        assert find_types() == []

    def test_deduplicates_across_path_dirs(self, tmp_path, monkeypatch):
        dir1 = tmp_path / 'dir1'
        dir2 = tmp_path / 'dir2'
        dir1.mkdir()
        dir2.mkdir()
        for d in (dir1, dir2):
            f = d / 'plcc-diagram-class'
            f.write_text('#!/bin/sh\n')
            f.chmod(0o755)
        monkeypatch.setenv('PATH', f'{dir1}:{dir2}')
        assert find_types() == ['class']

    def test_returns_empty_when_no_types(self, tmp_path, monkeypatch):
        monkeypatch.setenv('PATH', str(tmp_path))
        assert find_types() == []

    def test_finds_multiple_types(self, tmp_path, monkeypatch):
        for name in ('plcc-diagram-class', 'plcc-diagram-ebnf'):
            f = tmp_path / name
            f.write_text('#!/bin/sh\n')
            f.chmod(0o755)
        monkeypatch.setenv('PATH', str(tmp_path))
        assert sorted(find_types()) == ['class', 'ebnf']
