import json
from pathlib import Path
from unittest.mock import patch

from pymdm import SystemInfo


@patch("subprocess.check_output")
def test_get_serial_number(mock_check_output):
    """Test getting serial number."""
    mock_check_output.return_value = json.dumps(
        {"SPHardwareDataType": [{"serial_number": "C02ABC123DEF"}]}
    )

    serial = SystemInfo.get_serial_number()
    assert serial == "C02ABC123DEF"
    assert mock_check_output.called


@patch("subprocess.check_output")
def test_get_serial_number_failure(mock_check_output):
    """Test serial number returns None on failure."""
    mock_check_output.side_effect = Exception("Command failed")

    serial = SystemInfo.get_serial_number()
    assert serial is None


@patch("subprocess.check_output")
def test_get_console_user(mock_check_output):
    """Test getting console user."""
    mock_check_output.side_effect = ["testuser\n", "501\n"]  # username  # uid

    with patch("pathlib.Path.exists", return_value=True):
        result = SystemInfo.get_console_user()

        assert result is not None
        username, uid, home = result
        assert username == "testuser"
        assert uid == 501
        assert home == Path("/Users/testuser")


@patch("subprocess.check_output")
def test_get_console_user_invalid(mock_check_output):
    """Test console user returns None for invalid users."""
    mock_check_output.return_value = "root\n"

    result = SystemInfo.get_console_user()
    assert result is None


@patch("subprocess.check_output")
def test_get_console_user_missing_home(mock_check_output):
    """Test console user returns None if home doesn't exist."""
    mock_check_output.side_effect = ["testuser\n", "501\n"]

    with patch("pathlib.Path.exists", return_value=False):
        result = SystemInfo.get_console_user()
        assert result is None


def test_get_hostname():
    """Test getting hostname."""
    hostname = SystemInfo.get_hostname()
    assert isinstance(hostname, str)
    assert len(hostname) > 0


@patch("subprocess.check_output")
def test_get_user_full_name(mock_check_output):
    """Test getting user full name."""
    mock_check_output.return_value = "Test User\n"

    full_name = SystemInfo.get_user_full_name("testuser")
    assert full_name == "Test User"


@patch("subprocess.check_output")
def test_get_user_full_name_failure(mock_check_output):
    """Test full name returns None on failure."""
    mock_check_output.side_effect = Exception("Command failed")

    full_name = SystemInfo.get_user_full_name("testuser")
    assert full_name is None
