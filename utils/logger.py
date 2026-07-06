import logging
from datetime import datetime
import os
import sys


def setup_logger(name='SOT'):
    """
    Setup application logger
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Configured logger instance
    """
    
    # FIX: Determine appropriate logs directory based on environment
    logs_dir = _get_logs_directory()
    
    # Create logs directory if it doesn't exist
    try:
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
    except (PermissionError, OSError) as e:
        # If we can't create logs directory, fall back to temp directory
        import tempfile
        logs_dir = tempfile.gettempdir()
        print(f"Warning: Could not create logs directory, using temp: {logs_dir}")
    
    # Configure logging
    log_file = os.path.join(logs_dir, f"sot_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler - with error handling
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not create log file: {e}")
        # Continue without file logging
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_handler.setFormatter(formatter)
    
    # Add console handler
    logger.addHandler(console_handler)
    
    return logger


def _get_logs_directory():
    """
    Get appropriate logs directory based on whether running as exe or source
    
    FIX: Enhanced to handle different deployment scenarios
    """
    if getattr(sys, 'frozen', False):
        # Running as exe
        # Try to use AppData on Windows or user's home directory on other systems
        if sys.platform == 'win32':
            # Windows: Use AppData/Local
            appdata = os.environ.get('LOCALAPPDATA')
            if appdata:
                logs_dir = os.path.join(appdata, 'SOT', 'logs')
            else:
                # Fallback to user's home directory
                logs_dir = os.path.join(os.path.expanduser('~'), 'SOT', 'logs')
        else:
            # Linux/Mac: Use home directory
            logs_dir = os.path.join(os.path.expanduser('~'), '.sot', 'logs')
    else:
        # Running from source - use project directory
        base_path = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(base_path, '..', 'logs')
    
    return os.path.normpath(logs_dir)


# Global logger instance
logger = setup_logger()