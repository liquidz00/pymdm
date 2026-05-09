"""Tests for macOS (Darwin) platform implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

from pymdm.platforms.darwin import (
    DarwinCommandSupport,
    DarwinDefaults,
    DarwinPlatformInfo,
    DarwinServiceManager,
)

if TYPE_CHECKING:
    pass


class TestDarwinPlatformInfo:
    """Tests for DarwinPlatformInfo system information retrieval."""

    def test_invalid_users(self) -> None:
        """Test that macOS-specific invalid users are defined."""
        info = DarwinPlatformInfo()
        assert "root" in info.invalid_users
        assert "" in info.invalid_users
        assert "loginwindow" in info.invalid_users
        assert "_mbsetupuser" in info.invalid_users

    @patch("pymdm.platforms.darwin.subprocess.check_output")
    def test_get_serial_number_success(self, mock_check: Mock) -> None:
        """Test successful serial number retrieval via system_profiler."""
        mock_check.return_value = json.dumps(
            {"SPHardwareDataType": [{"serial_number": "C02ABC123DEF"}]}
        )
        info = DarwinPlatformInfo()
        serial = info.get_serial_number()
        assert serial == "C02ABC123DEF"
        mock_check.assert_called_once()

    @patch("pymdm.platforms.darwin.subprocess.check_output")
    def test_get_serial_number_failure(self, mock_check: Mock) -> None:
        """Test serial number returns None on failure."""
        mock_check.side_effect = Exception("Command failed")
        info = DarwinPlatformInfo()
        assert info.get_serial_number() is None

    @patch("pymdm.platforms.darwin.subprocess.check_output")
    def test_get_serial_number_bad_json(self, mock_check: Mock) -> None:
        """Test serial number returns None on bad JSON."""
        mock_check.return_value = "not json"
        info = DarwinPlatformInfo()
        assert info.get_serial_number() is None

    @patch("pymdm.platforms.darwin.subprocess.check_output")
    def test_get_console_user_success(self, mock_check: Mock) -> None:
        """Test successful console user retrieval."""
        mock_check.side_effect = ["testuser\n", "501\n"]
        info = DarwinPlatformInfo()

        with patch("pathlib.Path.exists", return_value=True):
            result = info.get_console_user()

        assert result is not None
        username, uid, home = result
        assert username == "testuser"
        assert uid == 501
        assert home == Path("/Users/testuser")

    @patch("pymdm.platforms.darwin.subprocess.check_output")
    def test_get_console_user_invalid_user(self, mock_check: Mock) -> None:
        """Test console user returns None for invalid users (loginwindow, etc.)."""
        mock_check.return_value = "loginwindow\n"
        info = DarwinPlatformInfo()
        assert info.get_console_user() is None

    @patch("pymdm.platforms.darwin.subprocess.check_output")
    def test_get_console_user_root(self, mock_check: Mock) -> None:
        """Test console user returns None when root is at console."""
        mock_check.return_value = "root\n"
        info = DarwinPlatformInfo()
        assert info.get_console_user() is None

    @patch("pymdm.platforms.darwin.subprocess.check_output")
    def test_get_console_user_missing_home(self, mock_check: Mock) -> None:
        """Test console user returns None if home directory doesn't exist."""
        mock_check.side_effect = ["testuser\n", "501\n"]
        info = DarwinPlatformInfo()

        with patch("pathlib.Path.exists", return_value=False):
            assert info.get_console_user() is None

    @patch("pymdm.platforms.darwin.subprocess.check_output")
    def test_get_console_user_stat_failure(self, mock_check: Mock) -> None:
        """Test console user returns None when stat command fails."""
        import subprocess

        mock_check.side_effect = subprocess.CalledProcessError(1, "stat")
        info = DarwinPlatformInfo()
        assert info.get_console_user() is None

    def test_get_hostname(self) -> None:
        """Test hostname retrieval returns a non-empty string."""
        info = DarwinPlatformInfo()
        hostname = info.get_hostname()
        assert isinstance(hostname, str)
        assert len(hostname) > 0

    @patch("pymdm.platforms.darwin.subprocess.check_output")
    def test_get_user_full_name_success(self, mock_check: Mock) -> None:
        """Test successful full name retrieval via id -F."""
        mock_check.return_value = "John Smith\n"
        info = DarwinPlatformInfo()
        assert info.get_user_full_name("jsmith") == "John Smith"

    @patch("pymdm.platforms.darwin.subprocess.check_output")
    def test_get_user_full_name_failure(self, mock_check: Mock) -> None:
        """Test full name returns None on failure."""
        mock_check.side_effect = Exception("id failed")
        info = DarwinPlatformInfo()
        assert info.get_user_full_name("nonexistent") is None

    def test_get_os_version_label(self) -> None:
        """Test OS version label starts with 'macOS Version:'."""
        info = DarwinPlatformInfo()
        label = info.get_os_version_label()
        assert label.startswith("macOS Version:")

    @patch("pymdm.platforms.darwin.platform.mac_ver")
    def test_get_os_version_label_uses_product_version(self, mock_mac_ver: Mock) -> None:
        """Label uses the macOS productVersion, not the Darwin kernel version.

        Regression: previously used platform.release() which returns the
        Darwin kernel (e.g. "25.4.0" on macOS 26.4.1). Users expect the
        marketing version they see in About This Mac.
        """
        mock_mac_ver.return_value = ("26.4.1", ("", "", ""), "arm64")
        info = DarwinPlatformInfo()
        assert info.get_os_version_label() == "macOS Version: 26.4.1"

    @patch("pymdm.platforms.darwin.platform.release")
    @patch("pymdm.platforms.darwin.platform.mac_ver")
    def test_get_os_version_label_falls_back_when_mac_ver_empty(
        self, mock_mac_ver: Mock, mock_release: Mock
    ) -> None:
        """If mac_ver() returns empty (SystemVersion.plist unreadable), fall back to release()."""
        mock_mac_ver.return_value = ("", ("", "", ""), "")
        mock_release.return_value = "25.4.0"
        info = DarwinPlatformInfo()
        assert info.get_os_version_label() == "macOS Version: 25.4.0"


