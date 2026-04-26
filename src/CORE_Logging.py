import os
import logging
from logging.handlers import RotatingFileHandler
from gi.repository import GLib, Gio
from .settings import settings

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
        
        self.log_dir = os.path.join(GLib.get_user_cache_dir(), "mousam")
        self.log_file = os.path.join(self.log_dir, self.LOG_FILE_NAME)
        
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

        self.logger = logging.getLogger("mousam")
        self._setup_logging()
        self._initialized = True

    def _setup_logging(self):
        # Clear existing handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        if not settings.debug_mode:
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

    def update_level(self):
        """Reload logging level based on current settings."""
        self._setup_logging()
        if settings.debug_mode:
            self.logger.info("Logging enabled")
            self.logger.info(f"Logging level set to: {logging.getLevelName(logging.DEBUG)}")

    def open_log_folder(self):
        """Open the folder containing the log files."""
        try:
            file = Gio.File.new_for_path(self.log_dir)
            Gio.AppInfo.launch_default_for_uri(file.get_uri(), None)
        except Exception as e:
            self.logger.error(f"Failed to open log folder: {e}")

    def open_log_file(self):
        """Open the current log file."""
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

# Initialize singleton on import
log_manager = LogManager()
