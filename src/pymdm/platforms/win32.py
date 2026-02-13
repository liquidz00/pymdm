"""
Windows (win32) platform implementation.

Provides system information retrieval and command execution support
using Windows-specific tools: PowerShell, wmic, net user, runas.
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
    """Windows implementation of PlatformInfo.

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
        """Get serial number via PowerShell (Get-CimInstance).

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
        """Get the currently logged-in user on Windows.

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
        """Retrieve system hostname.

        :return: System hostname
        :rtype: str
        """
        return default_get_hostname()

    def get_user_full_name(self, username: str) -> str | None:
        """Get full name for a Windows user via PowerShell or net user.

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
        """Return Windows version label for logging.

        :return: e.g. "Windows Version: 10.0.22631"
        :rtype: str
        """
        return f"Windows Version: {platform.version()}"


class Win32CommandSupport:
    """Windows implementation of PlatformCommandSupport.

    Uses ``runas`` for running commands as another user.
    Note: Windows ``runas`` prompts for a password interactively, so
    automated run-as-user is limited. For Intune scripts running as
    SYSTEM, consider using scheduled tasks or PowerShell remoting.
    """

    @property
    def min_user_uid(self) -> int:
        """Minimum UID threshold on Windows.

        Windows does not use numeric UIDs like Unix. This returns 0
        since UID validation is not applicable on Windows.

        :return: 0
        :rtype: int
        """
        return 0

    def run_as_user_command(self, command: list[str], username: str, uid: int) -> list[str]:
        """Wrap command with ``runas`` for Windows.

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
        cmd_str = subprocess.list2cmdline(command)
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
        """Validate user info for Windows.

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
