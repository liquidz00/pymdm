"""
pymdm - Cross-platform utility package for MDM deployment scripts.

Provides logging, MDM parameter parsing, webhook sending, system information
retrieval, command execution, and dialog integration. Supports macOS/Jamf Pro
and Windows/Intune platforms.
"""

__title__ = "pymdm"
__version__ = "0.7.0"


from .command_runner import CommandRunner
from .dialog import (
    CheckboxItem,
    Dialog,
    DialogExitCode,
    DialogReturn,
    DialogTemplate,
    SelectItem,
    SelectResult,
    SystemNotification,
    TextField,
)
from .logger import MdmLogger
from .mdm import get_provider
from .system_info import SystemInfo
from .text_tools import TextTools
from .webhook_sender import WebhookSender

__all__ = [
    "get_provider",
    "CheckboxItem",
    "CommandRunner",
    "Dialog",
    "DialogExitCode",
    "DialogReturn",
    "DialogTemplate",
    "MdmLogger",
    "SelectItem",
    "SelectResult",
    "SystemInfo",
    "SystemNotification",
    "TextField",
    "TextTools",
    "WebhookSender",
    "__version__",
]
