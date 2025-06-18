from fastapi import APIRouter, HTTPException
from typing import List
import logging

from ..models import AssetResponse, AssetCreate
from services.data_service import DataService

# Constants
ERROR_ASSET_NOT_FOUND = "Asset not found"
ERROR_ASSET_CREATION_FAILED = "Failed to create asset"
ERROR_ASSET_DELETION_FAILED = "Failed to delete asset"
ERROR_ASSET_RESURRECTION_FAILED = "Failed to resurrect asset"

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
        raise HTTPException(status_code=404, detail=ERROR_ASSET_NOT_FOUND)
    logger.info(f"Retrieved asset: {asset.name} (ID: {asset_id})")
    return asset

@router.post("", response_model=AssetResponse)
async def create_asset(asset: AssetCreate):
    """Create a new asset"""
    logger.info(f"Creating new asset: {asset.name}")
    try:
        created_asset = data_service.create_asset(asset.dict())
        logger.info(f"Successfully created asset: {asset.name} (ID: {created_asset.id})")
        return created_asset
    except ValueError as e:
        logger.warning(f"Asset creation failed: {str(e)}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create asset {asset.name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{ERROR_ASSET_CREATION_FAILED}: {str(e)}")

@router.post("/{asset_id}/resurrect", response_model=AssetResponse)
async def resurrect_asset(asset_id: int, asset: AssetCreate):
    """Resurrect a previously deleted asset"""
    logger.info(f"Attempting to resurrect asset with ID: {asset_id}")
    
    # Check if asset exists and is deleted
    existing_asset = data_service.get_asset_by_id_including_deleted(asset_id)
    if not existing_asset:
        logger.warning(f"Asset not found for resurrection: ID {asset_id}")
        raise HTTPException(status_code=404, detail=ERROR_ASSET_NOT_FOUND)
    
    if not existing_asset.is_deleted:
        logger.warning(f"Cannot resurrect - asset is not deleted: ID {asset_id}")
        raise HTTPException(status_code=409, detail="Asset is not deleted and cannot be resurrected")
    
    try:
        resurrected_asset = data_service.asset_repo.resurrect_asset(asset_id, asset.dict())
        logger.info(f"Successfully resurrected asset: {resurrected_asset.name} (ID: {asset_id})")
        return resurrected_asset
    except Exception as e:
        logger.error(f"Failed to resurrect asset ID {asset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{ERROR_ASSET_RESURRECTION_FAILED}: {str(e)}")

@router.delete("/{asset_id}")
async def delete_asset(asset_id: int):
    """Mark an asset as deleted"""
    logger.info(f"Attempting to delete asset with ID: {asset_id}")
    asset = data_service.get_asset_by_id(asset_id)
    if not asset:
        logger.warning(f"Cannot delete - asset not found: ID {asset_id}")
        raise HTTPException(status_code=404, detail=ERROR_ASSET_NOT_FOUND)
    
    try:
        data_service.mark_asset_deleted(asset_id)
        logger.info(f"Successfully deleted asset: {asset.name} (ID: {asset_id})")
        return {"message": "Asset marked as deleted"}
    except Exception as e:
        logger.error(f"Failed to delete asset ID {asset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{ERROR_ASSET_DELETION_FAILED}: {str(e)}")