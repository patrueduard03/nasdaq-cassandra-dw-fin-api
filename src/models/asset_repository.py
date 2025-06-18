from typing import List, Optional, Dict, Any
from datetime import datetime
from models.asset import Asset
from connect_database import session
import logging

logger = logging.getLogger(__name__)

# Temporal database constants
FAR_FUTURE_DATE = datetime(9999, 12, 31, 23, 59, 59)  # For current versions

# Query constants
ASSET_SELECT_ALL_QUERY = """
SELECT id, name, description, system_date, is_deleted,
       valid_from, valid_to, attributes 
FROM asset
WHERE is_deleted = false
ALLOW FILTERING
"""

ASSET_SELECT_ALL_INCLUDING_DELETED_QUERY = """
SELECT id, name, description, system_date, is_deleted,
       valid_from, valid_to, attributes 
FROM asset
ALLOW FILTERING
"""

ASSET_SELECT_BY_ID_QUERY = """
SELECT id, name, description, system_date, is_deleted,
       valid_from, valid_to, attributes 
FROM asset 
WHERE id = %s
ALLOW FILTERING
"""

ASSET_GET_ACTIVE_BY_SYMBOL_QUERY = """
SELECT id, name, description, system_date, is_deleted,
       valid_from, valid_to, attributes 
FROM asset
WHERE is_deleted = false
ALLOW FILTERING
"""

# Optimized query for current/latest versions using far-future date pattern
ASSET_SELECT_CURRENT_VERSIONS_QUERY = """
SELECT id, name, description, system_date, is_deleted,
       valid_from, valid_to, attributes 
FROM asset
WHERE valid_to = %s
ALLOW FILTERING
"""

ASSET_SELECT_CURRENT_ACTIVE_QUERY = """
SELECT id, name, description, system_date, is_deleted,
       valid_from, valid_to, attributes 
FROM asset
WHERE valid_to = %s AND is_deleted = false
ALLOW FILTERING
"""