class TestDarwinCommandSupport:
    """Tests for DarwinCommandSupport command execution."""

    def test_min_user_uid(self) -> None:
        """Test that macOS minimum UID is 500."""
        support = DarwinCommandSupport()
        assert support.min_user_uid == 500

    def test_run_as_user_command(self) -> None:
        """Test launchctl asuser command wrapping."""
        support = DarwinCommandSupport()
        result = support.run_as_user_command(
            ["/usr/bin/open", "-a", "Safari"],
            username="testuser",
            uid=501,
        )
        assert result == [
            "/bin/launchctl",
            "asuser",
            "501",
            "sudo",
            "-u",
            "testuser",
            "/usr/bin/open",
            "-a",
            "Safari",
        ]

    def test_validate_user_success(self) -> None:
        """Test valid user passes validation."""
        support = DarwinCommandSupport()
        assert support.validate_user("testuser", 501) is True

    def test_validate_user_none_username(self) -> None:
        """Test that None username fails validation."""
        support = DarwinCommandSupport()
        assert support.validate_user(None, 501) is False

    def test_validate_user_none_uid(self) -> None:
        """Test that None UID fails validation."""
        support = DarwinCommandSupport()
        assert support.validate_user("testuser", None) is False

    def test_validate_user_low_uid(self) -> None:
        """Test that UID < 500 fails validation on macOS."""
        support = DarwinCommandSupport()
        assert support.validate_user("daemon", 1) is False
        assert support.validate_user("testuser", 499) is False

    def test_validate_user_invalid_characters(self) -> None:
        """Test that invalid username characters fail validation."""
        support = DarwinCommandSupport()
        assert support.validate_user("test user", 501) is False
        assert support.validate_user("test;user", 501) is False

    def test_validate_user_valid_special_chars(self) -> None:
        """Test that allowed special characters pass validation."""
        support = DarwinCommandSupport()
        assert support.validate_user("test-user", 501) is True
        assert support.validate_user("test_user", 501) is True
        assert support.validate_user("first.last", 501) is True
        assert support.validate_user("user@domain.com", 501) is True


