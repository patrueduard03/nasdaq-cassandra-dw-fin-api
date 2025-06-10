from typing import List, Optional
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
        """Get all data sources."""
        query = """
        SELECT id, name, description, system_date, provider, attributes 
        FROM data_source
        """
        rows = self.session.execute(query)
        return [DataSource(
            id=row.id,
            name=row.name,
            description=row.description,
            system_date=row.system_date,
            provider=row.provider,
            attributes=row.attributes
        ) for row in rows]

    def get_data_source_by_id(self, data_source_id: int) -> Optional[DataSource]:
        """Get data source details by ID."""
        query = """
        SELECT id, name, description, system_date, provider, attributes 
        FROM data_source 
        WHERE id = %s
        """
        try:
            rows = list(self.session.execute(query, (data_source_id,)))
            if rows:
                row = rows[0]
                return DataSource(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                    system_date=row.system_date,
                    provider=row.provider,
                    attributes=row.attributes
                )
        except Exception:
            pass
        return None

    def get_by_provider(self, provider: str) -> Optional[DataSource]:
        """Get data source by provider name."""
        query = """
        SELECT id, name, description, system_date, provider, attributes 
        FROM data_source 
        WHERE provider = %s
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
                    attributes=row.attributes
                )
        except Exception:
            pass
        return None

    def save_data_source(self, data_source: DataSource) -> None:
        """Save a new data source."""
        query = """
        INSERT INTO data_source (
            id, name, description, system_date, provider, attributes
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        try:
            self.session.execute(query, (
                data_source.id,
                data_source.name,
                data_source.description,
                data_source.system_date,
                data_source.provider,
                data_source.attributes
            ))
            logger.info(f"Successfully saved data source: {data_source.name} (Provider: {data_source.provider})")
        except Exception as e:
            logger.error(f"Failed to save data source {data_source.name}: {str(e)}")
            raise

    def get_next_id(self) -> int:
        """Get next available data source ID."""
        query = "SELECT MAX(id) FROM data_source"
        row = self.session.execute(query).one()
        return (row[0] or 0) + 1 