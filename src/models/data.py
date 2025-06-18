from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, Any, Optional

@dataclass
class Data:
    """Time series data model for financial instruments with temporal support."""
    asset_id: int
    data_source_id: int
    business_date: date
    system_date: datetime
    values_double: Dict[str, float]
    values_int: Dict[str, int]
    values_text: Dict[str, str]
    is_deleted: bool
    valid_from: datetime
    valid_to: Optional[datetime] 