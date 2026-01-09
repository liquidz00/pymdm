import sys

import pytest

from pymdm import ParamParser


def test_param_parser_reserved_validation():
    """Test that reserved parameters raise ValueError."""
    for reserved in [0, 1, 2, 3]:
        with pytest.raises(ValueError, match="reserved by Jamf"):
            ParamParser.get(reserved)


def test_param_parser_out_of_range():
    """Test that parameters outside 4-11 raise ValueError."""
    with pytest.raises(ValueError, match="out of usable range"):
        ParamParser.get(12)

    with pytest.raises(ValueError, match="out of usable range"):
        ParamParser.get(-1)


def test_param_parser_get(monkeypatch):
    """Test getting Jamf parameters."""
    # Mock sys.argv
    test_args = ["script.py", "mount", "computer", "user", "value4", "value5"]
    monkeypatch.setattr(sys, "argv", test_args)

    assert ParamParser.get(4) == "value4"
    assert ParamParser.get(5) == "value5"
    assert ParamParser.get(6) is None  # Not provided


def test_param_parser_get_bool(monkeypatch):
    """Test boolean parameter parsing."""
    test_args = ["script.py", "m", "c", "u", "true", "false", "1", "yes", "no"]
    monkeypatch.setattr(sys, "argv", test_args)

    assert ParamParser.get_bool(4) is True
    assert ParamParser.get_bool(5) is False
    assert ParamParser.get_bool(6) is True
    assert ParamParser.get_bool(7) is True
    assert ParamParser.get_bool(8) is False
    assert ParamParser.get_bool(9) is False  # Not provided


def test_param_parser_get_int(monkeypatch):
    """Test integer parameter parsing."""
    test_args = ["script.py", "m", "c", "u", "42", "invalid", ""]
    monkeypatch.setattr(sys, "argv", test_args)

    assert ParamParser.get_int(4) == 42
    assert ParamParser.get_int(5, default=10) == 10  # Invalid
    assert ParamParser.get_int(6, default=5) == 5  # Empty
    assert ParamParser.get_int(7, default=0) == 0  # Not provided
