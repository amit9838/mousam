"""Logging for the app: get_logger() for modules, log_manager for its setup.

Importing this module is cheap and needs no GTK or GSettings, so the modules
that use get_logger stay importable on their own (tests/). It never reads
the settings: the app calls log_manager.setup(debug) once at start-up
(main.main) and update_level(debug) when debug mode changes. Until then the
"mousam" loggers are silent, as they are whenever debug mode is off.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

# Silent until setup() reads the debug-mode setting
logging.getLogger("mousam").setLevel(logging.CRITICAL + 1)


class LogManager:
    _instance = None
    LOG_FILE_NAME = "mousam.log"
    MAX_BYTES = 1024 * 1024  # 1MB
    BACKUP_COUNT = 3

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.logger = logging.getLogger("mousam")
        self.log_dir = None
        self.log_file = None
        self._initialized = True

    def setup(self, debug: bool) -> None:
        """Create the log folder and apply the debug-mode setting. Called once
        at start-up, before anything is logged."""
        # Imported here so that importing this module needs no GTK or GSettings
        from gi.repository import GLib

        self.log_dir = os.path.join(GLib.get_user_cache_dir(), "mousam")
        self.log_file = os.path.join(self.log_dir, self.LOG_FILE_NAME)
        os.makedirs(self.log_dir, exist_ok=True)
        self._setup_logging(debug)

    def _setup_logging(self, debug: bool):
        # Clear existing handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        if not debug:
            self.logger.setLevel(logging.CRITICAL + 1)
            return

        self.logger.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File Handler
        try:
            file_handler = RotatingFileHandler(
                self.log_file, maxBytes=self.MAX_BYTES, backupCount=self.BACKUP_COUNT
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to setup file logging: {e}")

    def update_level(self, debug: bool):
        """Turn logging on or off, when the debug-mode setting changes."""
        self._setup_logging(debug)
        if debug:
            self.logger.info("Logging enabled")
            self.logger.info(f"Logging level set to: {logging.getLevelName(logging.DEBUG)}")

    def open_log_folder(self):
        """Open the folder containing the log files."""
        from gi.repository import Gio

        try:
            file = Gio.File.new_for_path(self.log_dir)
            Gio.AppInfo.launch_default_for_uri(file.get_uri(), None)
        except Exception as e:
            self.logger.error(f"Failed to open log folder: {e}")

    def open_log_file(self):
        """Open the current log file."""
        from gi.repository import Gio

        try:
            file = Gio.File.new_for_path(self.log_file)
            Gio.AppInfo.launch_default_for_uri(file.get_uri(), None)
        except Exception as e:
            self.logger.error(f"Failed to open log file: {e}")

    def clear_logs(self):
        """Truncate the log file."""
        try:
            with open(self.log_file, 'w') as f:
                f.write('')
            self.logger.info("Log file cleared by user")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear log file: {e}")
            return False

# Helper function to get the logger directly
def get_logger(name=None):
    if name:
        return logging.getLogger(f"mousam.{name}")
    return logging.getLogger("mousam")

# The singleton; main.main() calls log_manager.setup(debug) at start-up
log_manager = LogManager()
