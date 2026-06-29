<!-- markdownlint-capture -->
<!-- markdownlint-disable -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `TextTools` — a small helper for the handful of Unix text idioms whose Python equivalent is non-obvious: `awk` (field extraction by delimiter), `sort` (multi-key, numeric-aware), and `uniq` (with `sort | uniq -c`-style counts). Each method accepts a multi-line `str` or a `list[str]`, and an optional `MdmLogger` enables debug-level call tracing
- `GenericParamParser` — a neutral positional `sys.argv` parameter parser. It is the new safe default for any platform or provider that isn't specifically Jamf or Intune
- `get_provider()` is now exported at the top level (`from pymdm import get_provider`)
- `PYMDM_MDM_PROVIDER` accepts a new `generic` value

### Changed

- **BREAKING:** the MDM provider layer moved from a `typing.Protocol` (`MdmParamProvider`) to an abstract base class (`MdmParamParser`). Providers now inherit — `JamfParamParser` and `IntuneParamParser` extend `GenericParamParser` — and the shared `get_bool` / `get_int` coercion lives once on the base instead of being duplicated per provider
- **BREAKING:** `IntuneParamProvider` renamed to `IntuneParamParser` for naming consistency across providers
- **BREAKING:** `get_provider()` no longer defaults macOS to Jamf. With no explicit provider and no `PYMDM_MDM_PROVIDER`, it now returns `GenericParamParser` on macOS (and any non-Windows platform) and `IntuneParamParser` only on Windows. Jamf shops should pass `get_provider("jamf")` or set `PYMDM_MDM_PROVIDER=jamf`. This removes a dangerous assumption that broke non-Jamf macOS fleets (Kandji, Mosyle), whose own `sys.argv` indices were rejected by Jamf's reserved-index guard

### Removed

- **BREAKING:** the top-level `ParamParser` Jamf facade. Replace `ParamParser.get(4)` / `ParamParser.get_bool(4)` with `get_provider().get(4)` / `get_provider().get_bool(4)` (importing via `from pymdm.mdm import get_provider`), or instantiate `JamfParamParser()` directly
- Dead backward-compat cruft in `system_info.py` (`_get_invalid_users`, duplicated `_INVALID_USERS`)

## [v0.6.0] - 2026-05-09

### Added

- `MdmLogger` accepts a `max_bytes` constructor parameter (defaults to `MAX_BYTES`, 100 MB) so log rotation is configurable per logger and deterministically testable
- `pymdm[managed]` extras marker for users running under MacAdmins `managed_python3`. Empty by design — signals intent without pulling a duplicate `requests` since `managed_python3` already bundles it
- PEP 561 `py.typed` marker shipped in the wheel via `[tool.setuptools.package-data]`. Downstream consumers now receive pymdm's type hints
- `DarwinDefaults` instance API supports user-context reads/writes via an optional `CommandRunner` and a per-call `as_user: bool = False` flag. When `as_user=True`, operations dispatch through `CommandRunner.run_as_user` (which uses `launchctl asuser` + `sudo -u` on macOS)

### Changed

- `WebhookSender` now lazy-imports `requests` inside its methods. The package imports cleanly without `requests` installed; calling `WebhookSender.send()` / `send_logfile()` without it raises a guided `ImportError` pointing to the correct extras install path
- `README.md` install section documents three explicit install paths: `pymdm[requests]` (standard), `pymdm[managed]` (managed_python3), and bare `pymdm` (no HTTP)

### Fixed

- `MdmLogger._format_script_name` was using `rstrip(".sh")` / `rstrip(".py")` which strips any character in the suffix set rather than the suffix itself — `"bash.sh"` rendered as `"Ba"` and `"setup.py"` as `"Setu"`. Now uses `removesuffix` so script names are formatted correctly
- `DarwinPlatformInfo.get_os_version_label` now uses `platform.mac_ver()[0]` (the macOS productVersion, e.g. `"26.4.1"`) instead of `platform.release()` which returns the Darwin kernel version (e.g. `"25.4.0"` on macOS 26.4.1) and was being incorrectly labeled "macOS Version" in startup logs
- Removed dead `subprocess.list2cmdline` call in `Win32CommandSupport.run_as_user_command`

### Removed

- **BREAKING:** `DarwinDefaults` static methods (`DarwinDefaults.read`, `.write`, `.delete`) are removed. The class is now instance-based — see Migration Notes

### Migration Notes

`DarwinDefaults` is the only breaking change in this release. All other public APIs (`SystemInfo`, `ParamParser`, `CommandRunner`, `MdmLogger`, `WebhookSender`, `Dialog`, `DarwinServiceManager`, `Win32Registry`, `Win32ServiceManager`) are backward compatible.

**Before (v0.5.x):**

