"""
pymdm.platforms - Cross-platform abstraction layer.

Provides platform-specific implementations for system information retrieval
and command execution. Auto-detects the current platform (macOS or Windows)
and returns the appropriate implementation.
"""

from ._base import PlatformCommandSupport, PlatformInfo
from ._detection import get_command_support, get_platform

__all__ = [
    "PlatformCommandSupport",
    "PlatformInfo",
    "get_command_support",
    "get_platform",
]
