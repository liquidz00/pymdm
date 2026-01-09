import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass, field, fields
from enum import Enum, IntEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .logger import MdmLogger

# Shared temp directory accessible by all local users on macOS
_SHARED_TEMP_DIR = "/Users/Shared"

_ALIASES = {
    "help_message": "helpmessage",
    "help_image": "helpimage",
    "button_size": "buttonsize",
    "button_style": "buttonstyle",
    "icon_size": "iconsize",
    "icon_alpha": "iconalpha",
    "overlay_icon": "overlayicon",
    "banner_image": "bannerimage",
    "banner_title": "bannertitle",
    "banner_text": "bannertext",
    "button1_text": "button1text",
    "button1_action": "button1action",
    "button2_text": "button2text",
    "button2_action": "button2action",
    "info_button_text": "infobuttontext",
    "info_button_action": "infobuttonaction",
    "video_position": "videoposition",
    "quit_on_info": "quitoninfo",
    # swiftDialog uses singular forms for these
    "textfields": "textfield",
    "checkboxes": "checkbox",
    "radioitems": "radiobutton",
}


class DialogExitCode(IntEnum):
    """swiftDialog exit codes."""

    ok = 0
    button2 = 2
    info_button = 3
    timer_expired = 4
    quit_command = 5
    user_quit = 10
    timer_zero = 20
    auth_failed = 30
    image_not_found = 201
    file_not_found = 202
    invalid_color = 203


class Style(str, Enum):
    presentation = "presentation"
    mini = "mini"
    centered = "centered"
    alert = "alert"
    caution = "caution"
    warning = "warning"


class MessageAlignment(str, Enum):
    left = "left"
    center = "center"
    right = "right"


class MessagePosition(str, Enum):
    top = "top"
    center = "center"
    bottom = "bottom"


class ButtonStyle(str, Enum):
    center = "center"
    centre = "centre"
    stack = "stack"


class ButtonSize(str, Enum):
    mini = "mini"
    small = "small"
    regular = "regular"
    large = "large"


@dataclass
class TextField:
    """
    Configuration for a text field in swiftDialog.

    :param title: Title/label for the text field (displayed to user)
    :type title: str
    :param prompt: Prompt text shown inside the field, defaults to None
    :type prompt: str | None, optional
    :param value: Default value, defaults to None
    :type value: str | None, optional
    :param secure: Whether input should be masked (password field), defaults to False
    :type secure: bool, optional
    :param required: Whether field is required, defaults to False
    :type required: bool, optional
    :param regex: Validation regex pattern, defaults to None
    :type regex: str | None, optional
    :param regexerror: Error message to show when regex validation fails, defaults to None
    :type regexerror: str | None, optional
    """

    title: str
    prompt: str | None = None
    value: str | None = None
    secure: bool = False
    required: bool = False
    regex: str | None = None
    regexerror: str | None = None


@dataclass
class SelectItem:
    """
    Configuration for a select/dropdown in swiftDialog.

    Each SelectItem represents a single dropdown menu with a label and options.

    :param title: Label displayed above the dropdown
    :type title: str
    :param values: List of options to choose from
    :type values: list[str]
    :param default: Default selected value (must match one of the values), defaults to None
    :type default: str | None, optional
    """

    title: str
    values: list[str] = field(default_factory=list)
    default: str | None = None


@dataclass
class CheckboxItem:
    """
    Configuration for a checkbox item in swiftDialog.

    :param label: Label text for the checkbox
    :type label: str
    :param checked: Whether checkbox is checked by default, defaults to False
    :type checked: bool, optional
    :param disabled: Whether checkbox is disabled, defaults to False
    :type disabled: bool, optional
    :param icon: Icon to display next to checkbox, defaults to None
    :type icon: str | None, optional
    """

    label: str
    checked: bool = False
    disabled: bool = False
    icon: str | None = None


