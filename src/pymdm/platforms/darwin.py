"""
macOS (Darwin) platform implementation.

Provides system information retrieval, command execution support,
defaults (plist) management, and launchd service management
using macOS-specific tools: system_profiler, stat, id, defaults, launchctl.
"""

from __future__ import annotations

import json
import platform
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from ._base import default_get_hostname

if TYPE_CHECKING:
    from ..command_runner import CommandRunner


class DarwinPlatformInfo:
    """
    macOS implementation of PlatformInfo.

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
        """
        Get serial number via system_profiler.

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
        """
        Get the currently logged-in console user on macOS.

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
        """
        Retrieve system hostname.

        :return: System hostname
        :rtype: str
        """
        return default_get_hostname()

    def get_user_full_name(self, username: str) -> str | None:
        """
        Get full name for a user via ``id -F`` (macOS-specific).

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
        """
        Return macOS version label for logging.

        Reads the marketing macOS productVersion (e.g. "15.4.1", "26.4.1")
        from ``platform.mac_ver()``. ``platform.release()`` was used previously
        but returns the Darwin kernel version (e.g. "25.4.0" on macOS 26.4.1),
        which is not what users expect to see in logs.

        :return: e.g. "macOS Version: 26.4.1"
        :rtype: str
        """
        product_version, _, _ = platform.mac_ver()
        if not product_version:
            # Extremely unusual fallback (SystemVersion.plist unreadable).
            # Better to surface *something* than crash.
            product_version = platform.release()
        return f"macOS Version: {product_version}"


class DarwinCommandSupport:
    """
    macOS implementation of PlatformCommandSupport.

    Uses ``launchctl asuser`` to run commands in the context of a logged-in user.
    """

    @property
    def min_user_uid(self) -> int:
        """
        Minimum UID for non-system accounts on macOS (500).

        :return: 500
        :rtype: int
        """
        return 500

    def run_as_user_command(self, command: list[str], username: str, uid: int) -> list[str]:
        """
        Wrap command with ``launchctl asuser`` for macOS.

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
        """
        Validate user info for macOS.

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
        if not re.match(r"^[a-zA-Z0-9._@-]+$", username):
            return False
        if uid < self.min_user_uid:
            return False
        return True


