# pymdm

A Python utility package for MDM deployment scripts, providing common functionality for Jamf Pro policy scripts and system automation.

Designed for use with [MacAdmins Python](https://github.com/macadmins/python) (`#!/usr/local/bin/managed_python3`), which comes pre-shipped with `requests` and other useful packages.

## Features

- **MdmLogger**: Structured logging with file output, rotation, and multiple log levels
- **ParamParser**: Safe parsing of Jamf Pro script parameters (4-11)
- **CommandRunner**: Secure subprocess execution with credential sanitization
- **SystemInfo**: System information helpers (serial number, console user, hostname)
- **WebhookSender**: Send logs and metadata to webhooks
- **Dialog**: swiftDialog integration for user-facing dialogs and notifications

## Installation

### From Source

```bash
uv pip install -e .
```

### Development

```bash
make install-dev  # Install with dev dependencies
make test         # Run tests
make format       # Format code with black and ruff
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

### Jamf Parameters

```python
from pymdm import ParamParser

# Get string parameter
webhook_url = ParamParser.get(4)  # $4 in Jamf policy

# Get boolean parameter
debug_mode = ParamParser.get_bool(5)  # "true", "1", "yes" → True

# Get integer parameter
timeout = ParamParser.get_int(6, default=30)
```

### Command Execution

```python
from pymdm import CommandRunner

runner = CommandRunner(logger=logger)

# Safe execution (list form)
output = runner.run(["/usr/bin/id", "-u", username])

# Shell execution (for pipes, etc.)
output = runner.run("ps aux | grep python", timeout=10)
```

### System Information

```python
from pymdm import SystemInfo

# Get serial number
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

## Complete Example

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

## Requirements

- Python 3.12+
- `requests` (included with [MacAdmins Python](https://github.com/macadmins/python))
