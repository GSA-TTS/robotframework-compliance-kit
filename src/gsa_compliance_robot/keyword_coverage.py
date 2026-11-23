"""Static keyword-coverage helpers for Robot Framework suites.

Three heuristic tools, none of which execute Robot or touch the network:

* ``check``: which keywords defined in imported ``.resource`` files are never referenced
  by any test file (case-insensitive prefix, ordered-word and fuzzy matching).
* ``generate-suite``: write a suite that calls every resource keyword through
  ``Run Keyword And Ignore Error`` so a coverage run records keyword usage.
* ``find-python-libs``: list test files that import a Python library.

The parsing is line based, not a full Robot parser, so results are a review aid.
"""

from __future__ import annotations

import argparse
import difflib
import glob
import json
import os
import re
import sys
from collections.abc import Iterable
from contextlib import suppress
from pathlib import Path
from typing import Any

SECTION_RE = re.compile(r"^\*\*\*\s*(?P<section>[A-Za-z][A-Za-z ]*?)\s*\*\*\*", re.I)
RESOURCE_RE = re.compile(r"^Resource\s+(?P<path>.+)$", re.I)
LIBRARY_RE = re.compile(r"^Library\s+(?P<lib>.+)$", re.I)
KEYWORDS_HEADING_RE = re.compile(r"^\s*\*{3}\s*Keywords\s*\*{3}\s*$", re.I)
ANY_HEADING_RE = re.compile(r"^\s*\*{3}\s*\w.*\*{3}\s*$", re.I)
_WS_RE = re.compile(r"\s+")


def _canonical_section(name: str) -> str:
    """Normalise a heading such as ``Test Cases`` or ``test case`` to a stable key."""
    lowered = _WS_RE.sub(" ", name.strip()).lower()
    return {"test case": "Test Cases", "task": "Tasks"}.get(lowered, lowered.title())


def parse_robot_file(path: str | Path) -> dict[str, Any]:
    """Return ``{"lines": [...], "sections": {name: [lines]}}`` for a Robot file."""
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        print(f"Failed to open {path}: {exc}", file=sys.stderr)
        return {"lines": [], "sections": {}}
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        match = SECTION_RE.match(line)
        if match:
            current = _canonical_section(match.group("section"))
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
    return {"lines": lines, "sections": sections}


def find_resource_imports(parsed: dict[str, Any]) -> list[str]:
    imports = []
    for line in parsed.get("sections", {}).get("Settings", []):
        match = RESOURCE_RE.match(line.strip())
        if match:
            imports.append(match.group("path").strip().strip("\"'"))
    return imports


