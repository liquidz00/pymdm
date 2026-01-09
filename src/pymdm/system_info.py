import json
import platform
import subprocess
from pathlib import Path


class SystemInfo:
    """Helper class for retrieving system information commonly needed in Jamf scripts."""

    _INVALID_USERS = ("root", "", "loginwindow", "_mbsetupuser")

    @staticmethod
    def get_serial_number() -> str | None:
        """Get serial number of machine."""
        try:
            result = subprocess.check_output(
                ["/usr/sbin/system_profiler", "SPHardwareDataType", "-json"],
                text=True,
            )
            data = json.loads(result)
            return data["SPHardwareDataType"][0]["serial_number"]
        except (subprocess.CalledProcessError, KeyError, json.JSONDecodeError, Exception):
            return None

    @staticmethod
    def get_console_user() -> tuple[str, int, Path] | None:
        """
        Get the currently logged in console user information.

        :return: Tuple of username, uid, and home directory path
        :rtype: tuple[str, int, Path] | None
        """
        try:
            username = subprocess.check_output(
                ["/usr/bin/stat", "-f%Su", "/dev/console"], text=True
            ).strip()
        except subprocess.CalledProcessError:
            return None

        if username in SystemInfo._INVALID_USERS:
            return None

        try:
            uid = int(subprocess.check_output(["/usr/bin/id", "-u", username], text=True).strip())
        except subprocess.CalledProcessError:
            return None

        home_path = Path(f"/Users/{username}")
        return (username, uid, home_path) if home_path.exists() else None

    @staticmethod
    def get_hostname() -> str:
        """Retrieve system hostname."""
        return platform.node()

    @staticmethod
    def get_user_full_name(username: str) -> str | None:
        """
        Get the full name for a given username.

        :param username: Username to lookup
        :type username: str
        :return: Full name or None if unavailable
        :rtype: str | None
        """
        try:
            return subprocess.check_output(["/usr/bin/id", "-F", username], text=True).strip()
        except (subprocess.CalledProcessError, Exception):
            return None
