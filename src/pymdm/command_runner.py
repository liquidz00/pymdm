"""
Safe subprocess execution with logging support.

Provides the CommandRunner class for running shell commands with credential
sanitization, timeout handling, and platform-aware run-as-user support.
"""

import re
import subprocess

from .logger import MdmLogger
from .platforms._detection import get_command_support


class CommandRunner:
    """Safe subprocess execution with logging support."""

    def __init__(
        self, logger: MdmLogger | None = None, username: str | None = None, uid: int | None = None
    ):
        """
        Initialize CommandRunner.

        :param logger: Optional MdmLogger instance for logging command execution, defaults to None
        :type logger: MdmLogger | None, optional
        :param username: If passed, the username of the logged in user to run a command as
        :type username: str | None, optional
        :param uid: If passed, the uid of the logged in user to run a command as
        :type uid: int | None, optional
        """
        self.logger = logger
        self.username = username
        self.uid = uid

    def _validate_user(self) -> bool:
        """
        Validates user information passed is both present and accurate.

        Delegates to the platform-specific implementation which checks:
            - Username and UID are both present
            - Username contains only valid characters
            - UID meets platform-specific minimum (500 on macOS)

        :return: True if validation is successful, False otherwise
        :rtype: bool
        """
        return get_command_support().validate_user(self.username, self.uid)

    @staticmethod
    def _sanitize_command(command: str | list[str]) -> str:
        """Sanitizes sensitive data in the command list."""
        # Convert to string when needed
        cmd_str = command if isinstance(command, str) else " ".join(command)
        # Order matters: more specific patterns first to avoid overlapping replacements
        replacements = [
            # Auth headers (e.g., "Authorization: Bearer token") - must come before general Bearer pattern
            (r"Authorization:\s*Bearer\s+\S+", "Authorization: Bearer <REDACTED>"),
            # API keys and tokens (e.g., "Bearer abc123", "token=abc123")
            (r"Bearer\s+\S+", "Bearer <REDACTED>"),
            (r"token[=:]\S+", "token=<REDACTED>"),
            (r"api[_-]?key[=:]\S+", "api_key=<REDACTED>"),
            # Credentials (e.g., "password=secret", "client_secret=xyz")
            (r"password[=:]\S+", "password=<REDACTED>"),
            (r"client[_-]?secret[=:]\S+", "client_secret=<REDACTED>"),
            (r"client[_-]?id[=:]\S+", "client_id=<REDACTED>"),
            # General Authorization header (only if not Bearer) - use negative lookahead
            (r"Authorization:\s*(?!Bearer)\S+", "Authorization: <REDACTED>"),
        ]

        sanitized = cmd_str
        for pattern, replacement in replacements:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized

    def run(
        self,
        command: str | list[str],
        timeout: int = 30,
        env: dict[str, str] | None = None,
    ) -> str:
        """
        Run a command and return its output.

        - Pass a list for safety: ["/usr/bin/id", "-u", username]
        - Pass a string for shell features: "command | grep something"

        :param command: Command string or list of arguments
        :type command: str | list[str]
        :param timeout: Timeout in seconds, defaults to 30
        :type timeout: int, optional
        :param env: Environment variables for the subprocess. Replaces the entire
            environment (same behavior as subprocess.run). None inherits the parent
            process environment.
        :type env: dict[str, str] | None, optional
        :return: Command output (stdout)
        :rtype: str
        """
        shell = isinstance(command, str)

        if self.logger:
            self.logger.debug(f"Running: {self._sanitize_command(command)}")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True,
                shell=shell,
                env=env,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            if self.logger:
                self.logger.error(f"Command failed: {e.stderr}")
            raise
        except subprocess.TimeoutExpired:
            if self.logger:
                self.logger.error(f"Command timed out after {timeout}s")
            raise

    def run_as_user(self, command: list[str], timeout: int = 30) -> str:
        """
        Run a command as the logged in user and return its output.

        Uses platform-specific mechanisms:
        - macOS: ``launchctl asuser`` + ``sudo -u``
        - Windows: PowerShell ``Start-Process -Credential``

        :param command: Command string or list of arguments
        :type command: list[str]
        :param timeout: Timeout in seconds, defaults to 30
        :type timeout: int, optional
        :return: Command output (stdout)
        :rtype: str
        """
        if not self._validate_user():
            if self.logger:
                self.logger.error(
                    f"User validation failed (username={self.username!r}, uid={self.uid!r})"
                )
            raise ValueError(
                f"run_as_user validation failed for username={self.username!r}, uid={self.uid!r}"
            )

        if self.logger:
            self.logger.debug(
                f"Running: {self._sanitize_command(command)} as the logged in user {self.username} (UID: {self.uid})"
            )

        # Delegate to platform-specific command wrapping
        platform_cmd = get_command_support().run_as_user_command(command, self.username, self.uid)

        try:
            return self.run(platform_cmd, timeout=timeout)
        except subprocess.CalledProcessError as e:
            if self.logger:
                self.logger.error(f"Command failed: {e.stderr}")
            raise
        except subprocess.TimeoutExpired:
            if self.logger:
                self.logger.error(f"Command timed out after {timeout}s")
            raise