def _resolve_resource(path: str, root: Path) -> Path | None:
    candidates = [Path(path)] if os.path.isabs(path) else []
    if not candidates:
        candidates = [
            root / path,
            root / "tests/resources" / path,
            root / "resources" / path,
        ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    base = os.path.basename(path)
    for found in sorted(root.rglob(base)):
        if found.is_file():
            return found
    return None


def find_keywords_in_resource(path: str, root: Path | None = None) -> list[str]:
    """Keyword names defined (column-0 lines of ``*** Keywords ***``) in a resource file."""
    full = _resolve_resource(path, root or Path.cwd())
    if full is None:
        return []
    names = []
    for line in parse_robot_file(full)["sections"].get("Keywords", []):
        if (
            not line.strip()
            or line.startswith((" ", "\t"))
            or line.strip().startswith("#")
        ):
            continue
        names.append(line.strip())
    return names


def find_keywords_called_in_tests(parsed: dict[str, Any]) -> set[str]:
    """Normalised, lower-cased indented lines of Test Cases and Keywords sections."""
    called = set()
    for section in ("Test Cases", "Tasks", "Keywords"):
        for line in parsed.get("sections", {}).get(section, []):
            if not line.strip() or line.strip().startswith("#"):
                continue
            if line.startswith((" ", "\t")):
                called.add(_WS_RE.sub(" ", line.strip()).lower())
    return called


def fuzzy_matches(keyword: str, called: Iterable[str], min_ratio: float = 0.75) -> bool:
    """True if a called token starts with, contains in order, or is similar to ``keyword``."""
    called = list(called)
    key = _WS_RE.sub(" ", keyword).strip().lower()
    if any(token.startswith(key) for token in called):
        return True
    words = key.split()
    for token in called:
        index, ok = 0, True
        for word in words:
            pos = token.find(word, index)
            if pos == -1:
                ok = False
                break
            index = pos + len(word)
        if ok:
            return True
    return any(
        difflib.SequenceMatcher(None, key, token).ratio() >= min_ratio
        for token in called
    )


def _is_common(resource: str) -> bool:
    return os.path.basename(resource).lower().endswith("common.resource")


def build_summary(
    test_paths: list[str], root: Path | None = None
) -> tuple[
    dict[str, Any], dict[str, list[str]], dict[str, set[str]], dict[str, list[str]]
]:
    """Return ``(summary, test_resources, test_called, resource_keywords)``."""
    root = root or Path.cwd()
    test_resources: dict[str, list[str]] = {}
    test_called: dict[str, set[str]] = {}
    resource_keywords: dict[str, list[str]] = {}
    for test in sorted(test_paths):
        parsed = parse_robot_file(test)
        test_resources[test] = find_resource_imports(parsed)
        test_called[test] = find_keywords_called_in_tests(parsed)
        for resource in test_resources[test]:
            if resource not in resource_keywords:
                resource_keywords[resource] = find_keywords_in_resource(resource, root)
    global_called: set[str] = (
        set().union(*test_called.values()) if test_called else set()
    )
    summary: dict[str, Any] = {
        "tests": {
            test: {"resources": res, "called": sorted(test_called[test])}
            for test, res in test_resources.items()
        },
        "resources": {},
        "total_resource_keywords": 0,
        "total_missing_keywords": 0,
        "global_called_keywords": [],
        "common": {},
    }
    for resource, keywords in resource_keywords.items():
        used = [k for k in keywords if fuzzy_matches(k, global_called)]
        unused = [k for k in keywords if k not in used]
        pct = (len(used) / len(keywords) * 100.0) if keywords else 100.0
        summary["resources"][resource] = {
            "defined": keywords,
            "defined_count": len(keywords),
            "used_by_any_test": sorted(used),
            "unused_by_any_test": sorted(unused),
            "missing": sorted(unused),
            "missing_count": len(unused),
            "global_coverage_pct": round(pct, 1),
            "ignore_in_failure": _is_common(resource),
        }
        if keywords and not _is_common(resource):
            summary["total_resource_keywords"] += len(keywords)
            summary["total_missing_keywords"] += len(unused)
    return summary, test_resources, test_called, resource_keywords


def _expand(patterns: str) -> list[str]:
    paths: list[str] = []
    for pattern in patterns.split():
        paths.extend(glob.glob(pattern, recursive=True))
    return paths


def run_check(args: argparse.Namespace) -> int:
    paths = _expand(args.tests)
    if not paths:
        print("No test files found for pattern:", args.tests)
        return 2
    summary, test_resources, test_called, resource_keywords = build_summary(paths)
    all_ok = True
    for test, resources in test_resources.items():
        print(f"\nTest: {test}")
        if not resources:
            print(
                f"[WARN] {test} imports no resources. Skipping coverage check for this test."
            )
            continue
        for resource in resources:
            keywords = resource_keywords.get(resource, [])
            info = summary["resources"].get(resource, {})
            if not keywords:
                print(
                    f"  [INFO] Resource {resource} not found or has no keywords (skipping)"
                )
                continue
            missed = [k for k in keywords if not fuzzy_matches(k, test_called[test])]
            if info.get("ignore_in_failure"):
                print(f"  Resource (common): {resource}")
                print(f"    Keywords defined: {len(keywords)}")
                print(f"    Unused in THIS test ({len(missed)}):")
                for name in missed:
                    print(f"      - {name}")
            elif missed:
                all_ok = False
                print(f"  Resource: {resource}")
                print(f"    Keywords defined: {len(keywords)}")
                print(f"    Missing ({len(missed)}):")
                for name in missed:
                    note = (
                        " (UNUSED by any test)"
                        if name in info["unused_by_any_test"]
                        else ""
                    )
                    print(f"      - {name}{note}")
            else:
                print(
                    f"  Resource: {resource} - all {len(keywords)} keywords referenced by tests"
                )
    out = Path(args.out)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\nWrote keyword coverage summary to: {out}")
    except OSError as exc:
        print(f"Failed to write summary JSON {out}: {exc}")
    if not all_ok:
        print(
            "\nResource keyword coverage checks FAILED: "
            f"{summary['total_missing_keywords']} missing keywords out of "
            f"{summary['total_resource_keywords']}"
        )
        return 3 if args.fail_on_missing else 0
    print(
        "\nResource keyword coverage checks PASSED: all resource keywords referenced by tests"
    )
    return 0


def extract_keywords_from_file(path: Path) -> list[str]:
    names: list[str] = []
    in_keywords = False
    with suppress(OSError):
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not in_keywords:
                in_keywords = bool(KEYWORDS_HEADING_RE.match(raw))
                continue
            if ANY_HEADING_RE.match(raw):
                break
            if raw.strip() and not raw.startswith((" ", "\t")):
                names.append(raw.strip())
    return names


def render_coverage_suite(
    resources_dir: Path, cwd: Path | None = None
) -> tuple[str, int, int]:
    """Deterministic suite text calling each unique resource keyword once, errors ignored.

    Returns ``(text, keyword_count, resource_count)``. Resources inside ``cwd`` are imported
    by relative path; others by absolute path.
    """
    base = (cwd or Path.cwd()).resolve()
    imported: list[Path] = []
    keywords: list[str] = []
    for resource in sorted(resources_dir.rglob("*.resource")):
        found = extract_keywords_from_file(resource)
        if not found:
            continue
        resolved = resource.resolve()
        try:
            imported.append(resolved.relative_to(base))
        except ValueError:
            imported.append(resolved)
        keywords.extend(found)
    unique = list(dict.fromkeys(keywords))
    lines = [
        "*** Settings ***",
        "Documentation    Auto-generated coverage suite: exercises resource keywords "
        "(no-op tolerant)",
    ]
    lines += [f"Resource    {path}" for path in imported]
    lines += [
        "Library    BuiltIn",
        "",
        "",
        "*** Test Cases ***",
        "Exercise Resource Keywords",
    ]
    lines += [
        "    [Documentation]    Invoke each resource keyword with Run Keyword And Ignore "
        "Error to record usage for coverage",
        "    [Timeout]    20 minutes",
    ]
    if unique:
        lines += [f"    Run Keyword And Ignore Error    {name}" for name in unique]
    else:
        lines.append("    Log    No keywords found in resources/")
    return "\n".join(lines) + "\n", len(unique), len(imported)


def run_generate(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    text, keywords, resources = render_coverage_suite(Path(args.resources_dir))
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out} with {keywords} keywords from {resources} resource files")
    return 0


def imports_python_library(path: str | Path) -> bool:
    """True if a ``Library`` import ends in ``.py`` or looks like a dotted module path."""
    for line in parse_robot_file(path)["sections"].get("Settings", []):
        match = LIBRARY_RE.match(line.strip())
        if match:
            lib = match.group("lib").strip().strip("\"'")
            if lib.endswith(".py") or "." in lib:
                return True
    return False


def run_find_python_libs(args: argparse.Namespace) -> int:
    for path in sorted(_expand(args.tests)):
        if imports_python_library(path):
            print(path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gsa-robot-keyword-coverage", description=__doc__
    )
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="report resource keywords no test references")
    check.add_argument("--tests", default="tests/**/test_*.robot")
    check.add_argument("--out", default="results/keyword_coverage.json")
    check.add_argument("--fail-on-missing", action="store_true")
    check.set_defaults(func=run_check)
    gen = sub.add_parser("generate-suite", help="write a suite calling every keyword")
    gen.add_argument("--resources-dir", "-r", default="resources")
    gen.add_argument("--out", "-o", default="tests/generated/keyword_coverage.robot")
    gen.set_defaults(func=run_generate)
    find = sub.add_parser(
        "find-python-libs", help="list tests importing Python libraries"
    )
    find.add_argument("--tests", default="tests/**/test_*.robot")
    find.set_defaults(func=run_find_python_libs)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
