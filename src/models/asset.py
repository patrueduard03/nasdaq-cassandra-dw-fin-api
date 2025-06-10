from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class Asset:
    """Financial asset model with temporal support."""
    id: int
    name: str
    description: str
    system_date: datetime
    is_deleted: bool
    valid_from: datetime
    valid_to: Optional[datetime]
    attributes: Dict[str, Any]