class AssetRepository:
    """Repository for managing financial assets with temporal support."""

    def __init__(self):
        self.session = session

    def get_all_assets(self) -> List[Asset]:
        """Get all financial assets, excluding deleted ones."""
        # Get ALL records (including deleted ones) to properly determine latest state
        rows = self.session.execute(ASSET_SELECT_ALL_INCLUDING_DELETED_QUERY)
        
        # Group by asset ID and get only currently valid assets
        current_time = datetime.now()
        asset_dict = {}
        
        for row in rows:
            # Check if this record is currently valid
            is_currently_valid = (
                row.valid_from <= current_time and 
                (row.valid_to is None or row.valid_to == FAR_FUTURE_DATE or row.valid_to > current_time)
            )
            
            if is_currently_valid:
                if row.id not in asset_dict or row.valid_from > asset_dict[row.id].valid_from:
                    asset_dict[row.id] = Asset(
                        id=row.id,
                        name=row.name,
                        description=row.description,
                        system_date=row.system_date,
                        is_deleted=row.is_deleted,
                        valid_from=row.valid_from,
                        valid_to=row.valid_to,
                        attributes=row.attributes
                    )
        
        # Filter out assets whose latest version is a deletion marker
        active_assets = []
        for asset in asset_dict.values():
            if not asset.is_deleted:  # Only include non-deleted latest versions
                active_assets.append(asset)
        
        return active_assets

    def get_all_assets_including_deleted(self) -> List[Asset]:
        """Get all financial assets including deleted ones (admin only) - returns ALL versions."""
        rows = self.session.execute(ASSET_SELECT_ALL_INCLUDING_DELETED_QUERY)
        
        # Return ALL versions, sorted by ID and then by valid_from (newest first)
        all_assets = []
        for row in rows:
            all_assets.append(Asset(
                id=row.id,
                name=row.name,
                description=row.description,
                system_date=row.system_date,
                is_deleted=row.is_deleted,
                valid_from=row.valid_from,
                valid_to=row.valid_to,
                attributes=row.attributes
            ))
        
        # Sort by ID first, then by valid_from (newest first for each ID)
        # This ensures proper temporal ordering for admin view
        all_assets.sort(key=lambda x: (x.id, -x.valid_from.timestamp()))
        return all_assets

    def get_asset_by_id(self, asset_id: int) -> Optional[Asset]:
        """Get asset details by ID, excluding deleted assets."""
        rows = self.session.execute(ASSET_SELECT_BY_ID_QUERY, (asset_id,))

        # Get the most recent version (regardless of deletion status) to check current state
        current_time = datetime.now()
        latest_row = None
        
        for row in rows:
            # Check if this record is currently valid (valid_from <= now < valid_to OR valid_to is NULL)
            is_currently_valid = (
                row.valid_from <= current_time and 
                (row.valid_to is None or row.valid_to == FAR_FUTURE_DATE or row.valid_to > current_time)
            )
            
            if is_currently_valid:
                if latest_row is None or row.valid_from > latest_row.valid_from:
                    latest_row = row
        
        # If the latest version is a deletion marker, return None (asset is deleted)
        if latest_row and latest_row.is_deleted:
            return None
                
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

    def get_asset_by_id_including_deleted(self, asset_id: int) -> Optional[Asset]:
        """Get asset details by ID, including deleted assets."""
        rows = self.session.execute(ASSET_SELECT_BY_ID_QUERY, (asset_id,))
        
        # Get the most recent version (highest valid_from)
        latest_row = None
        for row in rows:
            if latest_row is None or row.valid_from > latest_row.valid_from:
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
        """Mark an asset as deleted by creating a deletion marker record (temporal paradigm)."""
        current_asset = self.get_asset_by_id(asset_id)
        if not current_asset or current_asset.is_deleted:
            logger.warning(f"Attempted to delete non-existent or already deleted asset: ID {asset_id}")
            return
            
        now = datetime.now()
        
        # Check if there's already a current deletion marker
        # Get all records for this asset and check for active deletion marker
        all_records = list(self.session.execute(ASSET_SELECT_BY_ID_QUERY, (asset_id,)))
        has_active_deletion = any(record.is_deleted and 
                                (record.valid_to is None or record.valid_to == FAR_FUTURE_DATE) 
                                for record in all_records)
        
        if has_active_deletion:
            logger.warning(f"Current deletion marker already exists for asset ID {asset_id}")
            return
        
        # Step 1: Close the current active record by setting valid_to
        closed_current_asset = Asset(
            id=current_asset.id,
            name=current_asset.name,
            description=current_asset.description,
            system_date=current_asset.system_date,  # Keep original system_date
            is_deleted=current_asset.is_deleted,
            valid_from=current_asset.valid_from,
            valid_to=now,  # Close this version at deletion time
            attributes=current_asset.attributes
        )
        self.save_asset(closed_current_asset)
        
        # Step 2: Create the deletion marker record with far-future valid_to
        deleted_asset = Asset(
            id=current_asset.id,
            name=current_asset.name,
            description=current_asset.description,
            system_date=now,  # New system_date for the deletion record
            is_deleted=True,
            valid_from=now,  # Deletion marker starts from now
            valid_to=FAR_FUTURE_DATE,   # Current deletion marker uses far-future date
            attributes=current_asset.attributes
        )
        self.save_asset(deleted_asset)
        logger.info(f"Successfully marked asset as deleted: {current_asset.name} (ID: {asset_id})")

    def get_next_id(self) -> int:
        """Get next available asset ID."""
        query = "SELECT MAX(id) FROM asset"
        row = self.session.execute(query).one()
        return (row[0] or 0) + 1

    def get_active_asset_by_symbol(self, symbol: str) -> Optional[Asset]:
        """Get an active (non-deleted) asset by symbol."""
        query = """
        SELECT id, name, description, system_date, is_deleted,
               valid_from, valid_to, attributes 
        FROM asset
        WHERE is_deleted = false
        ALLOW FILTERING
        """
        rows = self.session.execute(query)
        
        # Find the most recent active version with matching symbol
        for row in rows:
            if (row.attributes and 
                row.attributes.get('symbol', '').upper() == symbol.upper()):
                return Asset(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                    system_date=row.system_date,
                    is_deleted=row.is_deleted,
                    valid_from=row.valid_from,
                    valid_to=row.valid_to,
                    attributes=row.attributes
                )
        return None

    def get_deleted_asset_by_symbol(self, symbol: str) -> Optional[Asset]:
        """Get a deleted asset by symbol for resurrection purposes."""
        query = """
        SELECT id, name, description, system_date, is_deleted,
               valid_from, valid_to, attributes 
        FROM asset
        ALLOW FILTERING
        """
        rows = self.session.execute(query)
        
        # Find the most recent deleted version with matching symbol
        latest_deleted = None
        for row in rows:
            if (row.is_deleted and 
                row.attributes and 
                row.attributes.get('symbol', '').upper() == symbol.upper()):
                if latest_deleted is None or row.valid_from > latest_deleted.valid_from:
                    latest_deleted = row
                    
        if latest_deleted:
            return Asset(
                id=latest_deleted.id,
                name=latest_deleted.name,
                description=latest_deleted.description,
                system_date=latest_deleted.system_date,
                is_deleted=latest_deleted.is_deleted,
                valid_from=latest_deleted.valid_from,
                valid_to=latest_deleted.valid_to,
                attributes=latest_deleted.attributes
            )
        return None

    def resurrect_asset(self, asset_id: int, updated_data: Dict[str, Any]) -> Asset:
        """Resurrect a deleted asset by creating a new active version."""
        # Check if asset exists and is currently deleted
        current_asset = self.get_asset_by_id_including_deleted(asset_id)
        if not current_asset or not current_asset.is_deleted:
            raise ValueError(f"Cannot resurrect - asset not found or is not deleted: ID {asset_id}")
        
        now = datetime.now()
        
        # Step 1: Close the current deletion marker by setting valid_to
        closed_deletion_marker = Asset(
            id=current_asset.id,
            name=current_asset.name,
            description=current_asset.description,
            system_date=current_asset.system_date,  # Keep original system_date
            is_deleted=True,  # Still a deletion marker, just closed
            valid_from=current_asset.valid_from,
            valid_to=now,  # Close the deletion marker
            attributes=current_asset.attributes
        )
        self.save_asset(closed_deletion_marker)
        
        # Step 2: Create new active version with far-future valid_to
        resurrected_asset = Asset(
            id=asset_id,  # Keep the same ID to maintain time series links
            name=updated_data.get('name', current_asset.name),
            description=updated_data.get('description', current_asset.description),
            system_date=now,
            is_deleted=False,
            valid_from=now,
            valid_to=FAR_FUTURE_DATE,  # Current version uses far-future date
            attributes=updated_data.get('attributes', current_asset.attributes)
        )
        self.save_asset(resurrected_asset)
        logger.info(f"Successfully resurrected asset: {resurrected_asset.name} (ID: {asset_id})")
        return resurrected_asset

    def update_asset(self, asset_id: int, updated_data: Dict[str, Any]) -> Asset:
        """Update an asset by creating a new version (temporal database pattern)."""
        current_asset = self.get_asset_by_id(asset_id)
        if not current_asset or current_asset.is_deleted:
            raise ValueError(f"Cannot update - asset not found or is deleted: ID {asset_id}")
        
        now = datetime.now()
        
        # Step 1: Close the current active record by setting valid_to
        # This is necessary for proper temporal querying
        closed_current_asset = Asset(
            id=current_asset.id,
            name=current_asset.name,
            description=current_asset.description,
            system_date=current_asset.system_date,  # Keep original system_date
            is_deleted=current_asset.is_deleted,
            valid_from=current_asset.valid_from,
            valid_to=now,  # Close this version at update time
            attributes=current_asset.attributes
        )
        self.save_asset(closed_current_asset)
        
        # Step 2: Create the new version with far-future valid_to
        updated_asset = Asset(
            id=current_asset.id,  # Keep the same ID
            name=updated_data.get('name', current_asset.name),
            description=updated_data.get('description', current_asset.description),
            system_date=now,
            is_deleted=False,
            valid_from=now,
            valid_to=FAR_FUTURE_DATE,  # Current version uses far-future date
            attributes=updated_data.get('attributes', current_asset.attributes)
        )
        self.save_asset(updated_asset)
        logger.info(f"Successfully updated asset: {updated_asset.name} (ID: {asset_id})")
        return updated_asset

    def get_asset_at_date(self, asset_id: int, target_date: datetime) -> Optional[Asset]:
        """Get asset state as it existed at a specific date (point-in-time query)."""
        query = """
        SELECT id, name, description, system_date, is_deleted,
               valid_from, valid_to, attributes 
        FROM asset 
        WHERE id = %s
        ALLOW FILTERING
        """
        rows = self.session.execute(query, (asset_id,))
        
        # Find the version that was valid at the target date
        for row in rows:
            if (row.valid_from <= target_date and 
                (row.valid_to is None or row.valid_to == FAR_FUTURE_DATE or row.valid_to > target_date)):
                return Asset(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                    system_date=row.system_date,
                    is_deleted=row.is_deleted,
                    valid_from=row.valid_from,
                    valid_to=row.valid_to,
                    attributes=row.attributes
                )
        return None