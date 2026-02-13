"""
macOS (Darwin) platform implementation.

Provides system information retrieval and command execution support
using macOS-specific tools: system_profiler, stat, id, launchctl.
"""

from __future__ import annotations

import json
import platform
import re
import subprocess
from pathlib import Path
from typing import ClassVar

from ._base import default_get_hostname


class DarwinPlatformInfo:
    """macOS implementation of PlatformInfo.

    Retrieves system information using macOS-specific binaries:
    - system_profiler for serial numbers
    - stat / id for console user details
    - id -F for user full names
    """

    invalid_users: ClassVar[tuple[str, ...]] = (
        "root",
        "",
        "loginwindow",
        "_mbsetupuser",
    )

    def get_serial_number(self) -> str | None:
        """Get serial number via system_profiler.

        :return: Hardware serial number, or None on failure
        :rtype: str | None
        """
        try:
            result = subprocess.check_output(
                ["/usr/sbin/system_profiler", "SPHardwareDataType", "-json"],
                text=True,
            )
            data = json.loads(result)
            return data["SPHardwareDataType"][0]["serial_number"]
        except (subprocess.CalledProcessError, KeyError, json.JSONDecodeError, Exception):
            return None

    def get_console_user(self) -> tuple[str, int, Path] | None:
        """Get the currently logged-in console user on macOS.

        Uses ``stat -f%Su /dev/console`` to determine the console owner,
        then ``id -u`` for the UID, and constructs the home path under /Users/.

        :return: Tuple of (username, uid, home_path), or None
        :rtype: tuple[str, int, Path] | None
        """
        try:
            username = subprocess.check_output(
                ["/usr/bin/stat", "-f%Su", "/dev/console"], text=True
            ).strip()
        except subprocess.CalledProcessError:
            return None

        if username in self.invalid_users:
            return None

        try:
            uid = int(subprocess.check_output(["/usr/bin/id", "-u", username], text=True).strip())
        except subprocess.CalledProcessError:
            return None

        home_path = Path(f"/Users/{username}")
        return (username, uid, home_path) if home_path.exists() else None

    def get_hostname(self) -> str:
        """Retrieve system hostname.

        :return: System hostname
        :rtype: str
        """
        return default_get_hostname()

    def get_user_full_name(self, username: str) -> str | None:
        """Get full name for a user via ``id -F`` (macOS-specific).

        :param username: Username to look up
        :type username: str
        :return: Full display name, or None on failure
        :rtype: str | None
        """
        try:
            return subprocess.check_output(["/usr/bin/id", "-F", username], text=True).strip()
        except (subprocess.CalledProcessError, Exception):
            return None

    def get_os_version_label(self) -> str:
        """Return macOS version label for logging.

        :return: e.g. "macOS Version: 24.5.0"
        :rtype: str
        """
        return f"macOS Version: {platform.release()}"


class DarwinCommandSupport:
    """macOS implementation of PlatformCommandSupport.

    Uses ``launchctl asuser`` to run commands in the context of a logged-in user.
    """

    @property
    def min_user_uid(self) -> int:
        """Minimum UID for non-system accounts on macOS (500).

        :return: 500
        :rtype: int
        """
        return 500

    def run_as_user_command(self, command: list[str], username: str, uid: int) -> list[str]:
        """Wrap command with ``launchctl asuser`` for macOS.

        :param command: Original command arguments
        :type command: list[str]
        :param username: Target username
        :type username: str
        :param uid: Target user UID
        :type uid: int
        :return: Command prefixed with launchctl asuser + sudo -u
        :rtype: list[str]
        """
        return [
            "/bin/launchctl",
            "asuser",
            str(uid),
            "sudo",
            "-u",
            username,
            *command,
        ]

    def validate_user(self, username: str | None, uid: int | None) -> bool:
        """Validate user info for macOS.

        Returns False if username/uid are missing, username has invalid
        characters, or UID is below the non-system threshold (500).

        :param username: Username to validate
        :type username: str | None
        :param uid: User ID to validate
        :type uid: int | None
        :return: True if valid
        :rtype: bool
        """
        if username is None or uid is None:
            return False
        if not re.match(r"^[a-zA-z0-9_-]+$", username):
            return False
        if uid < self.min_user_uid:
            return False
        return True
