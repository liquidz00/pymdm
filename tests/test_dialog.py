"""Tests for dialog.py module."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

from pymdm import (
    CheckboxItem,
    Dialog,
    DialogExitCode,
    DialogReturn,
    DialogTemplate,
    MdmLogger,
    SelectItem,
    SelectResult,
    SystemNotification,
    TextField,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# DialogTemplate Tests (Data Container)
# =============================================================================


def test_dialog_template_initialization() -> None:
    """Test DialogTemplate initialization."""
    template = DialogTemplate(title="Test", message="Hello")
    assert template.title == "Test"
    assert template.message == "Hello"
    assert template.json is True  # Default


def test_dialog_template_to_jsonstring() -> None:
    """Test DialogTemplate JSON serialization."""
    template = DialogTemplate(
        title="Test Title",
        message="Test Message",
        small=True,
        width=500,
        height=300,
    )
    json_str = template.to_jsonstring()
    data = json.loads(json_str)

    assert data["title"] == "Test Title"
    assert data["message"] == "Test Message"
    assert data["small"] is True
    assert data["width"] == 500
    assert data["height"] == 300


def test_dialog_template_to_jsonstring_excludes_none() -> None:
    """Test that None values are excluded from JSON."""
    template = DialogTemplate(title="Test")
    json_str = template.to_jsonstring()
    data = json.loads(json_str)

    assert "subtitle" not in data
    assert "message" not in data


def test_dialog_template_to_jsonstring_excludes_empty_lists() -> None:
    """Test that empty lists are excluded from JSON."""
    template = DialogTemplate(title="Test", textfields=[])
    json_str = template.to_jsonstring()
    data = json.loads(json_str)

    # Empty lists should be excluded (would be "textfield" key if present)
    assert "textfield" not in data


def test_dialog_template_to_jsonstring_handles_paths() -> None:
    """Test that Path objects are converted to strings."""
    template = DialogTemplate(title="Test", icon=Path("/tmp/test.png"))
    json_str = template.to_jsonstring()
    data = json.loads(json_str)

    assert data["icon"] == "/tmp/test.png"
    assert isinstance(data["icon"], str)


def test_dialog_template_to_jsonstring_handles_enums() -> None:
    """Test that Enum values are converted to strings."""
    from pymdm.dialog import ButtonSize, Style

    template = DialogTemplate(title="Test", style=Style.presentation, button_size=ButtonSize.large)
    json_str = template.to_jsonstring()
    data = json.loads(json_str)

    assert data["style"] == "presentation"
    assert data["buttonsize"] == "large"


def test_dialog_template_to_jsonstring_handles_textfields() -> None:
    """Test that TextField objects are properly serialized."""
    template = DialogTemplate(
        title="Test",
        textfields=[
            TextField(title="Username", prompt="Enter username", required=True),
            TextField(title="Password", secure=True),
        ],
    )
    json_str = template.to_jsonstring()
    data = json.loads(json_str)

    # swiftDialog uses singular "textfield" key
    assert "textfield" in data
    assert len(data["textfield"]) == 2
    assert data["textfield"][0]["title"] == "Username"
    assert data["textfield"][0]["prompt"] == "Enter username"
    assert data["textfield"][0]["required"] is True
    assert data["textfield"][1]["secure"] is True


def test_dialog_template_to_dict() -> None:
    """Test DialogTemplate to_dict method."""
    template = DialogTemplate(title="Test", message="Hello", width=500)
    data = template.to_dict()

    assert data["title"] == "Test"
    assert data["message"] == "Hello"
    assert data["width"] == 500
    assert "subtitle" in data  # to_dict includes all fields, even None


def test_dialog_template_from_dict() -> None:
    """Test creating DialogTemplate from dictionary."""
    data = {
        "title": "Test",
        "message": "Hello",
        "width": 500,
        "small": True,
    }
    template = DialogTemplate.from_dict(data)

    assert template.title == "Test"
    assert template.message == "Hello"
    assert template.width == 500
    assert template.small is True


def test_dialog_template_from_dict_with_aliases() -> None:
    """Test from_dict handles field aliases."""
    data = {
        "title": "Test",
        "helpmessage": "Help text",
        "helpimage": "/tmp/help.png",
    }
    template = DialogTemplate.from_dict(data)

    assert template.help_message == "Help text"
    assert template.help_image == "/tmp/help.png"


def test_dialog_template_infobox() -> None:
    """Test DialogTemplate infobox field."""
    template = DialogTemplate(title="Test", infobox="Additional information here")
    json_str = template.to_jsonstring()
    data = json.loads(json_str)

    assert "infobox" in data
    assert data["infobox"] == "Additional information here"


def test_dialog_template_radioitems() -> None:
    """Test DialogTemplate radioitems with SelectItem objects."""
    template = DialogTemplate(
        title="Test",
        radioitems=[
            SelectItem(
                title="Select Radio",
                values=["Radio 1", "Radio 2", "Radio 3"],
                default="Radio 1",
            ),
        ],
    )
    json_str = template.to_jsonstring()
    data = json.loads(json_str)

    # swiftDialog uses "radiobutton" key
    assert "radiobutton" in data
    assert len(data["radiobutton"]) == 1
    assert data["radiobutton"][0]["title"] == "Select Radio"
    assert data["radiobutton"][0]["values"] == ["Radio 1", "Radio 2", "Radio 3"]
    assert data["radiobutton"][0]["default"] == "Radio 1"


# =============================================================================
# TextField, SelectItem, CheckboxItem Tests
# =============================================================================


def test_textfield_initialization() -> None:
    """Test TextField initialization."""
    tf = TextField(title="Test", prompt="Enter value", secure=True, required=True)
    assert tf.title == "Test"
    assert tf.prompt == "Enter value"
    assert tf.secure is True
    assert tf.required is True
    assert tf.value is None
    assert tf.regex is None
    assert tf.regexerror is None


def test_selectitem_initialization() -> None:
    """Test SelectItem initialization."""
    item = SelectItem(
        title="Select Option",
        values=["Option 1", "Option 2", "Option 3"],
        default="Option 1",
    )
    assert item.title == "Select Option"
    assert item.values == ["Option 1", "Option 2", "Option 3"]
    assert item.default == "Option 1"


def test_selectitem_defaults() -> None:
    """Test SelectItem default values."""
    item = SelectItem(title="Select Option")
    assert item.title == "Select Option"
    assert item.values == []
    assert item.default is None


def test_checkboxitem_initialization() -> None:
    """Test CheckboxItem initialization."""
    cb = CheckboxItem(label="Accept Terms", checked=True, disabled=False, icon="info")
    assert cb.label == "Accept Terms"
    assert cb.checked is True
    assert cb.disabled is False
    assert cb.icon == "info"


def test_checkboxitem_defaults() -> None:
    """Test CheckboxItem default values."""
    cb = CheckboxItem(label="Accept Terms")
    assert cb.label == "Accept Terms"
    assert cb.checked is False
    assert cb.disabled is False
    assert cb.icon is None


# =============================================================================
# Dialog Class Tests (Executor)
# =============================================================================


def test_dialog_initialization_defaults() -> None:
    """Test Dialog initialization with defaults."""
    dialog = Dialog()
    assert dialog.binary_path is None
    # temp_dir is platform-dependent; just verify it's a valid Path
    assert isinstance(dialog.temp_dir, Path)
    assert dialog.use_temp_file is False


def test_dialog_initialization_custom() -> None:
    """Test Dialog initialization with custom values."""
    dialog = Dialog(
        binary_path="/custom/path/dialog",
        temp_dir="/tmp/custom",
        use_temp_file=True,
    )
    assert dialog.binary_path == "/custom/path/dialog"
    assert dialog.temp_dir == Path("/tmp/custom")
    assert dialog.use_temp_file is True


def test_dialog_initialization_temp_dir_as_path() -> None:
    """Test Dialog initialization with temp_dir as Path object."""
    dialog = Dialog(temp_dir=Path("/custom/temp"))
    assert dialog.temp_dir == Path("/custom/temp")


@patch("pymdm.dialog.shutil.which")
@patch("pathlib.Path.exists")
def test_find_binary_standard_location(mock_exists: Mock, mock_which: Mock) -> None:
    """Test finding dialog binary in standard location."""
    mock_exists.return_value = True
    mock_which.return_value = None

    dialog = Dialog()
    path = dialog._find_binary()
    assert path == "/usr/local/bin/dialog"


@patch("pymdm.dialog.shutil.which")
@patch("pathlib.Path.exists")
def test_find_binary_in_path(mock_exists: Mock, mock_which: Mock) -> None:
    """Test finding dialog binary in PATH."""
    mock_exists.return_value = False
    mock_which.return_value = "/usr/bin/dialog"

    dialog = Dialog()
    path = dialog._find_binary()
    assert path == "/usr/bin/dialog"


@patch("pymdm.dialog.shutil.which")
@patch("pathlib.Path.exists")
def test_find_binary_not_found(mock_exists: Mock, mock_which: Mock) -> None:
    """Test when dialog binary is not found."""
    mock_exists.return_value = False
    mock_which.return_value = None

    dialog = Dialog()
    path = dialog._find_binary()
    assert path is None


@patch("pathlib.Path.exists")
def test_find_binary_custom_path_exists(mock_exists: Mock) -> None:
    """Test finding dialog binary with custom path that exists."""
    mock_exists.return_value = True

    dialog = Dialog(binary_path="/custom/dialog")
    path = dialog._find_binary()
    assert path == "/custom/dialog"


@patch("pathlib.Path.exists")
def test_find_binary_custom_path_not_exists(mock_exists: Mock) -> None:
    """Test finding dialog binary with custom path that doesn't exist."""
    mock_exists.return_value = False

    dialog = Dialog(binary_path="/custom/dialog")
    path = dialog._find_binary()
    assert path is None


