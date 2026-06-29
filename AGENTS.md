# AGENTS.md

Instructions for AI coding agents working on pymdm. Tool-agnostic — applies
equally to Claude Code, Cursor, Aider, or any other coding assistant.

## What pymdm is

A cross-platform Python utility package for MDM deployment scripts. The primary
target is macOS / Jamf Pro running under [MacAdmins
Python](https://github.com/macadmins/python)
(`#!/usr/local/bin/managed_python3`). Windows / Intune is a secondary target
for mixed-platform fleets. Distributed on PyPI as `pymdm`.

This is a **library**, not a CLI. There is no `[project.scripts]` entry, no
`click` dependency, no `__main__.py`. Consumers `from pymdm import ...`. The
package ships a `py.typed` marker so downstream consumers receive its type
hints (PEP 561).

A goal is "no required runtime dependencies" so the package drops into
managed_python3 cleanly. `requests` is intentionally optional and lazy-imported
inside `WebhookSender`.

## Quick start

```bash
# Set up dev environment (uv handles the venv + deps)
make install-dev          # uv sync --extra dev

# Common make targets — `make help` lists every target with a description
make test                 # pytest tests/ -v
make test-cov             # pytest with coverage to term + coverage/htmlcov
make lint                 # ruff format --check + ruff check
make format               # ruff format + ruff check --fix
make build                # uv build (sdist + wheel)
make docs                 # sphinx-build -b html docs/ docs/_build/

# One-time per clone
make pre-commit-install
```

Run a single test: `uv run pytest tests/test_logger.py::test_format_script_name -v`.

## Project layout

```
src/pymdm/
├── __init__.py             # Public API surface; __version__ canonical here
├── py.typed                # PEP 561 marker (empty file, shipped in wheel)
├── command_runner.py       # CommandRunner — subprocess wrapper, credential sanitization, run_as_user
├── logger.py               # MdmLogger — structured logging, size-based rotation (max_bytes)
├── webhook_sender.py       # WebhookSender — requests-based poster, requests is LAZY-IMPORTED
├── dialog.py               # swiftDialog integration, macOS-only (gracefully no-ops elsewhere)
├── system_info.py          # Backward-compat facade over get_platform()
├── platforms/              # OS abstraction layer
│   ├── _base.py            # PlatformInfo + PlatformCommandSupport Protocols (@runtime_checkable)
│   ├── _detection.py       # get_platform() / get_command_support() lru_cached factories
│   ├── darwin.py           # DarwinPlatformInfo, DarwinCommandSupport, DarwinDefaults, DarwinServiceManager
│   └── win32.py            # Win32PlatformInfo, Win32CommandSupport, Win32Registry, Win32ServiceManager
└── mdm/                    # MDM provider abstraction layer
    ├── _base.py            # MdmParamParser ABC + GenericParamParser + get_provider() factory
    ├── jamf.py             # JamfParamParser (extends Generic; sys.argv[4..11]; 0–3 reserved by Jamf)
    └── intune.py           # IntuneParamParser (extends Generic; env vars + argv)

tests/                      # pytest, flat layout, conftest.py with shared fixtures
docs/                       # Sphinx + myst-parser; user-guide/, api-reference/
.cursor/rules/              # Editor-integrated AI guidance, scoped by glob
```

## Architecture

Two **orthogonal** abstraction layers compose to handle the
cross-platform / cross-MDM matrix (platforms are Protocol-based, mdm is an ABC):

1. **Platform layer** (`platforms/`) — OS-specific operations.
2. **MDM provider layer** (`mdm/`) — script-parameter conventions per provider.

They're independent: a Darwin host running Intune is supportable in principle
because the layers don't know about each other. Detection factories
(`get_platform()`, `get_command_support()`, `get_provider()`) read environment
variables (`PYMDM_PLATFORM`, `PYMDM_MDM_PROVIDER`) before falling back to
`sys.platform`.

`SystemInfo` (static methods) is a thin facade over the platform layer,
delegating to `get_platform()`. The MDM layer has no facade — call
`get_provider()` to get the right `MdmParamParser` subclass. (The old
`ParamParser` Jamf facade was removed in 0.7.0, BREAKING.)

`CommandRunner.run` and `run_as_user` carry `@overload` declarations for
`check=True` vs `check=False` so type-checkers see the right return type.
Don't drop the overloads.

### DarwinDefaults user-context API (v0.6+)

`DarwinDefaults` is **instance-based** — there are no static methods. The
constructor takes an optional `CommandRunner`; `read` / `write` / `delete`
accept `as_user: bool = False` per call:

```python
defaults = DarwinDefaults()  # root context
defaults.read("com.apple.SoftwareUpdate", "AutomaticCheckEnabled")

# User context — pipe through a configured CommandRunner
runner = CommandRunner(logger=logger, username="jappleseed", uid=501)
defaults = DarwinDefaults(runner=runner)
defaults.read("com.apple.dock", "orientation", as_user=True)
```

`as_user=True` without a configured runner raises `ValueError` to fail loudly
rather than silently running in root context.

## Conventions

### Code style

- **Ruff** for linting + formatting. `make lint` is the source of truth.
  Don't introduce Black, isort, autopep8, or yapf.
- **Line length 100**, double quotes, target Python 3.12.
- **Modern union syntax** (`str | None`, `list[int]`, `dict[str, Any]`) — NOT
  `Optional[T]`, `Union[A, B]`, `List[T]`, `Dict[K, V]`.
- **Sphinx/reST docstrings** for every public function, method, and class.
  Use `:param:`, `:type:`, `:return:`, `:rtype:`, `:raises:`. Do NOT use Google
  or NumPy docstring style. See `.cursor/rules/sphinx-docstrings.mdc`.
- **PEP 8 naming**: `snake_case` for funcs/vars, `PascalCase` for classes,
  `UPPER_CASE` for constants.
- **Type hints on everything**, including private helpers when their behavior
  isn't obvious from the signature.

### Synchronous, by design

pymdm is **not** async. There is no `asyncio`, no `httpx.AsyncClient`, no
`pytest.mark.asyncio`. MDM scripts are synchronous one-shot processes; adding
an async layer would only complicate the surface for no real benefit. Don't
suggest async refactors.

### Protocol (platforms) vs ABC (mdm)

The **platform layer** uses `typing.Protocol` with `@runtime_checkable`.
Implementations DO NOT inherit from the Protocol — they satisfy it
structurally. Keep it that way; structural subtyping is what makes mocking
and parallel implementations easy.

The **mdm layer** is deliberately an ABC (`MdmParamParser`). It was moved off
Protocol because the layer carries shared coercion code (`get_bool`/`get_int`
on the base) and pymdm owns every provider in-tree, so Protocol's headline
benefit (works with classes you don't control) doesn't apply. Providers
inherit: `JamfParamParser`/`IntuneParamParser` → `GenericParamParser` → `MdmParamParser`.

### Dependencies

- Managed by `uv`. `make install-dev` sets up `.venv` with all dev extras.
- `[project.dependencies]` is intentionally empty — runtime is stdlib-only by
  design.
- Optional extras: `requests`, `managed`, `docs`, `dev`. The `managed` extra
  is empty on purpose — it's a marker for users running under `managed_python3`
  (which already bundles requests).
- Don't add new top-level dependencies casually. The "no required runtime
  deps" property is the package's pitch for managed_python3 compatibility.

### Lazy imports for optional dependencies

`requests` is lazy-imported inside `webhook_sender.py` via
`_import_requests()`. Calling `WebhookSender.send()` without `requests`
installed raises a guided `ImportError`. Same pattern applies to `winreg`
(lazy-imported inside `Win32Registry` methods so `pymdm.platforms.win32`
imports cleanly on macOS). Don't `import requests` or `import winreg` at
module top.

### Errors

- Catch specific, expected exceptions where possible. `E722` is ignored in
  ruff, but bare `except` is still discouraged — prefer `except Exception:`
  with a contextual log.
- Platform helpers (`DarwinDefaults`, `Win32Registry`, etc.) follow a
  **non-raising convention**: return `None` / `False` on failure rather than
  raising. Don't change this — many callers depend on it.

### Commits

Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`,
`test:`, `build:`, `ci:`). Append `!` for breaking changes (e.g.
`feat(darwin)!: ...`) and include a `BREAKING CHANGE:` footer with migration
notes. Pre-commit + ruff + format-check enforced on every commit.

Branch naming: `feat/<description>`, `fix/<description>`,
`docs/<description>`, `chore/<description>`. Kebab-case descriptions.

### Style for examples

When writing example code in docstrings, READMEs, or tests, use `jappleseed`
(or `johnny.appleseed`) as the placeholder username. Never use anyone's real
name.

## Testing

- `pytest` only — no `pytest-asyncio`, no `pytest-mock`. Use `unittest.mock`
  directly for patching.
- Tests are in `tests/` (flat layout — no nested directories). Shared fixtures
  (`temp_dir`, `temp_log_file`, `mock_logger`) live in `tests/conftest.py`.
- Coverage is configured to run on every `pytest` invocation. Current floor:
  **90%**. The `--cov-fail-under=90` gate is commented out in `pyproject.toml`
  but enforced via review — don't drop below it without a discussion.
- **Mock at module-local references**: `pymdm.platforms.darwin.subprocess.run`,
  NOT global `subprocess.run`. Module-local patches survive refactors.
- For tests that flip platforms via `PYMDM_PLATFORM`, use the autouse fixture
  pattern from `test_system_info.py` — clear `lru_cache` before AND after.
- `Dialog` tests are macOS-only via `pytestmark =
  pytest.mark.skipif(sys.platform != "darwin", ...)`. Pure-Python pieces
  (`DialogTemplate.to_jsonstring`, `DialogReturn` parsing) could safely run
  everywhere — that's a known coverage gap, not a feature gate.
- No live network or subprocess calls. No timing-dependent assertions, no
  reliance on system locale or timezone.

## Things to be careful about

These are known rough spots / limitations. Don't refactor them as part of an
unrelated PR; flag them in an issue and tackle separately.

- **Windows code provenance.** Every line under `platforms/win32.py` and
  `tests/test_platforms_win32.py` was authored by AI agents — there's no
  contributor with deep Windows experience to verify behavior end-to-end.
  Be cautious with claims about Windows behavior; prefer mechanisms with
  documented Microsoft Learn references over recall.

- **`Win32PlatformInfo.get_console_user` is broken in SYSTEM context.**
  `os.getlogin()` returns the user who started the controlling terminal
  session, which is "SYSTEM" (or raises) in Intune SYSTEM context. The
  documented-correct API is `WTSQuerySessionInformation` via `ctypes` /
  `pywin32`. Not implemented today; flag if a feature depends on it.

- **`Win32CommandSupport.run_as_user_command` requires interactive auth.**
  It wraps with `Start-Process -Credential (Get-Credential ...)` — but
  `Get-Credential` is interactive, so the API does not work in MDM SYSTEM
  context. The docstring acknowledges it; the surface still presents as if
  it works. Don't introduce code that assumes Windows `run_as_user` "just
  works."

- **PowerShell f-string injection risk in `Win32PlatformInfo.get_user_full_name`.**
  Builds the command body with f-strings; usernames containing `'` break it.
  Low security risk (caller-controlled input) but a robustness issue.

- **Coverage gate is commented out in `pyproject.toml`.** Currently sitting at
  90%. Don't ship a PR that drops coverage; re-enabling the gate is fine
  whenever desired.

- **`Dialog` is large** (~900 lines, all in `dialog.py`). Could be split into
  template / return / executor modules. Style only — no functional issue.

## What's out of scope

- **Linux platform** — `_detection.py` explicitly raises `NotImplementedError`
  for `linux`. Adding Linux is reasonable future work but not currently
  supported. Discuss in an issue first.

- **More MDM providers.** Workspace ONE, Kandji, Mosyle, FileWave, JumpCloud,
  Addigy — all reasonable additions, all currently absent. Each requires a
  new `MdmParamParser` subclass (often extending `GenericParamParser`) + tests
  + at least one tester with access to the target system.

- **Async refactor.** See "Synchronous, by design" above.

- **A CLI surface** (`patcherctl`-style). pymdm is a library. If a script
  using pymdm makes sense as its own CLI, it belongs in a separate package.

- **Live-tenant integration tests.** All tests are unit-level with mocks.
  Full end-to-end against a real Jamf Pro instance is a release-time concern
  handled by smoke testing, not per-PR CI.

- **Adding new required runtime dependencies** without a strong case. The
  managed_python3 compatibility story depends on minimal deps.

## Where to look for more context

- `CHANGELOG.md` — release history, breaking changes flagged
- `README.md` — install paths (`[requests]` vs `[managed]`), Quick Start, full
  example scripts for both Jamf and Intune
- `docs/` — Sphinx site (publishes to https://pymdm.readthedocs.io)
- `docs/contributing.md` — contributor guide (also linked from root
  `CONTRIBUTING.md`)
- `pyproject.toml` — extras, ruff config, pytest config
- `.pre-commit-config.yaml` — required hooks
- `.cursor/rules/` — editor-integrated AI rules, scoped by glob:
  - `python-general-best-practices.mdc` — code style, type hints
  - `sphinx-docstrings.mdc` — docstring enforcement
  - `darwin-scripting.mdc` — macOS subprocess / TCC / launchctl / defaults
  - `windows-scripting.mdc` — PowerShell / winreg / sc.exe / runas caveats
  - `pymdm-architecture.mdc` — abstraction layer rules
  - `testing-conventions.mdc` — pytest patterns specific to this repo
- `CLAUDE.md` — equivalent guidance scoped to Claude Code; some overlap with
  this file is intentional, both are kept canonical
