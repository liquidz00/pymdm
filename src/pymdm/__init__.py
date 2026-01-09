"""
pymdm - Utility package for Jamf MDM deployment scripts.

Provides logging, Jamf parameter parsing, webhook sending, and swiftDialog integration.
"""

__title__ = "pymdm"
__version__ = "0.3.0"


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
from .param_parser import ParamParser
from .system_info import SystemInfo
from .webhook_sender import WebhookSender

__all__ = [
    "CheckboxItem",
    "CommandRunner",
    "Dialog",
    "DialogExitCode",
    "DialogReturn",
    "DialogTemplate",
    "ParamParser",
    "MdmLogger",
    "SelectItem",
    "SelectResult",
    "SystemInfo",
    "SystemNotification",
    "TextField",
    "WebhookSender",
    "__version__",
]
