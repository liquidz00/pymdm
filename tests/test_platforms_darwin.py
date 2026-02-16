"""Tests for macOS (Darwin) platform implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

from pymdm.platforms.darwin import (
    DarwinCommandSupport,
    DarwinPlatformInfo,
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
        assert support.validate_user("test@user", 501) is False

    def test_validate_user_valid_special_chars(self) -> None:
        """Test that allowed special characters pass validation."""
        support = DarwinCommandSupport()
        assert support.validate_user("test-user", 501) is True
        assert support.validate_user("test_user", 501) is True
        assert support.validate_user("first.last", 501) is True
