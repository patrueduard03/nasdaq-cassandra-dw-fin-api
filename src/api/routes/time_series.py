from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import date
import logging

from ..models import TimeSeriesDataResponse
from services.data_service import DataService

router = APIRouter(prefix="/time-series", tags=["time-series"])
data_service = DataService()
logger = logging.getLogger(__name__)

@router.get("/{asset_id}/{data_source_id}", response_model=List[TimeSeriesDataResponse])
async def get_time_series_data(
    asset_id: int,
    data_source_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """Get time series data for a specific asset and data source."""
    
    date_range = f" from {start_date} to {end_date}" if start_date and end_date else ""
    logger.info(f"Retrieving time series data for asset {asset_id}, data source {data_source_id}{date_range}")
    
    # Validate asset exists and is not deleted
    asset = data_service.get_asset_by_id(asset_id)
    if not asset:
        logger.warning(f"Time series request failed - asset not found or deleted: ID {asset_id}")
        raise HTTPException(status_code=404, detail="Asset not found or has been deleted")
    
    # Validate data source exists
    data_source = data_service.get_data_source_by_id(data_source_id)
    if not data_source:
        logger.warning(f"Time series request failed - data source not found: ID {data_source_id}")
        raise HTTPException(status_code=404, detail="Data source not found")
    
    try:
        data = data_service.get_time_series_data(
            asset_id,
            data_source_id,
            start_date,
            end_date
        )
        
        if not data:
            logger.warning(f"No time series data found for asset {asset_id} from data source {data_source_id}{date_range}")
            raise HTTPException(
                status_code=404, 
                detail=f"No time series data found for asset {asset_id} from data source {data_source_id}"
            )
        
        logger.info(f"Retrieved {len(data)} time series records for asset {asset_id} from data source {data_source_id}")
        return data
    except Exception as e:
        logger.error(f"Error retrieving time series data for asset {asset_id}, data source {data_source_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving time series data: {str(e)}") 