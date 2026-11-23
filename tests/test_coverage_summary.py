from __future__ import annotations

from pathlib import Path

import pytest

from gsa_compliance_robot import coverage_summary as cs

XML = """<?xml version="1.0"?>
<coverage line-rate="0.8" branch-rate="0.5" lines-covered="8" lines-valid="10">
  <packages><package><classes>
    <class filename="a.py" line-rate="0.2"/>
    <class filename="b.py" line-rate="1.0"/>
  </classes></package></packages>
</coverage>
"""


def test_render_table_and_lowest_files(tmp_path: Path) -> None:
    xml = tmp_path / "coverage.xml"
    xml.write_text(XML)
    text = "\n".join(cs.render(xml))
    assert "| Line coverage | 80.0% (8/10 lines) |" in text
    assert "| Branch coverage | 50.0% |" in text
    assert text.index("`a.py`") < text.index("`b.py`")


def test_main_prints_and_missing_file_exits_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    xml = tmp_path / "c.xml"
    xml.write_text(XML)
    assert cs.main(["--xml", str(xml)]) == 0
    assert "Lowest coverage files" in capsys.readouterr().out
    assert cs.main(["--xml", str(tmp_path / "missing.xml")]) == 1
    assert "not found" in capsys.readouterr().err


def test_render_rejects_xml_with_external_entities(tmp_path: Path) -> None:
    xml = tmp_path / "evil.xml"
    xml.write_text(
        '<?xml version="1.0"?><!DOCTYPE c [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
        '<coverage line-rate="1">&x;</coverage>'
    )
    from defusedxml import EntitiesForbidden

    with pytest.raises(EntitiesForbidden):
        cs.render(xml)
