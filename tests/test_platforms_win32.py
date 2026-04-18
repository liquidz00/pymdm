"""Tests for Windows (win32) platform implementation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

from pymdm.platforms.win32 import (
    Win32CommandSupport,
    Win32PlatformInfo,
    Win32Registry,
    Win32ServiceManager,
)

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class TestWin32PlatformInfo:
    """Tests for Win32PlatformInfo system information retrieval."""

    def test_invalid_users(self) -> None:
        """Test that Windows-specific invalid users are defined."""
        info = Win32PlatformInfo()
        assert "" in info.invalid_users
        assert "SYSTEM" in info.invalid_users
        assert "LOCAL SERVICE" in info.invalid_users
        assert "NETWORK SERVICE" in info.invalid_users

    @patch("pymdm.platforms.win32.subprocess.check_output")
    def test_get_serial_number_powershell(self, mock_check: Mock) -> None:
        """Test serial number retrieval via PowerShell."""
        mock_check.return_value = "ABC123DEF\n"
        info = Win32PlatformInfo()
        serial = info.get_serial_number()
        assert serial == "ABC123DEF"

    @patch("pymdm.platforms.win32.subprocess.check_output")
    def test_get_serial_number_powershell_fallback_wmic(self, mock_check: Mock) -> None:
        """Test serial number falls back to wmic when PowerShell fails."""
        # First call (PowerShell) fails, second call (wmic) succeeds
        mock_check.side_effect = [
            subprocess.CalledProcessError(1, "powershell"),
            "SerialNumber  \nABC123DEF  \n",
        ]
        info = Win32PlatformInfo()
        serial = info.get_serial_number()
        assert serial == "ABC123DEF"

    @patch("pymdm.platforms.win32.subprocess.check_output")
    def test_get_serial_number_all_fail(self, mock_check: Mock) -> None:
        """Test serial number returns None when all methods fail."""
        mock_check.side_effect = FileNotFoundError("not found")
        info = Win32PlatformInfo()
        assert info.get_serial_number() is None

    @patch("pymdm.platforms.win32.subprocess.check_output")
    def test_get_serial_number_oem_placeholder(self, mock_check: Mock) -> None:
        """Test serial number treats OEM placeholders as None."""
        mock_check.return_value = "To Be Filled By O.E.M.\n"
        info = Win32PlatformInfo()
        assert info.get_serial_number() is None

    @patch("pymdm.platforms.win32.os.getlogin")
    def test_get_console_user_success(self, mock_login: Mock) -> None:
        """Test successful console user retrieval."""
        mock_login.return_value = "testuser"
        info = Win32PlatformInfo()

        with patch.object(Path, "home", return_value=Path("C:/Users/testuser")):
            with patch("pathlib.Path.exists", return_value=True):
                result = info.get_console_user()

        assert result is not None
        username, uid, home = result
        assert username == "testuser"
        assert uid == 0  # Windows placeholder

    @patch("pymdm.platforms.win32.os.getlogin")
    def test_get_console_user_system(self, mock_login: Mock) -> None:
        """Test console user returns None for SYSTEM account."""
        mock_login.return_value = "SYSTEM"
        info = Win32PlatformInfo()
        assert info.get_console_user() is None

    @patch("pymdm.platforms.win32.os.getlogin")
    def test_get_console_user_os_error(self, mock_login: Mock, monkeypatch: MonkeyPatch) -> None:
        """Test console user falls back to USERNAME env var."""
        mock_login.side_effect = OSError("No console")
        monkeypatch.setenv("USERNAME", "fallbackuser")
        info = Win32PlatformInfo()

        with patch.object(Path, "home", return_value=Path("C:/Users/fallbackuser")):
            with patch("pathlib.Path.exists", return_value=True):
                result = info.get_console_user()

        assert result is not None
        assert result[0] == "fallbackuser"

    @patch("pymdm.platforms.win32.subprocess.check_output")
    def test_get_user_full_name_powershell(self, mock_check: Mock) -> None:
        """Test full name retrieval via PowerShell."""
        mock_check.return_value = "John Smith\n"
        info = Win32PlatformInfo()
        assert info.get_user_full_name("jsmith") == "John Smith"

    @patch("pymdm.platforms.win32.subprocess.check_output")
    def test_get_user_full_name_net_user_fallback(self, mock_check: Mock) -> None:
        """Test full name falls back to net user when PowerShell fails."""
        mock_check.side_effect = [
            subprocess.CalledProcessError(1, "powershell"),
            "User name                    jsmith\nFull Name                    John Smith\n",
        ]
        info = Win32PlatformInfo()
        assert info.get_user_full_name("jsmith") == "John Smith"

    @patch("pymdm.platforms.win32.subprocess.check_output")
    def test_get_user_full_name_failure(self, mock_check: Mock) -> None:
        """Test full name returns None when all methods fail."""
        mock_check.side_effect = FileNotFoundError("not found")
        info = Win32PlatformInfo()
        assert info.get_user_full_name("nonexistent") is None

    def test_get_hostname(self) -> None:
        """Test hostname retrieval returns a non-empty string."""
        info = Win32PlatformInfo()
        hostname = info.get_hostname()
        assert isinstance(hostname, str)
        assert len(hostname) > 0

    def test_get_os_version_label(self) -> None:
        """Test OS version label starts with 'Windows Version:'."""
        info = Win32PlatformInfo()
        label = info.get_os_version_label()
        assert label.startswith("Windows Version:")


class TestWin32CommandSupport:
    """Tests for Win32CommandSupport command execution."""

    def test_min_user_uid(self) -> None:
        """Test that Windows minimum UID is 0 (not applicable)."""
        support = Win32CommandSupport()
        assert support.min_user_uid == 0

    def test_validate_user_success(self) -> None:
        """Test valid Windows username passes validation."""
        support = Win32CommandSupport()
        assert support.validate_user("testuser", None) is True
        assert support.validate_user("test.user", None) is True
        assert support.validate_user("Test User", None) is True

    def test_validate_user_none_username(self) -> None:
        """Test that None username fails validation."""
        support = Win32CommandSupport()
        assert support.validate_user(None, 0) is False

    def test_validate_user_invalid_characters(self) -> None:
        """Test that invalid characters fail validation."""
        support = Win32CommandSupport()
        assert support.validate_user("test@user", 0) is False
        assert support.validate_user("test/user", 0) is False

    def test_run_as_user_command(self) -> None:
        """Test PowerShell run-as-user command wrapping."""
        support = Win32CommandSupport()
        result = support.run_as_user_command(
            ["notepad.exe", "test.txt"],
            username="testuser",
            uid=0,
        )
        assert result[0] == "powershell"
        assert "-NoProfile" in result
        assert "testuser" in " ".join(result)


class TestWin32Registry:
    """Tests for Win32Registry operations."""

    def test_hive_constants(self) -> None:
        assert Win32Registry.HKLM == 0x80000002
        assert Win32Registry.HKCU == 0x80000001
        assert Win32Registry.HKCR == 0x80000000
        assert Win32Registry.HKU == 0x80000003

    def test_type_constants(self) -> None:
        assert Win32Registry.REG_SZ == 1
        assert Win32Registry.REG_DWORD == 4
        assert Win32Registry.REG_BINARY == 3

    @patch.dict("sys.modules", {"winreg": Mock()})
    def test_read_existing_value(self) -> None:
        import sys

        mock_winreg = sys.modules["winreg"]
        mock_key = Mock()
        mock_key.__enter__ = Mock(return_value=mock_key)
        mock_key.__exit__ = Mock(return_value=False)
        mock_winreg.OpenKey.return_value = mock_key
        mock_winreg.QueryValueEx.return_value = ("Windows 11 Pro", 1)

        result = Win32Registry.read(
            Win32Registry.HKLM,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
            "ProductName",
        )
        assert result == "Windows 11 Pro"

    def test_read_missing_value(self) -> None:
        result = Win32Registry.read(Win32Registry.HKLM, r"SOFTWARE\Nonexistent", "Key")
        assert result is None

    @patch.dict("sys.modules", {"winreg": Mock()})
    def test_write_string(self) -> None:
        import sys

        mock_winreg = sys.modules["winreg"]
        mock_winreg.REG_SZ = 1
        mock_key = Mock()
        mock_key.__enter__ = Mock(return_value=mock_key)
        mock_key.__exit__ = Mock(return_value=False)
        mock_winreg.CreateKeyEx.return_value = mock_key

        result = Win32Registry.write(Win32Registry.HKLM, r"SOFTWARE\Test", "Setting", "value")
        assert result is True
        mock_winreg.SetValueEx.assert_called_once()

    @patch.dict("sys.modules", {"winreg": Mock()})
    def test_write_int_autodetects_dword(self) -> None:
        import sys

        mock_winreg = sys.modules["winreg"]
        mock_winreg.REG_DWORD = 4
        mock_key = Mock()
        mock_key.__enter__ = Mock(return_value=mock_key)
        mock_key.__exit__ = Mock(return_value=False)
        mock_winreg.CreateKeyEx.return_value = mock_key

        result = Win32Registry.write(Win32Registry.HKLM, r"SOFTWARE\Test", "Count", 42)
        assert result is True
        call_args = mock_winreg.SetValueEx.call_args[0]
        assert call_args[3] == 4  # REG_DWORD

    @patch.dict("sys.modules", {"winreg": Mock()})
    def test_delete_existing(self) -> None:
        import sys

        mock_winreg = sys.modules["winreg"]
        mock_winreg.KEY_SET_VALUE = 0x0002
        mock_key = Mock()
        mock_key.__enter__ = Mock(return_value=mock_key)
        mock_key.__exit__ = Mock(return_value=False)
        mock_winreg.OpenKey.return_value = mock_key

        result = Win32Registry.delete(Win32Registry.HKLM, r"SOFTWARE\Test", "Setting")
        assert result is True

    def test_delete_missing(self) -> None:
        result = Win32Registry.delete(Win32Registry.HKLM, r"SOFTWARE\Nonexistent", "Key")
        assert result is False


class TestWin32ServiceManager:
    """Tests for Win32ServiceManager operations."""

    @patch("subprocess.run")
    def test_is_running_true(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=0, stdout="STATE : 4  RUNNING")
        assert Win32ServiceManager.is_running("CrowdStrike Falcon") is True

    @patch("subprocess.run")
    def test_is_running_false_stopped(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=0, stdout="STATE : 1  STOPPED")
        assert Win32ServiceManager.is_running("SomeService") is False

    @patch("subprocess.run")
    def test_is_running_false_not_found(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=1060, stdout="")
        assert Win32ServiceManager.is_running("Nonexistent") is False

    @patch("subprocess.run")
    def test_stop_success(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=0)
        assert Win32ServiceManager.stop("TestService") is True
        assert mock_run.call_args[0][0] == ["sc", "stop", "TestService"]

    @patch("subprocess.run")
    def test_start_success(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=0)
        assert Win32ServiceManager.start("TestService") is True
        assert mock_run.call_args[0][0] == ["sc", "start", "TestService"]

    @patch("subprocess.run")
    def test_delete_success(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=0)
        assert Win32ServiceManager.delete("TestService") is True
        assert mock_run.call_args[0][0] == ["sc", "delete", "TestService"]

    @patch("subprocess.run")
    def test_stop_failure(self, mock_run: Mock) -> None:
        mock_run.return_value = Mock(returncode=1)
        assert Win32ServiceManager.stop("TestService") is False
