"""Tests for platform protocol conformance."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pymdm.platforms._base import (
    PlatformCommandSupport,
    PlatformDialogSupport,
    PlatformInfo,
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
    pass


class TestPlatformInfoProtocol:
    """Verify all PlatformInfo implementations satisfy the protocol."""

    @pytest.mark.parametrize(
        "impl_class",
        [DarwinPlatformInfo, Win32PlatformInfo, LinuxPlatformInfo],
        ids=["darwin", "win32", "linux"],
    )
    def test_is_platform_info(self, impl_class: type) -> None:
        """Test that implementation is recognized as PlatformInfo."""
        instance = impl_class()
        assert isinstance(instance, PlatformInfo)

    @pytest.mark.parametrize(
        "impl_class",
        [DarwinPlatformInfo, Win32PlatformInfo, LinuxPlatformInfo],
        ids=["darwin", "win32", "linux"],
    )
    def test_has_invalid_users(self, impl_class: type) -> None:
        """Test that implementation defines invalid_users class variable."""
        assert hasattr(impl_class, "invalid_users")
        assert isinstance(impl_class.invalid_users, tuple)
        assert len(impl_class.invalid_users) > 0

    @pytest.mark.parametrize(
        "impl_class",
        [DarwinPlatformInfo, Win32PlatformInfo, LinuxPlatformInfo],
        ids=["darwin", "win32", "linux"],
    )
    def test_has_required_methods(self, impl_class: type) -> None:
        """Test that implementation has all required methods."""
        instance = impl_class()
        assert callable(getattr(instance, "get_serial_number", None))
        assert callable(getattr(instance, "get_console_user", None))
        assert callable(getattr(instance, "get_hostname", None))
        assert callable(getattr(instance, "get_user_full_name", None))
        assert callable(getattr(instance, "get_os_version_label", None))


class TestPlatformCommandSupportProtocol:
    """Verify all PlatformCommandSupport implementations satisfy the protocol."""

    @pytest.mark.parametrize(
        "impl_class",
        [DarwinCommandSupport, Win32CommandSupport, LinuxCommandSupport],
        ids=["darwin", "win32", "linux"],
    )
    def test_is_command_support(self, impl_class: type) -> None:
        """Test that implementation is recognized as PlatformCommandSupport."""
        instance = impl_class()
        assert isinstance(instance, PlatformCommandSupport)

    @pytest.mark.parametrize(
        "impl_class",
        [DarwinCommandSupport, Win32CommandSupport, LinuxCommandSupport],
        ids=["darwin", "win32", "linux"],
    )
    def test_has_required_methods(self, impl_class: type) -> None:
        """Test that implementation has all required methods."""
        instance = impl_class()
        assert callable(getattr(instance, "run_as_user_command", None))
        assert callable(getattr(instance, "validate_user", None))
        assert isinstance(instance.min_user_uid, int)


class TestPlatformDialogSupportProtocol:
    """Verify all PlatformDialogSupport implementations satisfy the protocol."""

    @pytest.mark.parametrize(
        "impl_class",
        [DarwinDialogSupport, Win32DialogSupport, LinuxDialogSupport],
        ids=["darwin", "win32", "linux"],
    )
    def test_is_dialog_support(self, impl_class: type) -> None:
        """Test that implementation is recognized as PlatformDialogSupport."""
        instance = impl_class()
        assert isinstance(instance, PlatformDialogSupport)

    @pytest.mark.parametrize(
        "impl_class",
        [DarwinDialogSupport, Win32DialogSupport, LinuxDialogSupport],
        ids=["darwin", "win32", "linux"],
    )
    def test_has_required_properties(self, impl_class: type) -> None:
        """Test that implementation has all required properties."""
        instance = impl_class()
        assert isinstance(instance.shared_temp_dir, str)
        assert isinstance(instance.dialog_available, bool)
        assert isinstance(instance.unavailable_message, str)
        # standard_binary_path can be str or None
        assert instance.standard_binary_path is None or isinstance(
            instance.standard_binary_path, str
        )
