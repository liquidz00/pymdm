"""
pymdm.platforms - Cross-platform abstraction layer.

Provides platform-specific implementations for system information retrieval,
command execution, and dialog display. Auto-detects the current platform and
returns the appropriate implementation.
"""

from ._base import PlatformCommandSupport, PlatformDialogSupport, PlatformInfo
from ._detection import get_command_support, get_dialog_support, get_platform

__all__ = [
    "PlatformCommandSupport",
    "PlatformDialogSupport",
    "PlatformInfo",
    "get_command_support",
    "get_dialog_support",
    "get_platform",
]
