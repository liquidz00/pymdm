<!-- markdownlint-capture -->
<!-- markdownlint-disable -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Cross-platform support: macOS, Windows, and Linux
- Platform abstraction layer (`pymdm.platforms`) with OS-specific implementations
  - `pymdm.platforms.darwin` - macOS: system_profiler, launchctl, swiftDialog
  - `pymdm.platforms.win32` - Windows: PowerShell, wmic, runas
  - `pymdm.platforms.linux` - Linux: /sys/class/dmi, sudo, pwd
- MDM provider abstraction layer (`pymdm.mdm`) with provider-specific implementations
  - `pymdm.mdm.jamf` - Jamf Pro parameter parsing (extracted from ParamParser)
  - `pymdm.mdm.intune` - Intune parameter provider (env vars + argv)
- Auto-detection of platform and MDM provider with environment variable overrides
  - `PYMDM_PLATFORM` - override OS detection (darwin, win32, linux)
  - `PYMDM_MDM_PROVIDER` - override MDM provider (jamf, intune)
- Protocol-based interfaces for platform and provider extensibility
- Windows CI testing (windows-latest added to GitHub Actions matrix)
- Comprehensive test suite for all platform and provider modules (236 tests, 88% coverage)

### Changed

- `SystemInfo` now delegates to platform-specific implementations (backward compatible)
- `CommandRunner.run_as_user()` now uses platform-specific command wrapping (backward compatible)
- `CommandRunner._validate_user()` now uses platform-specific UID thresholds (backward compatible)
- `MdmLogger.log_startup()` now shows correct OS label per platform (was hardcoded "macOS Version")
- `Dialog` now checks platform support before attempting to show (graceful error on non-macOS)
- `Dialog.__init__` temp_dir default is now platform-aware (was hardcoded /Users/Shared)
- Updated project description and keywords for cross-platform scope

### Migration Notes

- All existing imports and public APIs are fully backward compatible
- No changes required for existing macOS/Jamf Pro scripts
- New Windows/Intune scripts should use `pymdm.mdm.IntuneParamProvider` or `pymdm.mdm.get_provider()`

## [v0.3.0] - 2026-01-09

### Added

- Initial version
