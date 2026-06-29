# Contributing

Thanks for your interest in contributing to pymdm! This guide covers local setup, the conventions the project follows, and how to land a change.

## Local setup

pymdm uses [uv](https://github.com/astral-sh/uv) for environment and dependency management. From a fresh clone:

```bash
make install-dev          # uv sync --extra dev
make pre-commit-install   # one-time per clone
```

`make help` lists every Make target with a short description.

## Running tests, lint, and format

```bash
make test            # full unit test suite
make test-cov        # tests with terminal coverage report
make test-cov-html   # tests with HTML coverage report (coverage/htmlcov/index.html)
make lint            # ruff format --check + ruff check
make format          # ruff format + ruff check --fix
```

The pre-commit hooks run a subset of these on every commit. If a hook fails, fix the underlying issue, re-stage, and commit again — don't pass `--no-verify`.

## Branch naming

- `feat/<short-description>` for new features
- `fix/<short-description>` for bug fixes
- `docs/<short-description>` for documentation-only changes
- `chore/<short-description>` for tooling, CI, dependencies

Keep descriptions kebab-case and concise. Example: `feat/intune-graph-helpers`.

## Conventional commits

The project uses [Conventional Commits](https://www.conventionalcommits.org/) so the changelog and version bumps stay reproducible.

```text
<type>(<scope>): <subject>

<body>

<footer>
```

- `<type>`: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `build`
- `<scope>`: optional, e.g. `darwin`, `win32`, `mdm`, `logger`, `webhook`
- Append `!` after the type/scope to mark a breaking change: `feat(darwin)!: ...`
- For breaking changes also include a `BREAKING CHANGE:` footer with migration notes.

Example:

```text
feat(darwin)!: rework DarwinDefaults to instance-based with user-context support

DarwinDefaults is now constructed with an optional CommandRunner; read/
write/delete accept as_user=True to dispatch through run_as_user.

BREAKING CHANGE: DarwinDefaults static methods are removed. Callers must
now instantiate (DarwinDefaults() preserves prior root-context behavior).
```

## Architecture orientation

pymdm has two orthogonal abstraction layers:

- **Platform layer** (`src/pymdm/platforms/`) — OS-specific operations (Darwin, Win32). Defined by `PlatformInfo` and `PlatformCommandSupport` Protocols.
- **MDM provider layer** (`src/pymdm/mdm/`) — Jamf vs Intune script parameter conventions. Defined by the `MdmParamParser` ABC, with `GenericParamParser` as the shared positional base.

`SystemInfo` is a thin facade over the platform layer. The MDM provider layer is reached through `get_provider()`, which returns the right `MdmParamParser` subclass.

Detection factories (`get_platform()`, `get_command_support()`, `get_provider()`) read environment variables (`PYMDM_PLATFORM`, `PYMDM_MDM_PROVIDER`) before falling back to `sys.platform`. Tests that flip platforms mid-run must call `clear_platform_cache()`.

For deeper agent-ready guidance, see [CLAUDE.md](https://github.com/liquidz00/pymdm/blob/main/CLAUDE.md) and `.cursor/rules/`.

## Adding a new platform or MDM provider

1. Implement the relevant contract (`PlatformInfo` + `PlatformCommandSupport` Protocols for OS; subclass the `MdmParamParser` ABC, or `GenericParamParser`, for MDM).
2. Add detection arms to `_detection.py` (platforms) or `_base.py::get_provider` (MDM).
3. Mirror the existing test files (`test_platforms_<name>.py` or `test_mdm_<name>.py`).
4. Update `README.md` install paths if the new platform changes the dependency story.
5. Update `CHANGELOG.md` under `[Unreleased]`.

## Tests

- `pytest` only (no `pytest-asyncio`, no `pytest-mock`).
- Mock at the module-local subprocess reference: `pymdm.platforms.darwin.subprocess.run`, NOT global `subprocess.run`.
- Shared fixtures (`temp_dir`, `temp_log_file`, `mock_logger`) live in `tests/conftest.py`.
- Tests must be deterministic — no live network/subprocess calls, no timing-dependent assertions.
- Coverage lives at 90% currently. Don't ship a PR that drops coverage; the gate is configured in `pyproject.toml` (currently commented out but enforced via review).

## Filing issues

- Bug reports: use the [bug report form](https://github.com/liquidz00/pymdm/issues/new?template=bug_report.yml).
- Feature requests: use the [feature request form](https://github.com/liquidz00/pymdm/issues/new?template=feature_request.yml).
- Documentation issues: file as a feature request with the **Documentation** scope.

## Style for examples

When writing example code in docstrings, READMEs, or tests, use `jappleseed` as the placeholder username — never anyone's real name.

## Releasing

Releases are workflow-driven via `build-release.yml`:

1. Bump `__version__` in `src/pymdm/__init__.py`.
2. Move `[Unreleased]` to a new dated heading in `CHANGELOG.md`.
3. Open a PR with these changes; merge to `main`.
4. Trigger the **Build, Release and Publish** workflow manually (`workflow_dispatch`).
5. The action validates the version isn't already tagged, builds sdist + wheel, publishes to PyPI, and drafts a GitHub release.