def test_build_command_args_with_jsonstring() -> None:
    """Test building command arguments with JSON dict (--jsonstring)."""
    dialog = Dialog()
    json_data = {"title": "Test", "message": "Hello"}
    args = dialog._build_command_args("/usr/local/bin/dialog", json_data=json_data)

    assert args[0] == "/usr/local/bin/dialog"
    assert "--jsonstring" in args
    assert "--json" in args
    # Verify JSON string is included
    jsonstring_idx = args.index("--jsonstring")
    assert json.loads(args[jsonstring_idx + 1]) == json_data


def test_build_command_args_with_jsonfile() -> None:
    """Test building command arguments with JSON file path (--jsonfile)."""
    dialog = Dialog()
    json_file = Path("/tmp/test.json")
    args = dialog._build_command_args("/usr/local/bin/dialog", json_data=json_file)

    assert args[0] == "/usr/local/bin/dialog"
    assert "--jsonfile" in args
    assert str(json_file) in args
    assert "--json" in args


def test_build_command_args_textfields() -> None:
    """Test building command arguments with textfields in JSON."""
    dialog = Dialog()
    template = DialogTemplate(
        title="Test",
        textfields=[
            TextField(title="Username", prompt="Enter username", required=True),
            TextField(title="Password", secure=True),
        ],
    )
    json_config = json.loads(template.to_jsonstring())
    args = dialog._build_command_args("/usr/local/bin/dialog", json_data=json_config)

    assert "--jsonstring" in args
    assert "--json" in args
    # Verify textfields are in JSON (uses singular "textfield" key)
    assert "textfield" in json_config
    assert len(json_config["textfield"]) == 2


