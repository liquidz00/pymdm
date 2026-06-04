---
layout: landing
---

# pymdm Documentation

:::{rst-class} lead
A cross-platform Python utility package for MDM deployment scripts, built for [MacAdmins Python](https://github.com/macadmins/python) and Jamf Pro workflows. Windows/Intune support included for mixed-platform fleets.
:::

:::{container} buttons
[User Guide](user-guide/index.md)
[API Reference](api-reference/index.md)
[GitHub](https://github.com/liquidz00/pymdm)
:::

## Features

:::::{grid} 1 2 2 2
:gutter: 2
:padding: 0
:class-row: surface

::::{grid-item-card} {iconify}`mdi:console` Core
- **CommandRunner** — Subprocess execution with credential sanitization and `check=False` mode
- **MdmLogger** — Structured logging with file output and rotation
- **SystemInfo** — Serial number, console user, hostname across platforms
- **WebhookSender** — Webhook delivery with optional custom headers
- **TextTools** — awk, sort, and uniq for parsing command output
::::

::::{grid-item-card} {iconify}`mdi:cellphone-link` MDM Parameters
- **ParamParser** — Jamf Pro script parameters 4-11
- **IntuneParamProvider** — Env var and argv parsing for Intune
- **Dialog** — swiftDialog integration (macOS)
::::

::::{grid-item-card} {iconify}`mdi:apple` macOS Helpers
- **DarwinDefaults** — Read, write, delete `defaults` plist values
- **DarwinServiceManager** — `launchctl` is_loaded, bootout, bootstrap
::::

::::{grid-item-card} {iconify}`mdi:microsoft-windows` Windows Helpers
- **Win32Registry** — Read, write, delete registry values via `winreg`
- **Win32ServiceManager** — `sc.exe` is_running, start, stop, delete
::::
:::::

## Quick Links

- [Installation](user-guide/install)
- [Quick Start](user-guide/quickstart)
- [API Reference](api-reference/index)
- [GitHub Repository](https://github.com/liquidz00/pymdm)
- [PyPI](https://pypi.org/project/pymdm/)

## Requirements

- {iconify}`material-icon-theme:python` Python 3.12+
- {iconify}`material-icon-theme:uv` [uv](https://github.com/astral-sh/uv) package manager (recommended)
- {iconify}`mdi:apple` macOS with [MacAdmins Python](https://github.com/macadmins/python) for Jamf Pro scripts
- {iconify}`mdi:microsoft-windows` Windows with Python 3.12+ for Intune scripts

```{toctree}
:caption: User Guide
:hidden:

user-guide/index
user-guide/install
user-guide/quickstart
user-guide/platform-support
```

```{toctree}
:caption: API Reference
:hidden:

api-reference/index
api-reference/command-runner
api-reference/logger
api-reference/system-info
api-reference/webhook-sender
api-reference/text-tools
api-reference/param-parser
api-reference/dialog
api-reference/platforms-darwin
api-reference/platforms-win32
api-reference/mdm
```

```{toctree}
:caption: Project
:hidden:

contributing
```
