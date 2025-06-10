from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class DataSource:
    """Data source model for financial data providers."""
    id: int
    name: str
    description: str
    system_date: datetime
    provider: str
    attributes: Dict[str, Any]