class DarwinDefaults:
    """
    Read, write, and delete macOS user defaults (plist) values.

    Wraps ``/usr/bin/defaults`` for non-raising plist operations: all methods
    return ``None`` or ``False`` on failure instead of raising.

    Operations run in the calling process's context by default (i.e. as root
    when the script is invoked under MDM). Pass a :class:`CommandRunner` with
    a ``username``/``uid`` to allow per-call ``as_user=True`` reads/writes
    against the logged-in user's domain.

    :Example:

        >>> # Root context (or whoever the script runs as)
        >>> defaults = DarwinDefaults()
        >>> defaults.read("com.apple.SoftwareUpdate", "AutomaticCheckEnabled")
        '1'

        >>> # User context — pipe through a configured CommandRunner
        >>> runner = CommandRunner(logger=logger, username="jappleseed", uid=501)
        >>> defaults = DarwinDefaults(runner=runner)
        >>> defaults.read("com.apple.dock", "orientation", as_user=True)
        'bottom'
        >>> defaults.write("com.apple.dock", "tilesize", "48", "-int", as_user=True)
        True
    """

    def __init__(self, runner: CommandRunner | None = None) -> None:
        """
        Construct a DarwinDefaults handler.

        :param runner: Optional CommandRunner. Required for ``as_user=True``
            calls; ignored otherwise. The runner must have ``username`` and
            ``uid`` set when ``as_user=True`` is used.
        :type runner: CommandRunner | None
        """
        self._runner = runner

    def read(self, domain: str, key: str, *, as_user: bool = False) -> str | None:
        """
        Read a defaults value by domain and key.

        :param domain: The plist domain (e.g., "com.apple.finder")
        :type domain: str
        :param key: The key to read
        :type key: str
        :param as_user: If True, run via the configured CommandRunner's
            ``run_as_user`` so the read targets the logged-in user's domain.
        :type as_user: bool
        :return: Value as string, or None if the key doesn't exist
        :rtype: str | None
        """
        cmd = ["/usr/bin/defaults", "read", domain, key]
        result = self._exec(cmd, as_user=as_user)
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    def write(
        self,
        domain: str,
        key: str,
        value: str,
        value_type: str = "-string",
        *,
        as_user: bool = False,
    ) -> bool:
        """
        Write a defaults value.

        :param domain: The plist domain
        :type domain: str
        :param key: The key to write
        :type key: str
        :param value: The value to set
        :type value: str
        :param value_type: defaults type flag (e.g., "-string", "-int", "-bool", "-float")
        :type value_type: str
        :param as_user: If True, run as the configured user (see read).
        :type as_user: bool
        :return: True if successful
        :rtype: bool
        """
        cmd = ["/usr/bin/defaults", "write", domain, key, value_type, str(value)]
        return self._exec(cmd, as_user=as_user).returncode == 0

    def delete(self, domain: str, key: str, *, as_user: bool = False) -> bool:
        """
        Delete a defaults key.

        :param domain: The plist domain
        :type domain: str
        :param key: The key to delete
        :type key: str
        :param as_user: If True, run as the configured user (see read).
        :type as_user: bool
        :return: True if deleted, False if missing or failed
        :rtype: bool
        """
        cmd = ["/usr/bin/defaults", "delete", domain, key]
        return self._exec(cmd, as_user=as_user).returncode == 0

    def _exec(self, cmd: list[str], *, as_user: bool) -> subprocess.CompletedProcess[str]:
        """
        Dispatch a defaults command in the appropriate user context.

        When ``as_user=True``, requires the instance to have been constructed
        with a CommandRunner that has username and uid set; raises
        :class:`ValueError` otherwise so callers fail loudly rather than
        silently running in root context.
        """
        if as_user:
            if self._runner is None:
                raise ValueError(
                    "DarwinDefaults: as_user=True requires a CommandRunner. "
                    "Construct with DarwinDefaults(runner=CommandRunner(...))."
                )
            if not self._runner.username or self._runner.uid is None:
                raise ValueError(
                    "DarwinDefaults: as_user=True requires the CommandRunner "
                    "to have both username and uid set."
                )
            return self._runner.run_as_user(cmd, check=False)
        return subprocess.run(cmd, capture_output=True, text=True)


class DarwinServiceManager:
    """
    Manage launchd services on macOS.

    Wraps ``/bin/launchctl`` for checking, loading, and unloading services.
    Targets use the launchctl domain-target format:
    ``system/com.example.daemon`` or ``gui/<uid>/com.example.agent``.

    :Example:

        >>> if DarwinServiceManager.is_loaded("system/com.example.daemon"):
        ...     DarwinServiceManager.bootout("system/com.example.daemon")
    """

    @staticmethod
    def is_loaded(target: str) -> bool:
        """
        Check if a launchd service is loaded.

        :param target: Service target (e.g., "system/com.example.daemon")
        :type target: str
        :return: True if the service is loaded
        :rtype: bool
        """
        result = subprocess.run(
            ["/bin/launchctl", "print", target],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    @staticmethod
    def bootout(target: str) -> bool:
        """
        Unload a launchd service.

        :param target: Service target (e.g., "system/com.example.daemon")
        :type target: str
        :return: True if successfully unloaded
        :rtype: bool
        """
        result = subprocess.run(
            ["/bin/launchctl", "bootout", target],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    @staticmethod
    def bootstrap(domain_target: str, plist_path: str) -> bool:
        """
        Load a launchd service from a plist.

        :param domain_target: Domain target (e.g., "system" or "gui/501")
        :type domain_target: str
        :param plist_path: Path to the launchd plist file
        :type plist_path: str
        :return: True if successfully loaded
        :rtype: bool
        """
        result = subprocess.run(
            ["/bin/launchctl", "bootstrap", domain_target, plist_path],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
