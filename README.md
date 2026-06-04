# pymdm

A Python utility package for macOS MDM deployment scripts, built for [MacAdmins Python](https://github.com/macadmins/python) (`#!/usr/local/bin/managed_python3`) and Jamf Pro workflows. Windows/Intune support is included for teams managing mixed-platform fleets.

📖 **[Full documentation →](https://pymdm.readthedocs.io/en/latest/)**

## What's Included

| Feature | macOS (Jamf) | Windows (Intune) |
|---|---|---|
| ParamParser (Jamf) | Yes | -- |
| Dialog (swiftDialog) | Yes | Graceful no-op |
| CommandRunner | Yes | Yes |
| TextTools | Yes | Yes |
| SystemInfo | Yes | Yes |
| MdmLogger | Yes | Yes |
| WebhookSender | Yes | Yes |
| IntuneParamProvider | -- | Yes |
| DarwinDefaults | Yes | -- |
| DarwinServiceManager | Yes | -- |
| Win32Registry | -- | Yes |
| Win32ServiceManager | -- | Yes |

See the [User Guide](https://pymdm.readthedocs.io/en/latest/user-guide/index.html) for what each piece does.

## Installation

```bash
pip install pymdm[requests]
```

`requests` is an optional extra because the primary target, MacAdmins [`managed_python3`](https://github.com/macadmins/python), already bundles it, so a plain `pip install pymdm` is enough there. The uv, source, and fleet-deployment paths are in the [installation guide](https://pymdm.readthedocs.io/en/latest/user-guide/install.html).

## Quick Example (macOS / Jamf Pro)

```python
#!/usr/local/bin/managed_python3
"""Example Jamf Pro policy script."""

from pymdm import MdmLogger, ParamParser, CommandRunner, SystemInfo, WebhookSender

logger = MdmLogger(debug=ParamParser.get_bool(4), output_path="/var/log/my_script.log")
runner = CommandRunner(logger=logger)
logger.log_startup("my_script", version="1.0.0")

try:
    serial = SystemInfo.get_serial_number()
    hostname = SystemInfo.get_hostname()
    logger.info(f"Running on {hostname} ({serial})")

    output = runner.run(["/usr/bin/sw_vers", "-productVersion"])
    logger.info(f"macOS version: {output}")

    webhook = WebhookSender(url=ParamParser.get(5), logger=logger)
    webhook.send(hostname=hostname, serial=serial, status="success")
except Exception as e:
    logger.log_exception("Script failed", e, exit_code=1)
```

Windows/Intune, platform helpers, and per-module usage live in the [Quick Start](https://pymdm.readthedocs.io/en/latest/user-guide/quickstart.html).

## Development

```bash
git clone https://github.com/liquidz00/pymdm.git
cd pymdm
make install-dev   # dev dependencies (includes docs tooling)
make test
make format
make help          # list every target
```

See [CONTRIBUTING](CONTRIBUTING.md) to get started, and the [CHANGELOG](CHANGELOG.md) for release notes and version migration steps.

## Requirements

- Python 3.12+
- `requests` (bundled with [MacAdmins Python](https://github.com/macadmins/python))

## License

[Apache 2.0](LICENSE)