@dataclass
class DialogTemplate:
    """
    Template for configuring swiftDialog dialogs.

    This dataclass provides a comprehensive interface for defining dialog
    configurations including text fields, selects, checkboxes, timers, and more.
    Use the :class:`Dialog` class to display templates.

    :param title: Dialog title (required)
    :type title: str
    :param subtitle: Optional subtitle text
    :type subtitle: str | None, optional
    :param message: Main message content (supports markdown)
    :type message: str | None, optional

    :Example:

        >>> template = DialogTemplate(
        ...     title="Welcome",
        ...     message="Please enter your details",
        ...     textfields=[TextField(title="Username", required=True)],
        ... )
        >>> dialog = Dialog()
        >>> result = dialog.show(template)
    """

    # Basic content
    title: str = ""
    subtitle: str | None = None
    message: str | None = None

    # Layout/style
    style: Style | None = None
    alignment: MessageAlignment | None = None
    position: MessagePosition | None = None

    # Help opts
    help_message: str | None = None
    help_image: str | Path | None = None

    # Icon & banner
    icon: str | Path | None = None
    icon_size: int | None = None
    icon_alpha: int | None = None
    overlay_icon: str | Path | None = None
    banner_image: str | Path | None = None
    banner_title: str | None = None
    banner_text: str | None = None

    # Buttons
    button1_text: str | None = None  # --button1text
    button1_action: str | None = None  # --button1action
    button2_text: str | None = None  # --button2text
    button2_action: str | None = None  # --button2action
    info_button_text: str | None = None  # --infobuttontext
    info_button_action: str | None = None  # --infobuttonaction
    button_style: ButtonStyle | None = None  # --buttonstyle
    button_size: ButtonSize | None = None  # --buttonsize

    # Useful toggles
    small: bool = False
    big: bool = False
    fullscreen: bool = False
    ontop: bool = False
    moveable: bool = False

    # Window sizing
    width: int | None = None
    height: int | None = None

    # Text fields (swiftDialog uses singular "textfield")
    textfields: list[TextField] = field(default_factory=list)

    # Select lists/dropdowns (list of SelectItem with title, value, default)
    selectitems: list[SelectItem] = field(default_factory=list)

    # Radio buttons (swiftDialog uses "radiobutton", list of SelectItem)
    radioitems: list[SelectItem] = field(default_factory=list)

    # Checkboxes (swiftDialog uses singular "checkbox", list of CheckboxItem)
    checkboxes: list[CheckboxItem] = field(default_factory=list)

    # Infobox for displaying additional information
    infobox: str | None = None

    # Timer and progress
    timer: int | None = None  # Timer in seconds
    timerbar: bool = False  # Show progress bar with timer
    progress: int | None = None  # Progress percentage (0-100)

    # Command file for dynamic updates
    commandfile: str | Path | None = None

    # JSON output flag
    json: bool = True  # Default to JSON output for structured parsing

    # Additional options
    webcontent: str | None = None  # URL or HTML content
    video: str | Path | None = None  # Video file path
    video_position: str | None = None  # "top" or "bottom"
    quitkey: str | None = None  # Custom quit key combination
    quit_on_info: bool = False  # Quit when info button is clicked

    def to_jsonstring(self) -> str:
        """
        Convert DialogTemplate to JSON string for swiftDialog.

        :return: JSON string representation
        :rtype: str
        """
        data = {}
        for f in fields(self):
            val = getattr(self, f.name)
            # Skip None values and empty lists
            if val is None:
                continue
            if isinstance(val, list) and len(val) == 0:
                continue
            # Skip False boolean values for optional flags (but include True)
            if isinstance(val, bool) and not val:
                continue

            key = _ALIASES.get(f.name, f.name)

            # Handle Path objects
            if isinstance(val, Path):
                val = str(val)
            # Handle Enum values
            elif isinstance(val, Enum):
                val = val.value
            # Handle TextField objects - convert to swiftDialog format
            elif isinstance(val, list) and len(val) > 0 and isinstance(val[0], TextField):
                textfield_dicts = []
                for tf in val:
                    tf_dict: dict[str, Any] = {"title": tf.title}
                    if tf.prompt:
                        tf_dict["prompt"] = tf.prompt
                    if tf.value:
                        tf_dict["value"] = tf.value
                    if tf.secure:
                        tf_dict["secure"] = tf.secure
                    if tf.required:
                        tf_dict["required"] = tf.required
                    if tf.regex:
                        tf_dict["regex"] = tf.regex
                    if tf.regexerror:
                        tf_dict["regexerror"] = tf.regexerror
                    textfield_dicts.append(tf_dict)
                val = textfield_dicts
            # Handle SelectItem objects (for selectitems and radioitems)
            elif isinstance(val, list) and len(val) > 0 and isinstance(val[0], SelectItem):
                select_dicts = []
                for item in val:
                    item_dict: dict[str, Any] = {"title": item.title}
                    if item.values:
                        item_dict["values"] = item.values
                    if item.default:
                        item_dict["default"] = item.default
                    select_dicts.append(item_dict)
                val = select_dicts
            # Handle CheckboxItem objects
            elif isinstance(val, list) and len(val) > 0 and isinstance(val[0], CheckboxItem):
                checkbox_dicts = []
                for cb in val:
                    cb_dict: dict[str, Any] = {"label": cb.label}
                    if cb.checked:
                        cb_dict["checked"] = cb.checked
                    if cb.disabled:
                        cb_dict["disabled"] = cb.disabled
                    if cb.icon:
                        cb_dict["icon"] = cb.icon
                    checkbox_dicts.append(cb_dict)
                val = checkbox_dicts

            data[key] = val
        return json.dumps(data)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert DialogTemplate to a dictionary.

        :return: Dictionary representation of the template
        :rtype: dict[str, Any]

        :Example:

            >>> template = DialogTemplate(title="Test", message="Hello")
            >>> d = template.to_dict()
            >>> d["title"]
            'Test'
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DialogTemplate":
        """
        Create DialogTemplate from a dictionary.

        :param data: Dictionary with dialog configuration options
        :type data: dict[str, Any]
        :return: DialogTemplate instance
        :rtype: DialogTemplate

        :Example:

            >>> data = {"title": "Test", "message": "Hello", "width": 500}
            >>> template = DialogTemplate.from_dict(data)
            >>> template.title
            'Test'
        """
        reverse_aliases = {v: k for k, v in _ALIASES.items()}
        normalized = {reverse_aliases.get(k, k): v for k, v in data.items()}
        return cls(**normalized)


