# core/logger.py

import logging
import logging.handlers
import sys
import threading
from pathlib import Path
from typing import Optional, Dict

# Configuration Constants
LOG_DIR: Path = Path("logs")
DEFAULT_LOG_LEVEL: int = logging.INFO
LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(threadName)-12s | %(name)-15s | %(filename)s:%(lineno)d | %(message)s"
DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB per log file
BACKUP_COUNT: int = 5  # Keep 5 backup log files


class LoggerFactory:
    """
    A thread-safe factory for creating and managing logger instances across the NotifyAI application.
    Implements a Singleton pattern to ensure that loggers are configured consistently and 
    logging handlers are not duplicated across different modules.
    """
    
    _instance: Optional['LoggerFactory'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> 'LoggerFactory':
        """
        Controls the creation of the LoggerFactory instance ensuring only one instance exists.
        
        Returns:
            LoggerFactory: The singleton instance of the factory.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LoggerFactory, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """
        Initializes the factory, creating the required log directory if it does not already exist.
        Safeguarded by a lock to prevent race conditions during initialization.
        """
        with self._lock:
            if getattr(self, '_initialized', False):
                return
                
            self._loggers: Dict[str, logging.Logger] = {}
            self._setup_log_directory()
            self._initialized = True

    def _setup_log_directory(self) -> None:
        """
        Creates the logging directory using pathlib. 
        Catches and reports permission issues to stderr as a fallback, exiting if critical.
        """
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            sys.stderr.write(f"CRITICAL: Failed to create log directory at {LOG_DIR}. Error: {error}\n")
            sys.exit(1)

    def get_logger(self, name: str, level: int = DEFAULT_LOG_LEVEL) -> logging.Logger:
        """
        Retrieves a fully configured logger instance by name.
        
        Args:
            name (str): The name of the logger, typically __name__ from the calling module.
            level (int): The logging level to set for this logger. Defaults to logging.INFO.
            
        Returns:
            logging.Logger: The configured logger instance ready for use.
        """
        with self._lock:
            if name in self._loggers:
                return self._loggers[name]

            logger: logging.Logger = logging.getLogger(name)
            
            # Prevent log messages from being propagated to the root logger to avoid duplication
            logger.propagate = False
            
            # Configure handlers only if they haven't been added yet
            if not logger.handlers:
                logger.setLevel(level)
                formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

                # Configure Standard Output Console Handler
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(level)
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)

                # Configure Rotating File Handler
                log_file: Path = LOG_DIR / "notifyai.log"
                try:
                    file_handler = logging.handlers.RotatingFileHandler(
                        filename=str(log_file),
                        maxBytes=MAX_BYTES,
                        backupCount=BACKUP_COUNT,
                        encoding='utf-8'
                    )
                    file_handler.setLevel(level)
                    file_handler.setFormatter(formatter)
                    logger.addHandler(file_handler)
                except OSError as error:
                    sys.stderr.write(f"WARNING: Failed to initialize file handler for {log_file}. Error: {error}\n")

            self._loggers[name] = logger
            return logger


def get_logger(name: str, level: int = DEFAULT_LOG_LEVEL) -> logging.Logger:
    """
    Convenience functional wrapper to retrieve a logger without explicitly instantiating the factory.
    
    Args:
        name (str): The name of the module requesting the logger.
        level (int): The desired logging level.
        
    Returns:
        logging.Logger: The fully configured logger instance.
    """
    factory = LoggerFactory()
    return factory.get_logger(name, level)


# Module-level logger for internal core/logger.py execution metrics
logger = get_logger(__name__, logging.DEBUG)
logger.debug("NotifyAI logging subsystem initialized successfully.")
