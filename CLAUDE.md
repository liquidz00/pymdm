# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`pymdm` is a cross-platform Python utility package for MDM deployment scripts. The primary target is macOS / Jamf Pro running under [MacAdmins Python](https://github.com/macadmins/python) (`#!/usr/local/bin/managed_python3`), with Windows / Intune as a secondary target for mixed fleets.

Python 3.12+ required. Built with setuptools; managed with `uv`.

## Common commands

All development tasks go through the `Makefile` (which wraps `uv`). `make help` lists every target with a description.

- `make install-dev` — `uv sync --extra dev` (sets up `.venv`)
- `make test` — run the full unit test suite
- `make test-cov` / `make test-cov-html` — coverage reports (HTML lands in `coverage/htmlcov/`)
- `make lint` — `ruff format --check` + `ruff check`
- `make format` — `ruff format` + `ruff check --fix`
- `make build` — `uv build --sdist --wheel`
- `make pre-commit-install` — install the pre-commit hooks once per clone

Run a single test: `uv run pytest tests/test_command_runner.py::TestCommandRunner::test_name -v`.

`pytest` is pre-configured (see `pyproject.toml`) to always run with coverage against `src/`. The `--cov-fail-under=90` gate is currently commented out — current coverage sits at 90% so re-enabling is safe whenever desired.

## Architecture

The package has two orthogonal abstraction layers that compose to handle the cross-platform / cross-MDM matrix:

### 1. Platform layer (`src/pymdm/platforms/`)

Abstracts **OS-specific** operations. Two `typing.Protocol`s defined in `_base.py`:

- `PlatformInfo` — serial number, console user, hostname, full name, OS version label
- `PlatformCommandSupport` — `run_as_user_command()` wrapping, user validation, min UID

Concrete implementations: `darwin.py` (`DarwinPlatformInfo`, `DarwinCommandSupport`, plus `DarwinDefaults`, `DarwinServiceManager`) and `win32.py` (`Win32PlatformInfo`, `Win32CommandSupport`, plus `Win32Registry`, `Win32ServiceManager`).

`_detection.py` exports `get_platform()` / `get_command_support()`, both `@lru_cache`d singletons. Detection reads `PYMDM_PLATFORM` env var first (values: `darwin`, `win32`), then falls back to `sys.platform`. Tests that need to flip platforms mid-run must call `clear_platform_cache()` after changing the env var.

### 2. MDM layer (`src/pymdm/mdm/`)

Abstracts **MDM provider** script-parameter conventions. `MdmParamProvider` protocol in `_base.py` defines `get` / `get_bool` / `get_int`. Implementations: `JamfParamParser` (reads `sys.argv[4..11]`; indices 0–3 are reserved by Jamf) and `IntuneParamProvider` (env vars or positional argv).

`get_provider()` in `mdm/_base.py` dispatches on explicit arg → `PYMDM_MDM_PROVIDER` env var → platform default (`jamf` on darwin, `intune` on win32).

### 3. Top-level facades

The public API in `src/pymdm/__init__.py` re-exports user-facing classes. Several of these are thin **backward-compat facades** over the layered implementations — preserve this when refactoring:

- `ParamParser` (`param_parser.py`) — static-method facade that delegates to a shared `JamfParamParser` instance.
- `SystemInfo` (`system_info.py`) — static-method facade that delegates to `get_platform()`.
- `CommandRunner` (`command_runner.py`) — uses `get_command_support()` for `run_as_user` wrapping and user validation; includes credential sanitization in `_sanitize_command` (ordering of regexes matters — more specific patterns first). Supports `check=False` to return `subprocess.CompletedProcess` directly, and `**kwargs` passthrough to `subprocess.run`.
- `MdmLogger` (`logger.py`) — structured logging with size-based rotation. `max_bytes` is a constructor parameter (defaults to 100 MB, `MAX_BYTES`). Backups land at `<logfile>.old`.
- `WebhookSender` (`webhook_sender.py`) — `requests`-based poster with optional auth headers. `requests` is **lazy-imported**: the package imports cleanly without it; `_import_requests()` raises a guided `ImportError` at first call if missing.
- `Dialog` (`dialog.py`) — swiftDialog integration, macOS-only (gracefully no-ops elsewhere).

