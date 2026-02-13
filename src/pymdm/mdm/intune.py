"""
Microsoft Intune MDM provider implementation.

Handles Intune-specific script parameter parsing. Intune scripts on Windows
typically receive parameters as command-line arguments or environment variables.
This provider supports both patterns.
"""

from __future__ import annotations

import os
import sys


class IntuneParamProvider:
    """Intune parameter provider.

    Intune scripts can receive parameters in multiple ways:
    1. Command-line arguments (sys.argv) -- addressed by integer key
    2. Environment variables -- addressed by string key

    Unlike Jamf, Intune does not reserve specific parameter indices.
    Integer keys map directly to sys.argv indices (0 = script name, 1+ = args).
    String keys are looked up as environment variables, optionally with an
    ``INTUNE_`` prefix.

    Satisfies the MdmParamProvider protocol.

    :Example:

        >>> provider = IntuneParamProvider()
        >>> # Get from sys.argv[1]
        >>> value = provider.get(1)
        >>> # Get from environment variable
        >>> value = provider.get("WEBHOOK_URL")
    """

    @staticmethod
    def _get_env(name: str) -> str | None:
        """Look up an environment variable with optional INTUNE_ prefix.

        Tries the exact name first, then with INTUNE_ prefix.

        :param name: Environment variable name
        :type name: str
        :return: Variable value, or None if not found
        :rtype: str | None
        """
        value = os.environ.get(name)
        if value is not None:
            return value
        # Try with INTUNE_ prefix
        return os.environ.get(f"INTUNE_{name}")

    def get(self, key: int | str) -> str | None:
        """Get a script parameter by key.

        Integer keys are looked up in sys.argv. String keys are looked
        up as environment variables (with optional INTUNE_ prefix fallback).

        :param key: Parameter key (int for argv index, str for env var name)
        :type key: int | str
        :return: Parameter value, or None if not set
        :rtype: str | None
        """
        if isinstance(key, int):
            return sys.argv[key] if len(sys.argv) > key else None
        if isinstance(key, str):
            return self._get_env(key)
        return None

    def get_bool(self, key: int | str) -> bool:
        """Get a script parameter and convert to boolean.

        :param key: Parameter key
        :type key: int | str
        :return: Boolean value (False if parameter is missing)
        :rtype: bool
        """
        value = self.get(key)
        if not value:
            return False
        return value.strip().lower() in ("true", "1", "yes", "y")

    def get_int(self, key: int | str, default: int = 0) -> int:
        """Get a script parameter and convert to integer.

        :param key: Parameter key
        :type key: int | str
        :param default: Default value if parameter is missing or invalid
        :type default: int
        :return: Integer value
        :rtype: int
        """
        value = self.get(key)
        if not value:
            return default
        try:
            return int(value.strip())
        except ValueError:
            return default
