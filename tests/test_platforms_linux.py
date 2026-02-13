"""Tests for Linux platform implementation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

from pymdm.platforms.linux import (
    LinuxCommandSupport,
    LinuxDialogSupport,
    LinuxPlatformInfo,
)

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class TestLinuxPlatformInfo:
    """Tests for LinuxPlatformInfo system information retrieval."""

    def test_invalid_users(self) -> None:
        """Test that Linux-specific invalid users are defined."""
        info = LinuxPlatformInfo()
        assert "root" in info.invalid_users
        assert "" in info.invalid_users
        assert "gdm" in info.invalid_users
        assert "nobody" in info.invalid_users

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.read_text", return_value="ABC123DEF\n")
    def test_get_serial_number_sysfs(self, mock_read: Mock, mock_exists: Mock) -> None:
        """Test serial number retrieval from /sys/class/dmi."""
        info = LinuxPlatformInfo()
        serial = info.get_serial_number()
        assert serial == "ABC123DEF"

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.read_text", return_value="To Be Filled By O.E.M.\n")
    def test_get_serial_number_oem_placeholder(self, mock_read: Mock, mock_exists: Mock) -> None:
        """Test serial number treats OEM placeholders as unavailable."""
        info = LinuxPlatformInfo()
        # First attempt via sysfs returns OEM placeholder, then dmidecode fallback
        with patch("subprocess.check_output", side_effect=FileNotFoundError("no dmidecode")):
            serial = info.get_serial_number()
        assert serial is None

    @patch("pathlib.Path.exists", return_value=False)
    @patch("subprocess.check_output")
    def test_get_serial_number_dmidecode_fallback(
        self, mock_check: Mock, mock_exists: Mock
    ) -> None:
        """Test serial number falls back to dmidecode."""
        mock_check.return_value = "XYZ789\n"
        info = LinuxPlatformInfo()
        serial = info.get_serial_number()
        assert serial == "XYZ789"

    @patch("pathlib.Path.exists", return_value=False)
    @patch("subprocess.check_output", side_effect=FileNotFoundError("not found"))
    def test_get_serial_number_all_fail(self, mock_check: Mock, mock_exists: Mock) -> None:
        """Test serial number returns None when all methods fail."""
        info = LinuxPlatformInfo()
        assert info.get_serial_number() is None

    @patch("pwd.getpwnam")
    @patch("os.getlogin")
    @patch("subprocess.check_output", side_effect=FileNotFoundError("no logname"))
    def test_get_console_user_via_getlogin(
        self,
        mock_check: Mock,
        mock_login: Mock,
        mock_pwd: Mock,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Test console user retrieval via os.getlogin()."""
        monkeypatch.delenv("SUDO_USER", raising=False)
        mock_login.return_value = "testuser"
        mock_pwd_entry = Mock()
        mock_pwd_entry.pw_uid = 1000
        mock_pwd_entry.pw_dir = "/home/testuser"
        mock_pwd.return_value = mock_pwd_entry

        info = LinuxPlatformInfo()
        with patch("pathlib.Path.exists", return_value=True):
            result = info.get_console_user()

        assert result is not None
        username, uid, home = result
        assert username == "testuser"
        assert uid == 1000
        assert home == Path("/home/testuser")

    @patch("pwd.getpwnam")
    def test_get_console_user_via_sudo_user(self, mock_pwd: Mock, monkeypatch: MonkeyPatch) -> None:
        """Test console user retrieval via SUDO_USER env var."""
        monkeypatch.setenv("SUDO_USER", "adminuser")
        mock_pwd_entry = Mock()
        mock_pwd_entry.pw_uid = 1001
        mock_pwd_entry.pw_dir = "/home/adminuser"
        mock_pwd.return_value = mock_pwd_entry

        info = LinuxPlatformInfo()
        with patch("pathlib.Path.exists", return_value=True):
            result = info.get_console_user()

        assert result is not None
        assert result[0] == "adminuser"

    @patch("os.getlogin")
    @patch("subprocess.check_output", side_effect=FileNotFoundError("no logname"))
    def test_get_console_user_root_via_sudo(
        self, mock_check: Mock, mock_login: Mock, monkeypatch: MonkeyPatch
    ) -> None:
        """Test console user returns None when SUDO_USER is root."""
        monkeypatch.setenv("SUDO_USER", "root")
        mock_login.side_effect = OSError("no terminal")

        info = LinuxPlatformInfo()
        assert info.get_console_user() is None

    @patch("pwd.getpwnam")
    def test_get_user_full_name_from_gecos(self, mock_pwd: Mock) -> None:
        """Test full name retrieval from passwd GECOS field."""
        mock_entry = Mock()
        mock_entry.pw_gecos = "John Smith,Room 101,555-1234,555-5678"
        mock_pwd.return_value = mock_entry

        info = LinuxPlatformInfo()
        assert info.get_user_full_name("jsmith") == "John Smith"

    @patch("pwd.getpwnam")
    def test_get_user_full_name_simple_gecos(self, mock_pwd: Mock) -> None:
        """Test full name when GECOS has no commas."""
        mock_entry = Mock()
        mock_entry.pw_gecos = "Jane Doe"
        mock_pwd.return_value = mock_entry

        info = LinuxPlatformInfo()
        assert info.get_user_full_name("jdoe") == "Jane Doe"

    @patch("pwd.getpwnam", side_effect=KeyError("user not found"))
    def test_get_user_full_name_unknown_user(self, mock_pwd: Mock) -> None:
        """Test full name returns None for unknown user."""
        info = LinuxPlatformInfo()
        assert info.get_user_full_name("nonexistent") is None

    def test_get_hostname(self) -> None:
        """Test hostname retrieval returns a non-empty string."""
        info = LinuxPlatformInfo()
        hostname = info.get_hostname()
        assert isinstance(hostname, str)
        assert len(hostname) > 0

    def test_get_os_version_label(self) -> None:
        """Test OS version label starts with 'Linux Version:'."""
        info = LinuxPlatformInfo()
        label = info.get_os_version_label()
        assert label.startswith("Linux Version:")


