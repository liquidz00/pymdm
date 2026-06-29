"""
Windows (win32) platform implementation.

Provides system information retrieval, command execution support,
registry management, and Windows service management using
Windows-specific tools: PowerShell, wmic, net user, runas, sc.exe, winreg.
"""

from __future__ import annotations

import os
import platform
import re
import subprocess
from pathlib import Path
from typing import ClassVar

from ._base import default_get_hostname


class Win32PlatformInfo:
    """
    Windows implementation of PlatformInfo.

    Retrieves system information using Windows-specific commands:
    - PowerShell / wmic for serial numbers
    - os.getlogin() / environment variables for console user
    - net user / PowerShell for user full names
    """

    invalid_users: ClassVar[tuple[str, ...]] = (
        "",
        "SYSTEM",
        "LOCAL SERVICE",
        "NETWORK SERVICE",
    )

    def get_serial_number(self) -> str | None:
        """
        Get serial number via PowerShell (Get-CimInstance).

        Falls back to wmic if PowerShell is unavailable.

        :return: Hardware serial number, or None on failure
        :rtype: str | None
        """
        # Try PowerShell first (preferred, wmic is deprecated)
        try:
            result = subprocess.check_output(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(Get-CimInstance -ClassName Win32_BIOS).SerialNumber",
                ],
                text=True,
                timeout=15,
            )
            serial = result.strip()
            if serial and serial.lower() not in ("", "none", "to be filled by o.e.m."):
                return serial
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback to wmic
        try:
            result = subprocess.check_output(
                ["wmic", "bios", "get", "serialnumber"],
                text=True,
                timeout=15,
            )
            lines = [line.strip() for line in result.strip().splitlines() if line.strip()]
            # First line is header "SerialNumber", second is value
            if len(lines) >= 2:
                serial = lines[1]
                if serial.lower() not in ("", "none", "to be filled by o.e.m."):
                    return serial
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def get_console_user(self) -> tuple[str, int, Path] | None:
        """
        Get the currently logged-in user on Windows.

        Uses os.getlogin() for the username, and Path.home() for the
        home directory. Windows does not use UIDs in the same way as
        Unix; we return 0 as a placeholder.

        :return: Tuple of (username, uid, home_path), or None
        :rtype: tuple[str, int, Path] | None
        """
        try:
            username = os.getlogin()
        except OSError:
            # Fallback to environment variable
            username = os.environ.get("USERNAME", "")

        if not username or username in self.invalid_users:
            return None

        home_path = Path.home()
        # Windows doesn't have Unix UIDs; use 0 as placeholder
        # The uid field is kept for API compatibility
        uid = 0
        return (username, uid, home_path) if home_path.exists() else None

    def get_hostname(self) -> str:
        """
        Retrieve system hostname.

        :return: System hostname
        :rtype: str
        """
        return default_get_hostname()

    def get_user_full_name(self, username: str) -> str | None:
        """
        Get full name for a Windows user via PowerShell or net user.

        :param username: Username to look up
        :type username: str
        :return: Full display name, or None on failure
        :rtype: str | None
        """
        # Try PowerShell (more reliable for domain-joined machines)
        try:
            result = subprocess.check_output(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"(Get-LocalUser -Name '{username}').FullName",
                ],
                text=True,
                timeout=15,
            )
            full_name = result.strip()
            if full_name:
                return full_name
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback to net user
        try:
            result = subprocess.check_output(
                ["net", "user", username],
                text=True,
                timeout=15,
            )
            for line in result.splitlines():
                if line.strip().startswith("Full Name"):
                    parts = line.split(None, 2)
                    if len(parts) >= 3:
                        return parts[2].strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def get_os_version_label(self) -> str:
        """
        Return Windows version label for logging.

        :return: e.g. "Windows Version: 10.0.22631"
        :rtype: str
        """
        return f"Windows Version: {platform.version()}"


class Win32CommandSupport:
    """
    Windows implementation of PlatformCommandSupport.

    Uses ``runas`` for running commands as another user.
    Note: Windows ``runas`` prompts for a password interactively, so
    automated run-as-user is limited. For Intune scripts running as
    SYSTEM, consider using scheduled tasks or PowerShell remoting.
    """

    @property
    def min_user_uid(self) -> int:
        """
        Minimum UID threshold on Windows.

        Windows does not use numeric UIDs like Unix. This returns 0
        since UID validation is not applicable on Windows.

        :return: 0
        :rtype: int
        """
        return 0

    def run_as_user_command(self, command: list[str], username: str, uid: int) -> list[str]:
        """
        Wrap command with ``runas`` for Windows.

        Note: ``runas`` requires interactive password input. For
        non-interactive execution in MDM contexts, consider using
        PowerShell ``Start-Process -Credential`` or scheduled tasks.

        :param command: Original command arguments
        :type command: list[str]
        :param username: Target username
        :type username: str
        :param uid: Target user UID (unused on Windows)
        :type uid: int
        :return: Command prefixed with runas
        :rtype: list[str]
        """
        # Use PowerShell Start-Process for better automation support
        return [
            "powershell",
            "-NoProfile",
            "-Command",
            f"Start-Process -FilePath '{command[0]}' "
            f"-ArgumentList '{' '.join(command[1:])}' "
            f"-Credential (Get-Credential -UserName '{username}' -Message 'Enter password') "
            f"-Wait -NoNewWindow",
        ]

    def validate_user(self, username: str | None, uid: int | None) -> bool:
        """
        Validate user info for Windows.

        On Windows, we only check that a username is provided and
        contains valid characters. UID is not used.

        :param username: Username to validate
        :type username: str | None
        :param uid: User ID (ignored on Windows)
        :type uid: int | None
        :return: True if valid
        :rtype: bool
        """
        if username is None:
            return False
        # Windows usernames: alphanumeric, dots, hyphens, underscores, spaces
        if not re.match(r"^[a-zA-Z0-9._\- ]+$", username):
            return False
        return True


