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
