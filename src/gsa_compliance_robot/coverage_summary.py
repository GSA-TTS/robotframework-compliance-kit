"""Print a GitHub-Actions-friendly Markdown summary of a Cobertura ``coverage.xml``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

LOWEST_ROWS = 10
DEFAULT_XML = Path("results/coverage-report/coverage.xml")


def _parse(path: Path):
    try:
        import defusedxml.ElementTree as ET
    except ImportError as exc:  # pragma: no cover - exercised by the install extra
        raise RuntimeError(
            "defusedxml is required to read coverage XML; install gsa-compliance-robot[coverage]"
        ) from exc
    return ET.parse(path).getroot()


def render(xml_path: Path) -> list[str]:
    root = _parse(xml_path)
    line_rate = float(root.attrib.get("line-rate", 0)) * 100
    branch_rate = float(root.attrib.get("branch-rate", 0)) * 100
    covered = root.attrib.get("lines-covered", "?")
    valid = root.attrib.get("lines-valid", "?")
    lines = [
        "| Metric | Value |",
        "|--------|-------|",
        f"| Line coverage | {line_rate:.1f}% ({covered}/{valid} lines) |",
        f"| Branch coverage | {branch_rate:.1f}% |",
        "",
    ]
    rows = sorted(
        (float(c.attrib.get("line-rate", 1)) * 100, c.attrib.get("filename", "?"))
        for c in root.findall(".//class")
    )
    if rows:
        lines += [
            "**Lowest coverage files:**",
            "| File | Line % |",
            "|------|--------|",
        ]
        lines += [f"| `{name}` | {rate:.0f}% |" for rate, name in rows[:LOWEST_ROWS]]
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", type=Path, default=DEFAULT_XML)
    args = parser.parse_args(argv)
    if not args.xml.exists():
        print(f"Coverage XML not found at {args.xml}", file=sys.stderr)
        return 1
    print("\n".join(render(args.xml)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
