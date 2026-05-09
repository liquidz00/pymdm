import pytest

from pymdm import MdmLogger


def test_logger_initialization():
    """Test basic logger initialization."""
    logger = MdmLogger()
    assert logger.debug_enabled is False
    assert logger.quiet is False
    assert logger.output_path is None


def test_logger_with_output_path(temp_log_file):
    """Test logger creates log file."""
    logger = MdmLogger(output_path=temp_log_file)
    logger.info("Test message")

    assert temp_log_file.exists()
    content = temp_log_file.read_text()
    assert "Test message" in content
    assert "[INFO]" in content


def test_logger_debug_mode(temp_log_file, capsys):
    """Test debug messages only show when debug=True."""
    # Debug disabled
    logger = MdmLogger(debug=False, output_path=temp_log_file)
    logger.debug("Debug message")

    captured = capsys.readouterr()
    assert "Debug message" not in captured.out

    # Debug enabled
    logger = MdmLogger(debug=True, output_path=temp_log_file)
    logger.debug("Debug message")

    captured = capsys.readouterr()
    assert "Debug message" in captured.out


def test_logger_quiet_mode(capsys):
    """Test quiet mode suppresses INFO messages."""
    logger = MdmLogger(quiet=True)
    logger.info("Info message")
    logger.warn("Warning message")

    captured = capsys.readouterr()
    assert "Info message" not in captured.out
    assert "Warning message" in captured.out


def test_logger_log_levels(capsys):
    """Test all log level convenience methods."""
    logger = MdmLogger(debug=True)

    logger.info("Info message")
    logger.warn("Warning message")
    logger.error("Error message")
    logger.debug("Debug message")

    captured = capsys.readouterr()
    assert "[INFO]" in captured.out
    assert "[WARN]" in captured.out
    assert "[DEBUG]" in captured.out
    assert "[ERROR]" in captured.err


def test_logger_log_rotation(temp_dir):
    """Test log file rotation when size limit exceeded."""
    log_file = temp_dir / "rotate.log"
    # Use a small threshold so we can verify rotation deterministically
    logger = MdmLogger(output_path=log_file, max_bytes=200)

    logger.info("x" * 300)  # exceeds 200 bytes
    logger.info("After rotation")

    backup = temp_dir / "rotate.log.old"
    assert backup.exists()
    # The post-rotation log file holds only the second message
    assert "After rotation" in log_file.read_text()
    assert "x" * 300 in backup.read_text()


def test_logger_no_rotation_below_threshold(temp_dir):
    """Log files smaller than max_bytes are not rotated."""
    log_file = temp_dir / "small.log"
    logger = MdmLogger(output_path=log_file, max_bytes=10_000)

    logger.info("hello")
    logger.info("world")

    backup = temp_dir / "small.log.old"
    assert not backup.exists()
    content = log_file.read_text()
    assert "hello" in content
    assert "world" in content


def test_logger_startup_info(capsys):
    """Test log_startup method."""
    logger = MdmLogger()
    logger.log_startup("test_script", version="1.0.0")

    captured = capsys.readouterr()
    assert "test_script" in captured.out
    assert "1.0.0" in captured.out
    assert "Python:" in captured.out
    # OS version label is platform-dependent
    assert "Version:" in captured.out


def test_logger_get_log_path(temp_log_file):
    """Test get_log_path returns correct path."""
    logger = MdmLogger(output_path=temp_log_file)
    assert logger.get_log_path() == temp_log_file


def test_logger_flush():
    """Test flush method doesn't raise errors."""
    logger = MdmLogger()
    logger.flush()  # Should not raise


def test_logger_log_exception(capsys):
    """Test exception logging with traceback."""
    logger = MdmLogger()

    try:
        raise ValueError("Test error")
    except ValueError as e:
        logger.log_exception("Something went wrong", e)

    captured = capsys.readouterr()
    assert "Something went wrong" in captured.err
    assert "ValueError: Test error" in captured.err
    assert "Traceback" in captured.err


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("error", {"message": "fatal", "exit_code": 1}),
        ("warn", {"message": "bad", "exit_code": 2}),
        ("debug", {"message": "dbg", "exit_code": 3}),
    ],
)
def test_logger_exit_code_forwarding(method, kwargs):
    """Test that error/warn/debug forward exit_code to sys.exit."""
    logger = MdmLogger(debug=True)
    with pytest.raises(SystemExit) as exc_info:
        getattr(logger, method)(**kwargs)
    assert exc_info.value.code == kwargs["exit_code"]


def test_logger_log_exception_exit_code():
    """Test that log_exception forwards exit_code to sys.exit."""
    logger = MdmLogger()
    with pytest.raises(SystemExit) as exc_info:
        logger.log_exception("boom", ValueError("err"), exit_code=4)
    assert exc_info.value.code == 4


@pytest.mark.parametrize(
    "raw,expected",
    [
        # .sh suffix — bug repro: rstrip(".sh") on "bash.sh" yielded "ba"
        ("bash.sh", "Bash (shell)"),
        ("setup.sh", "Setup (shell)"),
        ("ssh-config.sh", "Ssh Config (shell)"),
        # .py suffix — bug repro: rstrip(".py") on "setup.py" yielded "setu"
        ("setup.py", "Setup (python)"),
        ("clear_downloads.py", "Clear Downloads (python)"),
        ("zoom_camera_allowed.py", "Zoom Camera Allowed (python)"),
        # No suffix — passthrough
        ("custom_script", "custom_script"),
        # Edge: name ends with chars from the suffix set but is not the suffix
        ("happy", "happy"),
    ],
)
def test_format_script_name(raw, expected):
    """_format_script_name uses removesuffix, not rstrip."""
    assert MdmLogger._format_script_name(raw) == expected
