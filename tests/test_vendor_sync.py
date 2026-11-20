from __future__ import annotations

from pathlib import Path

import pytest

from gsa_compliance_robot.vendor_sync import (
    LOCKFILE_NAME,
    check_resources,
    main,
    sync_resources,
)


def test_no_args_prints_help_and_returns_zero(capsys):
    rc = main([])
    assert rc == 0
    captured = capsys.readouterr()
    assert "gsa-robot-vendor" in captured.out


def test_help_command_returns_zero(capsys):
    rc = main(["help"])
    assert rc == 0


def test_sync_and_check_roundtrip(tmp_path: Path, capsys):
    dest = tmp_path / "vendor"
    rc_sync = main(["sync", "--dest", str(dest), "--version", "0.2.0"])
    assert rc_sync == 0
    assert (dest / LOCKFILE_NAME).is_file()
    env_res = dest / "env.resource"
    assert env_res.is_file()
    assert env_res.read_text(encoding="utf-8").startswith(
        "# VENDORED from gsa-compliance-robot v0.2.0 \u2014 do not edit\n"
    )

    rc_check = main(["check", "--dest", str(dest), "--version", "0.2.0"])
    assert rc_check == 0
    rc_sync_check = main(
        ["sync", "--check", "--dest", str(dest), "--version", "0.2.0"]
    )
    assert rc_sync_check == 0
    captured = capsys.readouterr()
    assert "OK" in captured.out


def test_check_detects_tampered_missing_and_extra_files(tmp_path: Path, capsys):
    dest = tmp_path / "vendor"
    sync_resources(dest, version="0.2.0")

    # Tamper with a resource file
    env_res = dest / "env.resource"
    env_res.write_text(
        env_res.read_text(encoding="utf-8") + "# drift\n", encoding="utf-8"
    )
    errors = check_resources(dest, version="0.2.0")
    assert any("Content/SHA-256 mismatch for env.resource" in e for e in errors)
    rc_tamper = main(["check", "--dest", str(dest)])
    assert rc_tamper == 1
    captured = capsys.readouterr()
    assert "DRIFT" in captured.err

    # Restore and add an unexpected extra .resource file
    sync_resources(dest, version="0.2.0")
    (dest / "extra.resource").write_text("*** Keywords ***\n", encoding="utf-8")
    errors = check_resources(dest, version="0.2.0")
    assert any("Unexpected extra resource file" in e for e in errors)

    # Remove lockfile
    (dest / "extra.resource").unlink()
    (dest / LOCKFILE_NAME).unlink()
    errors = check_resources(dest, version="0.2.0")
    assert any("Missing lockfile" in e for e in errors)


def test_invalid_command_raises_system_exit():
    with pytest.raises(SystemExit):
        main(["bogus-command"])
