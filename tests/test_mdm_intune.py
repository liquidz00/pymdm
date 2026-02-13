"""Tests for Intune MDM provider implementation."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from pymdm.mdm.intune import IntuneParamProvider

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class TestIntuneParamProvider:
    """Tests for IntuneParamProvider MDM parameter parsing."""

    def test_get_from_argv(self, monkeypatch: MonkeyPatch) -> None:
        """Test retrieving parameters from sys.argv by integer index."""
        test_args = ["script.ps1", "value1", "value2"]
        monkeypatch.setattr(sys, "argv", test_args)

        provider = IntuneParamProvider()
        assert provider.get(0) == "script.ps1"
        assert provider.get(1) == "value1"
        assert provider.get(2) == "value2"
        assert provider.get(3) is None  # Not provided

    def test_get_from_env(self, monkeypatch: MonkeyPatch) -> None:
        """Test retrieving parameters from environment variables."""
        monkeypatch.setenv("WEBHOOK_URL", "https://example.com")
        monkeypatch.setenv("DEBUG_MODE", "true")

        provider = IntuneParamProvider()
        assert provider.get("WEBHOOK_URL") == "https://example.com"
        assert provider.get("DEBUG_MODE") == "true"
        assert provider.get("NONEXISTENT") is None

    def test_get_from_env_with_intune_prefix(self, monkeypatch: MonkeyPatch) -> None:
        """Test that INTUNE_ prefixed env vars are found as fallback."""
        monkeypatch.setenv("INTUNE_WEBHOOK_URL", "https://intune.example.com")

        provider = IntuneParamProvider()
        assert provider.get("WEBHOOK_URL") == "https://intune.example.com"

    def test_get_env_direct_takes_precedence(self, monkeypatch: MonkeyPatch) -> None:
        """Test that direct env var name takes precedence over INTUNE_ prefix."""
        monkeypatch.setenv("WEBHOOK_URL", "https://direct.com")
        monkeypatch.setenv("INTUNE_WEBHOOK_URL", "https://prefixed.com")

        provider = IntuneParamProvider()
        assert provider.get("WEBHOOK_URL") == "https://direct.com"

    def test_get_bool_from_argv(self, monkeypatch: MonkeyPatch) -> None:
        """Test boolean parameter parsing from sys.argv."""
        test_args = ["script.ps1", "true", "false", "1", "yes", "no"]
        monkeypatch.setattr(sys, "argv", test_args)

        provider = IntuneParamProvider()
        assert provider.get_bool(1) is True
        assert provider.get_bool(2) is False
        assert provider.get_bool(3) is True
        assert provider.get_bool(4) is True
        assert provider.get_bool(5) is False

    def test_get_bool_from_env(self, monkeypatch: MonkeyPatch) -> None:
        """Test boolean parameter parsing from environment variables."""
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("VERBOSE", "0")

        provider = IntuneParamProvider()
        assert provider.get_bool("DEBUG") is True
        assert provider.get_bool("VERBOSE") is False
        assert provider.get_bool("NONEXISTENT") is False

    def test_get_int_from_argv(self, monkeypatch: MonkeyPatch) -> None:
        """Test integer parameter parsing from sys.argv."""
        test_args = ["script.ps1", "42", "invalid", ""]
        monkeypatch.setattr(sys, "argv", test_args)

        provider = IntuneParamProvider()
        assert provider.get_int(1) == 42
        assert provider.get_int(2, default=10) == 10  # Invalid
        assert provider.get_int(3, default=5) == 5  # Empty
        assert provider.get_int(4, default=0) == 0  # Not provided

    def test_get_int_from_env(self, monkeypatch: MonkeyPatch) -> None:
        """Test integer parameter parsing from environment variables."""
        monkeypatch.setenv("TIMEOUT", "60")
        monkeypatch.setenv("RETRIES", "invalid")

        provider = IntuneParamProvider()
        assert provider.get_int("TIMEOUT") == 60
        assert provider.get_int("RETRIES", default=3) == 3
        assert provider.get_int("NONEXISTENT", default=30) == 30

    def test_no_reserved_params(self, monkeypatch: MonkeyPatch) -> None:
        """Test that Intune has no reserved parameter indices."""
        test_args = ["script.ps1", "arg1", "arg2", "arg3"]
        monkeypatch.setattr(sys, "argv", test_args)

        provider = IntuneParamProvider()
        # All indices should work (no reserved params like Jamf)
        assert provider.get(0) == "script.ps1"
        assert provider.get(1) == "arg1"
        assert provider.get(2) == "arg2"
        assert provider.get(3) == "arg3"
