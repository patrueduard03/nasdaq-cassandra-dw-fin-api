from fastapi import APIRouter, HTTPException
from typing import List
import logging

from ..models import DataSourceResponse, DataSourceCreate
from services.data_service import DataService

# Constants
ERROR_DATA_SOURCE_NOT_FOUND = "Data source not found"
ERROR_DATA_SOURCE_CREATION_FAILED = "Failed to create data source"
ERROR_DATA_SOURCE_UPDATE_FAILED = "Failed to update data source"
ERROR_DATA_SOURCE_DELETION_FAILED = "Failed to delete data source"

router = APIRouter(prefix="/data-sources", tags=["data-sources"])
data_service = DataService()
logger = logging.getLogger(__name__)

@router.post("", response_model=DataSourceResponse)
async def create_data_source(data_source: DataSourceCreate):
    """Create a new data source"""
    logger.info(f"Creating new data source: {data_source.name} (Provider: {data_source.provider})")
    try:
        created_data_source = data_service.create_data_source(data_source)
        logger.info(f"Successfully created data source: {data_source.name} (ID: {created_data_source.id})")
        return created_data_source
    except Exception as e:
        logger.error(f"Failed to create data source {data_source.name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{ERROR_DATA_SOURCE_CREATION_FAILED}: {str(e)}")

@router.get("", response_model=List[DataSourceResponse])
async def get_all_data_sources():
    """Get all data sources"""
    logger.info("Retrieving all data sources")
    data_sources = data_service.get_all_data_sources()
    logger.info(f"Retrieved {len(data_sources)} data sources")
    return data_sources

@router.get("/admin/all", response_model=List[DataSourceResponse])
async def get_all_data_sources_including_deleted():
    """Get all data sources including deleted ones (admin only)"""
    logger.info("Retrieving all data sources including deleted (admin mode)")
    data_sources = data_service.get_all_data_sources_including_deleted()
    logger.info(f"Retrieved {len(data_sources)} data sources (including deleted)")
    return data_sources

@router.get("/{data_source_id}", response_model=DataSourceResponse)
async def get_data_source(data_source_id: int):
    """Get data source details"""
    logger.info(f"Retrieving data source with ID: {data_source_id}")
    data_source = data_service.get_data_source_by_id(data_source_id)
    if not data_source:
        logger.warning(f"Data source not found: ID {data_source_id}")
        raise HTTPException(status_code=404, detail=ERROR_DATA_SOURCE_NOT_FOUND)
    logger.info(f"Retrieved data source: {data_source.name} (ID: {data_source_id})")
    return data_source

@router.get("/provider/{provider}", response_model=DataSourceResponse)
async def get_data_source_by_provider(provider: str):
    """Get data source by provider"""
    logger.info(f"Retrieving data source for provider: {provider}")
    data_source = data_service.get_data_source_by_provider(provider)
    if not data_source:
        logger.warning(f"Data source not found for provider: {provider}")
        raise HTTPException(status_code=404, detail=ERROR_DATA_SOURCE_NOT_FOUND)
    logger.info(f"Retrieved data source: {data_source.name} for provider {provider}")
    return data_source

@router.put("/{data_source_id}", response_model=DataSourceResponse)
async def update_data_source(data_source_id: int, data_source: DataSourceCreate):
    """Update a data source by creating a new version (temporal database pattern)"""
    logger.info(f"Attempting to update data source with ID: {data_source_id}")
    
    # Check if data source exists and is not deleted
    existing_data_source = data_service.get_data_source_by_id(data_source_id)
    if not existing_data_source:
        logger.warning(f"Data source not found for update: ID {data_source_id}")
        raise HTTPException(status_code=404, detail=ERROR_DATA_SOURCE_NOT_FOUND)
    
    if existing_data_source.is_deleted:
        logger.warning(f"Cannot update - data source is deleted: ID {data_source_id}")
        raise HTTPException(status_code=409, detail="Data source is deleted and cannot be updated")
    
    try:
        updated_data_source = data_service.data_source_repo.update_data_source(data_source_id, data_source.dict())
        logger.info(f"Successfully updated data source: {updated_data_source.name} (ID: {data_source_id})")
        return updated_data_source
    except Exception as e:
        logger.error(f"Failed to update data source ID {data_source_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{ERROR_DATA_SOURCE_UPDATE_FAILED}: {str(e)}")

@router.delete("/{data_source_id}")
async def delete_data_source(data_source_id: int):
    """Mark a data source as deleted"""
    logger.info(f"Attempting to delete data source with ID: {data_source_id}")
    data_source = data_service.get_data_source_by_id(data_source_id)
    if not data_source:
        logger.warning(f"Cannot delete - data source not found: ID {data_source_id}")
        raise HTTPException(status_code=404, detail=ERROR_DATA_SOURCE_NOT_FOUND)
    
    try:
        data_service.mark_data_source_deleted(data_source_id)
        logger.info(f"Successfully deleted data source: {data_source.name} (ID: {data_source_id})")
        return {"message": "Data source marked as deleted"}
    except Exception as e:
        logger.error(f"Failed to delete data source ID {data_source_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{ERROR_DATA_SOURCE_DELETION_FAILED}: {str(e)}")

@router.post("/{data_source_id}/resurrect", response_model=DataSourceResponse)
async def resurrect_data_source(data_source_id: int, data_source: DataSourceCreate):
    """Resurrect a previously deleted data source"""
    logger.info(f"Attempting to resurrect data source with ID: {data_source_id}")
    
    # Check if data source exists and is deleted
    existing_data_source = data_service.get_data_source_by_id_including_deleted(data_source_id)
    if not existing_data_source:
        logger.warning(f"Data source not found for resurrection: ID {data_source_id}")
        raise HTTPException(status_code=404, detail=ERROR_DATA_SOURCE_NOT_FOUND)
    
    if not existing_data_source.is_deleted:
        logger.warning(f"Cannot resurrect - data source is not deleted: ID {data_source_id}")
        raise HTTPException(status_code=409, detail="Data source is not deleted and cannot be resurrected")
    
    try:
        resurrected_data_source = data_service.data_source_repo.resurrect_data_source(data_source_id, data_source.dict())
        logger.info(f"Successfully resurrected data source: {resurrected_data_source.name} (ID: {data_source_id})")
        return resurrected_data_source
    except Exception as e:
        logger.error(f"Failed to resurrect data source ID {data_source_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resurrect data source: {str(e)}")