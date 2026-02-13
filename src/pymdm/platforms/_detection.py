"""
Platform detection and factory functions.

Auto-detects the current platform (or reads an override from the
PYMDM_PLATFORM environment variable) and returns the appropriate
platform-specific implementation. Currently supports macOS and Windows.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache

from ._base import PlatformCommandSupport, PlatformInfo


@lru_cache(maxsize=1)
def get_platform() -> PlatformInfo:
    """Auto-detect and return the platform-specific PlatformInfo implementation.

    The detection order is:
    1. ``PYMDM_PLATFORM`` environment variable (values: "darwin", "win32")
    2. ``sys.platform`` automatic detection

    :return: Platform-specific PlatformInfo instance
    :rtype: PlatformInfo
    :raises NotImplementedError: If the platform is not supported
    """
    platform_key = os.environ.get("PYMDM_PLATFORM", sys.platform).lower()

    if platform_key == "darwin":
        from .darwin import DarwinPlatformInfo

        return DarwinPlatformInfo()

    if platform_key in ("win32", "windows"):
        from .win32 import Win32PlatformInfo

        return Win32PlatformInfo()

    raise NotImplementedError(
        f"Platform '{platform_key}' is not supported by pymdm. "
        f"Supported platforms: darwin, win32. "
        f"Set the PYMDM_PLATFORM environment variable to override detection."
    )


@lru_cache(maxsize=1)
def get_command_support() -> PlatformCommandSupport:
    """Auto-detect and return the platform-specific PlatformCommandSupport implementation.

    The detection order is:
    1. ``PYMDM_PLATFORM`` environment variable (values: "darwin", "win32")
    2. ``sys.platform`` automatic detection

    :return: Platform-specific PlatformCommandSupport instance
    :rtype: PlatformCommandSupport
    :raises NotImplementedError: If the platform is not supported
    """
    platform_key = os.environ.get("PYMDM_PLATFORM", sys.platform).lower()

    if platform_key == "darwin":
        from .darwin import DarwinCommandSupport

        return DarwinCommandSupport()

    if platform_key in ("win32", "windows"):
        from .win32 import Win32CommandSupport

        return Win32CommandSupport()

    raise NotImplementedError(
        f"Platform '{platform_key}' is not supported by pymdm. "
        f"Supported platforms: darwin, win32. "
        f"Set the PYMDM_PLATFORM environment variable to override detection."
    )


def clear_platform_cache() -> None:
    """Clear the cached platform instances.

    Useful for testing when you need to switch platform implementations
    between tests by changing the PYMDM_PLATFORM environment variable.
    """
    get_platform.cache_clear()
    get_command_support.cache_clear()