class TestLinuxCommandSupport:
    """Tests for LinuxCommandSupport command execution."""

    def test_min_user_uid(self) -> None:
        """Test that Linux minimum UID is 1000."""
        support = LinuxCommandSupport()
        assert support.min_user_uid == 1000

    def test_run_as_user_command(self) -> None:
        """Test sudo -u command wrapping for Linux."""
        support = LinuxCommandSupport()
        result = support.run_as_user_command(
            ["/usr/bin/firefox"],
            username="testuser",
            uid=1000,
        )
        assert result == ["sudo", "-u", "testuser", "/usr/bin/firefox"]

    def test_validate_user_success(self) -> None:
        """Test valid Linux user passes validation."""
        support = LinuxCommandSupport()
        assert support.validate_user("testuser", 1000) is True
        assert support.validate_user("test-user", 1001) is True

    def test_validate_user_none_username(self) -> None:
        """Test that None username fails validation."""
        support = LinuxCommandSupport()
        assert support.validate_user(None, 1000) is False

    def test_validate_user_none_uid(self) -> None:
        """Test that None UID fails validation."""
        support = LinuxCommandSupport()
        assert support.validate_user("testuser", None) is False

    def test_validate_user_low_uid(self) -> None:
        """Test that UID < 1000 fails validation on Linux."""
        support = LinuxCommandSupport()
        assert support.validate_user("daemon", 1) is False
        assert support.validate_user("testuser", 999) is False

    def test_validate_user_invalid_characters(self) -> None:
        """Test that invalid username characters fail validation."""
        support = LinuxCommandSupport()
        assert support.validate_user("test user", 1000) is False
        assert support.validate_user("test@user", 1000) is False


class TestLinuxDialogSupport:
    """Tests for LinuxDialogSupport dialog configuration."""

    def test_shared_temp_dir(self) -> None:
        """Test Linux shared temp directory is /tmp."""
        support = LinuxDialogSupport()
        assert support.shared_temp_dir == "/tmp"

    def test_standard_binary_path_none(self) -> None:
        """Test that no standard dialog binary exists on Linux."""
        support = LinuxDialogSupport()
        assert support.standard_binary_path is None

    def test_dialog_not_available(self) -> None:
        """Test that dialog is not available on Linux."""
        support = LinuxDialogSupport()
        assert support.dialog_available is False

    def test_unavailable_message(self) -> None:
        """Test informative unavailable message on Linux."""
        support = LinuxDialogSupport()
        msg = support.unavailable_message
        assert "not available" in msg.lower()
        assert "Linux" in msg