@dataclass
class SelectResult:
    """Parsed result from a dropdown/select field."""

    selected_value: str
    selected_index: int


@dataclass
class SystemNotification:
    """
    Configuration for swiftDialog system notifications (toast).

    Unlike full dialogs, notifications only support a limited set of properties.
    All other DialogTemplate properties are ignored by swiftDialog when
    `--notification` is used.

    Docs: https://github.com/swiftDialog/swiftDialog/wiki/Notifications
    """

    title: str
    message: str | None = None
    subtitle: str | None = None
    icon: str | Path | None = None

    button1_text: str | None = None
    button1_action: str | None = None
    button2_text: str | None = None
    button2_action: str | None = None

    def to_jsonstring(self) -> str:
        """Convert to JSON string for swiftDialog."""
        data: dict[str, Any] = {"title": self.title}
        if self.message:
            data["message"] = self.message
        if self.subtitle:
            data["subtitle"] = self.subtitle
        if self.icon:
            data["icon"] = str(self.icon) if isinstance(self.icon, Path) else self.icon
        if self.button1_text:
            data["button1text"] = self.button1_text
        if self.button1_action:
            data["button1action"] = self.button1_action
        if self.button2_text:
            data["button2text"] = self.button2_text
        if self.button2_action:
            data["button2action"] = self.button2_action
        return json.dumps(data)