class TestDarwinDefaults:
    """Tests for DarwinDefaults plist operations.

    Covers both root-context calls (no CommandRunner needed) and
    user-context calls via ``as_user=True`` with a configured runner.
    """

    @patch("pymdm.platforms.darwin.subprocess.run")
    def test_read_existing_key(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=0, stdout="1\n")
        defaults = DarwinDefaults()
        result = defaults.read("com.apple.finder", "ShowHardDrivesOnDesktop")
        assert result == "1"
        assert mock_run.call_args[0][0] == [
            "/usr/bin/defaults",
            "read",
            "com.apple.finder",
            "ShowHardDrivesOnDesktop",
        ]

    @patch("pymdm.platforms.darwin.subprocess.run")
    def test_read_missing_key(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=1, stdout="")
        result = DarwinDefaults().read("com.apple.finder", "NonexistentKey")
        assert result is None

    @patch("pymdm.platforms.darwin.subprocess.run")
    def test_write_string(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=0)
        result = DarwinDefaults().write("com.example.app", "Setting", "value")
        assert result is True
        assert mock_run.call_args[0][0] == [
            "/usr/bin/defaults",
            "write",
            "com.example.app",
            "Setting",
            "-string",
            "value",
        ]

    @patch("pymdm.platforms.darwin.subprocess.run")
    def test_write_bool(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=0)
        result = DarwinDefaults().write("com.example.app", "Enabled", "true", "-bool")
        assert result is True
        assert "-bool" in mock_run.call_args[0][0]

    @patch("pymdm.platforms.darwin.subprocess.run")
    def test_write_failure(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=1)
        result = DarwinDefaults().write("com.example.app", "Setting", "value")
        assert result is False

    @patch("pymdm.platforms.darwin.subprocess.run")
    def test_delete_existing(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=0)
        result = DarwinDefaults().delete("com.example.app", "Setting")
        assert result is True

    @patch("pymdm.platforms.darwin.subprocess.run")
    def test_delete_missing(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=1)
        result = DarwinDefaults().delete("com.example.app", "NonexistentKey")
        assert result is False

    def test_as_user_without_runner_raises(self) -> None:
        """as_user=True with no runner is a configuration error."""
        defaults = DarwinDefaults()
        with pytest.raises(ValueError, match="requires a CommandRunner"):
            defaults.read("com.apple.dock", "orientation", as_user=True)

    def test_as_user_with_partial_runner_raises(self) -> None:
        """as_user=True with a runner missing username/uid is a configuration error."""
        from pymdm import CommandRunner

        defaults = DarwinDefaults(runner=CommandRunner())  # no username/uid
        with pytest.raises(ValueError, match="username and uid"):
            defaults.read("com.apple.dock", "orientation", as_user=True)

    def test_as_user_read_uses_runner_run_as_user(self) -> None:
        """as_user=True dispatches through CommandRunner.run_as_user."""
        from unittest.mock import MagicMock

        runner = MagicMock()
        runner.username = "jappleseed"
        runner.uid = 501
        runner.run_as_user.return_value = Mock(returncode=0, stdout="bottom\n")

        defaults = DarwinDefaults(runner=runner)
        result = defaults.read("com.apple.dock", "orientation", as_user=True)

        assert result == "bottom"
        runner.run_as_user.assert_called_once_with(
            ["/usr/bin/defaults", "read", "com.apple.dock", "orientation"],
            check=False,
        )

    def test_as_user_write_uses_runner_run_as_user(self) -> None:
        """as_user=True writes route through CommandRunner.run_as_user."""
        from unittest.mock import MagicMock

        runner = MagicMock()
        runner.username = "jappleseed"
        runner.uid = 501
        runner.run_as_user.return_value = Mock(returncode=0)

        defaults = DarwinDefaults(runner=runner)
        result = defaults.write("com.apple.dock", "tilesize", "48", "-int", as_user=True)

        assert result is True
        called_cmd = runner.run_as_user.call_args[0][0]
        assert called_cmd == [
            "/usr/bin/defaults",
            "write",
            "com.apple.dock",
            "tilesize",
            "-int",
            "48",
        ]

    def test_as_user_false_uses_subprocess_even_with_runner(self) -> None:
        """A configured runner is ignored when as_user=False — instance can do both."""
        from unittest.mock import MagicMock

        runner = MagicMock()
        runner.username = "jappleseed"
        runner.uid = 501
        defaults = DarwinDefaults(runner=runner)

        with patch("pymdm.platforms.darwin.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="ok\n")
            defaults.read("com.apple.SoftwareUpdate", "AutomaticCheckEnabled")
            mock_run.assert_called_once()
        runner.run_as_user.assert_not_called()


class TestDarwinServiceManager:
    """Tests for DarwinServiceManager launchctl operations."""

    @patch("subprocess.run")
    def test_is_loaded_true(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=0)
        assert DarwinServiceManager.is_loaded("system/com.example.daemon") is True
        assert mock_run.call_args[0][0] == ["/bin/launchctl", "print", "system/com.example.daemon"]

    @patch("subprocess.run")
    def test_is_loaded_false(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=113)
        assert DarwinServiceManager.is_loaded("system/com.example.daemon") is False

    @patch("subprocess.run")
    def test_bootout_success(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=0)
        assert DarwinServiceManager.bootout("system/com.example.daemon") is True
        assert mock_run.call_args[0][0] == [
            "/bin/launchctl",
            "bootout",
            "system/com.example.daemon",
        ]

    @patch("subprocess.run")
    def test_bootout_failure(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=3)
        assert DarwinServiceManager.bootout("system/com.example.daemon") is False

    @patch("subprocess.run")
    def test_bootstrap_success(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=0)
        result = DarwinServiceManager.bootstrap(
            "system", "/Library/LaunchDaemons/com.example.daemon.plist"
        )
        assert result is True
        assert mock_run.call_args[0][0] == [
            "/bin/launchctl",
            "bootstrap",
            "system",
            "/Library/LaunchDaemons/com.example.daemon.plist",
        ]

    @patch("subprocess.run")
    def test_bootstrap_failure(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=1)
        result = DarwinServiceManager.bootstrap("system", "/nonexistent.plist")
        assert result is False