```python
from pymdm.platforms.darwin import DarwinDefaults

DarwinDefaults.read("com.apple.SoftwareUpdate", "AutomaticCheckEnabled")
DarwinDefaults.write("com.example.app", "Setting", "value")
DarwinDefaults.delete("com.example.app", "Setting")
```

**After (v0.6.0):**

```python
from pymdm.platforms.darwin import DarwinDefaults

# Root context (preserves prior behavior — drop-in replacement)
defaults = DarwinDefaults()
defaults.read("com.apple.SoftwareUpdate", "AutomaticCheckEnabled")
defaults.write("com.example.app", "Setting", "value")
defaults.delete("com.example.app", "Setting")

# User context — pipe through a configured CommandRunner
from pymdm import CommandRunner

runner = CommandRunner(logger=logger, username="jappleseed", uid=501)
defaults = DarwinDefaults(runner=runner)
defaults.read("com.apple.dock", "orientation", as_user=True)
defaults.write("com.apple.dock", "tilesize", "48", "-int", as_user=True)
```

`as_user=True` without a configured `CommandRunner` raises `ValueError` to fail loudly rather than silently falling through to root context.

### Install paths (clarified)

| Use case | Command |
|---|---|
| Standard pip install with `WebhookSender` | `pip install pymdm[requests]` |
| MacAdmins `managed_python3` (bundles `requests`) | `pip install pymdm[managed]` |
| No HTTP needed | `pip install pymdm` |

## [v0.5.0] - 2026-04-18

### Added

- `CommandRunner.run()` accepts `check` parameter — `check=False` returns `subprocess.CompletedProcess` instead of `str`, enabling callers to inspect exit codes without exception handling
- `CommandRunner.run()` and `run_as_user()` accept `**kwargs` passthrough to `subprocess.run`
- `WebhookSender` accepts optional `headers` parameter for header-based webhook authentication
- `DarwinDefaults` class (`pymdm.platforms.darwin`) — read, write, and delete macOS `defaults` plist values
- `DarwinServiceManager` class (`pymdm.platforms.darwin`) — `launchctl` service management: is_loaded, bootout, bootstrap
- `Win32Registry` class (`pymdm.platforms.win32`) — read, write, and delete Windows registry values via `winreg`
- `Win32ServiceManager` class (`pymdm.platforms.win32`) — Windows service management via `sc.exe`: is_running, start, stop, delete

## [v0.4.3] - 2026-02-25

### Fixed

- Darwin username validation regex now accepts `@` in usernames (e.g. `user@domain.com`)
- `run_as_user` error messages now include actual username and uid values for easier debugging

## [v0.4.2] - 2026-02-16

### Fixed

- Logger methods `error()`, `warn()`, `debug()`, and `log_exception()` now correctly forward `exit_code` to `update_log()` (was silently landing on `startup` parameter since v0.4.0)
- Darwin username validation regex now accepts `.` (period) in usernames

## [v0.4.1] - 2026-02-15

### Added

- `env` parameter on `CommandRunner.run()` for passing custom environment variables to subprocesses

## [v0.4.0] - 2026-02-13

### Added

- Windows/Intune support alongside existing macOS/Jamf Pro functionality
- Platform abstraction layer (`pymdm.platforms`) with OS-specific implementations
  - `pymdm.platforms.darwin` - macOS: system_profiler, launchctl
  - `pymdm.platforms.win32` - Windows: PowerShell, wmic, runas
- MDM provider abstraction layer (`pymdm.mdm`) with provider-specific implementations
  - `pymdm.mdm.jamf` - Jamf Pro parameter parsing (extracted from ParamParser)
  - `pymdm.mdm.intune` - Intune parameter provider (env vars + argv)
- Auto-detection of platform and MDM provider with environment variable overrides
  - `PYMDM_PLATFORM` - override OS detection (darwin, win32)
  - `PYMDM_MDM_PROVIDER` - override MDM provider (jamf, intune)
- Protocol-based interfaces for platform and provider extensibility
- Windows CI testing (windows-latest added to GitHub Actions matrix)
- Comprehensive test suite for all platform and provider modules (188 tests, 87% coverage)

### Changed

- `SystemInfo` now delegates to platform-specific implementations (backward compatible)
- `CommandRunner.run_as_user()` now uses platform-specific command wrapping (backward compatible)
- `CommandRunner._validate_user()` now uses platform-specific UID thresholds (backward compatible)
- `MdmLogger.log_startup()` now shows correct OS label per platform (was hardcoded "macOS Version")
- `Dialog.show()` now returns a graceful error on non-macOS platforms (swiftDialog is macOS-only)
- Updated project description and keywords for cross-platform scope

### Migration Notes

- All existing imports and public APIs are fully backward compatible
- No changes required for existing macOS/Jamf Pro scripts
- New Windows/Intune scripts should use `pymdm.mdm.IntuneParamProvider` or `pymdm.mdm.get_provider()`

## [v0.3.0] - 2026-01-09

### Added

- Initial version