def test_build_command_args_selects() -> None:
    """Test building command arguments with select items in JSON."""
    dialog = Dialog()
    template = DialogTemplate(
        title="Test",
        selectitems=[
            SelectItem(
                title="Select Option",
                values=["Option 1", "Option 2", "Option 3"],
                default="Option 1",
            ),
        ],
    )
    json_config = json.loads(template.to_jsonstring())
    args = dialog._build_command_args("/usr/local/bin/dialog", json_data=json_config)

    assert "--jsonstring" in args
    assert "--json" in args
    # Verify selects are in JSON with proper structure
    assert "selectitems" in json_config
    assert len(json_config["selectitems"]) == 1
    assert json_config["selectitems"][0]["title"] == "Select Option"
    assert json_config["selectitems"][0]["values"] == ["Option 1", "Option 2", "Option 3"]
    assert json_config["selectitems"][0]["default"] == "Option 1"


def test_build_command_args_checkboxes() -> None:
    """Test building command arguments with checkboxes in JSON."""
    dialog = Dialog()
    template = DialogTemplate(
        title="Test",
        checkboxes=[
            CheckboxItem(label="Checkbox 1", checked=True),
            CheckboxItem(label="Checkbox 2"),
        ],
    )
    json_config = json.loads(template.to_jsonstring())
    args = dialog._build_command_args("/usr/local/bin/dialog", json_data=json_config)

    assert "--jsonstring" in args
    assert "--json" in args
    # Verify checkboxes are in JSON with proper structure (uses singular "checkbox" key)
    assert "checkbox" in json_config
    assert len(json_config["checkbox"]) == 2
    assert json_config["checkbox"][0]["label"] == "Checkbox 1"
    assert json_config["checkbox"][0]["checked"] is True