class Win32Registry:
    """
    Read, write, and delete Windows registry values.

    Wraps the ``winreg`` stdlib module for non-raising registry operations.
    Hive constants are exposed as class attributes for convenience.

    :Example:

        >>> val = Win32Registry.read(
        ...     Win32Registry.HKLM,
        ...     r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
        ...     "ProductName",
        ... )
    """

    HKCR: int = 0x80000000
    HKCU: int = 0x80000001
    HKLM: int = 0x80000002
    HKU: int = 0x80000003

    REG_SZ: int = 1
    REG_EXPAND_SZ: int = 2
    REG_BINARY: int = 3
    REG_DWORD: int = 4
    REG_MULTI_SZ: int = 7
    REG_QWORD: int = 11

    @staticmethod
    def read(hive: int, subkey: str, value_name: str) -> str | int | bytes | None:
        """
        Read a registry value.

        :param hive: Registry hive (e.g., Win32Registry.HKLM)
        :type hive: int
        :param subkey: Registry subkey path
        :type subkey: str
        :param value_name: Name of the value to read
        :type value_name: str
        :return: Value, or None if the key/value doesn't exist
        :rtype: str | int | bytes | None
        """
        try:
            import winreg

            with winreg.OpenKey(hive, subkey) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
                return value
        except (OSError, ImportError):
            return None

    @staticmethod
    def write(
        hive: int,
        subkey: str,
        value_name: str,
        value: str | int,
        value_type: int | None = None,
    ) -> bool:
        """
        Write a registry value. Creates the subkey if it doesn't exist.

        :param hive: Registry hive (e.g., Win32Registry.HKLM)
        :type hive: int
        :param subkey: Registry subkey path
        :type subkey: str
        :param value_name: Name of the value to write
        :type value_name: str
        :param value: Value to set
        :type value: str | int
        :param value_type: Registry type (e.g., Win32Registry.REG_SZ).
            Auto-detected from value type if omitted.
        :type value_type: int | None
        :return: True if successful
        :rtype: bool
        """
        try:
            import winreg

            if value_type is None:
                value_type = winreg.REG_SZ if isinstance(value, str) else winreg.REG_DWORD
            with winreg.CreateKeyEx(hive, subkey) as key:
                winreg.SetValueEx(key, value_name, 0, value_type, value)
            return True
        except (OSError, ImportError):
            return False

    @staticmethod
    def delete(hive: int, subkey: str, value_name: str) -> bool:
        """
        Delete a registry value.

        :param hive: Registry hive (e.g., Win32Registry.HKLM)
        :type hive: int
        :param subkey: Registry subkey path
        :type subkey: str
        :param value_name: Name of the value to delete
        :type value_name: str
        :return: True if deleted, False if missing or failed
        :rtype: bool
        """
        try:
            import winreg

            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, value_name)
            return True
        except (OSError, ImportError):
            return False


class Win32ServiceManager:
    """
    Manage Windows services via ``sc.exe``.

    :Example:

        >>> if Win32ServiceManager.is_running("CrowdStrike Falcon"):
        ...     Win32ServiceManager.stop("CrowdStrike Falcon")
    """

    @staticmethod
    def is_running(service_name: str) -> bool:
        """
        Check if a Windows service is running.

        :param service_name: Service name
        :type service_name: str
        :return: True if the service is currently running
        :rtype: bool
        """
        result = subprocess.run(
            ["sc", "query", service_name],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and "RUNNING" in result.stdout

    @staticmethod
    def stop(service_name: str) -> bool:
        """
        Stop a Windows service.

        :param service_name: Service name
        :type service_name: str
        :return: True if successfully stopped
        :rtype: bool
        """
        result = subprocess.run(
            ["sc", "stop", service_name],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    @staticmethod
    def start(service_name: str) -> bool:
        """
        Start a Windows service.

        :param service_name: Service name
        :type service_name: str
        :return: True if successfully started
        :rtype: bool
        """
        result = subprocess.run(
            ["sc", "start", service_name],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    @staticmethod
    def delete(service_name: str) -> bool:
        """
        Delete (remove) a Windows service.

        :param service_name: Service name
        :type service_name: str
        :return: True if successfully deleted
        :rtype: bool
        """
        result = subprocess.run(
            ["sc", "delete", service_name],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
