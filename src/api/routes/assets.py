from fastapi import APIRouter, HTTPException
from typing import List
import logging

from ..models import AssetResponse, AssetCreate
from services.data_service import DataService

router = APIRouter(prefix="/assets", tags=["assets"])
data_service = DataService()
logger = logging.getLogger(__name__)

@router.get("", response_model=List[AssetResponse])
async def get_all_assets():
    """Get all financial assets"""
    logger.info("Retrieving all assets")
    assets = data_service.get_all_assets()
    logger.info(f"Retrieved {len(assets)} assets")
    return assets

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: int):
    """Get asset details"""
    logger.info(f"Retrieving asset with ID: {asset_id}")
    asset = data_service.get_asset_by_id(asset_id)
    if not asset:
        logger.warning(f"Asset not found: ID {asset_id}")
        raise HTTPException(status_code=404, detail="Asset not found")
    logger.info(f"Retrieved asset: {asset.name} (ID: {asset_id})")
    return asset

@router.post("", response_model=AssetResponse)
async def create_asset(asset: AssetCreate):
    """Create a new asset"""
    logger.info(f"Creating new asset: {asset.name}")
    created_asset = data_service.create_asset(asset.dict())
    logger.info(f"Successfully created asset: {asset.name} (ID: {created_asset.id})")
    return created_asset

@router.delete("/{asset_id}")
async def delete_asset(asset_id: int):
    """Mark an asset as deleted"""
    logger.info(f"Attempting to delete asset with ID: {asset_id}")
    asset = data_service.get_asset_by_id(asset_id)
    if not asset:
        logger.warning(f"Cannot delete - asset not found: ID {asset_id}")
        raise HTTPException(status_code=404, detail="Asset not found")
    
    try:
        data_service.mark_asset_deleted(asset_id)
        logger.info(f"Successfully deleted asset: {asset.name} (ID: {asset_id})")
        return {"message": "Asset marked as deleted"}
    except Exception as e:
        logger.error(f"Failed to delete asset ID {asset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete asset: {str(e)}") 