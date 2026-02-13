"""Tests for Jamf Pro MDM provider implementation."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from pymdm.mdm.jamf import JamfParamParser

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class TestJamfParamParser:
    """Tests for JamfParamParser MDM parameter parsing."""

    def test_reserved_params_raise_error(self) -> None:
        """Test that reserved parameters (0-3) raise ValueError."""
        parser = JamfParamParser()
        for reserved in [0, 1, 2, 3]:
            with pytest.raises(ValueError, match="reserved by Jamf"):
                parser.get(reserved)

    def test_out_of_range_params_raise_error(self) -> None:
        """Test that out-of-range parameters raise ValueError."""
        parser = JamfParamParser()
        with pytest.raises(ValueError, match="out of usable range"):
            parser.get(12)
        with pytest.raises(ValueError, match="out of usable range"):
            parser.get(-1)

    def test_string_key_raises_type_error(self) -> None:
        """Test that string keys raise TypeError for Jamf parser."""
        parser = JamfParamParser()
        with pytest.raises(TypeError, match="must be integers"):
            parser.get("webhook_url")

    def test_get_valid_params(self, monkeypatch: MonkeyPatch) -> None:
        """Test retrieving valid Jamf parameters."""
        test_args = ["script.py", "mount", "computer", "user", "value4", "value5"]
        monkeypatch.setattr(sys, "argv", test_args)

        parser = JamfParamParser()
        assert parser.get(4) == "value4"
        assert parser.get(5) == "value5"
        assert parser.get(6) is None  # Not provided

    def test_get_bool(self, monkeypatch: MonkeyPatch) -> None:
        """Test boolean parameter parsing."""
        test_args = ["script.py", "m", "c", "u", "true", "false", "1", "yes", "no"]
        monkeypatch.setattr(sys, "argv", test_args)

        parser = JamfParamParser()
        assert parser.get_bool(4) is True
        assert parser.get_bool(5) is False
        assert parser.get_bool(6) is True
        assert parser.get_bool(7) is True
        assert parser.get_bool(8) is False
        assert parser.get_bool(9) is False  # Not provided

    def test_get_int(self, monkeypatch: MonkeyPatch) -> None:
        """Test integer parameter parsing."""
        test_args = ["script.py", "m", "c", "u", "42", "invalid", ""]
        monkeypatch.setattr(sys, "argv", test_args)

        parser = JamfParamParser()
        assert parser.get_int(4) == 42
        assert parser.get_int(5, default=10) == 10  # Invalid
        assert parser.get_int(6, default=5) == 5  # Empty
        assert parser.get_int(7, default=0) == 0  # Not provided

    def test_class_constants(self) -> None:
        """Test that Jamf-specific constants are correctly defined."""
        assert JamfParamParser._RESERVED_PARAMS == (0, 1, 2, 3)
        assert JamfParamParser._MIN_USABLE_PARAM == 4
        assert JamfParamParser._MAX_USABLE_PARAM == 11

    def test_boundary_params(self, monkeypatch: MonkeyPatch) -> None:
        """Test boundary parameters 4 and 11."""
        test_args = [
            "script.py",
            "m",
            "c",
            "u",
            "p4",
            "p5",
            "p6",
            "p7",
            "p8",
            "p9",
            "p10",
            "p11",
        ]
        monkeypatch.setattr(sys, "argv", test_args)

        parser = JamfParamParser()
        assert parser.get(4) == "p4"
        assert parser.get(11) == "p11"
