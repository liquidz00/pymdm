"""
Protocol definitions for platform-specific implementations.

These protocols define the contracts that each platform (darwin, win32, linux)
must satisfy. Using Protocols (structural subtyping) instead of ABCs so that
implementations don't need to inherit -- this makes testing and mocking easier.
"""

from __future__ import annotations

import platform
from pathlib import Path
from typing import ClassVar, Protocol, runtime_checkable


@runtime_checkable
class PlatformInfo(Protocol):
    """Protocol for platform-specific system information retrieval.

    Each platform implementation must provide methods for retrieving
    serial numbers, console user details, hostnames, and user full names.
    """

    invalid_users: ClassVar[tuple[str, ...]]
    """Usernames that should be treated as 'no real user logged in'."""

    def get_serial_number(self) -> str | None:
        """Get the hardware serial number of the machine.

        :return: Serial number string, or None if unavailable
        :rtype: str | None
        """
        ...

    def get_console_user(self) -> tuple[str, int, Path] | None:
        """Get the currently logged-in console user information.

        :return: Tuple of (username, uid, home_directory), or None if no valid user
        :rtype: tuple[str, int, Path] | None
        """
        ...

    def get_hostname(self) -> str:
        """Retrieve the system hostname.

        :return: System hostname
        :rtype: str
        """
        ...

    def get_user_full_name(self, username: str) -> str | None:
        """Get the full (display) name for a given username.

        :param username: Username to look up
        :type username: str
        :return: Full name or None if unavailable
        :rtype: str | None
        """
        ...

    def get_os_version_label(self) -> str:
        """Return a human-readable OS version string for logging.

        :return: OS version label, e.g. "macOS Version: 24.5.0"
        :rtype: str
        """
        ...


@runtime_checkable
class PlatformCommandSupport(Protocol):
    """Protocol for platform-specific command execution support.

    Covers run-as-user semantics and user validation, which differ by OS.
    """

    def run_as_user_command(self, command: list[str], username: str, uid: int) -> list[str]:
        """Wrap a command to execute as a specific user.

        Returns the full command list including OS-specific prefix
        (e.g., launchctl asuser on macOS, runas on Windows).

        :param command: The original command arguments
        :type command: list[str]
        :param username: Target username to run as
        :type username: str
        :param uid: Target user's UID (or 0 on platforms where irrelevant)
        :type uid: int
        :return: The wrapped command ready for subprocess execution
        :rtype: list[str]
        """
        ...

    def validate_user(self, username: str | None, uid: int | None) -> bool:
        """Validate that the given user information is present and reasonable.

        :param username: Username to validate
        :type username: str | None
        :param uid: User ID to validate
        :type uid: int | None
        :return: True if the user info is valid for this platform
        :rtype: bool
        """
        ...

    @property
    def min_user_uid(self) -> int:
        """Minimum UID for non-system user accounts on this platform.

        :return: Minimum UID threshold (e.g. 500 on macOS, 1000 on Linux)
        :rtype: int
        """
        ...


@runtime_checkable
class PlatformDialogSupport(Protocol):
    """Protocol for platform-specific dialog/UI support.

    Covers dialog binary discovery, temp directory locations, and
    platform availability checks for GUI dialogs.
    """

    @property
    def shared_temp_dir(self) -> str:
        """Default shared temp directory for multi-user dialog files.

        :return: Path string to shared temp directory
        :rtype: str
        """
        ...

    @property
    def standard_binary_path(self) -> str | None:
        """Standard installation path for the dialog binary on this platform.

        :return: Path string, or None if no standard location exists
        :rtype: str | None
        """
        ...

    @property
    def dialog_available(self) -> bool:
        """Whether GUI dialogs are supported on this platform.

        :return: True if dialog functionality is available
        :rtype: bool
        """
        ...

    @property
    def unavailable_message(self) -> str:
        """Human-readable message explaining why dialogs are unavailable.

        :return: Explanation string
        :rtype: str
        """
        ...


def default_get_hostname() -> str:
    """Cross-platform hostname retrieval using stdlib.

    :return: System hostname
    :rtype: str
    """
    return platform.node()
