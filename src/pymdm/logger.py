import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path

MAX_BYTES = 1048576 * 100  # 100 MB


class MdmLogger:
    def __init__(
        self,
        debug: bool = False,
        quiet: bool = False,
        output_path: Path | str | None = None,
    ):
        self.debug_enabled = debug
        self.quiet = quiet
        self.output_path = Path(output_path) if output_path else None

    def _create_logfile(self) -> None:
        """Ensures the passed output_path for logs exists."""
        if self.output_path and not self.output_path.exists():
            self.output_path.parent.mkdir(exist_ok=True, parents=True)
            self.output_path.touch()

    def _check_log_size(self, max_bytes: int = MAX_BYTES) -> None:
        """Rotate log file if it exceeds max_bytes."""
        if self.output_path and self.output_path.exists():
            if self.output_path.stat().st_size > max_bytes:
                # Rename current log to .old
                backup = self.output_path.with_suffix(self.output_path.suffix + ".old")
                if backup.exists():
                    backup.unlink()
                self.output_path.rename(backup)

    @staticmethod
    def _format_script_name(script_name: str) -> str:
        if script_name.endswith(".sh"):
            shell_script = script_name.rstrip(".sh")
            shell_script = shell_script.replace("-", " ").title()
            return f"{shell_script} (shell)"

        if script_name.endswith(".py"):
            py_script = script_name.rstrip(".py")
            py_script = py_script.replace("_", " ").title()
            return f"{py_script} (python)"

        return script_name

    def log_startup(self, script_name: str, version: str | None = None) -> None:
        """Log script startup information."""
        self.info(f"{'=' * 50}", startup=True)
        self.info(f"Script: {self._format_script_name(script_name)}")
        if version:
            self.info(f"Version: {version}")
        self.info(f"Python: {platform.python_version()}")
        self.info(f"{self._get_os_version_label()}")
        self.info(f"{'=' * 50}")

    @staticmethod
    def _get_os_version_label() -> str:
        """Get the OS version label from the platform layer.

        Falls back to a generic label if the platform layer is unavailable.

        :return: OS version label string
        :rtype: str
        """
        try:
            from .platforms._detection import get_platform

            return get_platform().get_os_version_label()
        except (ImportError, NotImplementedError):
            return f"OS Version: {platform.release()}"

    def update_log(
        self, level: str, message: str, startup: bool = False, exit_code: int | None = None
    ) -> None:
        """
        Log a message with the specified level and optionally exit.

        :param level: The log level (info, warn, error, debug)
        :type level: str
        :param message: The message to log
        :type message: str
        :param startup: If True, adds new line to first log message
        :type startup: bool, defaults to False
        :param exit_code: If provided, exit with this code after logging, defaults to None
        :type exit_code: int | None, optional
        """
        level_upper = level.upper()

        # Skip debug unless enabled
        if level_upper == "DEBUG" and not self.debug_enabled:
            if exit_code is not None:
                sys.exit(exit_code)
            return

        # Skip info if quiet is enabled (keep warn and error)
        if (level_upper == "INFO" or level_upper == "DEBUG") and self.quiet:
            if exit_code is not None:
                sys.exit(exit_code)
            return

        # Format log output like bash
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        startup_message = f"\n[{timestamp}] [{level_upper}] {message.strip()}"
        normal_message = f"[{timestamp}] [{level_upper}] {message.strip()}"
        formatted_message = startup_message if startup else normal_message

        stream = sys.stderr if level_upper == "ERROR" else sys.stdout
        stream.write(f"{formatted_message}\n")

        # Automatically write to file if output_path is provided
        if self.output_path:
            self._check_log_size()
            self._create_logfile()
            with open(self.output_path, "a") as log_file:
                log_file.write(f"{formatted_message}\n")

        if exit_code is not None:
            sys.exit(exit_code)

    def debug(self, message: str, exit_code: int | None = None) -> None:
        """Log a DEBUG message."""
        self.update_log("debug", message, exit_code=exit_code)

    def info(
        self, message: str, startup: bool | None = False, exit_code: int | None = None
    ) -> None:
        """Log an INFO message."""
        self.update_log("info", message, startup, exit_code)

    def warn(self, message: str, exit_code: int | None = None) -> None:
        """Log a WARN message."""
        self.update_log("warn", message, exit_code=exit_code)

    def error(self, message: str, exit_code: int | None = None) -> None:
        """Log an ERROR message."""
        self.update_log("error", message, exit_code=exit_code)

    def get_log_path(self) -> Path | None:
        """Return the log file path if configured."""
        return self.output_path

    def flush(self) -> None:
        """Ensure all pending writes are flushed to disk."""
        sys.stdout.flush()
        sys.stderr.flush()

    def log_exception(self, message: str, exc: Exception, exit_code: int | None = None) -> None:
        """Log an exception with full traceback."""
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        full_message = f"{message}\n{tb}"
        self.update_log("error", full_message, exit_code=exit_code)
