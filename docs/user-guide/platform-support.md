# Platform Support

:::{rst-class} lead
pymdm supports macOS (Jamf Pro) and Windows (Intune) managed endpoints.
:::

## Feature Matrix

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

## Environment Variables

| Variable | Purpose | Values |
|---|---|---|
| `PYMDM_PLATFORM` | Override platform auto-detection | `darwin`, `win32` |
| `PYMDM_MDM_PROVIDER` | Override MDM provider auto-detection | `jamf`, `intune` |

## Auto-Detection

pymdm auto-detects the current platform and MDM provider at import time. Override with environment variables when testing cross-platform scripts locally:

```python
from pymdm.platforms import get_platform
from pymdm.mdm import get_provider

platform = get_platform()    # DarwinPlatformInfo or Win32PlatformInfo
provider = get_provider()    # JamfParamParser or IntuneParamProvider
```

## Task Mapping: Jamf vs Intune

| Jamf Pro | Intune Equivalent | pymdm API |
|---|---|---|
| `ParamParser.get(4)` | `IntuneParamProvider().get("PARAM_NAME")` | `get_provider().get(...)` |
| `ParamParser.get_bool(5)` | `IntuneParamProvider().get_bool("FLAG")` | `get_provider().get_bool(...)` |
| Script params via `sys.argv[4-11]` | Env vars or `sys.argv` | Provider-specific |
| `jamf recon` | Microsoft Graph API | Not in pymdm (use provider SDK) |
| swiftDialog | Windows toast/WPF | `Dialog` (macOS only) |
