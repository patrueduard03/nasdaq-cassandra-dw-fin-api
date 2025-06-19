from typing import List, Optional, Dict, Any
from datetime import datetime
from models.data_source import DataSource
from connect_database import session
from constants import FAR_FUTURE_DATE
import logging

logger = logging.getLogger(__name__)

# Query constants
DATA_SOURCE_SELECT_ALL_QUERY = """
SELECT id, name, description, system_date, provider, attributes,
       is_deleted, valid_from, valid_to
FROM data_source
ALLOW FILTERING
"""

DATA_SOURCE_SELECT_BY_ID_QUERY = """
SELECT id, name, description, system_date, provider, attributes,
       is_deleted, valid_from, valid_to
FROM data_source 
WHERE id = %s
ALLOW FILTERING
"""

# Optimized query for current/latest versions using far-future date pattern
DATA_SOURCE_SELECT_CURRENT_VERSIONS_QUERY = """
SELECT id, name, description, system_date, provider, attributes,
       is_deleted, valid_from, valid_to
FROM data_source
WHERE valid_to = %s
ALLOW FILTERING
"""

DATA_SOURCE_SELECT_CURRENT_ACTIVE_QUERY = """
SELECT id, name, description, system_date, provider, attributes,
       is_deleted, valid_from, valid_to
FROM data_source
WHERE valid_to = %s AND is_deleted = false
ALLOW FILTERING
"""

