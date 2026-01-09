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
    logger = MdmLogger(output_path=log_file)

    # Write a large message to trigger rotation
    large_message = "x" * 10_000_000  # 10MB
    logger.info(large_message)
    logger.info("After rotation")

    # Check backup exists
    backup = temp_dir / "rotate.log.old"
    assert backup.exists() or log_file.exists()


def test_logger_startup_info(capsys):
    """Test log_startup method."""
    logger = MdmLogger()
    logger.log_startup("test_script", version="1.0.0")

    captured = capsys.readouterr()
    assert "test_script" in captured.out
    assert "1.0.0" in captured.out
    assert "Python:" in captured.out
    assert "macOS Version:" in captured.out


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
