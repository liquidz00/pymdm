"""
System information helpers.

Provides a backward-compatible facade over platform-specific implementations.
On macOS, behavior is identical to the original implementation.
On other platforms, delegates to the appropriate platform module.
"""

from pathlib import Path

from .platforms._detection import get_platform


class SystemInfo:
    """Helper class for retrieving system information commonly needed in MDM scripts.

    This class delegates to platform-specific implementations while preserving
    the original static-method API for backward compatibility.
    """

    # Expose invalid_users from the current platform for backward compatibility
    @staticmethod
    def _get_invalid_users() -> tuple[str, ...]:
        """Get the invalid users tuple for the current platform.

        :return: Tuple of usernames considered invalid
        :rtype: tuple[str, ...]
        """
        return get_platform().invalid_users

    # Keep _INVALID_USERS as a class-level descriptor for backward compatibility
    # Code that accessed SystemInfo._INVALID_USERS directly will still work
    _INVALID_USERS = ("root", "", "loginwindow", "_mbsetupuser")

    @staticmethod
    def get_serial_number() -> str | None:
        """Get serial number of machine.

        Delegates to the platform-specific implementation.

        :return: Hardware serial number, or None if unavailable
        :rtype: str | None
        """
        return get_platform().get_serial_number()

    @staticmethod
    def get_console_user() -> tuple[str, int, Path] | None:
        """Get the currently logged in console user information.

        Delegates to the platform-specific implementation.

        :return: Tuple of username, uid, and home directory path
        :rtype: tuple[str, int, Path] | None
        """
        return get_platform().get_console_user()

    @staticmethod
    def get_hostname() -> str:
        """Retrieve system hostname.

        :return: System hostname
        :rtype: str
        """
        return get_platform().get_hostname()

    @staticmethod
    def get_user_full_name(username: str) -> str | None:
        """Get the full name for a given username.

        Delegates to the platform-specific implementation.

        :param username: Username to lookup
        :type username: str
        :return: Full name or None if unavailable
        :rtype: str | None
        """
        return get_platform().get_user_full_name(username)