class DataSourceRepository:
    """Repository for managing data sources."""

    def __init__(self):
        self.session = session

    def get_all_data_sources(self) -> List[DataSource]:
        """Get all data sources, excluding deleted ones."""
        # Get ALL records (including deleted ones) to properly determine latest state
        rows = self.session.execute(DATA_SOURCE_SELECT_ALL_QUERY)
        
        # Group by data source ID and get only currently valid data sources
        current_time = datetime.now()
        data_source_dict = {}
        
        for row in rows:
            # Check if this record is currently valid
            is_currently_valid = (
                row.valid_from <= current_time and 
                (row.valid_to is None or row.valid_to == FAR_FUTURE_DATE or row.valid_to > current_time)
            )
            
            if is_currently_valid:
                if row.id not in data_source_dict or row.valid_from > data_source_dict[row.id].valid_from:
                    data_source_dict[row.id] = DataSource(
                        id=row.id,
                        name=row.name,
                        description=row.description,
                        system_date=row.system_date,
                        provider=row.provider,
                        attributes=row.attributes or {},
                        is_deleted=row.is_deleted,
                        valid_from=row.valid_from,
                        valid_to=row.valid_to
                    )
        
        # Filter out data sources whose latest version is a deletion marker
        active_data_sources = []
        for data_source in data_source_dict.values():
            if not data_source.is_deleted:  # Only include non-deleted latest versions
                active_data_sources.append(data_source)
        
        return active_data_sources

    def get_all_data_sources_including_deleted(self) -> List[DataSource]:
        """Get all data sources including deleted ones (admin only) - returns ALL versions."""
        rows = self.session.execute(DATA_SOURCE_SELECT_ALL_QUERY)
        
        # Return ALL versions, sorted by ID and then by valid_from (newest first)
        all_data_sources = []
        for row in rows:
            all_data_sources.append(DataSource(
                id=row.id,
                name=row.name,
                description=row.description,
                system_date=row.system_date,
                provider=row.provider,
                attributes=row.attributes or {},
                is_deleted=row.is_deleted,
                valid_from=row.valid_from,
                valid_to=row.valid_to
            ))
        
        # Sort by ID first, then by valid_from (newest first for each ID)
        all_data_sources.sort(key=lambda x: (x.id, -x.valid_from.timestamp()))
        return all_data_sources

    def get_data_source_by_id(self, data_source_id: int) -> Optional[DataSource]:
        """Get data source details by ID, excluding deleted ones."""
        try:
            rows = list(self.session.execute(DATA_SOURCE_SELECT_BY_ID_QUERY, (data_source_id,)))
            
            # Get the most recent version (regardless of deletion status) to check current state
            current_time = datetime.now()
            latest_row = None
            
            for row in rows:
                # Check if this record is currently valid
                is_currently_valid = (
                    row.valid_from <= current_time and 
                    (row.valid_to is None or row.valid_to == FAR_FUTURE_DATE or row.valid_to > current_time)
                )
                
                if is_currently_valid:
                    if latest_row is None or row.valid_from > latest_row.valid_from:
                        latest_row = row
            
            # If the latest version is a deletion marker, return None (data source is deleted)
            if latest_row and latest_row.is_deleted:
                return None
                    
            if latest_row:
                return DataSource(
                    id=latest_row.id,
                    name=latest_row.name,
                    description=latest_row.description,
                    system_date=latest_row.system_date,
                    provider=latest_row.provider,
                    attributes=latest_row.attributes or {},
                    is_deleted=latest_row.is_deleted,
                    valid_from=latest_row.valid_from,
                    valid_to=latest_row.valid_to
                )
        except Exception:
            pass
        return None

    def get_data_source_by_id_including_deleted(self, data_source_id: int) -> Optional[DataSource]:
        """Get data source details by ID, including deleted ones."""
        try:
            rows = list(self.session.execute(DATA_SOURCE_SELECT_BY_ID_QUERY, (data_source_id,)))
            
            # Get the most recent version (highest valid_from)
            latest_row = None
            for row in rows:
                if latest_row is None or row.valid_from > latest_row.valid_from:
                    latest_row = row
                    
            if latest_row:
                return DataSource(
                    id=latest_row.id,
                    name=latest_row.name,
                    description=latest_row.description,
                    system_date=latest_row.system_date,
                    provider=latest_row.provider,
                    attributes=latest_row.attributes or {},
                    is_deleted=latest_row.is_deleted,
                    valid_from=latest_row.valid_from,
                    valid_to=latest_row.valid_to
                )
        except Exception:
            pass
        return None

    def get_by_provider(self, provider: str) -> Optional[DataSource]:
        """Get data source by provider name, excluding deleted ones."""
        query = """
        SELECT id, name, description, system_date, provider, attributes,
               is_deleted, valid_from, valid_to
        FROM data_source 
        WHERE provider = %s AND is_deleted = false
        ALLOW FILTERING
        """
        try:
            rows = list(self.session.execute(query, (provider,)))
            if rows:
                row = rows[0]
                return DataSource(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                    system_date=row.system_date,
                    provider=row.provider,
                    attributes=row.attributes or {},
                    is_deleted=row.is_deleted,
                    valid_from=row.valid_from,
                    valid_to=row.valid_to
                )
        except Exception:
            pass
        return None

    def save_data_source(self, data_source: DataSource) -> None:
        """Save a new data source."""
        query = """
        INSERT INTO data_source (
            id, name, description, system_date, provider, attributes,
            is_deleted, valid_from, valid_to
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            # Ensure attributes is never None when saving
            attributes_to_save = data_source.attributes if data_source.attributes is not None else {}
            
            self.session.execute(query, (
                data_source.id,
                data_source.name,
                data_source.description,
                data_source.system_date,
                data_source.provider,
                attributes_to_save,
                data_source.is_deleted,
                data_source.valid_from,
                data_source.valid_to
            ))
            logger.info(f"Successfully saved data source: {data_source.name} (Provider: {data_source.provider})")
        except Exception as e:
            logger.error(f"Failed to save data source {data_source.name}: {str(e)}")
            raise

    def mark_deleted(self, data_source_id: int) -> None:
        """Mark a data source as deleted by creating a deletion marker record (temporal paradigm)."""
        current_data_source = self.get_data_source_by_id(data_source_id)
        if not current_data_source or current_data_source.is_deleted:
            logger.warning(f"Attempted to delete non-existent or already deleted data source: ID {data_source_id}")
            return
            
        now = datetime.now()
        
        # Check if there's already a current deletion marker
        # Get all records for this data source and check for active deletion marker
        all_records = list(self.session.execute(DATA_SOURCE_SELECT_BY_ID_QUERY, (data_source_id,)))
        has_active_deletion = any(record.is_deleted and 
                                (record.valid_to is None or record.valid_to == FAR_FUTURE_DATE) 
                                for record in all_records)
        
        if has_active_deletion:
            logger.warning(f"Current deletion marker already exists for data source ID {data_source_id}")
            return
        
        # Step 1: Close the current active record by setting valid_to
        closed_current_data_source = DataSource(
            id=current_data_source.id,
            name=current_data_source.name,
            description=current_data_source.description,
            system_date=current_data_source.system_date,  # Keep original system_date
            provider=current_data_source.provider,
            attributes=current_data_source.attributes,
            is_deleted=current_data_source.is_deleted,
            valid_from=current_data_source.valid_from,
            valid_to=now  # Close this version at deletion time
        )
        self.save_data_source(closed_current_data_source)
        
        # Step 2: Create the deletion marker record with far-future valid_to
        deleted_data_source = DataSource(
            id=current_data_source.id,
            name=current_data_source.name,
            description=current_data_source.description,
            system_date=now,  # New system_date for the deletion record
            provider=current_data_source.provider,
            attributes=current_data_source.attributes,
            is_deleted=True,
            valid_from=now,  # Deletion marker starts from now
            valid_to=FAR_FUTURE_DATE   # Current deletion marker uses far-future date
        )
        self.save_data_source(deleted_data_source)
        logger.info(f"Successfully marked data source as deleted: {current_data_source.name} (ID: {data_source_id})")

    def resurrect_data_source(self, data_source_id: int, updated_data: Dict[str, Any]) -> DataSource:
        """Resurrect a deleted data source by creating a new active version."""
        # Check if data source exists and is currently deleted
        current_data_source = self.get_data_source_by_id_including_deleted(data_source_id)
        if not current_data_source or not current_data_source.is_deleted:
            raise ValueError(f"Cannot resurrect - data source not found or is not deleted: ID {data_source_id}")
        
        now = datetime.now()
        
        # Step 1: Close the current deletion marker by setting valid_to
        closed_deletion_marker = DataSource(
            id=current_data_source.id,
            name=current_data_source.name,
            description=current_data_source.description,
            system_date=current_data_source.system_date,  # Keep original system_date
            provider=current_data_source.provider,
            attributes=current_data_source.attributes,
            is_deleted=True,  # Still a deletion marker, just closed
            valid_from=current_data_source.valid_from,
            valid_to=now  # Close the deletion marker
        )
        self.save_data_source(closed_deletion_marker)
        
        # Step 2: Create new active version with far-future valid_to
        resurrected_data_source = DataSource(
            id=data_source_id,  # Keep the same ID to maintain relationships
            name=updated_data.get('name', current_data_source.name),
            description=updated_data.get('description', current_data_source.description),
            system_date=now,
            provider=updated_data.get('provider', current_data_source.provider),
            attributes=updated_data.get('attributes', current_data_source.attributes),
            is_deleted=False,
            valid_from=now,
            valid_to=FAR_FUTURE_DATE  # Current version uses far-future date
        )
        self.save_data_source(resurrected_data_source)
        logger.info(f"Successfully resurrected data source: {resurrected_data_source.name} (ID: {data_source_id})")
        return resurrected_data_source

    def update_data_source(self, data_source_id: int, updated_data: Dict[str, Any]) -> DataSource:
        """Update a data source by creating a new version (temporal database pattern)."""
        current_data_source = self.get_data_source_by_id(data_source_id)
        if not current_data_source or current_data_source.is_deleted:
            raise ValueError(f"Cannot update - data source not found or is deleted: ID {data_source_id}")
        
        now = datetime.now()
        
        # Step 1: Close the current active record by setting valid_to
        # This is necessary for proper temporal querying
        closed_current_data_source = DataSource(
            id=current_data_source.id,
            name=current_data_source.name,
            description=current_data_source.description,
            system_date=current_data_source.system_date,  # Keep original system_date
            provider=current_data_source.provider,
            attributes=current_data_source.attributes,
            is_deleted=current_data_source.is_deleted,
            valid_from=current_data_source.valid_from,
            valid_to=now  # Close this version at update time
        )
        self.save_data_source(closed_current_data_source)
        
        # Step 2: Create the new version with far-future valid_to
        updated_data_source = DataSource(
            id=current_data_source.id,  # Keep the same ID
            name=updated_data.get('name', current_data_source.name),
            description=updated_data.get('description', current_data_source.description),
            system_date=now,
            provider=updated_data.get('provider', current_data_source.provider),
            attributes=updated_data.get('attributes', current_data_source.attributes),
            is_deleted=False,
            valid_from=now,
            valid_to=FAR_FUTURE_DATE  # Current version uses far-future date
        )
        self.save_data_source(updated_data_source)
        logger.info(f"Successfully updated data source: {updated_data_source.name} (ID: {data_source_id})")
        return updated_data_source

    def get_data_source_at_date(self, data_source_id: int, target_date: datetime) -> Optional[DataSource]:
        """Get data source state as it existed at a specific date (point-in-time query)."""
        rows = self.session.execute(DATA_SOURCE_SELECT_BY_ID_QUERY, (data_source_id,))
        
        # Find the version that was valid at the target date
        for row in rows:
            if (row.valid_from <= target_date and 
                (row.valid_to is None or row.valid_to == FAR_FUTURE_DATE or row.valid_to > target_date)):
                return DataSource(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                    system_date=row.system_date,
                    provider=row.provider,
                    attributes=row.attributes or {},
                    is_deleted=row.is_deleted,
                    valid_from=row.valid_from,
                    valid_to=row.valid_to
                )
        return None

    def get_next_id(self) -> int:
        """Get next available data source ID."""
        query = "SELECT MAX(id) FROM data_source"
        row = self.session.execute(query).one()
        return (row[0] or 0) + 1