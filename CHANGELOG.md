<!-- markdownlint-capture -->
<!-- markdownlint-disable -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
