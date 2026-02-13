"""Tests for platform detection and factory functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pymdm.platforms._detection import (
    clear_platform_cache,
    get_command_support,
    get_dialog_support,
    get_platform,
)
from pymdm.platforms.darwin import (
    DarwinCommandSupport,
    DarwinDialogSupport,
    DarwinPlatformInfo,
)
from pymdm.platforms.linux import (
    LinuxCommandSupport,
    LinuxDialogSupport,
    LinuxPlatformInfo,
)
from pymdm.platforms.win32 import (
    Win32CommandSupport,
    Win32DialogSupport,
    Win32PlatformInfo,
)

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Clear platform detection cache before each test."""
    clear_platform_cache()
    yield
    clear_platform_cache()


class TestGetPlatform:
    """Tests for get_platform() factory function."""

    def test_darwin_detection(self, monkeypatch: MonkeyPatch) -> None:
        """Test that Darwin platform is detected correctly."""
        monkeypatch.setenv("PYMDM_PLATFORM", "darwin")
        result = get_platform()
        assert isinstance(result, DarwinPlatformInfo)

    def test_win32_detection(self, monkeypatch: MonkeyPatch) -> None:
        """Test that Win32 platform is detected correctly."""
        monkeypatch.setenv("PYMDM_PLATFORM", "win32")
        result = get_platform()
        assert isinstance(result, Win32PlatformInfo)

    def test_windows_alias_detection(self, monkeypatch: MonkeyPatch) -> None:
        """Test that 'windows' alias resolves to Win32 platform."""
        monkeypatch.setenv("PYMDM_PLATFORM", "windows")
        result = get_platform()
        assert isinstance(result, Win32PlatformInfo)

    def test_linux_detection(self, monkeypatch: MonkeyPatch) -> None:
        """Test that Linux platform is detected correctly."""
        monkeypatch.setenv("PYMDM_PLATFORM", "linux")
        result = get_platform()
        assert isinstance(result, LinuxPlatformInfo)

    def test_unsupported_platform(self, monkeypatch: MonkeyPatch) -> None:
        """Test that unsupported platforms raise NotImplementedError."""
        monkeypatch.setenv("PYMDM_PLATFORM", "freebsd")
        with pytest.raises(NotImplementedError, match="freebsd"):
            get_platform()

    def test_env_var_override(self, monkeypatch: MonkeyPatch) -> None:
        """Test that PYMDM_PLATFORM env var overrides sys.platform."""
        monkeypatch.setenv("PYMDM_PLATFORM", "linux")
        result = get_platform()
        assert isinstance(result, LinuxPlatformInfo)

    def test_case_insensitive(self, monkeypatch: MonkeyPatch) -> None:
        """Test that platform detection is case-insensitive."""
        monkeypatch.setenv("PYMDM_PLATFORM", "DARWIN")
        result = get_platform()
        assert isinstance(result, DarwinPlatformInfo)


class TestGetCommandSupport:
    """Tests for get_command_support() factory function."""

    def test_darwin_command_support(self, monkeypatch: MonkeyPatch) -> None:
        """Test Darwin command support is returned for macOS."""
        monkeypatch.setenv("PYMDM_PLATFORM", "darwin")
        result = get_command_support()
        assert isinstance(result, DarwinCommandSupport)

    def test_win32_command_support(self, monkeypatch: MonkeyPatch) -> None:
        """Test Win32 command support is returned for Windows."""
        monkeypatch.setenv("PYMDM_PLATFORM", "win32")
        result = get_command_support()
        assert isinstance(result, Win32CommandSupport)

    def test_linux_command_support(self, monkeypatch: MonkeyPatch) -> None:
        """Test Linux command support is returned for Linux."""
        monkeypatch.setenv("PYMDM_PLATFORM", "linux")
        result = get_command_support()
        assert isinstance(result, LinuxCommandSupport)

    def test_unsupported_platform(self, monkeypatch: MonkeyPatch) -> None:
        """Test that unsupported platforms raise NotImplementedError."""
        monkeypatch.setenv("PYMDM_PLATFORM", "freebsd")
        with pytest.raises(NotImplementedError):
            get_command_support()


class TestGetDialogSupport:
    """Tests for get_dialog_support() factory function."""

    def test_darwin_dialog_support(self, monkeypatch: MonkeyPatch) -> None:
        """Test Darwin dialog support is returned for macOS."""
        monkeypatch.setenv("PYMDM_PLATFORM", "darwin")
        result = get_dialog_support()
        assert isinstance(result, DarwinDialogSupport)

    def test_win32_dialog_support(self, monkeypatch: MonkeyPatch) -> None:
        """Test Win32 dialog support is returned for Windows."""
        monkeypatch.setenv("PYMDM_PLATFORM", "win32")
        result = get_dialog_support()
        assert isinstance(result, Win32DialogSupport)

    def test_linux_dialog_support(self, monkeypatch: MonkeyPatch) -> None:
        """Test Linux dialog support is returned for Linux."""
        monkeypatch.setenv("PYMDM_PLATFORM", "linux")
        result = get_dialog_support()
        assert isinstance(result, LinuxDialogSupport)

    def test_unsupported_platform(self, monkeypatch: MonkeyPatch) -> None:
        """Test that unsupported platforms raise NotImplementedError."""
        monkeypatch.setenv("PYMDM_PLATFORM", "freebsd")
        with pytest.raises(NotImplementedError):
            get_dialog_support()


class TestClearPlatformCache:
    """Tests for clear_platform_cache() utility."""

    def test_cache_clear_allows_redetection(self, monkeypatch: MonkeyPatch) -> None:
        """Test that clearing cache allows new platform detection."""
        monkeypatch.setenv("PYMDM_PLATFORM", "darwin")
        first = get_platform()
        assert isinstance(first, DarwinPlatformInfo)

        clear_platform_cache()
        monkeypatch.setenv("PYMDM_PLATFORM", "linux")
        second = get_platform()
        assert isinstance(second, LinuxPlatformInfo)
