import re
import subprocess

from .logger import MdmLogger


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

        Method will return False if:
            - Username and UID are both None
            - Username contains invalid characters
            - UID is less than 500 (non-system accounts are created with UIDs higher than 500)

        :return: True if validation is successful, False otherwise
        :rtype: bool
        """
        if self.username is None or self.uid is None:
            return False
        if self.username is not None and not re.match(r"^[a-zA-z0-9_-]+$", self.username):
            return False
        if self.uid is not None and self.uid < 500:
            return False
        return True

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

    def run(self, command: str | list[str], timeout: int = 30) -> str:
        """
        Run a command and return its output.

        - Pass a list for safety: ["/usr/bin/id", "-u", username]
        - Pass a string for shell features: "command | grep something"

        :param command: Command string or list of arguments
        :type command: str | list[str]
        :param timeout: Timeout in seconds, defaults to 30
        :type timeout: int, optional
        :return: Command output (stdout)
        :rtype: str
        """
        shell = isinstance(command, str)

        if self.logger:
            self.logger.debug(f"Running: {self._sanitize_command(command)}")

        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=timeout, check=True, shell=shell
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

        :param command: Command string or list of arguments
        :type command: list[str]
        :param timeout: Timeout in seconds, defaults to 30
        :type timeout: int, optional
        :return: Command output (stdout)
        :rtype: str
        """
        if not self._validate_user():
            if self.logger:
                self.logger.error("Cannot run as user: username and uid are both required")
            raise ValueError(
                "run_as_user requires both username and uid to be set on CommandRunner"
            )

        if self.logger:
            self.logger.debug(
                f"Running: {self._sanitize_command(command)} as the logged in user {self.username} (UID: {self.uid})"
            )

        try:
            return self.run(
                ["/bin/launchctl", "asuser", str(self.uid), "sudo", "-u", self.username, *command],
                timeout=timeout,
            )
        except subprocess.CalledProcessError as e:
            if self.logger:
                self.logger.error(f"Command failed: {e.stderr}")
            raise
        except subprocess.TimeoutExpired:
            if self.logger:
                self.logger.error(f"Command timed out after {timeout}s")
            raise
