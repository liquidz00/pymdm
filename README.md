# pymdm

A Python utility package for macOS MDM deployment scripts, built for [MacAdmins Python](https://github.com/macadmins/python) (`#!/usr/local/bin/managed_python3`) and Jamf Pro workflows. Windows/Intune support is also available for teams managing mixed-platform fleets.

## Features

- **ParamParser**: Safe parsing of Jamf Pro script parameters 4-11 (macOS)
- **Dialog**: swiftDialog integration for user-facing dialogs and notifications (macOS)
- **CommandRunner**: Secure subprocess execution with credential sanitization, platform-aware run-as-user, and `check=False` mode for raw `CompletedProcess` access
- **SystemInfo**: System information helpers — serial number, console user, hostname
- **MdmLogger**: Structured logging with file output, rotation, and multiple log levels
- **WebhookSender**: Send logs and metadata to webhooks with optional custom headers
- **IntuneParamProvider**: Env var and argv parameter parsing for Intune scripts (Windows)
- **DarwinDefaults**: Read, write, and delete macOS `defaults` plist values (macOS)
- **DarwinServiceManager**: Manage launchd services — is_loaded, bootout, bootstrap (macOS)
- **Win32Registry**: Read, write, and delete Windows registry values via `winreg` (Windows)
- **Win32ServiceManager**: Manage Windows services via `sc.exe` (Windows)

### Platform Support

| Feature | macOS (Jamf) | Windows (Intune) |
|---|---|---|
| ParamParser (Jamf) | Yes | — |
| Dialog (swiftDialog) | Yes | Graceful no-op |
| CommandRunner | Yes | Yes |
| SystemInfo | Yes | Yes |
| MdmLogger | Yes | Yes |
| WebhookSender | Yes | Yes |
| IntuneParamProvider | — | Yes |
| DarwinDefaults | Yes | — |
| DarwinServiceManager | Yes | — |
| Win32Registry | — | Yes |
| Win32ServiceManager | — | Yes |

## Installation

`pymdm` keeps `requests` as an optional dependency because the primary deployment
target — MacAdmins [`managed_python3`](https://github.com/macadmins/python) —
already bundles it. Pick the install path that matches your runtime:

```bash
# Standard pip install (most users): pulls in requests
pip install pymdm[requests]

# MacAdmins managed_python3: requests is already bundled, no extras needed
pip install pymdm[managed]

# Bare install (no HTTP): WebhookSender will raise ImportError when used
pip install pymdm
```

### From Source

```bash
uv pip install -e ".[requests]"
```

### Development

```bash
make install     # Install with dev dependencies (includes requests + docs)
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

# Safe execution (list form) — returns str
output = runner.run(["/usr/bin/id", "-u", username])

# check=False returns subprocess.CompletedProcess
result = runner.run(["/usr/bin/some_tool", "--check"], check=False)
if result.returncode != 0:
    logger.warn(f"Tool exited {result.returncode}: {result.stderr}")

# Pass kwargs through to subprocess.run
output = runner.run(["ls", "-la"], cwd="/tmp")

# Run as logged-in user (platform-aware)
runner = CommandRunner(logger=logger, username="jsmith", uid=501)
output = runner.run_as_user(["/usr/bin/open", "-a", "Safari"])
```

### System Information

```python
from pymdm import SystemInfo

# Get serial number
# macOS: system_profiler | Windows: PowerShell/wmic
serial = SystemInfo.get_serial_number()

# Get console user info
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
    logger=logger,
    headers={"Authorization": "Bearer <token>"},
)

# Send log with metadata
webhook.send(
    hostname=SystemInfo.get_hostname(),
    serial=SystemInfo.get_serial_number(),
    script_name="my_deployment_script",
    status="success"
)
```

### macOS Defaults (plist)

```python
from pymdm.platforms.darwin import DarwinDefaults

# Read a preference value
val = DarwinDefaults.read("com.apple.finder", "ShowHardDrivesOnDesktop")

# Write a string value
DarwinDefaults.write("com.example.app", "Setting", "value")

# Write a boolean value
DarwinDefaults.write("com.example.app", "Enabled", "true", "-bool")

# Delete a key
DarwinDefaults.delete("com.example.app", "Setting")
```

### macOS Service Management

```python
from pymdm.platforms.darwin import DarwinServiceManager

# Check if a launchd service is loaded
if DarwinServiceManager.is_loaded("system/com.example.daemon"):
    DarwinServiceManager.bootout("system/com.example.daemon")

# Load a service from a plist
DarwinServiceManager.bootstrap("system", "/Library/LaunchDaemons/com.example.daemon.plist")
```

### Windows Registry

```python
from pymdm.platforms.win32 import Win32Registry

# Read a registry value
product = Win32Registry.read(
    Win32Registry.HKLM,
    r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
    "ProductName",
)

# Write a string value (auto-detects REG_SZ)
Win32Registry.write(Win32Registry.HKLM, r"SOFTWARE\MyApp", "Setting", "value")

# Write an integer (auto-detects REG_DWORD)
Win32Registry.write(Win32Registry.HKLM, r"SOFTWARE\MyApp", "Count", 42)

# Delete a value
Win32Registry.delete(Win32Registry.HKLM, r"SOFTWARE\MyApp", "Setting")
```

### Windows Service Management

```python
from pymdm.platforms.win32 import Win32ServiceManager

if Win32ServiceManager.is_running("CrowdStrike Falcon"):
    Win32ServiceManager.stop("CrowdStrike Falcon")

Win32ServiceManager.start("MyService")
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
| `PYMDM_PLATFORM` | Override platform auto-detection | `darwin`, `win32` |
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
│   ├── darwin.py       # macOS: system_profiler, launchctl, defaults
│   └── win32.py        # Windows: PowerShell, wmic, runas, winreg, sc.exe
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
