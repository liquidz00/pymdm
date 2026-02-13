"""
Protocol definitions for MDM provider implementations.

Defines the contract that each MDM provider (Jamf, Intune, etc.) must satisfy
for script parameter parsing and MDM-specific operations.
"""

from __future__ import annotations

import os
import sys
from typing import Protocol, runtime_checkable


@runtime_checkable
class MdmParamProvider(Protocol):
    """Protocol for MDM provider-specific script parameter parsing.

    Each MDM provider handles script parameters differently:
    - Jamf Pro: positional args via sys.argv[4..11]
    - Intune: environment variables or command-line arguments
    """

    def get(self, key: int | str) -> str | None:
        """Get a script parameter by key.

        :param key: Parameter key (int index for Jamf, str name for Intune)
        :type key: int | str
        :return: Parameter value, or None if not set
        :rtype: str | None
        """
        ...

    def get_bool(self, key: int | str) -> bool:
        """Get a script parameter and convert to boolean.

        :param key: Parameter key
        :type key: int | str
        :return: Boolean value (False if parameter is missing)
        :rtype: bool
        """
        ...

    def get_int(self, key: int | str, default: int = 0) -> int:
        """Get a script parameter and convert to integer.

        :param key: Parameter key
        :type key: int | str
        :param default: Default value if parameter is missing or invalid
        :type default: int
        :return: Integer value
        :rtype: int
        """
        ...


def get_provider(provider: str | None = None) -> MdmParamProvider:
    """Get the MDM parameter provider instance.

    Detection order:
    1. Explicit ``provider`` argument ("jamf" or "intune")
    2. ``PYMDM_MDM_PROVIDER`` environment variable
    3. Platform-based default: "jamf" on macOS, "intune" on Windows

    :param provider: Explicit provider name, defaults to None (auto-detect)
    :type provider: str | None, optional
    :return: MDM provider instance
    :rtype: MdmParamProvider
    :raises ValueError: If the provider name is not recognized
    """
    if provider is None:
        provider = os.environ.get("PYMDM_MDM_PROVIDER")

    if provider is None:
        # Default based on platform
        if sys.platform == "darwin":
            provider = "jamf"
        elif sys.platform == "win32":
            provider = "intune"
        else:
            provider = "jamf"  # Default to Jamf for Linux/other

    provider = provider.lower().strip()

    if provider == "jamf":
        from .jamf import JamfParamParser

        return JamfParamParser()

    if provider == "intune":
        from .intune import IntuneParamProvider

        return IntuneParamProvider()

    raise ValueError(
        f"Unknown MDM provider '{provider}'. "
        f"Supported providers: jamf, intune. "
        f"Set the PYMDM_MDM_PROVIDER environment variable to override detection."
    )
