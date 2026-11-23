from __future__ import annotations

import json
from pathlib import Path

import pytest

from gsa_compliance_robot import keyword_coverage as kc

RESOURCE = """*** Settings ***
Library    Collections

*** Keywords ***
Alpha Keyword
    [Documentation]    doc
    Log    alpha

# a comment
Beta Keyword
    Log    beta

Never Called Keyword
    Log    nope
"""

TEST = """*** Settings ***
Resource    shared.resource
Library    helper.py

*** Test Cases ***
First
    Alpha Keyword
    Beta Keyword    arg
"""


@pytest.fixture
def tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "tests" / "resources").mkdir(parents=True)
    (tmp_path / "tests" / "resources" / "shared.resource").write_text(RESOURCE)
    (tmp_path / "tests" / "test_one.robot").write_text(TEST)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_parse_and_imports(tree: Path) -> None:
    parsed = kc.parse_robot_file(tree / "tests" / "test_one.robot")
    assert kc.find_resource_imports(parsed) == ["shared.resource"]
    assert "alpha keyword" in kc.find_keywords_called_in_tests(parsed)


def test_parse_missing_file_is_empty_and_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert kc.parse_robot_file(tmp_path / "nope.robot")["sections"] == {}
    assert "Failed to open" in capsys.readouterr().err


def test_keywords_defined_skip_indented_comments_and_blank(tree: Path) -> None:
    assert kc.find_keywords_in_resource("shared.resource", tree) == [
        "Alpha Keyword",
        "Beta Keyword",
        "Never Called Keyword",
    ]
    assert kc.find_keywords_in_resource("missing.resource", tree) == []


def test_fuzzy_matches_prefix_ordered_words_and_ratio() -> None:
    assert kc.fuzzy_matches("Get Thing", ["get thing now"])
    assert kc.fuzzy_matches("Get Thing", ["get the big thing"])
    assert kc.fuzzy_matches("Get Thingy", ["get thing"])
    assert not kc.fuzzy_matches("Delete Everything", ["log", "get thing"])


def test_summary_reports_unused_keyword_and_ignores_common(tree: Path) -> None:
    summary, *_ = kc.build_summary(["tests/test_one.robot"], tree)
    info = summary["resources"]["shared.resource"]
    assert info["unused_by_any_test"] == ["Never Called Keyword"]
    assert info["global_coverage_pct"] == 66.7
    assert summary["total_missing_keywords"] == 1
    common = tree / "tests" / "resources" / "common.resource"
    common.write_text(RESOURCE)
    (tree / "tests" / "test_two.robot").write_text(
        TEST.replace("shared.resource", "common.resource")
    )
    summary, *_ = kc.build_summary(["tests/test_two.robot"], tree)
    assert summary["resources"]["common.resource"]["ignore_in_failure"] is True
    assert summary["total_missing_keywords"] == 0


def test_check_cli_exit_codes_and_json(
    tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tree / "results" / "kc.json"
    argv = ["check", "--tests", "tests/test_*.robot", "--out", str(out)]
    assert kc.main(argv) == 0
    assert kc.main([*argv, "--fail-on-missing"]) == 3
    assert "FAILED" in capsys.readouterr().out
    assert json.loads(out.read_text())["total_missing_keywords"] == 1
    assert kc.main(["check", "--tests", "nothing/*.robot", "--out", str(out)]) == 2


def test_check_cli_passes_when_all_keywords_used(tree: Path) -> None:
    (tree / "tests" / "test_one.robot").write_text(TEST + "    Never Called Keyword\n")
    out = tree / "kc.json"
    assert (
        kc.main(
            [
                "check",
                "--tests",
                "tests/test_*.robot",
                "--out",
                str(out),
                "--fail-on-missing",
            ]
        )
        == 0
    )


def test_check_handles_test_without_resources(
    tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tree / "tests" / "test_empty.robot").write_text(
        "*** Test Cases ***\nT\n    Log    x\n"
    )
    kc.main(
        ["check", "--tests", "tests/test_empty.robot", "--out", str(tree / "o.json")]
    )
    assert "imports no resources" in capsys.readouterr().out


def test_generate_suite_is_deterministic_and_dedupes(tree: Path) -> None:
    res = tree / "tests" / "resources"
    (res / "other.resource").write_text(RESOURCE)
    out = tree / "generated" / "suite.robot"
    args = ["generate-suite", "--resources-dir", str(res), "--out", str(out)]
    assert kc.main(args) == 0
    first = out.read_bytes()
    assert kc.main(args) == 0
    assert first == out.read_bytes()
    text = out.read_text()
    assert text.count("Run Keyword And Ignore Error    Alpha Keyword") == 1
    assert "Resource    tests/resources/other.resource" in text


def test_generate_suite_with_no_keywords_logs(tmp_path: Path) -> None:
    text, count, resources = kc.render_coverage_suite(tmp_path, cwd=tmp_path)
    assert count == 0 and resources == 0 and "No keywords found" in text


def test_generate_suite_uses_absolute_path_outside_cwd(tmp_path: Path) -> None:
    res = tmp_path / "res"
    res.mkdir()
    (res / "a.resource").write_text(RESOURCE)
    other = tmp_path / "elsewhere"
    other.mkdir()
    text, _, _ = kc.render_coverage_suite(res, cwd=other)
    assert f"Resource    {(res / 'a.resource').resolve()}" in text


def test_find_python_libs(tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tree / "tests" / "test_plain.robot").write_text(
        "*** Settings ***\nLibrary    Collections\n"
    )
    assert kc.main(["find-python-libs", "--tests", "tests/test_*.robot"]) == 0
    assert capsys.readouterr().out.split() == ["tests/test_one.robot"]
    assert kc.imports_python_library(tree / "tests" / "test_one.robot")
    assert not kc.imports_python_library(tree / "tests" / "test_plain.robot")
