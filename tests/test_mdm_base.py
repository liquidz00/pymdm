"""Tests for MDM provider base protocol and factory."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from pymdm.mdm._base import MdmParamProvider, get_provider
from pymdm.mdm.intune import IntuneParamProvider
from pymdm.mdm.jamf import JamfParamParser

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class TestMdmParamProviderProtocol:
    """Verify all MdmParamProvider implementations satisfy the protocol."""

    @pytest.mark.parametrize(
        "impl_class",
        [JamfParamParser, IntuneParamProvider],
        ids=["jamf", "intune"],
    )
    def test_is_param_provider(self, impl_class: type) -> None:
        """Test that implementation is recognized as MdmParamProvider."""
        instance = impl_class()
        assert isinstance(instance, MdmParamProvider)

    @pytest.mark.parametrize(
        "impl_class",
        [JamfParamParser, IntuneParamProvider],
        ids=["jamf", "intune"],
    )
    def test_has_required_methods(self, impl_class: type) -> None:
        """Test that implementation has all required methods."""
        instance = impl_class()
        assert callable(getattr(instance, "get", None))
        assert callable(getattr(instance, "get_bool", None))
        assert callable(getattr(instance, "get_int", None))


class TestGetProvider:
    """Tests for get_provider() factory function."""

    def test_explicit_jamf(self) -> None:
        """Test explicit Jamf provider selection."""
        provider = get_provider("jamf")
        assert isinstance(provider, JamfParamParser)

    def test_explicit_intune(self) -> None:
        """Test explicit Intune provider selection."""
        provider = get_provider("intune")
        assert isinstance(provider, IntuneParamProvider)

    def test_env_var_override(self, monkeypatch: MonkeyPatch) -> None:
        """Test PYMDM_MDM_PROVIDER env var override."""
        monkeypatch.setenv("PYMDM_MDM_PROVIDER", "intune")
        provider = get_provider()
        assert isinstance(provider, IntuneParamProvider)

    def test_default_on_darwin(self, monkeypatch: MonkeyPatch) -> None:
        """Test that Jamf is default on macOS (darwin)."""
        monkeypatch.delenv("PYMDM_MDM_PROVIDER", raising=False)
        monkeypatch.setattr(sys, "platform", "darwin")
        provider = get_provider()
        assert isinstance(provider, JamfParamParser)

    def test_default_on_win32(self, monkeypatch: MonkeyPatch) -> None:
        """Test that Intune is default on Windows (win32)."""
        monkeypatch.delenv("PYMDM_MDM_PROVIDER", raising=False)
        monkeypatch.setattr(sys, "platform", "win32")
        provider = get_provider()
        assert isinstance(provider, IntuneParamProvider)

    def test_unknown_provider_raises(self) -> None:
        """Test that unknown provider names raise ValueError."""
        with pytest.raises(ValueError, match="Unknown MDM provider"):
            get_provider("workspace_one")

    def test_case_insensitive(self) -> None:
        """Test that provider names are case-insensitive."""
        provider = get_provider("JAMF")
        assert isinstance(provider, JamfParamParser)

        provider = get_provider("Intune")
        assert isinstance(provider, IntuneParamProvider)
