"""Vendor-sync CLI stub.

Phase 0/1 scope note: the full vendor-sync workflow (copy pinned .resource
files into a consumer repo under tests/resources/vendor/, write a
vendor.lock.json with sha256 hashes, and a `--check` mode for CI drift
detection) is intentionally deferred — see the "Vendoring" tracking issue.

For now this is a minimal placeholder so `gsa-robot-vendor --help` resolves
and the console-script entry point in pyproject.toml is valid. Consumers
should install this package as a normal Python dependency
(`pip install gsa-compliance-robot`) and import `.resource` files directly
from the installed package path via `Resource` imports, e.g.:

    Resource    ${EXECDIR}/.venv/lib/python3.*/site-packages/gsa_compliance_robot/resources/env.resource

or more robustly, resolve the path in Python/Robot via
`importlib.resources.files("gsa_compliance_robot.resources")`.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gsa-robot-vendor",
        description=(
            "Vendor-sync CLI for gsa-compliance-robot .resource files "
            "(full implementation tracked separately; see repo issues)."
        ),
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        choices=["sync", "check", "help"],
        help="Not yet implemented in this bootstrap release.",
    )
    args = parser.parse_args(argv)

    if args.command in ("sync", "check"):
        print(
            "gsa-robot-vendor: 'sync'/'check' are not implemented in this "
            "bootstrap release. See the repository issue tracker for the "
            "vendoring rollout plan.",
            file=sys.stderr,
        )
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
