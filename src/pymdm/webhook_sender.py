from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .logger import MdmLogger

if TYPE_CHECKING:
    import requests as requests_module  # noqa: F401


_REQUESTS_MISSING_MESSAGE = (
    "WebhookSender requires the 'requests' library. "
    "Install it with one of:\n"
    "  pip install pymdm[requests]   # standard installs\n"
    "  pip install pymdm[managed]    # MacAdmins managed_python3 (requests already bundled)\n"
    "If you're running under managed_python3 and still see this error, your interpreter "
    "may not be the managed one — confirm with `which python3`."
)


def _import_requests():
    """Lazy-import the ``requests`` library with a helpful error if missing.

    ``requests`` is intentionally an optional dependency: MacAdmins
    ``managed_python3`` ships with it bundled, so requiring it as a hard
    dependency would be redundant for the primary target. Plain pip users
    should install via the ``[requests]`` extra.
    """
    try:
        import requests
    except ImportError as e:  # pragma: no cover - exercised only without requests
        raise ImportError(_REQUESTS_MISSING_MESSAGE) from e
    return requests


class WebhookSender:
    """Helper class for sending log files to Tray webhooks."""

    def __init__(
        self,
        url: str,
        logger: MdmLogger,
        logfile: Path | str | None = None,
        headers: dict[str, str] | None = None,
    ):
        """
        Initialize WebhookSender.

        :param url: The Tray webhook URL.
        :type url: str
        :param logger: MdmLogger instance for logging webhook operations
        :type logger: MdmLogger
        :param logfile: Path to log file to send, defaults to None
        :type logfile: Path | str | None, optional
        :param headers: Optional HTTP headers to include in requests (e.g., for authentication)
        :type headers: dict[str, str] | None, optional
        """
        self.url = url
        self.logger = logger
        self.logfile = Path(logfile) if logfile else logger.get_log_path()
        self.headers = headers

    def send_logfile(self, **metadata: Any) -> bool:
        """
        Send log file to Tray webhook with optional metadata.

        :param metadata: Additional metadata to include (e.g., hostname, serial, user, script_name)
        :return: True if successful, False otherwise
        :rtype: bool
        """
        if not self.logfile or not self.logfile.exists():
            self.logger.error(f"Log file not found: {self.logfile}")
            return False

        # Add timestamp if not provided
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now(timezone.utc).isoformat()

        self.logger.info(f"Sending info to webhook: {self.logfile.name}")

        requests = _import_requests()
        try:
            with open(self.logfile, "rb") as f:
                files = {"logfile": (self.logfile.name, f, "text/plain")}

                response = requests.post(
                    self.url, data=metadata, files=files, headers=self.headers, timeout=30
                )

                if response.ok:
                    self.logger.info(
                        f"Webhook sent successfully: {response.status_code} {response.text}"
                    )
                    return True
                else:
                    self.logger.warn(
                        f"Failed to send webhook: {response.status_code} {response.text}"
                    )
                    return False
        except requests.RequestException as e:
            self.logger.warn(f"Request error sending webhook: {str(e)}")
            return False
        except Exception as e:
            self.logger.warn(f"Error sending webhook: {str(e)}")
            return False

    def send(self, **metadata: Any) -> bool:
        """
        Send information to a webhook with optional metadata.

        :param metadata: Additional metadata to include (e.g., hostname, serial, user, script_name)
        :return: True if successful, False otherwise
        :rtype: bool
        """
        # Add timestamp if not provided
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now(timezone.utc).isoformat()

        self.logger.info(f"Sending data to webhook URL ending in: {self.url[-8:]}")

        requests = _import_requests()
        try:
            response = requests.post(self.url, json=metadata, headers=self.headers, timeout=30)

            if response.ok:
                self.logger.info(
                    f"Webhook sent successfully: {response.status_code} {response.text}"
                )
                return True
            else:
                self.logger.warn(f"Failed to send webhook: {response.status_code} {response.text}")
                return False
        except requests.RequestException as e:
            self.logger.warn(f"Request error sending webhook: {str(e)}")
            return False
        except Exception as e:
            self.logger.warn(f"Error sending webhook: {str(e)}")
            return False
