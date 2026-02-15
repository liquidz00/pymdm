from unittest.mock import Mock, patch

import pytest

from pymdm import CommandRunner, MdmLogger


def test_command_runner_initialization():
    """Test CommandRunner initialization."""
    runner = CommandRunner()
    assert runner.logger is None

    logger = MdmLogger()
    runner = CommandRunner(logger=logger)
    assert runner.logger == logger


@patch("subprocess.run")
def test_run_with_list(mock_run):
    """Test running command with list (no shell)."""
    mock_result = Mock()
    mock_result.stdout = "output\n"
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    runner = CommandRunner()
    result = runner.run(["/bin/echo", "hello"])

    assert result == "output"
    assert mock_run.called
    assert mock_run.call_args.kwargs["shell"] is False


@patch("subprocess.run")
def test_run_with_string(mock_run):
    """Test running command with string (shell=True)."""
    mock_result = Mock()
    mock_result.stdout = "output\n"
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    runner = CommandRunner()
    result = runner.run("echo hello | grep hello")

    assert result == "output"
    assert mock_run.called
    assert mock_run.call_args.kwargs["shell"] is True


@patch("subprocess.run")
def test_run_with_timeout(mock_run):
    """Test command timeout handling."""
    import subprocess

    mock_run.side_effect = subprocess.TimeoutExpired("cmd", 10)

    runner = CommandRunner()

    with pytest.raises(subprocess.TimeoutExpired):
        runner.run(["/bin/sleep", "100"], timeout=1)


@patch("subprocess.run")
def test_run_with_error(mock_run):
    """Test command error handling."""
    import subprocess

    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="error")

    runner = CommandRunner()

    with pytest.raises(subprocess.CalledProcessError):
        runner.run(["/bin/false"])


def test_sanitize_command_bearer_token():
    """Test Bearer token sanitization."""
    cmd = ["curl", "-H", "Authorization: Bearer sk-abc123"]
    sanitized = CommandRunner._sanitize_command(cmd)

    assert "Bearer <REDACTED>" in sanitized
    assert "sk-abc123" not in sanitized


def test_sanitize_command_password():
    """Test password sanitization."""
    cmd = ["curl", "-u", "user:password=secret123"]
    sanitized = CommandRunner._sanitize_command(cmd)

    assert "password=<REDACTED>" in sanitized
    assert "secret123" not in sanitized


def test_sanitize_command_string():
    """Test sanitization works with strings too."""
    cmd = "curl -H 'Authorization: Bearer token123' https://api.example.com"
    sanitized = CommandRunner._sanitize_command(cmd)

    assert "Bearer <REDACTED>" in sanitized
    assert "token123" not in sanitized


@patch("subprocess.run")
def test_run_with_env(mock_run):
    """Test running command with custom environment."""
    mock_result = Mock()
    mock_result.stdout = "output\n"
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    env = {"PATH": "/usr/bin:/bin", "CUSTOM_VAR": "value"}
    runner = CommandRunner()
    runner.run(["/usr/bin/echo", "hello"], env=env)

    assert mock_run.call_args.kwargs["env"] is env


@patch("subprocess.run")
def test_run_without_env(mock_run):
    """Test that env defaults to None (inherit parent environment)."""
    mock_result = Mock()
    mock_result.stdout = "output\n"
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    runner = CommandRunner()
    runner.run(["/usr/bin/echo", "hello"])

    assert mock_run.call_args.kwargs["env"] is None


@patch("subprocess.run")
def test_run_with_logger(mock_run, capsys):
    """Test command runner with logger."""
    mock_result = Mock()
    mock_result.stdout = "output\n"
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    logger = MdmLogger(debug=True)
    runner = CommandRunner(logger=logger)
    runner.run(["/bin/echo", "hello"])

    captured = capsys.readouterr()
    assert "Running:" in captured.out
