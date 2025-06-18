from fastapi import APIRouter, HTTPException, Query
from datetime import date
from typing import Optional
import logging

from ..models import (
    NasdaqIngestionRequest, 
    DataCoverageRequest, 
    ExtendCoverageRequest, 
    RefreshDataRequest
)
from services.data_ingestion_service import DataIngestionService

router = APIRouter(prefix="/ingest", tags=["ingestion"])
data_ingestion = DataIngestionService()
logger = logging.getLogger(__name__)

@router.post("/nasdaq")
async def ingest_nasdaq_data(request: NasdaqIngestionRequest):
    """Ingest data from Nasdaq.
    
    Args:
        request: NasdaqIngestionRequest containing:
            - asset_id: ID of the asset to ingest data for
            - data_source_id: ID of the data source
            - start_date: Start date for data ingestion
            - end_date: End date for data ingestion
    
    Returns:
        dict: Message with number of data points ingested
    """
    logger.info(f"Starting Nasdaq data ingestion for asset {request.asset_id}, data source {request.data_source_id}, dates {request.start_date} to {request.end_date}")
    
    try:
        # Ingest data
        data_ingestion.ingest_nasdaq_data(
            request.asset_id,
            request.data_source_id,
            request.start_date,
            request.end_date
        )
        logger.info(f"Successfully completed Nasdaq data ingestion for asset {request.asset_id}")
        return {"message": "Successfully ingested data"}
    except ValueError as e:
        logger.error(f"Nasdaq ingestion validation error for asset {request.asset_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Nasdaq ingestion failed for asset {request.asset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest data: {str(e)}")

@router.get("/status")
async def get_ingestion_status(asset_id: Optional[int] = Query(None), data_source_id: Optional[int] = Query(None)):
    """Get ingestion status for all assets or filter by asset_id/data_source_id.
    
    Args:
        asset_id: Optional asset ID to filter by
        data_source_id: Optional data source ID to filter by
    
    Returns:
        list: List of ingestion status objects
    """
    try:
        status_list = data_ingestion.get_ingestion_status(asset_id, data_source_id)
        return {
            "status": "success",
            "count": len(status_list),
            "data": status_list
        }
    except Exception as e:
        logger.error(f"Error getting ingestion status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get ingestion status: {str(e)}")

@router.get("/availability/{asset_id}/{data_source_id}")
async def check_data_availability(asset_id: int, data_source_id: int):
    """Check data availability for a specific asset and data source.
    
    Args:
        asset_id: Asset ID
        data_source_id: Data source ID
    
    Returns:
        dict: Data availability information
    """
    try:
        availability = data_ingestion.check_data_availability(asset_id, data_source_id)
        return {
            "status": "success",
            "data": availability
        }
    except Exception as e:
        logger.error(f"Error checking data availability: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check data availability: {str(e)}")

@router.post("/nasdaq/refresh")
async def refresh_nasdaq_data(request: NasdaqIngestionRequest):
    """Refresh existing data from Nasdaq using temporal paradigm.
    
    Args:
        request: NasdaqIngestionRequest containing asset_id, data_source_id, start_date, end_date
    
    Returns:
        dict: Message with refresh results
    """
    logger.info(f"Starting Nasdaq data refresh for asset {request.asset_id}, data source {request.data_source_id}")
    
    try:
        # Use force_refresh=True to update existing data
        data_ingestion.ingest_nasdaq_data(
            request.asset_id,
            request.data_source_id,
            request.start_date,
            request.end_date,
            force_refresh=True
        )
        logger.info(f"Successfully refreshed Nasdaq data for asset {request.asset_id}")
        return {"message": "Successfully refreshed data with temporal versioning"}
    except ValueError as e:
        logger.error(f"Nasdaq refresh validation error for asset {request.asset_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Nasdaq refresh failed for asset {request.asset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh data: {str(e)}")

@router.get("/compatible-data-sources/{asset_id}")
async def get_compatible_data_sources(asset_id: int):
    """Get information about data sources and their existing data status for the given asset.
    
    Args:
        asset_id: Asset ID
    
    Returns:
        list: List of data source information with existing data status
    """
    try:
        # Get existing data source IDs for this asset
        existing_ds_ids = data_ingestion.data_repository.get_compatible_data_sources_for_asset(asset_id)
        logger.info(f"Asset {asset_id} has existing data in data sources: {existing_ds_ids}")
        
        # Get all Nasdaq data sources
        all_data_sources = data_ingestion.data_source_repository.get_all_data_sources()
        nasdaq_data_sources = [ds for ds in all_data_sources if 'nasdaq' in ds.provider.lower()]
        logger.info(f"Found {len(nasdaq_data_sources)} Nasdaq data sources total")
        
        # Return all Nasdaq sources with information about existing data
        result_data = []
        for ds in nasdaq_data_sources:
            has_data = ds.id in existing_ds_ids
            result_data.append({
                "id": ds.id,
                "name": ds.name,
                "provider": ds.provider,
                "has_existing_data": has_data
            })
            logger.debug(f"Data source {ds.id} ({ds.name}): has_existing_data={has_data}")
        
        return {
            "status": "success",
            "data": result_data
        }
    except Exception as e:
        logger.error(f"Error getting compatible data sources: {str(e)}")
        # Return empty list on error so the frontend can fallback gracefully
        return {
            "status": "error", 
            "data": [],
            "message": str(e)
        }