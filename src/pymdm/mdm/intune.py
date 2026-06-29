"""
Microsoft Intune MDM provider implementation.

Handles Intune-specific script parameter parsing. Intune scripts on Windows
typically receive parameters as command-line arguments or environment variables.
This provider supports both patterns.
"""

from __future__ import annotations

import os

from ._base import GenericParamParser


class IntuneParamParser(GenericParamParser):
    """
    Intune parameter parser.

    Intune scripts can receive parameters in multiple ways:
    1. Command-line arguments (sys.argv) -- addressed by integer key
    2. Environment variables -- addressed by string key

    Unlike Jamf, Intune does not reserve specific parameter indices.
    Integer keys map directly to sys.argv indices (0 = script name, 1+ = args).
    String keys are looked up as environment variables, optionally with an
    ``INTUNE_`` prefix.

    Extends GenericParamParser with environment-variable lookup for string keys.

    :Example:

        >>> provider = IntuneParamParser()
        >>> # Get from sys.argv[1]
        >>> value = provider.get(1)
        >>> # Get from environment variable
        >>> value = provider.get("WEBHOOK_URL")
    """

    @staticmethod
    def _get_env(name: str) -> str | None:
        """
        Look up an environment variable with optional INTUNE_ prefix.

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
        """
        Get a script parameter by key.

        Integer keys are looked up in sys.argv. String keys are looked
        up as environment variables (with optional ``INTUNE_`` prefix fallback).

        :param key: Parameter key (int for argv index, str for env var name)
        :type key: int | str
        :return: Parameter value, or None if not set
        :rtype: str | None
        """
        if isinstance(key, int):
            return super().get(key)
        if isinstance(key, str):
            return self._get_env(key)
        return None
