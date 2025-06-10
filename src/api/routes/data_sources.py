from fastapi import APIRouter, HTTPException
from typing import List
import logging

from ..models import DataSourceResponse, DataSourceCreate
from services.data_service import DataService

router = APIRouter(prefix="/data-sources", tags=["data-sources"])
data_service = DataService()
logger = logging.getLogger(__name__)

@router.post("", response_model=DataSourceResponse)
async def create_data_source(data_source: DataSourceCreate):
    """Create a new data source"""
    logger.info(f"Creating new data source: {data_source.name} (Provider: {data_source.provider})")
    created_data_source = data_service.create_data_source(data_source)
    logger.info(f"Successfully created data source: {data_source.name} (ID: {created_data_source.id})")
    return created_data_source

@router.get("", response_model=List[DataSourceResponse])
async def get_all_data_sources():
    """Get all data sources"""
    logger.info("Retrieving all data sources")
    data_sources = data_service.get_all_data_sources()
    logger.info(f"Retrieved {len(data_sources)} data sources")
    return data_sources

@router.get("/{data_source_id}", response_model=DataSourceResponse)
async def get_data_source(data_source_id: int):
    """Get data source details"""
    logger.info(f"Retrieving data source with ID: {data_source_id}")
    data_source = data_service.get_data_source_by_id(data_source_id)
    if not data_source:
        logger.warning(f"Data source not found: ID {data_source_id}")
        raise HTTPException(status_code=404, detail="Data source not found")
    logger.info(f"Retrieved data source: {data_source.name} (ID: {data_source_id})")
    return data_source

@router.get("/provider/{provider}", response_model=DataSourceResponse)
async def get_data_source_by_provider(provider: str):
    """Get data source by provider"""
    logger.info(f"Retrieving data source for provider: {provider}")
    data_source = data_service.get_data_source_by_provider(provider)
    if not data_source:
        logger.warning(f"Data source not found for provider: {provider}")
        raise HTTPException(status_code=404, detail="Data source not found")
    logger.info(f"Retrieved data source: {data_source.name} for provider {provider}")
    return data_source 