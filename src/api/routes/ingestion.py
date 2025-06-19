from fastapi import APIRouter, HTTPException, Query
from datetime import date
from typing import Optional
import logging
import uuid
import asyncio

from ..models import (
    NasdaqIngestionRequest, 
    DataCoverageRequest, 
    ExtendCoverageRequest, 
    RefreshDataRequest
)
from services.data_ingestion_service import DataIngestionService

router = APIRouter(prefix="/ingest", tags=["ingestion"])
logger = logging.getLogger(__name__)

def get_progress_callback():
    """Get progress callback function from the main app's connection manager"""
    try:
        from ..main import manager
        return manager.send_progress_update
    except ImportError:
        return None

@router.post("/nasdaq")
async def ingest_nasdaq_data(request: NasdaqIngestionRequest):
    """Ingest data from Nasdaq with real-time progress updates.
    
    Args:
        request: NasdaqIngestionRequest containing:
            - asset_id: ID of the asset to ingest data for
            - data_source_id: ID of the data source
            - start_date: Start date for data ingestion
            - end_date: End date for data ingestion
    
    Returns:
        dict: Message with session ID for tracking progress
    """
    session_id = str(uuid.uuid4())
    logger.info(f"Starting Nasdaq data ingestion (session: {session_id}) for asset {request.asset_id}, data source {request.data_source_id}, dates {request.start_date} to {request.end_date}")
    
    try:
        # Create service with progress callback
        progress_callback = get_progress_callback()
        data_ingestion = DataIngestionService(progress_callback=progress_callback)
        
        # Start ingestion in background
        asyncio.create_task(data_ingestion.ingest_nasdaq_data(
            asset_id=request.asset_id,
            data_source_id=request.data_source_id,
            start_date=request.start_date,
            end_date=request.end_date,
            force_refresh=request.force_refresh,
            session_id=session_id
        ))
        
        return {
            "message": "Data ingestion started successfully",
            "session_id": session_id,
            "asset_id": request.asset_id,
            "data_source_id": request.data_source_id,
            "date_range": f"{request.start_date} to {request.end_date}"
        }
        
    except ValueError as e:
        logger.error(f"Validation error in ingestion request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start data ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start data ingestion: {str(e)}")

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
        # Create service instance
        data_ingestion = DataIngestionService()
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
        # Create service instance
        data_ingestion = DataIngestionService()
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
    """Refresh existing data from Nasdaq using temporal paradigm with real-time progress updates.
    
    Args:
        request: NasdaqIngestionRequest containing asset_id, data_source_id, start_date, end_date
    
    Returns:
        dict: Message with session ID for tracking progress
    """
    session_id = str(uuid.uuid4())
    logger.info(f"Starting Nasdaq data refresh (session: {session_id}) for asset {request.asset_id}, data source {request.data_source_id}")
    
    try:
        # Create service with progress callback
        progress_callback = get_progress_callback()
        data_ingestion = DataIngestionService(progress_callback=progress_callback)
        
        # Start refresh in background
        asyncio.create_task(data_ingestion.ingest_nasdaq_data(
            request.asset_id,
            request.data_source_id,
            request.start_date,
            request.end_date,
            session_id=session_id,
            force_refresh=True
        ))
        
        logger.info(f"Started Nasdaq data refresh task for asset {request.asset_id} (session: {session_id})")
        return {
            "message": "Data refresh started",
            "session_id": session_id
        }
    except ValueError as e:
        logger.error(f"Nasdaq refresh validation error for asset {request.asset_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Nasdaq refresh failed for asset {request.asset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start refresh: {str(e)}")

@router.get("/compatible-data-sources/{asset_id}")
async def get_compatible_data_sources(asset_id: int):
    """Get information about data sources and their existing data status for the given asset.
    
    Args:
        asset_id: Asset ID
    
    Returns:
        list: List of data source information with existing data status
    """
    try:
        # Create service instance
        data_ingestion = DataIngestionService()
        
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

@router.get("/progress/{session_id}")
async def get_ingestion_progress(session_id: str):
    """Get progress for a specific ingestion session (WebSocket fallback).
    
    Args:
        session_id: The session ID returned when starting ingestion
    
    Returns:
        dict: Progress information for the session
    """
    try:
        # For now, return a basic response since the ingestion is asynchronous
        # In a real implementation, you'd track session progress in a database or cache
        return {
            "status": "processing",
            "progress": 75,  # Default progress when we can't get real status
            "message": "Processing data ingestion...",
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Error getting ingestion progress for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")