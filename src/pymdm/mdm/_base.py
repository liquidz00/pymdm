"""
Abstract base class for MDM provider implementations.

Defines the contract that each MDM provider (Jamf, Intune, etc.) must satisfy
for script parameter parsing, plus the shared value-coercion helpers.
"""

from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod


class MdmParamParser(ABC):
    """
    Abstract base class for MDM provider-specific script parameter parsing.

    Each MDM provider handles script parameters differently:
    - Jamf Pro: positional args via `sys.argv[4..11]`
    - Intune: environment variables or command-line arguments

    Subclasses implement `get`; `get_bool` and `get_int` are shared here.
    """

    @abstractmethod
    def get(self, key: int | str) -> str | None:
        """
        Get a script parameter by key.

        :param key: Parameter key (int index for Jamf, str name for Intune)
        :type key: int | str
        :return: Parameter value, or None if not set
        :rtype: str | None
        """
        ...

    def get_bool(self, key: int | str) -> bool:
        """
        Get a script parameter and convert to boolean.

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
        """
        Get a script parameter and convert to integer.

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


class GenericParamParser(MdmParamParser):
    """
    Generic positional parameter parser.

    The neutral default for providers that pass parameters as plain positional
    ``sys.argv`` arguments with no reserved indices. Used when no provider is
    specified and the platform isn't recognized as Jamf or Intune.
    """

    def get(self, key: int | str) -> str | None:
        """
        Get a positional parameter by ``sys.argv`` index.

        :param key: Positional argument index
        :type key: int | str
        :return: Parameter value, or None if the index is out of range
        :rtype: str | None
        :raises TypeError: If key is not an integer
        """
        if not isinstance(key, int):
            raise TypeError(
                f"Generic parameter keys must be integers (got {type(key).__name__}). "
                f"Use an integer sys.argv index."
            )
        return sys.argv[key] if len(sys.argv) > key else None


def get_provider(provider: str | None = None) -> MdmParamParser:
    """
    Get the MDM parameter provider instance.

    Detection order:
    1. Explicit ``provider`` argument ("jamf", "intune", or "generic")
    2. ``PYMDM_MDM_PROVIDER`` environment variable
    3. Platform-based default: "intune" on Windows, "generic" everywhere else

    :param provider: Explicit provider name, defaults to None (auto-detect)
    :type provider: str | None, optional
    :return: MDM provider instance
    :rtype: MdmParamParser
    :raises ValueError: If the provider name is not recognized
    """
    if provider is None:
        provider = os.environ.get("PYMDM_MDM_PROVIDER")

    if provider is None:
        # macOS is not assumed to be Jamf; the neutral positional parser is the safe default
        if sys.platform == "win32":
            provider = "intune"
        else:
            provider = "generic"

    provider = provider.lower().strip()

    match provider:
        case "jamf":
            from .jamf import JamfParamParser

            return JamfParamParser()
        case "intune":
            from .intune import IntuneParamParser

            return IntuneParamParser()
        case "generic":
            return GenericParamParser()
        case _:
            raise ValueError(
                f"Unknown MDM provider '{provider}'. "
                f"Supported providers: jamf, intune, generic. "
                f"Set the PYMDM_MDM_PROVIDER environment variable to override detection."
            )