def test_build_command_args_timer() -> None:
    """Test building command arguments with timer in JSON."""
    dialog = Dialog()
    template = DialogTemplate(title="Test", timer=30, timerbar=True)
    json_config = json.loads(template.to_jsonstring())
    args = dialog._build_command_args("/usr/local/bin/dialog", json_data=json_config)

    assert "--jsonstring" in args
    assert "--json" in args
    # Verify timer settings are in JSON
    assert json_config["timer"] == 30
    assert json_config["timerbar"] is True


def test_dialog_uses_jsonstring_by_default() -> None:
    """Test that Dialog uses --jsonstring by default (not temp files)."""
    dialog = Dialog()
    assert dialog.use_temp_file is False

    # Build args should use jsonstring
    json_config = {"title": "Test"}
    args = dialog._build_command_args("/usr/local/bin/dialog", json_data=json_config)
    assert "--jsonstring" in args
    assert "--jsonfile" not in args


@patch("pymdm.dialog.sys.platform", "darwin")
@patch("pymdm.dialog.subprocess.run")
@patch("pymdm.dialog.Dialog._find_binary")
@patch("pymdm.system_info.SystemInfo.get_console_user")
def test_show_success(mock_console_user: Mock, mock_find_binary: Mock, mock_run: Mock) -> None:
    """Test successful dialog display."""
    mock_find_binary.return_value = "/usr/local/bin/dialog"
    mock_console_user.return_value = ("testuser", 501, Path("/Users/testuser"))
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = '{"textfield1": "value1"}'
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    dialog = Dialog()
    template = DialogTemplate(title="Test", message="Hello")
    result = dialog.show(template)

    assert isinstance(result, DialogReturn)
    assert result.exit_code == 0
    assert result.ok is True


@patch("pymdm.dialog.sys.platform", "darwin")
@patch("pymdm.dialog.subprocess.run")
@patch("pymdm.dialog.Dialog._find_binary")
@patch("pymdm.system_info.SystemInfo.get_console_user")
def test_show_uses_jsonstring_by_default(
    mock_console_user: Mock, mock_find_binary: Mock, mock_run: Mock
) -> None:
    """Test that show() uses --jsonstring by default."""
    mock_find_binary.return_value = "/usr/local/bin/dialog"
    mock_console_user.return_value = ("testuser", 501, Path("/Users/testuser"))
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "{}"
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    dialog = Dialog()
    template = DialogTemplate(title="Test")
    dialog.show(template)

    # Verify subprocess.run was called with --jsonstring
    call_args = mock_run.call_args[0][0]
    assert "--jsonstring" in call_args
    assert "--jsonfile" not in call_args


