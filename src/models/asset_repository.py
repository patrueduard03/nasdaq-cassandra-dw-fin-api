from typing import List, Optional
from datetime import datetime
from models.asset import Asset
from connect_database import session
import logging

logger = logging.getLogger(__name__)

class AssetRepository:
    """Repository for managing financial assets with temporal support."""

    def __init__(self):
        self.session = session

    def get_all_assets(self) -> List[Asset]:
        """Get all financial assets, excluding deleted ones."""
        query = """
        SELECT id, name, description, system_date, is_deleted,
               valid_from, valid_to, attributes 
        FROM asset
        WHERE is_deleted = false
        ALLOW FILTERING
        """
        rows = self.session.execute(query)
        return [Asset(
            id=row.id,
            name=row.name,
            description=row.description,
            system_date=row.system_date,
            is_deleted=row.is_deleted,
            valid_from=row.valid_from,
            valid_to=row.valid_to,
            attributes=row.attributes
        ) for row in rows]

    def get_asset_by_id(self, asset_id: int) -> Optional[Asset]:
        """Get asset details by ID, excluding deleted assets."""
        query = """
        SELECT id, name, description, system_date, is_deleted,
               valid_from, valid_to, attributes 
        FROM asset 
        WHERE id = %s
        ALLOW FILTERING
        """
        rows = self.session.execute(query, (asset_id,))
        
        # Get the most recent version (highest valid_from) that is not deleted
        latest_row = None
        for row in rows:
            if not row.is_deleted and (latest_row is None or row.valid_from > latest_row.valid_from):
                latest_row = row
                
        if latest_row:
            return Asset(
                id=latest_row.id,
                name=latest_row.name,
                description=latest_row.description,
                system_date=latest_row.system_date,
                is_deleted=latest_row.is_deleted,
                valid_from=latest_row.valid_from,
                valid_to=latest_row.valid_to,
                attributes=latest_row.attributes
            )
        return None

    def save_asset(self, asset: Asset) -> None:
        """Save a new asset version."""
        query = """
        INSERT INTO asset (
            id, name, description, system_date, is_deleted,
            valid_from, valid_to, attributes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            self.session.execute(query, (
                asset.id,
                asset.name,
                asset.description,
                asset.system_date,
                asset.is_deleted,
                asset.valid_from,
                asset.valid_to,
                asset.attributes
            ))
            logger.info(f"Successfully saved asset: {asset.name} (ID: {asset.id})")
        except Exception as e:
            logger.error(f"Failed to save asset {asset.name}: {str(e)}")
            raise

    def mark_deleted(self, asset_id: int) -> None:
        """Mark an asset as deleted by creating a new version."""
        current_asset = self.get_asset_by_id(asset_id)
        if current_asset and not current_asset.is_deleted:
            now = datetime.now()
            
            # First, invalidate the current version by setting valid_to
            current_asset.valid_to = now
            self.save_asset(current_asset)
            
            # Then create a new version marked as deleted
            deleted_asset = Asset(
                id=current_asset.id,
                name=current_asset.name,
                description=current_asset.description,
                system_date=now,
                is_deleted=True,
                valid_from=now,
                valid_to=None,
                attributes=current_asset.attributes
            )
            self.save_asset(deleted_asset)
            logger.info(f"Successfully marked asset as deleted: {current_asset.name} (ID: {asset_id})")
        else:
            logger.warning(f"Attempted to delete non-existent or already deleted asset: ID {asset_id}")

    def get_next_id(self) -> int:
        """Get next available asset ID."""
        query = "SELECT MAX(id) FROM asset"
        row = self.session.execute(query).one()
        return (row[0] or 0) + 1