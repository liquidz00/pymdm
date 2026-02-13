"""Tests for SystemInfo facade.

These tests verify the SystemInfo facade works correctly by forcing the
Darwin platform backend (which the original tests were written against).
Platform-specific implementation tests live in test_platforms_*.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from pymdm.platforms._detection import clear_platform_cache

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture(autouse=True)
def _force_darwin_platform(monkeypatch: MonkeyPatch) -> None:
    """Force Darwin platform for all tests in this module.

    The original test_system_info tests were written against macOS-specific
    subprocess calls. By forcing PYMDM_PLATFORM=darwin, the SystemInfo facade
    delegates to DarwinPlatformInfo regardless of the runner OS.
    """
    clear_platform_cache()
    monkeypatch.setenv("PYMDM_PLATFORM", "darwin")
    yield
    clear_platform_cache()


# Import SystemInfo after fixture is defined (it's used at call time, not import time)
from pymdm import SystemInfo


@patch("pymdm.platforms.darwin.subprocess.check_output")
def test_get_serial_number(mock_check_output) -> None:
    """Test getting serial number."""
    mock_check_output.return_value = json.dumps(
        {"SPHardwareDataType": [{"serial_number": "C02ABC123DEF"}]}
    )

    serial = SystemInfo.get_serial_number()
    assert serial == "C02ABC123DEF"
    assert mock_check_output.called


@patch("pymdm.platforms.darwin.subprocess.check_output")
def test_get_serial_number_failure(mock_check_output) -> None:
    """Test serial number returns None on failure."""
    mock_check_output.side_effect = Exception("Command failed")

    serial = SystemInfo.get_serial_number()
    assert serial is None


@patch("pymdm.platforms.darwin.subprocess.check_output")
def test_get_console_user(mock_check_output) -> None:
    """Test getting console user."""
    mock_check_output.side_effect = ["testuser\n", "501\n"]  # username  # uid

    with patch("pathlib.Path.exists", return_value=True):
        result = SystemInfo.get_console_user()

        assert result is not None
        username, uid, home = result
        assert username == "testuser"
        assert uid == 501
        assert home == Path("/Users/testuser")


@patch("pymdm.platforms.darwin.subprocess.check_output")
def test_get_console_user_invalid(mock_check_output) -> None:
    """Test console user returns None for invalid users."""
    mock_check_output.return_value = "root\n"

    result = SystemInfo.get_console_user()
    assert result is None


@patch("pymdm.platforms.darwin.subprocess.check_output")
def test_get_console_user_missing_home(mock_check_output) -> None:
    """Test console user returns None if home doesn't exist."""
    mock_check_output.side_effect = ["testuser\n", "501\n"]

    with patch("pathlib.Path.exists", return_value=False):
        result = SystemInfo.get_console_user()
        assert result is None


def test_get_hostname() -> None:
    """Test getting hostname."""
    hostname = SystemInfo.get_hostname()
    assert isinstance(hostname, str)
    assert len(hostname) > 0


@patch("pymdm.platforms.darwin.subprocess.check_output")
def test_get_user_full_name(mock_check_output) -> None:
    """Test getting user full name."""
    mock_check_output.return_value = "Test User\n"

    full_name = SystemInfo.get_user_full_name("testuser")
    assert full_name == "Test User"


@patch("pymdm.platforms.darwin.subprocess.check_output")
def test_get_user_full_name_failure(mock_check_output) -> None:
    """Test full name returns None on failure."""
    mock_check_output.side_effect = Exception("Command failed")

    full_name = SystemInfo.get_user_full_name("testuser")
    assert full_name is None