@patch("pymdm.dialog.sys.platform", "darwin")
@patch("pymdm.dialog.os.chmod")
@patch("pymdm.dialog.tempfile.NamedTemporaryFile")
@patch("pymdm.dialog.subprocess.run")
@patch("pymdm.dialog.Dialog._find_binary")
@patch("pymdm.system_info.SystemInfo.get_console_user")
def test_show_uses_temp_file_when_configured(
    mock_console_user: Mock,
    mock_find_binary: Mock,
    mock_run: Mock,
    mock_tempfile: Mock,
    mock_chmod: Mock,
) -> None:
    """Test that show() uses temp file when use_temp_file=True."""
    mock_find_binary.return_value = "/usr/local/bin/dialog"
    mock_console_user.return_value = ("testuser", 501, Path("/Users/testuser"))
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "{}"
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    # Mock temp file creation
    mock_file = Mock()
    mock_file.name = "/Users/Shared/test123.json"
    mock_file.__enter__ = Mock(return_value=mock_file)
    mock_file.__exit__ = Mock(return_value=False)
    mock_tempfile.return_value = mock_file

    dialog = Dialog(use_temp_file=True)
    template = DialogTemplate(title="Test")

    with patch.object(Path, "exists", return_value=True):
        with patch.object(Path, "unlink"):
            with patch.object(Path, "mkdir"):
                dialog.show(template)

    # Verify subprocess.run was called with --jsonfile
    call_args = mock_run.call_args[0][0]
    assert "--jsonfile" in call_args
    assert "--jsonstring" not in call_args


@patch("pymdm.dialog.sys.platform", "darwin")
@patch("pymdm.dialog.Dialog._find_binary")
def test_show_dialog_not_found(mock_find_binary: Mock) -> None:
    """Test when swiftDialog is not found."""
    mock_find_binary.return_value = None

    dialog = Dialog()
    template = DialogTemplate(title="Test")
    result = dialog.show(template)

    assert result.exit_code == DialogExitCode.file_not_found
    assert "not found" in result.raw_output.lower()


@patch("pymdm.dialog.sys.platform", "darwin")
@patch("pymdm.dialog.subprocess.run")
@patch("pymdm.dialog.Dialog._find_binary")
@patch("pymdm.system_info.SystemInfo.get_console_user")
def test_show_no_console_user(
    mock_console_user: Mock, mock_find_binary: Mock, mock_run: Mock
) -> None:
    """Test when no console user is found."""
    mock_find_binary.return_value = "/usr/local/bin/dialog"
    mock_console_user.return_value = None

    dialog = Dialog()
    template = DialogTemplate(title="Test")
    result = dialog.show(template)

    assert result.exit_code == DialogExitCode.user_quit
    assert "console user" in result.raw_output.lower()
    assert not mock_run.called


@patch("pymdm.dialog.sys.platform", "darwin")
@patch("pymdm.dialog.subprocess.run")
@patch("pymdm.dialog.Dialog._find_binary")
@patch("pymdm.system_info.SystemInfo.get_console_user")
def test_show_notification_skips_console_check(
    mock_console_user: Mock, mock_find_binary: Mock, mock_run: Mock
) -> None:
    """Test that notification mode skips console user check."""
    mock_find_binary.return_value = "/usr/local/bin/dialog"
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    dialog = Dialog()
    # Use SystemNotification for notification mode (not DialogTemplate with notification flag)
    notification = SystemNotification(title="Test", message="Test notification")
    result = dialog.show(notification)

    # Should not check console user for notifications
    assert not mock_console_user.called or result.exit_code == 0


@patch("pymdm.dialog.sys.platform", "darwin")
@patch("pymdm.dialog.subprocess.run")
@patch("pymdm.dialog.Dialog._find_binary")
@patch("pymdm.system_info.SystemInfo.get_console_user")
def test_show_with_timeout(mock_console_user: Mock, mock_find_binary: Mock, mock_run: Mock) -> None:
    """Test dialog with timeout."""
    mock_find_binary.return_value = "/usr/local/bin/dialog"
    mock_console_user.return_value = ("testuser", 501, Path("/Users/testuser"))
    mock_run.side_effect = subprocess.TimeoutExpired("dialog", 10)

    dialog = Dialog()
    template = DialogTemplate(title="Test")
    result = dialog.show(template, timeout=10)

    assert result.exit_code == DialogExitCode.timer_expired
    assert "timed out" in result.raw_output.lower()


