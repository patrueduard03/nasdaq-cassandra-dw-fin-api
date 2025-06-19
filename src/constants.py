"""
Application-wide constants to avoid duplication and ensure consistency.
"""
from datetime import datetime

# Temporal database constants
FAR_FUTURE_DATE = datetime(9999, 12, 31, 23, 59, 59)  # For current versions

# API response constants
DEFAULT_ERROR_MESSAGES = {
    'ASSET_NOT_FOUND': 'Asset not found',
    'DATA_SOURCE_NOT_FOUND': 'Data source not found',
    'INVALID_DATE_RANGE': 'Invalid date range provided',
    'VALIDATION_ERROR': 'Validation error in request data',
    'DATABASE_ERROR': 'Database operation failed',
    'INGESTION_ERROR': 'Data ingestion failed'
}

# Database operation constants
DEFAULT_BATCH_SIZE = 100
DEFAULT_PAGE_SIZE = 1000
MAX_RECONNECT_ATTEMPTS = 3

# Data ingestion constants
NASDAQ_DATASET_CODE = "WIKI/PRICES"
PROGRESS_UPDATE_INTERVAL = 100  # Records processed between progress updates
MAX_INGESTION_TIMEOUT = 3600  # 1 hour in seconds

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
