from pathlib import Path
from unittest.mock import Mock, patch

from pymdm import MdmLogger, WebhookSender


def test_webhook_sender_initialization(mock_logger):
    """Test WebhookSender initialization."""
    sender = WebhookSender(url="https://example.com", logger=mock_logger)
    assert sender.url == "https://example.com"
    assert sender.logger == mock_logger
    assert sender.logfile is None
    assert sender.headers is None


def test_webhook_sender_with_headers(mock_logger):
    """Test WebhookSender initialization with custom headers."""
    headers = {"Authorization": "Bearer test-token"}
    sender = WebhookSender(url="https://example.com", logger=mock_logger, headers=headers)
    assert sender.headers == headers


def test_webhook_sender_with_logfile(mock_logger, temp_log_file):
    """Test WebhookSender with log file."""
    temp_log_file.touch()
    sender = WebhookSender(url="https://example.com", logger=mock_logger, logfile=temp_log_file)
    assert sender.logfile == temp_log_file


def test_webhook_sender_uses_logger_path(temp_log_file):
    """Test WebhookSender uses logger's output_path if not provided."""
    logger = MdmLogger(output_path=temp_log_file)
    sender = WebhookSender(url="https://example.com", logger=logger)
    assert sender.logfile == temp_log_file


@patch("requests.post")
def test_webhook_send_success(mock_post, mock_logger, temp_log_file):
    """Test successful webhook send."""
    temp_log_file.write_text("Test log content")

    # Mock successful response
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    sender = WebhookSender(url="https://example.com", logger=mock_logger, logfile=temp_log_file)

    result = sender.send(hostname="test-host", serial="ABC123")

    assert result is True
    assert mock_post.called

    # Check that metadata was included in the JSON body
    call_kwargs = mock_post.call_args.kwargs
    json_data = call_kwargs["json"]
    assert json_data["hostname"] == "test-host"
    assert json_data["serial"] == "ABC123"
    assert "timestamp" in json_data


@patch("requests.post")
def test_webhook_send_failure(mock_post, mock_logger, temp_log_file):
    """Test failed webhook send."""
    temp_log_file.write_text("Test log content")

    # Mock failed response
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_post.return_value = mock_response

    sender = WebhookSender(url="https://example.com", logger=mock_logger, logfile=temp_log_file)

    result = sender.send()
    assert result is False


def test_webhook_send_missing_logfile(mock_logger):
    """Test webhook send with missing log file."""
    sender = WebhookSender(
        url="https://example.com", logger=mock_logger, logfile=Path("/nonexistent/file.log")
    )

    result = sender.send()
    assert result is False


@patch("requests.post")
def test_webhook_send_with_headers(mock_post, mock_logger, temp_log_file):
    """Test that custom headers are passed through to requests.post."""
    temp_log_file.write_text("Test log content")

    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    headers = {"Authorization": "Bearer test-token", "X-Custom": "value"}
    sender = WebhookSender(
        url="https://example.com", logger=mock_logger, logfile=temp_log_file, headers=headers
    )

    result = sender.send(hostname="test-host")

    assert result is True
    assert mock_post.call_args.kwargs["headers"] is headers


@patch("requests.post")
def test_webhook_send_logfile_with_headers(mock_post, mock_logger, temp_log_file):
    """Test that custom headers are passed through on send_logfile."""
    temp_log_file.write_text("Test log content")

    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    headers = {"Authorization": "Bearer test-token"}
    sender = WebhookSender(
        url="https://example.com", logger=mock_logger, logfile=temp_log_file, headers=headers
    )

    result = sender.send_logfile(hostname="test-host")

    assert result is True
    assert mock_post.call_args.kwargs["headers"] is headers
