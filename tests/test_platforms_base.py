"""Tests for platform protocol conformance."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pymdm.platforms._base import (
    PlatformCommandSupport,
    PlatformInfo,
)
from pymdm.platforms.darwin import (
    DarwinCommandSupport,
    DarwinPlatformInfo,
)
from pymdm.platforms.win32 import (
    Win32CommandSupport,
    Win32PlatformInfo,
)

if TYPE_CHECKING:
    pass


class TestPlatformInfoProtocol:
    """Verify all PlatformInfo implementations satisfy the protocol."""

    @pytest.mark.parametrize(
        "impl_class",
        [DarwinPlatformInfo, Win32PlatformInfo],
        ids=["darwin", "win32"],
    )
    def test_is_platform_info(self, impl_class: type) -> None:
        """Test that implementation is recognized as PlatformInfo."""
        instance = impl_class()
        assert isinstance(instance, PlatformInfo)

    @pytest.mark.parametrize(
        "impl_class",
        [DarwinPlatformInfo, Win32PlatformInfo],
        ids=["darwin", "win32"],
    )
    def test_has_invalid_users(self, impl_class: type) -> None:
        """Test that implementation defines invalid_users class variable."""
        assert hasattr(impl_class, "invalid_users")
        assert isinstance(impl_class.invalid_users, tuple)
        assert len(impl_class.invalid_users) > 0

    @pytest.mark.parametrize(
        "impl_class",
        [DarwinPlatformInfo, Win32PlatformInfo],
        ids=["darwin", "win32"],
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
        [DarwinCommandSupport, Win32CommandSupport],
        ids=["darwin", "win32"],
    )
    def test_is_command_support(self, impl_class: type) -> None:
        """Test that implementation is recognized as PlatformCommandSupport."""
        instance = impl_class()
        assert isinstance(instance, PlatformCommandSupport)

    @pytest.mark.parametrize(
        "impl_class",
        [DarwinCommandSupport, Win32CommandSupport],
        ids=["darwin", "win32"],
    )
    def test_has_required_methods(self, impl_class: type) -> None:
        """Test that implementation has all required methods."""
        instance = impl_class()
        assert callable(getattr(instance, "run_as_user_command", None))
        assert callable(getattr(instance, "validate_user", None))
        assert isinstance(instance.min_user_uid, int)
