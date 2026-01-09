from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from .logger import MdmLogger


class WebhookSender:
    """Helper class for sending log files to Tray webhooks."""

    def __init__(self, url: str, logger: MdmLogger, logfile: Path | str | None = None):
        """
        Initialize WebhookSender.

        :param url: The Tray webhook URL.
        :type url: str
        :param logger: MdmLogger instance for logging webhook operations
        :type logger: MdmLogger
        :param logfile: Path to log file to send, defaults to None
        :type logfile: Path | str | None, optional
        """
        self.url = url
        self.logger = logger
        # Use provided logfile, or fall back to logger's output_path
        self.logfile = Path(logfile) if logfile else logger.get_log_path()

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

        try:
            with open(self.logfile, "rb") as f:
                files = {"logfile": (self.logfile.name, f, "text/plain")}

                response = requests.post(self.url, data=metadata, files=files, timeout=30)

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

        try:
            response = requests.post(self.url, json=metadata, timeout=30)

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
