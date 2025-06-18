from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class DataSource:
    """Data source model for financial data providers with temporal support."""
    id: int
    name: str
    description: str
    system_date: datetime
    provider: str
    attributes: Dict[str, Any]
    is_deleted: bool
    valid_from: datetime
    valid_to: Optional[datetime]