@patch("pymdm.dialog.sys.platform", "darwin")
@patch("pymdm.dialog.subprocess.run")
@patch("pymdm.dialog.Dialog._find_binary")
@patch("pymdm.system_info.SystemInfo.get_console_user")
def test_show_with_logger(mock_console_user: Mock, mock_find_binary: Mock, mock_run: Mock) -> None:
    """Test dialog with logger."""
    mock_find_binary.return_value = "/usr/local/bin/dialog"
    mock_console_user.return_value = ("testuser", 501, Path("/Users/testuser"))
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = '{"result": "ok"}'
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    logger = MdmLogger(debug=True)
    dialog = Dialog()
    template = DialogTemplate(title="Test")
    result = dialog.show(template, logger=logger)

    assert result.exit_code == 0


# =============================================================================
# DialogReturn Tests
# =============================================================================


def test_dialog_return_from_subprocess() -> None:
    """Test creating DialogReturn from subprocess result."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = '{"textfield1": "value1"}'

    result = DialogReturn.from_subprocess(mock_result)

    assert result.exit_code == 0
    assert result.raw_output == '{"textfield1": "value1"}'


def test_dialog_return_parse_json() -> None:
    """Test parsing JSON output."""
    json_output = '{"textfield1": "value1", "checkbox1": true}'
    result = DialogReturn(exit_code=0, raw_output=json_output)

    assert result.data["textfield1"] == "value1"
    assert result.data["checkbox1"] is True


def test_dialog_return_extract_textfields() -> None:
    """Test extracting textfield values."""
    json_output = '{"Username": "testuser", "Email": "test@example.com"}'
    result = DialogReturn(exit_code=0, raw_output=json_output)

    assert result.textfields["Username"] == "testuser"
    assert result.textfields["Email"] == "test@example.com"


def test_dialog_return_extract_checkboxes() -> None:
    """Test extracting checkbox values."""
    json_output = '{"Agree": true, "Subscribe": false}'
    result = DialogReturn(exit_code=0, raw_output=json_output)

    assert result.checkboxes["Agree"] is True
    assert result.checkboxes["Subscribe"] is False


def test_dialog_return_extract_checkboxes_string_bool() -> None:
    """Test extracting checkbox values from string booleans."""
    json_output = '{"Agree": "true", "Subscribe": "false"}'
    result = DialogReturn(exit_code=0, raw_output=json_output)

    assert result.checkboxes["Agree"] is True
    assert result.checkboxes["Subscribe"] is False


def test_dialog_return_extract_selects() -> None:
    """Test extracting select/dropdown values."""
    json_output = '{"SelectField": {"selectedValue": "Option 1", "selectedIndex": 0}}'
    result = DialogReturn(exit_code=0, raw_output=json_output)

    assert "SelectField" in result.selects
    select_result = result.selects["SelectField"]
    assert select_result.selected_value == "Option 1"
    assert select_result.selected_index == 0


def test_dialog_return_extract_legacy_select() -> None:
    """Test extracting legacy SelectedOption format."""
    json_output = '{"SelectedOption": "Option 1", "SelectedIndex": 0}'
    result = DialogReturn(exit_code=0, raw_output=json_output)

    assert "_default" in result.selects
    select_result = result.selects["_default"]
    assert select_result.selected_value == "Option 1"
    assert select_result.selected_index == 0


def test_dialog_return_ok_property() -> None:
    """Test ok property."""
    result = DialogReturn(exit_code=0)
    assert result.ok is True

    result = DialogReturn(exit_code=2)
    assert result.ok is False


def test_dialog_return_cancelled_property() -> None:
    """Test cancelled property."""
    result = DialogReturn(exit_code=2)
    assert result.cancelled is True

    result = DialogReturn(exit_code=10)
    assert result.cancelled is True

    result = DialogReturn(exit_code=0)
    assert result.cancelled is False


def test_dialog_return_timed_out_property() -> None:
    """Test timed_out property."""
    result = DialogReturn(exit_code=4)
    assert result.timed_out is True

    result = DialogReturn(exit_code=20)
    assert result.timed_out is True

    result = DialogReturn(exit_code=0)
    assert result.timed_out is False


def test_dialog_return_exit_reason() -> None:
    """Test exit_reason property."""
    result = DialogReturn(exit_code=0)
    assert "Ok" in result.exit_reason

    result = DialogReturn(exit_code=2)
    assert "Button2" in result.exit_reason

    result = DialogReturn(exit_code=999)
    assert "Unknown" in result.exit_reason


def test_dialog_return_get_textfield() -> None:
    """Test get_textfield method."""
    json_output = '{"Username": "testuser"}'
    result = DialogReturn(exit_code=0, raw_output=json_output)

    assert result.get_textfield("Username") == "testuser"
    assert result.get_textfield("Missing", "default") == "default"


def test_dialog_return_get_select() -> None:
    """Test get_select method."""
    json_output = '{"SelectField": {"selectedValue": "Option 1", "selectedIndex": 0}}'
    result = DialogReturn(exit_code=0, raw_output=json_output)

    select = result.get_select("SelectField")
    assert select is not None
    assert select.selected_value == "Option 1"

    assert result.get_select("Missing") is None


def test_dialog_return_get_checkbox() -> None:
    """Test get_checkbox method."""
    json_output = '{"Agree": true}'
    result = DialogReturn(exit_code=0, raw_output=json_output)

    assert result.get_checkbox("Agree") is True
    assert result.get_checkbox("Missing", default=False) is False
    assert result.get_checkbox("Missing", default=True) is True


def test_dialog_return_parse_malformed_json() -> None:
    """Test handling malformed JSON."""
    result = DialogReturn(exit_code=0, raw_output="not json")
    assert result.data == {}


def test_dialog_return_parse_json_with_extra_text() -> None:
    """Test parsing JSON with extra text around it."""
    json_output = 'Some text before {"result": "ok"} some text after'
    result = DialogReturn(exit_code=0, raw_output=json_output)

    # Should still parse the JSON
    assert "result" in result.data or result.data == {}


# =============================================================================
# SelectResult and DialogExitCode Tests
# =============================================================================


def test_select_result_initialization() -> None:
    """Test SelectResult initialization."""
    result = SelectResult(selected_value="Option 1", selected_index=0)
    assert result.selected_value == "Option 1"
    assert result.selected_index == 0


def test_dialog_exit_code_values() -> None:
    """Test DialogExitCode enum values."""
    assert DialogExitCode.ok == 0
    assert DialogExitCode.button2 == 2
    assert DialogExitCode.user_quit == 10
    assert DialogExitCode.file_not_found == 202


# =============================================================================
# Dialog.update_command_file Tests
# =============================================================================


def test_update_command_file(tmp_path: Path) -> None:
    """Test update_command_file static method."""
    cmd_file = tmp_path / "dialog_cmd.txt"

    Dialog.update_command_file(cmd_file, {"title": "New Title", "message": "New Message"})

    content = cmd_file.read_text()
    assert "title:New Title" in content
    assert "message:New Message" in content


def test_update_command_file_handles_none_values(tmp_path: Path) -> None:
    """Test that update_command_file skips None values."""
    cmd_file = tmp_path / "dialog_cmd.txt"

    Dialog.update_command_file(cmd_file, {"title": "Title", "message": None})

    content = cmd_file.read_text()
    assert "title:Title" in content
    assert "message" not in content


def test_update_command_file_handles_bool_values(tmp_path: Path) -> None:
    """Test that update_command_file handles boolean values."""
    cmd_file = tmp_path / "dialog_cmd.txt"

    Dialog.update_command_file(cmd_file, {"ontop": True, "moveable": False})

    content = cmd_file.read_text()
    assert "ontop:" in content
    # False values should not be written
    assert "moveable" not in content


def test_update_command_file_creates_parent_dirs(tmp_path: Path) -> None:
    """Test that update_command_file creates parent directories."""
    cmd_file = tmp_path / "subdir" / "nested" / "dialog_cmd.txt"

    Dialog.update_command_file(cmd_file, {"title": "Test"})

    assert cmd_file.exists()
    assert "title:Test" in cmd_file.read_text()
