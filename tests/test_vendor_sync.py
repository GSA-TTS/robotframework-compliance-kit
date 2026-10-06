from __future__ import annotations

import pytest

from gsa_compliance_robot.vendor_sync import main


class TestVendorSyncPlaceholder:
    """The vendor-sync CLI is intentionally a placeholder in this release.

    Full implementation (copy pinned .resource files into consumer repos,
    write a lockfile, support --check for CI drift detection) is tracked
    separately. These tests pin down the current, deliberately limited
    behavior so a future implementation PR has a clear "before" baseline
    and doesn't accidentally change the help/error UX without noticing.
    """

    def test_no_args_prints_help_and_returns_zero(self, capsys):
        rc = main([])
        assert rc == 0
        captured = capsys.readouterr()
        assert "gsa-robot-vendor" in captured.out

    def test_help_command_returns_zero(self, capsys):
        rc = main(["help"])
        assert rc == 0

    def test_sync_command_not_implemented_returns_nonzero(self, capsys):
        rc = main(["sync"])
        assert rc == 1
        captured = capsys.readouterr()
        assert "not implemented" in captured.err

    def test_check_command_not_implemented_returns_nonzero(self, capsys):
        rc = main(["check"])
        assert rc == 1
        captured = capsys.readouterr()
        assert "not implemented" in captured.err

    def test_invalid_command_raises_system_exit(self):
        with pytest.raises(SystemExit):
            main(["bogus-command"])
