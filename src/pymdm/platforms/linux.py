"""
Linux platform implementation.

Provides system information retrieval and command execution support
using Linux-specific tools and /proc, /sys, /etc filesystems.
"""

from __future__ import annotations

import os
import platform
import pwd
import re
import subprocess
from pathlib import Path
from typing import ClassVar

from ._base import default_get_hostname


class LinuxPlatformInfo:
    """Linux implementation of PlatformInfo.

    Retrieves system information using:
    - dmidecode or /sys/class/dmi for serial numbers
    - who / logname / environment for console user
    - getent / passwd for user full names
    """

    invalid_users: ClassVar[tuple[str, ...]] = (
        "root",
        "",
        "gdm",
        "lightdm",
        "sddm",
        "nobody",
    )

    def get_serial_number(self) -> str | None:
        """Get serial number from DMI data.

        Tries /sys/class/dmi/id/product_serial first (no root needed),
        then falls back to dmidecode (requires root).

        :return: Hardware serial number, or None on failure
        :rtype: str | None
        """
        # Try sysfs first (no root required)
        dmi_path = Path("/sys/class/dmi/id/product_serial")
        try:
            if dmi_path.exists():
                serial = dmi_path.read_text().strip()
                if serial and serial.lower() not in ("", "none", "to be filled by o.e.m."):
                    return serial
        except (PermissionError, OSError):
            pass

        # Fallback to dmidecode (requires root)
        try:
            result = subprocess.check_output(
                ["dmidecode", "-s", "system-serial-number"],
                text=True,
                timeout=10,
            )
            serial = result.strip()
            if serial and serial.lower() not in ("", "none", "to be filled by o.e.m."):
                return serial
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def get_console_user(self) -> tuple[str, int, Path] | None:
        """Get the currently logged-in user on Linux.

        Tries multiple methods: SUDO_USER env var (for scripts run via sudo),
        logname, then os.getlogin().

        :return: Tuple of (username, uid, home_path), or None
        :rtype: tuple[str, int, Path] | None
        """
        username = None

        # If running as root via sudo, get the original user
        sudo_user = os.environ.get("SUDO_USER")
        if sudo_user and sudo_user not in self.invalid_users:
            username = sudo_user

        # Try logname
        if not username:
            try:
                result = subprocess.check_output(["logname"], text=True, timeout=5).strip()
                if result and result not in self.invalid_users:
                    username = result
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                pass

        # Fallback to os.getlogin
        if not username:
            try:
                login = os.getlogin()
                if login and login not in self.invalid_users:
                    username = login
            except OSError:
                pass

        if not username:
            return None

        # Get UID and home directory from passwd database
        try:
            pw = pwd.getpwnam(username)
            uid = pw.pw_uid
            home_path = Path(pw.pw_dir)
        except KeyError:
            return None

        return (username, uid, home_path) if home_path.exists() else None

    def get_hostname(self) -> str:
        """Retrieve system hostname.

        :return: System hostname
        :rtype: str
        """
        return default_get_hostname()

    def get_user_full_name(self, username: str) -> str | None:
        """Get full name for a user from the passwd database (GECOS field).

        :param username: Username to look up
        :type username: str
        :return: Full display name, or None on failure
        :rtype: str | None
        """
        try:
            pw = pwd.getpwnam(username)
            # GECOS field format: "Full Name,Room,Work Phone,Home Phone,Other"
            gecos = pw.pw_gecos
            if gecos:
                # Take just the full name part (before first comma)
                full_name = gecos.split(",")[0].strip()
                return full_name if full_name else None
        except KeyError:
            pass
        return None

    def get_os_version_label(self) -> str:
        """Return Linux version label for logging.

        :return: e.g. "Linux Version: 6.1.0-generic"
        :rtype: str
        """
        return f"Linux Version: {platform.release()}"


class LinuxDialogSupport:
    """Linux implementation of PlatformDialogSupport.

    swiftDialog is not available on Linux. Dialog functionality
    returns graceful "not supported" responses. Future implementations
    may integrate with zenity, kdialog, or similar tools.
    """

    @property
    def shared_temp_dir(self) -> str:
        """Shared temp directory on Linux.

        :return: "/tmp"
        :rtype: str
        """
        return "/tmp"

    @property
    def standard_binary_path(self) -> str | None:
        """No standard swiftDialog binary on Linux.

        :return: None
        :rtype: str | None
        """
        return None

    @property
    def dialog_available(self) -> bool:
        """swiftDialog is not available on Linux.

        :return: False
        :rtype: bool
        """
        return False

    @property
    def unavailable_message(self) -> str:
        """Explanation for why dialogs are unavailable on Linux.

        :return: Human-readable message
        :rtype: str
        """
        return (
            "swiftDialog is not available on Linux. "
            "Dialog functionality is macOS-only. "
            "Consider using zenity, kdialog, or similar Linux dialog tools."
        )


class LinuxCommandSupport:
    """Linux implementation of PlatformCommandSupport.

    Uses ``su`` or ``runuser`` to execute commands as another user.
    """

    @property
    def min_user_uid(self) -> int:
        """Minimum UID for non-system accounts on Linux (typically 1000).

        :return: 1000
        :rtype: int
        """
        return 1000

    def run_as_user_command(self, command: list[str], username: str, uid: int) -> list[str]:
        """Wrap command with ``sudo -u`` for Linux.

        :param command: Original command arguments
        :type command: list[str]
        :param username: Target username
        :type username: str
        :param uid: Target user UID (unused in command, validated separately)
        :type uid: int
        :return: Command prefixed with sudo -u
        :rtype: list[str]
        """
        return ["sudo", "-u", username, *command]

    def validate_user(self, username: str | None, uid: int | None) -> bool:
        """Validate user info for Linux.

        Returns False if username/uid are missing, username has invalid
        characters, or UID is below the non-system threshold (1000).

        :param username: Username to validate
        :type username: str | None
        :param uid: User ID to validate
        :type uid: int | None
        :return: True if valid
        :rtype: bool
        """
        if username is None or uid is None:
            return False
        if not re.match(r"^[a-zA-Z0-9._-]+$", username):
            return False
        if uid < self.min_user_uid:
            return False
        return True