### 4. DarwinDefaults user-context API (v0.6+)

`DarwinDefaults` is **instance-based** — there are no static methods. The constructor takes an optional `CommandRunner`; `read` / `write` / `delete` accept `as_user: bool = False` per call:

```python
# Root context (or whatever the script runs as)
defaults = DarwinDefaults()
defaults.read("com.apple.SoftwareUpdate", "AutomaticCheckEnabled")

# User context — pipe through a configured CommandRunner
runner = CommandRunner(logger=logger, username="jappleseed", uid=501)
defaults = DarwinDefaults(runner=runner)
defaults.read("com.apple.dock", "orientation", as_user=True)
defaults.write("com.apple.dock", "tilesize", "48", "-int", as_user=True)
```

`as_user=True` without a configured runner raises `ValueError` to fail loudly rather than silently running in root context.

### Version

Single source of truth is `__version__` in `src/pymdm/__init__.py`, wired into `pyproject.toml` via `tool.setuptools.dynamic`. Bump there when releasing.

### Type hints distribution (PEP 561)

`src/pymdm/py.typed` is shipped in the wheel via `[tool.setuptools.package-data]`. Downstream consumers receive pymdm's type hints. Don't break the typing contract — preserve overload signatures (e.g. `CommandRunner.run`) and keep public APIs annotated.

## Optional dependencies

`requests` is intentionally optional. Three install paths documented in the README:

- `pip install pymdm[requests]` — standard installs that need WebhookSender
- `pip install pymdm[managed]` — managed_python3 (already bundles requests; empty marker extra)
- `pip install pymdm` — bare; WebhookSender raises ImportError if used

If you add new HTTP code, keep the lazy-import discipline. Don't `import requests` at module top.

## Platform References

- macOS `defaults` and `launchctl`: use `man defaults`, `man launchctl` as source of truth
- macOS version label: use `platform.mac_ver()[0]`, NOT `platform.release()` (which returns the Darwin kernel version)
- Windows registry: winreg stdlib docs (https://docs.python.org/3/library/winreg.html)
- Windows services: `sc.exe` — `sc /?` for subcommand reference
- subprocess patterns: always use list form, never `shell=True` unless pipes are required

## Conventions

- `from __future__ import annotations` is used in the platform/mdm modules for forward refs. Follow this pattern in new modules that need it.
- Protocols over ABCs — both abstraction layers use `typing.Protocol` with `@runtime_checkable` so implementations don't inherit. Don't convert to ABCs.
- Ruff is the single linter/formatter. Line length 100. Rules enabled: a narrow select (`E101`, `F401`, `F403`, `I001`, `N801`, `N802`, `N806`); `E722` is ignored; `__init__.py` files ignore `F401`.
- pre-commit hooks in `.pre-commit-config.yaml`: ruff format + check, validate-pyproject, file hygiene, secrets detection. Run `make pre-commit-install` once per clone.
- Tests mirror source file layout (`test_<module>.py`). Shared fixtures (`temp_dir`, `temp_log_file`, `mock_logger`) are in `tests/conftest.py`.
- For example users in code/docstrings, use `jappleseed` (or `johnny.appleseed`).
- Conventional commits expected. Branch naming: `feat/<description>`, `fix/<description>`. Breaking changes use `!` (e.g. `feat(darwin)!: ...`) and a `BREAKING CHANGE:` footer.

## Cursor rules (for AI-assisted editing)

`.cursor/rules/` contains scoped guidance for editor-integrated AI:

- `python-general-best-practices.mdc` — code style, type hints, what this repo is and isn't
- `sphinx-docstrings.mdc` — Sphinx/reST docstring enforcement
- `darwin-scripting.mdc` — macOS-specific patterns (paths, subprocess, TCC, defaults, launchctl)
- `windows-scripting.mdc` — Windows-specific patterns (PowerShell, winreg, sc.exe, runas caveats)
- `pymdm-architecture.mdc` — abstraction layer rules (Protocol, lazy imports, facades)
- `testing-conventions.mdc` — pytest patterns specific to this repo
