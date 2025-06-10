from models.data import Data
from connect_database import session
from typing import List, Optional, Any
from datetime import datetime, date
from cassandra.util import Date as CassandraDate
import logging

logger = logging.getLogger(__name__)

class DataRepository:
    def __init__(self, session_=None):
        self.session = session_ or session

    def get_time_series_data(
        self,
        asset_id: int,
        data_source_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Data]:
        """Return time-series data for a specified asset and data source, excluding deleted assets."""
        
        # First check if asset exists and is not deleted
        asset_query = """
        SELECT id, is_deleted FROM asset 
        WHERE id = %s AND is_deleted = false
        ALLOW FILTERING
        """
        asset_rows = self.session.execute(asset_query, (asset_id,))
        if not list(asset_rows):
            logger.warning(f"Asset {asset_id} not found or is deleted")
            return []
        
        query = """
        SELECT asset_id, data_source_id, business_date, system_date,
               values_double, values_int, values_text
        FROM data 
        WHERE asset_id=%s AND data_source_id=%s
        """
        params: List[Any] = [asset_id, data_source_id]
        
        if start_date:
            query += " AND business_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND business_date <= %s"
            params.append(end_date)
            
        query += " ORDER BY business_date DESC, system_date DESC ALLOW FILTERING"
        
        rows = self.session.execute(query, params)
        return [
            Data(
                asset_id=row.asset_id,
                data_source_id=row.data_source_id,
                business_date=row.business_date.date() if isinstance(row.business_date, CassandraDate) else row.business_date,
                system_date=row.system_date,
                values_double=row.values_double or {},
                values_int=row.values_int or {},
                values_text=row.values_text or {}
            ) for row in rows
        ]

    def save(self, data: Data):
        """Save time series data"""
        query = """
        INSERT INTO data (
            asset_id, data_source_id, business_date, system_date,
            values_double, values_int, values_text
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        # Convert date to string format for Cassandra
        business_date_str = data.business_date.strftime('%Y-%m-%d') if isinstance(data.business_date, date) else data.business_date
        
        try:
            self.session.execute(query, (
                data.asset_id,
                data.data_source_id,
                business_date_str,
                data.system_date,
                data.values_double,
                data.values_int,
                data.values_text
            ))
            logger.debug(f"Successfully saved data record for asset_id={data.asset_id}, date={business_date_str}")
        except Exception as e:
            logger.error(f"Failed to save data record for asset_id={data.asset_id}, date={business_date_str}: {str(e)}")
            raise 