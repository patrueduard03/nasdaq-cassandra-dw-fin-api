from typing import Dict, Any, Optional
from datetime import datetime, date
from pydantic import BaseModel

class AssetBase(BaseModel):
    name: str
    description: str
    attributes: Dict[str, Any]

class AssetCreate(AssetBase):
    pass

class AssetResponse(AssetBase):
    id: int
    system_date: datetime
    is_deleted: bool
    valid_from: datetime
    valid_to: Optional[datetime]

    class Config:
        from_attributes = True

class DataSourceBase(BaseModel):
    name: str
    description: Optional[str] = None
    provider: str
    attributes: Dict[str, Any] = {}

class DataSourceCreate(DataSourceBase):
    pass

class DataSourceResponse(DataSourceBase):
    id: int
    system_date: datetime
    is_deleted: bool
    valid_from: datetime
    valid_to: Optional[datetime]

    class Config:
        from_attributes = True

class TimeSeriesDataResponse(BaseModel):
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

    class Config:
        from_attributes = True

class NasdaqIngestionRequest(BaseModel):
    asset_id: int
    data_source_id: int
    start_date: date
    end_date: date 