import logging
import sys
from config import settings

def setup_logging():
    """Setup logging configuration"""
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.INFO)
    
    # Application loggers
    logging.getLogger('services').setLevel(logging.INFO)
    logging.getLogger('routes').setLevel(logging.INFO)
    logging.getLogger('auth').setLevel(logging.INFO)
