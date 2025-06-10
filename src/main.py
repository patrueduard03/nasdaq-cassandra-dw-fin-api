import uvicorn
import logging
import sys
import socket
import os
from pathlib import Path

# Setup global logging configuration
def setup_logging():
    """Configure comprehensive logging for the entire application."""
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Console handler for immediate feedback
            logging.StreamHandler(sys.stdout),
            # File handler for persistent logging
            logging.FileHandler(log_dir / "app.log"),
        ]
    )
    
    # Set specific log levels for different components
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("cassandra").setLevel(logging.WARNING)  # Reduce cassandra noise
    
    # Create separate logger for ingestion with its own file
    ingestion_logger = logging.getLogger("data_ingestion")
    if not ingestion_logger.handlers:
        ingestion_handler = logging.FileHandler(log_dir / "ingestion.log")
        ingestion_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        ingestion_logger.addHandler(ingestion_handler)
        ingestion_logger.setLevel(logging.INFO)

# Setup logging before any other imports
setup_logging()
logger = logging.getLogger(__name__)

def is_port_available(port: int) -> bool:
    """Check if a port is available for binding."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('0.0.0.0', port))
            return True
    except OSError:
        return False

from typing import List, Optional

def find_available_port(preferred_ports: Optional[List[int]] = None) -> int:
    """Find an available port from a list of preferred ports."""
    if preferred_ports is None:
        preferred_ports = [8000, 8001, 8002, 8003, 8004, 8005, 8080, 8888, 9000]
    
    for port in preferred_ports:
        if is_port_available(port):
            return port
    
    # If none of the preferred ports are available, find any available port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('0.0.0.0', 0))
        return sock.getsockname()[1]

def main():
    """Main application entry point with error handling"""
    try:
        logger.info("Starting Acme Ltd Financial Data Warehouse API...")
        
        # Import app here to delay database connection
        from api.main import app
        
        # Find an available port
        port = find_available_port()
        logger.info(f"Selected port: {port}")
        
        if port != 8000:
            logger.warning(f"Port 8000 was not available, using port {port} instead")
        
        logger.info(f"API will be available at: http://localhost:{port}")
        logger.info(f"API Documentation will be available at: http://localhost:{port}/docs")
        
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"
        )
    except ImportError as e:
        logger.error(f"Failed to import application modules: {e}")
        logger.error("Please check your dependencies and database configuration")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()