@dataclass
class DialogReturn:
    """
    Structured result from a swiftDialog invocation.

    Captures:
      - exit_code: The process return code (see DialogExitCode)
      - raw_output: The raw stdout string
      - data: Parsed JSON dict when --json flag was used
      - textfields: Dict of textfield label -> user input
      - selects: Dict of select title -> SelectResult
      - checkboxes: Dict of checkbox label -> bool
    """

    exit_code: int
    raw_output: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    textfields: dict[str, str] = field(default_factory=dict)
    selects: dict[str, SelectResult] = field(default_factory=dict)
    checkboxes: dict[str, bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Parse raw_output if it looks like JSON."""
        if self.raw_output and not self.data:
            self._try_parse_json()
        if self.data:
            self._extract_fields()

    def _try_parse_json(self) -> None:
        """
        Attempt to parse raw_output as JSON.

        Handles various JSON formats that swiftDialog might return.
        """
        if not self.raw_output:
            return

        stripped = self.raw_output.strip()
        if not stripped:
            return

        # Try to parse as JSON
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                self.data = json.loads(stripped)
            except json.JSONDecodeError:
                # Try to extract JSON from mixed content
                # Sometimes swiftDialog might output other text before/after JSON
                json_start = stripped.find("{")
                json_end = stripped.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    try:
                        json_str = stripped[json_start:json_end]
                        self.data = json.loads(json_str)
                    except (json.JSONDecodeError, ValueError):
                        # If still fails, leave data empty
                        pass

    def _extract_fields(self) -> None:
        """
        Extract textfields, selects, and checkboxes from parsed data.

        Handles various output formats from swiftDialog.
        """
        if not self.data:
            return

        for key, val in self.data.items():
            # Skip None values
            if val is None:
                continue

            # Handle select/dropdown results
            # Format: {"SelectField": {"selectedValue": "option", "selectedIndex": 0}}
            if isinstance(val, dict):
                if "selectedValue" in val:
                    try:
                        self.selects[key] = SelectResult(
                            selected_value=str(val["selectedValue"]),
                            selected_index=int(val.get("selectedIndex", -1)),
                        )
                    except (ValueError, TypeError, KeyError):
                        # Skip invalid select data
                        continue
                else:
                    # Might be a nested structure, skip for now
                    continue

            # Handle legacy SelectedOption/SelectedIndex format
            elif key == "SelectedOption":
                try:
                    idx = int(self.data.get("SelectedIndex", -1))
                    self.selects["_default"] = SelectResult(
                        selected_value=str(val),
                        selected_index=idx,
                    )
                except (ValueError, TypeError):
                    # Skip invalid data
                    pass

            # Skip SelectedIndex as it's handled with SelectedOption
            elif key == "SelectedIndex":
                continue

            # Handle boolean checkboxes
            elif isinstance(val, bool):
                self.checkboxes[key] = val

            # Handle string boolean values
            elif isinstance(val, str):
                val_lower = val.lower().strip()
                if val_lower in ("true", "false"):
                    self.checkboxes[key] = val_lower == "true"
                else:
                    # Assume it's a textfield value
                    # Only add if it's not empty or if it's a known textfield pattern
                    if val or key.lower().endswith(("field", "input", "text")):
                        self.textfields[key] = val

            # Handle numeric values (might be from progress bars or other fields)
            elif isinstance(val, (int, float)):
                # Don't automatically add to textfields, but could be useful
                # Skip for now to avoid polluting textfields
                pass

    @property
    def ok(self) -> bool:
        """True if user clicked Ok/Button1."""
        return self.exit_code == DialogExitCode.ok

    @property
    def cancelled(self) -> bool:
        """True if user clicked Cancel/Button2 or quit."""
        return self.exit_code in (
            DialogExitCode.button2,
            DialogExitCode.user_quit,
        )

    @property
    def timed_out(self) -> bool:
        """True if dialog closed due to timer expiration."""
        return self.exit_code in (
            DialogExitCode.timer_expired,
            DialogExitCode.timer_zero,
        )

    @property
    def exit_reason(self) -> str:
        """Human-readable exit reason."""
        try:
            return DialogExitCode(self.exit_code).name.replace("_", " ").title()
        except ValueError:
            return f"Unknown ({self.exit_code})"

    def get_textfield(self, label: str, default: str = "") -> str:
        """Get a textfield value by label."""
        return self.textfields.get(label, default)

    def get_select(self, title: str) -> SelectResult | None:
        """Get a select result by title."""
        return self.selects.get(title)

    def get_checkbox(self, label: str, default: bool = False) -> bool:
        """Get a checkbox value by label."""
        return self.checkboxes.get(label, default)

    @classmethod
    def from_subprocess(cls, result: subprocess.CompletedProcess) -> "DialogReturn":
        """Create from a subprocess.CompletedProcess result."""
        return cls(
            exit_code=result.returncode,
            raw_output=result.stdout or "",
        )


class Dialog:
    """
    Executor class for displaying swiftDialog dialogs.

    This class handles binary discovery, command building, subprocess execution,
    and temp file management for displaying :class:`DialogTemplate` configurations.

    By default, passes JSON configuration via --jsonstring (in-memory) to avoid
    file permission issues when running as root via MDM. When use_temp_file=True,
    creates a world-readable temp file for compatibility with all users.

    :param binary_path: Path to swiftDialog binary, or None to auto-discover
    :type binary_path: str | None, optional
    :param temp_dir: Directory for temp file creation. Defaults to /Users/Shared
        for multi-user accessibility. Only used when use_temp_file=True
    :type temp_dir: str | Path, optional
    :param use_temp_file: If True, write JSON config to a temp file instead of
        passing as string. The temp file is created with world-readable
        permissions (0o644) for MDM compatibility. Defaults to False
    :type use_temp_file: bool, optional

    :Example:

        >>> dialog = Dialog()
        >>> template = DialogTemplate(title="Hello", message="World")
        >>> result = dialog.show(template)
        >>> if result.ok:
        ...     print("User clicked OK")
    """

    def __init__(
        self,
        binary_path: str | None = None,
        temp_dir: str | Path = _SHARED_TEMP_DIR,
        use_temp_file: bool = False,
    ) -> None:
        """
        Initialize the Dialog executor.

        :param binary_path: Path to swiftDialog binary, or None to auto-discover
        :type binary_path: str | None, optional
        :param temp_dir: Directory for temp file creation, defaults to /Users/Shared
        :type temp_dir: str | Path, optional
        :param use_temp_file: If True, use temp files instead of --jsonstring, defaults to False
        :type use_temp_file: bool, optional
        """
        self.binary_path = binary_path
        self.temp_dir = Path(temp_dir) if isinstance(temp_dir, str) else temp_dir
        self.use_temp_file = use_temp_file

    def _find_binary(self) -> str | None:
        """
        Find swiftDialog binary in standard locations.

        If a binary_path was provided at initialization, returns that path
        if the file exists. Otherwise, checks standard installation locations.

        :return: Path to dialog binary or None if not found
        :rtype: str | None
        """
        # Use configured path if provided
        if self.binary_path:
            if Path(self.binary_path).exists():
                return self.binary_path
            return None

        # Check standard installation location
        standard_path = "/usr/local/bin/dialog"
        if Path(standard_path).exists():
            return standard_path

        # Check PATH
        dialog_path = shutil.which("dialog")
        if dialog_path:
            return dialog_path

        return None

    def _build_temp_file(self, json_config_str: str) -> Path:
        """
        Create a world-readable temp file with JSON configuration.

        :param json_config_str: JSON string to write to temp file
        :type json_config_str: str
        :return: Path to created temp file
        :rtype: Path
        """
        # Use shared temp directory for multi-user accessibility
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Create temporary file for JSON configuration
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
            encoding="utf-8",
            dir=str(self.temp_dir),
        ) as f:
            f.write(json_config_str)
            json_file = Path(f.name)

        # Set world-readable permissions so swiftDialog (running as logged-in user)
        # can read the file even when this script runs as root via MDM
        os.chmod(json_file, 0o644)
        return json_file

    def _build_command_args(
        self,
        dialog_path: str,
        json_data: dict | Path | None = None,
        system_notification: bool = False,
    ) -> list[str]:
        """
        Build command-line arguments for swiftDialog.

        Uses JSON input for configuration. Supports both in-memory JSON strings
        (--jsonstring) and JSON files (--jsonfile) for flexibility.

        :param dialog_path: Path to swiftDialog binary
        :type dialog_path: str
        :param json_data: JSON dict (uses --jsonstring) or Path to JSON file
            (uses --jsonfile), defaults to None
        :type json_data: dict | Path | None, optional
        :param system_notification: If True, adds `--notification` argument to args
        :type system_notification: bool
        :return: List of command arguments
        :rtype: list[str]
        """
        args = [dialog_path]

        if system_notification:
            args.extend(["--notification"])

        if isinstance(json_data, dict):
            args.extend(["--jsonstring", json.dumps(json_data)])
        elif isinstance(json_data, Path):
            args.extend(["--jsonfile", str(json_data)])

        # Always request JSON output for structured parsing
        args.append("--json")

        return args

    def show(
        self,
        template: DialogTemplate | SystemNotification,
        logger: "MdmLogger | None" = None,
        timeout: int | None = None,
        check_console_user: bool = True,
    ) -> DialogReturn:
        """
        Display the dialog using swiftDialog.

        :param template: DialogTemplate or SystemNotification with dialog configuration
        :type template: DialogTemplate | SystemNotification
        :param logger: Optional MdmLogger instance for logging, defaults to None
        :type logger: MdmLogger | None, optional
        :param timeout: Timeout in seconds for dialog execution, defaults to None
        :type timeout: int | None, optional
        :param check_console_user: Whether to check for console user before
            showing dialog, defaults to True
        :type check_console_user: bool, optional
        :return: DialogReturn instance with results
        :rtype: DialogReturn
        """
        # Import here to avoid circular imports
        from .system_info import SystemInfo

        is_notification = isinstance(template, SystemNotification)

        # Find dialog binary
        dialog_path = self._find_binary()
        if not dialog_path:
            error_msg = (
                "swiftDialog not found. Please install swiftDialog to use dialog functionality."
            )
            if logger:
                logger.error(error_msg)
            return DialogReturn(
                exit_code=DialogExitCode.file_not_found,
                raw_output=error_msg,
            )

        # Check for console user if needed (for GUI dialogs)
        if check_console_user and not is_notification:
            console_user = SystemInfo.get_console_user()
            if not console_user:
                error_msg = "No console user found. Cannot display dialog."
                if logger:
                    logger.warn(error_msg)
                return DialogReturn(
                    exit_code=DialogExitCode.user_quit,
                    raw_output=error_msg,
                )

        # Validate file paths
        if is_notification:
            file_paths = [template.icon] if template.icon else []
        else:
            file_paths = [
                template.icon,
                template.help_image,
                template.overlay_icon,
                template.banner_image,
                template.video,
                template.commandfile,
            ]
        for file_path in file_paths:
            if file_path:
                path_obj = Path(file_path)
                if not path_obj.is_absolute() or not path_obj.exists():
                    if logger:
                        logger.warn(f"File path may not exist: {file_path}")

        # Generate JSON configuration
        json_config_str = template.to_jsonstring()
        json_config = json.loads(json_config_str)

        # Temp files only make sense for complex DialogTemplates, not simple notifications
        use_temp = self.use_temp_file and not is_notification

        json_file: Path | None = None
        try:
            if use_temp:
                json_file = self._build_temp_file(json_config_str)

                # Build command arguments with file path
                cmd_args = self._build_command_args(dialog_path, json_data=json_file)

                if logger:
                    logger.debug(f"Created temp JSON file: {json_file} with permissions 0644")
            else:
                # Default: pass JSON as string (no temp file, no permission issues)
                cmd_args = self._build_command_args(
                    dialog_path, json_data=json_config, system_notification=is_notification
                )

            # Execute dialog using subprocess.run to get full CompletedProcess object
            if logger:
                logger.debug(f"Executing swiftDialog: {' '.join(cmd_args)}")
                logger.debug(f"JSON config: {json_config_str}")

            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if logger:
                if result.returncode != 0:
                    logger.debug(f"swiftDialog exited with code {result.returncode}")
                if result.stderr:
                    logger.debug(f"swiftDialog stderr: {result.stderr}")

            return DialogReturn.from_subprocess(result)

        except subprocess.TimeoutExpired:
            error_msg = f"Dialog execution timed out after {timeout} seconds"
            if logger:
                logger.error(error_msg)
            return DialogReturn(
                exit_code=DialogExitCode.timer_expired,
                raw_output=error_msg,
            )
        except Exception as e:
            error_msg = f"Error executing swiftDialog: {str(e)}"
            if logger:
                logger.error(error_msg)
            return DialogReturn(
                exit_code=DialogExitCode.file_not_found,
                raw_output=error_msg,
            )
        finally:
            # Clean up temporary JSON file if created
            if json_file and json_file.exists():
                try:
                    json_file.unlink()
                except Exception:
                    pass  # Best effort cleanup

    @staticmethod
    def update_command_file(command_file: str | Path, updates: dict[str, Any]) -> None:
        """
        Update dialog content dynamically via command file.

        This method writes update commands to the command file specified
        in the dialog template, allowing real-time updates to dialog content.

        :param command_file: Path to the command file
        :type command_file: str | Path
        :param updates: Dictionary of updates (e.g., {"title": "New Title", "message": "New Message"})
        :type updates: dict[str, Any]
        :raises IOError: If the command file cannot be written
        """
        cmd_file = Path(command_file)
        cmd_file.parent.mkdir(parents=True, exist_ok=True)

        # swiftDialog command file format: one command per line
        # Format: command:value
        lines = []
        for key, value in updates.items():
            if value is None:
                continue
            # Convert key to swiftDialog command format
            cmd_key = key.replace("_", "")
            if isinstance(value, bool):
                if value:
                    lines.append(f"{cmd_key}:")
            elif isinstance(value, Path):
                lines.append(f"{cmd_key}:{value}")
            else:
                lines.append(f"{cmd_key}:{value}")

        try:
            with open(cmd_file, "w") as f:
                f.write("\n".join(lines) + "\n")
        except IOError as e:
            raise IOError(f"Failed to write command file {command_file}: {e}") from e
