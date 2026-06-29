# Quick Start

:::{rst-class} lead
Write your first MDM deployment script with pymdm.
:::

## macOS / Jamf Pro

```python
#!/usr/local/bin/managed_python3
"""Example Jamf Pro policy script."""

from pymdm import (
    MdmLogger,
    CommandRunner,
    SystemInfo,
    WebhookSender,
)
from pymdm.mdm import get_provider

# Setup
params = get_provider("jamf")    # explicit; get_provider() now defaults to GenericParamParser
logger = MdmLogger(
    debug=params.get_bool(4),
    output_path="/var/log/my_script.log",
)
runner = CommandRunner(logger=logger)

logger.log_startup("my_script", version="1.0.0")

try:
    serial = SystemInfo.get_serial_number()
    hostname = SystemInfo.get_hostname()
    logger.info(f"Running on {hostname} ({serial})")

    output = runner.run(["/usr/bin/sw_vers", "-productVersion"])
    logger.info(f"macOS version: {output}")

    # check=False returns subprocess.CompletedProcess
    result = runner.run(["/usr/bin/some_tool", "--check"], check=False)
    if result.returncode != 0:
        logger.warn(f"Tool exited {result.returncode}")

    webhook = WebhookSender(url=params.get(5), logger=logger)
    webhook.send(hostname=hostname, serial=serial, status="success")

except Exception as e:
    logger.log_exception("Script failed", e, exit_code=1)
```

## Windows / Intune

```python
"""Example Intune deployment script."""

from pymdm import MdmLogger, CommandRunner, SystemInfo, WebhookSender
from pymdm.mdm import get_provider

params = get_provider()    # IntuneParamParser on Windows
logger = MdmLogger(
    debug=params.get_bool("DEBUG"),
    output_path=r"C:\ProgramData\Scripts\my_script.log",
)
runner = CommandRunner(logger=logger)

logger.log_startup("my_script", version="1.0.0")

try:
    serial = SystemInfo.get_serial_number()
    hostname = SystemInfo.get_hostname()
    logger.info(f"Running on {hostname} ({serial})")

    output = runner.run(
        ["powershell", "-Command", "Get-ComputerInfo | Select-Object OsVersion"]
    )
    logger.info(f"System info: {output}")

    webhook_url = params.get("WEBHOOK_URL")
    if webhook_url:
        webhook = WebhookSender(
            url=webhook_url,
            logger=logger,
            headers={"Authorization": "Bearer " + params.get("API_TOKEN")},
        )
        webhook.send(hostname=hostname, serial=serial, status="success")

except Exception as e:
    logger.log_exception("Script failed", e, exit_code=1)
```

## Platform Helpers

### macOS Defaults and Services

```python
from pymdm import CommandRunner
from pymdm.platforms.darwin import DarwinDefaults, DarwinServiceManager

# Read/write macOS defaults (instance-based as of v0.6.0)
defaults = DarwinDefaults()
val = defaults.read("com.apple.finder", "ShowHardDrivesOnDesktop")
defaults.write("com.example.app", "Enabled", "true", "-bool")
defaults.delete("com.example.app", "OldSetting")

# User-context writes: pass a CommandRunner with the console user's uid
runner = CommandRunner(username="jappleseed", uid=501)
DarwinDefaults(runner=runner).write("com.apple.dock", "tilesize", "48", "-int", as_user=True)

# Manage launchd services
if DarwinServiceManager.is_loaded("system/com.example.daemon"):
    DarwinServiceManager.bootout("system/com.example.daemon")

DarwinServiceManager.bootstrap(
    "system", "/Library/LaunchDaemons/com.example.daemon.plist"
)
```

### Windows Registry and Services

```python
from pymdm.platforms.win32 import Win32Registry, Win32ServiceManager

# Read/write Windows registry
product = Win32Registry.read(
    Win32Registry.HKLM,
    r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
    "ProductName",
)
Win32Registry.write(Win32Registry.HKLM, r"SOFTWARE\MyApp", "Setting", "value")
Win32Registry.write(Win32Registry.HKLM, r"SOFTWARE\MyApp", "Count", 42)

# Manage Windows services
if Win32ServiceManager.is_running("CrowdStrike Falcon"):
    Win32ServiceManager.stop("CrowdStrike Falcon")
```
