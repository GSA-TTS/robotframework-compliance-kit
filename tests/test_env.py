from __future__ import annotations

import os

import pytest

from gsa_compliance_robot import env


class TestLoadEnvFile:
    def test_no_env_file_returns_empty_list(self, tmp_path):
        result = env.load_env_file(tmp_path)
        assert result == []

    def test_loads_simple_key_value_pairs(self, tmp_path, monkeypatch):
        monkeypatch.delenv("FOO_TEST_VAR", raising=False)
        (tmp_path / ".env").write_text("FOO_TEST_VAR=bar\n")
        loaded = env.load_env_file(tmp_path)
        assert loaded == ["FOO_TEST_VAR"]
        assert os.environ["FOO_TEST_VAR"] == "bar"

    def test_skips_comments_and_blank_lines(self, tmp_path, monkeypatch):
        monkeypatch.delenv("FOO_TEST_VAR2", raising=False)
        (tmp_path / ".env").write_text(
            "# a comment\n\nFOO_TEST_VAR2=baz\n   \n# another\n"
        )
        loaded = env.load_env_file(tmp_path)
        assert loaded == ["FOO_TEST_VAR2"]
        assert os.environ["FOO_TEST_VAR2"] == "baz"

    def test_strips_inline_comments(self, tmp_path, monkeypatch):
        monkeypatch.delenv("FOO_TEST_VAR3", raising=False)
        (tmp_path / ".env").write_text("FOO_TEST_VAR3=qux # inline comment\n")
        env.load_env_file(tmp_path)
        assert os.environ["FOO_TEST_VAR3"] == "qux"

    def test_searches_parent_directories(self, tmp_path, monkeypatch):
        monkeypatch.delenv("FOO_TEST_PARENT", raising=False)
        (tmp_path / ".env").write_text("FOO_TEST_PARENT=parentval\n")
        nested = tmp_path / "a" / "b"
        nested.mkdir(parents=True)
        loaded = env.load_env_file(nested)
        assert loaded == ["FOO_TEST_PARENT"]
        assert os.environ["FOO_TEST_PARENT"] == "parentval"

    def test_ignores_lines_without_equals(self, tmp_path, monkeypatch):
        monkeypatch.delenv("FOO_TEST_VAR4", raising=False)
        (tmp_path / ".env").write_text("not a valid line\nFOO_TEST_VAR4=ok\n")
        loaded = env.load_env_file(tmp_path)
        assert loaded == ["FOO_TEST_VAR4"]


class TestMaskValue:
    def test_empty_string_returns_empty(self):
        assert env.mask_value("") == ""

    def test_short_value_fully_masked(self):
        assert env.mask_value("short") == "****"

    def test_long_value_preserves_first_and_last_four(self):
        assert env.mask_value("abcdefghij") == "abcd****ghij"

    def test_exactly_eight_chars_fully_masked(self):
        assert env.mask_value("12345678") == "****"

    def test_nine_chars_uses_first_last(self):
        assert env.mask_value("123456789") == "1234****6789"


class TestValidateRequiredEnvVars:
    def test_passes_when_all_set(self, monkeypatch):
        monkeypatch.setenv("REQ_VAR_A", "x")
        monkeypatch.setenv("REQ_VAR_B", "y")
        env.validate_required_env_vars("REQ_VAR_A", "REQ_VAR_B")

    def test_raises_listing_missing_vars(self, monkeypatch):
        monkeypatch.delenv("REQ_VAR_MISSING", raising=False)
        monkeypatch.setenv("REQ_VAR_PRESENT", "x")
        with pytest.raises(ValueError, match="REQ_VAR_MISSING"):
            env.validate_required_env_vars("REQ_VAR_PRESENT", "REQ_VAR_MISSING")

    def test_raises_for_empty_value(self, monkeypatch):
        monkeypatch.setenv("REQ_VAR_EMPTY", "")
        with pytest.raises(ValueError, match="REQ_VAR_EMPTY"):
            env.validate_required_env_vars("REQ_VAR_EMPTY")
