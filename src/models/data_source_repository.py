from typing import List, Optional, Dict, Any
from datetime import datetime
from models.data_source import DataSource
from connect_database import session
import logging

logger = logging.getLogger(__name__)

class DataSourceRepository:
    """Repository for managing data sources."""

    def __init__(self):
        self.session = session

    def get_all_data_sources(self) -> List[DataSource]:
        """Get all data sources, excluding deleted ones."""
        query = """
        SELECT id, name, description, system_date, provider, attributes,
               is_deleted, valid_from, valid_to
        FROM data_source
        WHERE is_deleted = false
        ALLOW FILTERING
        """
        rows = self.session.execute(query)
        return [DataSource(
            id=row.id,
            name=row.name,
            description=row.description,
            system_date=row.system_date,
            provider=row.provider,
            attributes=row.attributes or {},
            is_deleted=row.is_deleted,
            valid_from=row.valid_from,
            valid_to=row.valid_to
        ) for row in rows]

    def get_data_source_by_id(self, data_source_id: int) -> Optional[DataSource]:
        """Get data source details by ID, excluding deleted ones."""
        query = """
        SELECT id, name, description, system_date, provider, attributes,
               is_deleted, valid_from, valid_to
        FROM data_source 
        WHERE id = %s
        ALLOW FILTERING
        """
        try:
            rows = list(self.session.execute(query, (data_source_id,)))
            
            # Get the most recent version that is not deleted
            latest_row = None
            for row in rows:
                if not row.is_deleted and (latest_row is None or row.valid_from > latest_row.valid_from):
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

    def get_data_source_by_id_including_deleted(self, data_source_id: int) -> Optional[DataSource]:
        """Get data source details by ID, including deleted ones."""
        query = """
        SELECT id, name, description, system_date, provider, attributes,
               is_deleted, valid_from, valid_to
        FROM data_source 
        WHERE id = %s
        ALLOW FILTERING
        """
        try:
            rows = list(self.session.execute(query, (data_source_id,)))
            
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
        """Mark a data source as deleted by creating a new version."""
        current_data_source = self.get_data_source_by_id(data_source_id)
        if current_data_source and not current_data_source.is_deleted:
            now = datetime.now()
            
            # First, invalidate the current version by setting valid_to
            current_data_source.valid_to = now
            self.save_data_source(current_data_source)
            
            # Then create a new version marked as deleted
            deleted_data_source = DataSource(
                id=current_data_source.id,
                name=current_data_source.name,
                description=current_data_source.description,
                system_date=now,
                provider=current_data_source.provider,
                attributes=current_data_source.attributes,
                is_deleted=True,
                valid_from=now,
                valid_to=None
            )
            self.save_data_source(deleted_data_source)
            logger.info(f"Successfully marked data source as deleted: {current_data_source.name} (ID: {data_source_id})")
        else:
            logger.warning(f"Attempted to delete non-existent or already deleted data source: ID {data_source_id}")

    def resurrect_data_source(self, data_source_id: int, updated_data: Dict[str, Any]) -> DataSource:
        """Resurrect a deleted data source by creating a new active version."""
        now = datetime.now()
        
        # Create new active version
        resurrected_data_source = DataSource(
            id=data_source_id,
            name=updated_data.get('name', ''),
            description=updated_data.get('description', ''),
            system_date=now,
            provider=updated_data.get('provider', ''),
            attributes=updated_data.get('attributes', {}),
            is_deleted=False,
            valid_from=now,
            valid_to=None
        )
        self.save_data_source(resurrected_data_source)
        logger.info(f"Successfully resurrected data source: {resurrected_data_source.name} (ID: {data_source_id})")
        return resurrected_data_source

    def get_next_id(self) -> int:
        """Get next available data source ID."""
        query = "SELECT MAX(id) FROM data_source"
        row = self.session.execute(query).one()
        return (row[0] or 0) + 1