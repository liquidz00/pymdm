# API Reference

:::{rst-class} lead
Complete API documentation for all pymdm modules.
:::

## Core Modules

- [CommandRunner](command-runner) -- Subprocess execution with credential sanitization
- [MdmLogger](logger) -- Structured logging with rotation
- [SystemInfo](system-info) -- Cross-platform system information
- [WebhookSender](webhook-sender) -- HTTP webhook sender
- [TextTools](text-tools) -- awk, sort, and uniq for parsing command output
- [Dialog](dialog) -- swiftDialog integration (macOS)

## Platform Modules

- [platforms.darwin](platforms-darwin) -- macOS: DarwinPlatformInfo, DarwinCommandSupport, DarwinDefaults, DarwinServiceManager
- [platforms.win32](platforms-win32) -- Windows: Win32PlatformInfo, Win32CommandSupport, Win32Registry, Win32ServiceManager

## MDM Provider Modules

- [mdm](mdm) -- GenericParamParser, JamfParamParser, IntuneParamParser, auto-detection
