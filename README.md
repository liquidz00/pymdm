# pymdm

A cross-platform Python utility package for MDM deployment scripts, providing common functionality for Jamf Pro, Microsoft Intune, and other endpoint management workflows.

Originally designed for use with [MacAdmins Python](https://github.com/macadmins/python) (`#!/usr/local/bin/managed_python3`), now supports macOS, Windows, and Linux.

## Features

- **MdmLogger**: Structured logging with file output, rotation, and multiple log levels
- **ParamParser**: Safe parsing of MDM script parameters (Jamf Pro parameters 4-11)
- **CommandRunner**: Secure subprocess execution with credential sanitization and platform-aware run-as-user
- **SystemInfo**: Cross-platform system information helpers (serial number, console user, hostname)
- **WebhookSender**: Send logs and metadata to webhooks
- **Dialog**: swiftDialog integration for user-facing dialogs and notifications (macOS)

### Cross-Platform Support

| Feature | macOS (Jamf) | Windows (Intune) | Linux |
|---|---|---|---|
| SystemInfo | Full | Full | Full |
| CommandRunner | Full | Full | Full |
| MdmLogger | Full | Full | Full |
| WebhookSender | Full | Full | Full |
| ParamParser (Jamf) | Full | N/A | N/A |
| IntuneParamProvider | N/A | Full | N/A |
| Dialog (swiftDialog) | Full | Graceful stub | Graceful stub |

## Installation

### From Source

```bash
uv pip install -e .
```

### Development

```bash
make install     # Install with dev dependencies
make test        # Run tests
make format      # Format code with ruff
```

## Quick Start

### Logging

```python
from pymdm import MdmLogger

logger = MdmLogger(
    debug=True,
    output_path="/var/log/my_script.log"
)

logger.info("Script started")
logger.debug("Detailed information")
logger.warn("Warning message")
logger.error("Error occurred", exit_code=1)
```

### Jamf Parameters (macOS)

```python
from pymdm import ParamParser

# Get string parameter
webhook_url = ParamParser.get(4)  # $4 in Jamf policy

# Get boolean parameter
debug_mode = ParamParser.get_bool(5)  # "true", "1", "yes" -> True

# Get integer parameter
timeout = ParamParser.get_int(6, default=30)
```

### Intune Parameters (Windows)

```python
from pymdm.mdm import IntuneParamProvider

provider = IntuneParamProvider()

# Get from sys.argv
value = provider.get(1)

# Get from environment variable
webhook_url = provider.get("WEBHOOK_URL")

# Boolean from env var
debug = provider.get_bool("DEBUG_MODE")
```

### Auto-Detect MDM Provider

```python
from pymdm.mdm import get_provider

# Automatically selects Jamf on macOS, Intune on Windows
# Override with PYMDM_MDM_PROVIDER env var
provider = get_provider()

value = provider.get(4)  # Jamf: sys.argv[4], Intune: sys.argv[4]
debug = provider.get_bool("DEBUG")  # Intune: env var lookup
```

### Command Execution

```python
from pymdm import CommandRunner

runner = CommandRunner(logger=logger)

# Safe execution (list form)
output = runner.run(["/usr/bin/id", "-u", username])

# Shell execution (for pipes, etc.)
output = runner.run("ps aux | grep python", timeout=10)

# Run as logged-in user (platform-aware)
# macOS: uses launchctl asuser
# Linux: uses sudo -u
# Windows: uses PowerShell Start-Process
runner = CommandRunner(logger=logger, username="jsmith", uid=501)
output = runner.run_as_user(["/usr/bin/open", "-a", "Safari"])
```

### System Information

```python
from pymdm import SystemInfo

# Get serial number (cross-platform)
# macOS: system_profiler | Windows: PowerShell/wmic | Linux: /sys/class/dmi
serial = SystemInfo.get_serial_number()

# Get console user info (cross-platform)
user_info = SystemInfo.get_console_user()
if user_info:
    username, uid, home_path = user_info

# Get hostname
hostname = SystemInfo.get_hostname()

# Get full name
full_name = SystemInfo.get_user_full_name("jsmith")
```

### Webhook Integration

```python
from pymdm import WebhookSender, MdmLogger

logger = MdmLogger(output_path="/var/log/script.log")
webhook = WebhookSender(
    url="https://hooks.tray.io/...",
    logger=logger
)

# Send log with metadata
webhook.send(
    hostname=SystemInfo.get_hostname(),
    serial=SystemInfo.get_serial_number(),
    script_name="my_deployment_script",
    status="success"
)
```

## Complete Example (macOS / Jamf Pro)

```python
#!/usr/local/bin/managed_python3
"""Example Jamf Pro policy script."""

from pymdm import (
    MdmLogger,
    ParamParser,
    CommandRunner,
    SystemInfo,
    WebhookSender,
)

# Setup
logger = MdmLogger(
    debug=ParamParser.get_bool(4),
    output_path="/var/log/my_script.log"
)
runner = CommandRunner(logger=logger)

logger.log_startup("my_script", version="1.0.0")

try:
    # Get system info
    serial = SystemInfo.get_serial_number()
    hostname = SystemInfo.get_hostname()

    logger.info(f"Running on {hostname} ({serial})")

    # Execute command
    output = runner.run(["/usr/bin/sw_vers", "-productVersion"])
    logger.info(f"macOS version: {output}")

    # Send results
    webhook = WebhookSender(
        url=ParamParser.get(5),
        logger=logger
    )
    webhook.send(
        hostname=hostname,
        serial=serial,
        status="success"
    )

except Exception as e:
    logger.log_exception("Script failed", e, exit_code=1)
```

## Complete Example (Windows / Intune)

```python
"""Example Intune deployment script."""

from pymdm import MdmLogger, CommandRunner, SystemInfo, WebhookSender
from pymdm.mdm import IntuneParamProvider

# Setup
params = IntuneParamProvider()
logger = MdmLogger(
    debug=params.get_bool("DEBUG"),
    output_path="C:\\ProgramData\\Scripts\\my_script.log"
)
runner = CommandRunner(logger=logger)

logger.log_startup("my_script", version="1.0.0")

try:
    serial = SystemInfo.get_serial_number()
    hostname = SystemInfo.get_hostname()

    logger.info(f"Running on {hostname} ({serial})")

    # Windows-specific command
    output = runner.run(["powershell", "-Command", "Get-ComputerInfo | Select-Object OsVersion"])
    logger.info(f"System info: {output}")

    webhook_url = params.get("WEBHOOK_URL")
    if webhook_url:
        webhook = WebhookSender(url=webhook_url, logger=logger)
        webhook.send(hostname=hostname, serial=serial, status="success")

except Exception as e:
    logger.log_exception("Script failed", e, exit_code=1)
```

## Platform Configuration

### Environment Variables

| Variable | Purpose | Values |
|---|---|---|
| `PYMDM_PLATFORM` | Override platform auto-detection | `darwin`, `win32`, `linux` |
| `PYMDM_MDM_PROVIDER` | Override MDM provider auto-detection | `jamf`, `intune` |

### Task Mapping: Jamf vs Intune

| Jamf Pro | Intune Equivalent | pymdm API |
|---|---|---|
| `ParamParser.get(4)` | `IntuneParamProvider().get("PARAM_NAME")` | `get_provider().get(...)` |
| `ParamParser.get_bool(5)` | `IntuneParamProvider().get_bool("FLAG")` | `get_provider().get_bool(...)` |
| Script params via `sys.argv[4-11]` | Env vars or `sys.argv` | Provider-specific |
| `jamf recon` | Microsoft Graph API | Not in pymdm (use provider SDK) |
| swiftDialog | Windows toast/WPF | `Dialog` (macOS only) |

## Migration Notes

### From pymdm < 0.4.0

All existing imports and APIs are fully backward compatible. No changes required for macOS/Jamf scripts:

```python
# These all work exactly as before
from pymdm import SystemInfo, CommandRunner, ParamParser, MdmLogger
```

For new Windows/Intune scripts, use the new provider APIs:

```python
from pymdm.mdm import IntuneParamProvider, get_provider
from pymdm.platforms import get_platform
```

## Architecture

```
pymdm/
├── platforms/          # OS-specific implementations
│   ├── darwin.py       # macOS: system_profiler, launchctl, swiftDialog
│   ├── win32.py        # Windows: PowerShell, wmic, runas
│   └── linux.py        # Linux: /sys/class/dmi, sudo, pwd
├── mdm/                # MDM provider implementations
│   ├── jamf.py         # Jamf Pro: sys.argv[4-11] parsing
│   └── intune.py       # Intune: env vars, flexible argv
├── command_runner.py   # Cross-platform subprocess wrapper
├── dialog.py           # swiftDialog integration (macOS)
├── logger.py           # Structured logging
├── param_parser.py     # Backward-compat Jamf parser facade
├── system_info.py      # Cross-platform system info facade
└── webhook_sender.py   # HTTP webhook sender
```

## Requirements

- Python 3.12+
- `requests` (included with [MacAdmins Python](https://github.com/macadmins/python))
