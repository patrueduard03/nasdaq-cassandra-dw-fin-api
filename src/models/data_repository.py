from models.data import Data
from connect_database import session
from constants import FAR_FUTURE_DATE, DEFAULT_BATCH_SIZE
from typing import List, Optional, Any, Tuple
from datetime import datetime, date
from cassandra.query import BatchStatement, SimpleStatement, BatchType
from cassandra.util import Date as CassandraDate
import logging

logger = logging.getLogger(__name__)

class DataRepository:
    def __init__(self, session_=None):
        self.session = session_ or session
        # Prepare statements for better performance
        self._prepare_statements()

    def _prepare_statements(self):
        """Prepare frequently used statements for better performance"""
        self.insert_stmt = self.session.prepare("""
            INSERT INTO data (
                asset_id, data_source_id, business_date, system_date,
                values_double, values_int, values_text,
                is_deleted, valid_from, valid_to
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        
        self.update_valid_to_stmt = self.session.prepare("""
            UPDATE data SET valid_to = ?
            WHERE asset_id = ? AND data_source_id = ? AND business_date = ? AND system_date = ?
        """)
        
        self.check_existing_stmt = self.session.prepare("""
            SELECT asset_id, data_source_id, business_date, system_date
            FROM data 
            WHERE asset_id = ? AND data_source_id = ? AND business_date = ? 
            AND is_deleted = false AND valid_to > ?
            ALLOW FILTERING
        """)

    def get_time_series_data(
        self,
        asset_id: int,
        data_source_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_deleted: bool = False
    ) -> List[Data]:
        """Return time-series data for a specified asset and data source with temporal support."""
        
        # First check if asset exists and is not deleted (unless including deleted)
        if not include_deleted:
            asset_query = """
            SELECT id, is_deleted FROM asset 
            WHERE id = %s AND is_deleted = false
            ALLOW FILTERING
            """
            asset_rows = self.session.execute(asset_query, (asset_id,))
            if not list(asset_rows):
                logger.warning(f"Asset {asset_id} not found or is deleted")
                return []
        
        # Build query with temporal logic - get only current versions unless specifically requesting all
        query = """
        SELECT asset_id, data_source_id, business_date, system_date,
               values_double, values_int, values_text,
               is_deleted, valid_from, valid_to
        FROM data 
        WHERE asset_id=%s AND data_source_id=%s
        """
        params: List[Any] = [asset_id, data_source_id]
        
        # Add deletion filter unless explicitly including deleted data
        if not include_deleted:
            query += " AND is_deleted = false"
        
        if start_date:
            query += " AND business_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND business_date <= %s"
            params.append(end_date)
            
        query += " ORDER BY business_date DESC, system_date DESC ALLOW FILTERING"
        
        rows = self.session.execute(query, params)
        
        # For temporal data, we need to get only the current version of each business_date
        # Group by business_date and get the latest version (highest valid_from)
        if not include_deleted:
            data_by_date = {}
            current_time = datetime.now()
            
            for row in rows:
                # Check if this record is currently valid
                is_currently_valid = (
                    row.valid_from <= current_time and 
                    (row.valid_to is None or row.valid_to > current_time or 
                     str(row.valid_to) == '9999-12-31 23:59:59')  # Handle far-future date
                )
                
                if is_currently_valid:
                    business_date = row.business_date.date() if isinstance(row.business_date, CassandraDate) else row.business_date
                    
                    # Keep only the latest version for each business_date
                    if (business_date not in data_by_date or 
                        row.valid_from > data_by_date[business_date].valid_from):
                        data_by_date[business_date] = Data(
                            asset_id=row.asset_id,
                            data_source_id=row.data_source_id,
                            business_date=business_date,
                            system_date=row.system_date,
                            values_double=row.values_double or {},
                            values_int=row.values_int or {},
                            values_text=row.values_text or {},
                            is_deleted=row.is_deleted or False,
                            valid_from=row.valid_from,
                            valid_to=row.valid_to
                        )
            
            # Return sorted by business_date (most recent first)
            result = list(data_by_date.values())
            result.sort(key=lambda x: x.business_date, reverse=True)
            return result
        else:
            # Include all versions when requested (for admin/temporal analysis)
            return [
                Data(
                    asset_id=row.asset_id,
                    data_source_id=row.data_source_id,
                    business_date=row.business_date.date() if isinstance(row.business_date, CassandraDate) else row.business_date,
                    system_date=row.system_date,
                    values_double=row.values_double or {},
                    values_int=row.values_int or {},
                    values_text=row.values_text or {},
                    is_deleted=row.is_deleted or False,
                    valid_from=row.valid_from,
                    valid_to=row.valid_to
                ) for row in rows
            ]

    def save(self, data: Data):
        """Save time series data"""
        query = """
        INSERT INTO data (
            asset_id, data_source_id, business_date, system_date,
            values_double, values_int, values_text,
            is_deleted, valid_from, valid_to
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                data.values_text,
                data.is_deleted,
                data.valid_from,
                data.valid_to
            ))
            logger.debug(f"Successfully saved data record for asset_id={data.asset_id}, date={business_date_str}")
        except Exception as e:
            logger.error(f"Failed to save data record for asset_id={data.asset_id}, date={business_date_str}: {str(e)}")
            raise

    def get_existing_data_for_date(self, asset_id: int, data_source_id: int, business_date: date) -> Optional[Data]:
        """Check if active data already exists for a specific business date."""
        query = """
        SELECT asset_id, data_source_id, business_date, system_date,
               values_double, values_int, values_text,
               is_deleted, valid_from, valid_to
        FROM data 
        WHERE asset_id=%s AND data_source_id=%s AND business_date=%s 
        AND is_deleted = false
        ALLOW FILTERING
        """
        
        current_time = datetime.now()
        rows = self.session.execute(query, (asset_id, data_source_id, business_date.strftime('%Y-%m-%d')))
        
        # Find the currently active record (if any)
        for row in rows:
            is_currently_valid = (
                row.valid_from <= current_time and 
                (row.valid_to is None or row.valid_to > current_time or 
                 str(row.valid_to) == '9999-12-31 23:59:59')
            )
            
            if is_currently_valid:
                return Data(
                    asset_id=row.asset_id,
                    data_source_id=row.data_source_id,
                    business_date=row.business_date.date() if isinstance(row.business_date, CassandraDate) else row.business_date,
                    system_date=row.system_date,
                    values_double=row.values_double or {},
                    values_int=row.values_int or {},
                    values_text=row.values_text or {},
                    is_deleted=row.is_deleted or False,
                    valid_from=row.valid_from,
                    valid_to=row.valid_to
                )
        
        return None

    def get_data_coverage_period(self, asset_id: int, data_source_id: int) -> Optional[Tuple[date, date]]:
        """Get the current coverage period for an asset's data."""
        query = """
        SELECT MIN(business_date) as min_date, MAX(business_date) as max_date
        FROM data 
        WHERE asset_id=%s AND data_source_id=%s AND is_deleted = false
        ALLOW FILTERING
        """
        
        try:
            rows = self.session.execute(query, (asset_id, data_source_id))
            row = rows.one()
            
            if row and row.min_date and row.max_date:
                min_date = row.min_date.date() if isinstance(row.min_date, CassandraDate) else row.min_date
                max_date = row.max_date.date() if isinstance(row.max_date, CassandraDate) else row.max_date
                return (min_date, max_date)
                
        except Exception as e:
            logger.error(f"Error getting coverage period for asset {asset_id}, data_source {data_source_id}: {str(e)}")
        
        return None

    def save_with_temporal_logic(self, data: Data) -> bool:
        """Save data with proper temporal versioning - close existing records if they exist."""
        try:
            # Check if data already exists for this business date
            existing_data = self.get_existing_data_for_date(
                data.asset_id, data.data_source_id, data.business_date
            )
            
            if existing_data:
                # Close the existing record by updating its valid_to
                self._close_existing_data_record(
                    data.asset_id, data.data_source_id, data.business_date, 
                    existing_data.valid_from, data.valid_from
                )
                logger.info(f"Closed existing data record for asset {data.asset_id}, date {data.business_date}")
            
            # Insert the new record
            self.save(data)
            return True
            
        except Exception as e:
            logger.error(f"Error saving data with temporal logic: {str(e)}")
            return False

    def _close_existing_data_record(self, asset_id: int, data_source_id: int, 
                                   business_date: date, existing_valid_from: datetime, 
                                   new_valid_from: datetime):
        """Close an existing data record by setting its valid_to timestamp."""
        # Create a new record that's identical to the existing one but with valid_to set
        # This maintains the temporal paradigm where records are never updated
        
        # First, get the existing record details
        query = """
        SELECT asset_id, data_source_id, business_date, system_date,
               values_double, values_int, values_text,
               is_deleted, valid_from, valid_to
        FROM data 
        WHERE asset_id=%s AND data_source_id=%s AND business_date=%s 
        AND valid_from=%s
        ALLOW FILTERING
        """
        
        rows = self.session.execute(query, (
            asset_id, data_source_id, business_date.strftime('%Y-%m-%d'), existing_valid_from
        ))
        
        existing_row = rows.one()
        if existing_row:
            # Insert a new record that's identical but with valid_to set to mark it as closed
            close_query = """
            INSERT INTO data (
                asset_id, data_source_id, business_date, system_date,
                values_double, values_int, values_text,
                is_deleted, valid_from, valid_to
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            self.session.execute(close_query, (
                existing_row.asset_id,
                existing_row.data_source_id,
                existing_row.business_date,
                existing_row.system_date,
                existing_row.values_double,
                existing_row.values_int,
                existing_row.values_text,
                existing_row.is_deleted,
                existing_row.valid_from,
                new_valid_from  # Set valid_to to when the new record becomes valid
            ))

    def get_assets_with_data(self, data_source_id: Optional[int] = None) -> List[Tuple[int, int, date, date]]:
        """Get list of assets that have data, with their coverage periods."""
        query = """
        SELECT asset_id, data_source_id, MIN(business_date) as min_date, MAX(business_date) as max_date
        FROM data 
        WHERE is_deleted = false
        """
        params = []
        
        if data_source_id:
            query += " AND data_source_id = %s"
            params.append(data_source_id)
        
        query += " GROUP BY asset_id, data_source_id ALLOW FILTERING"
        
        try:
            rows = self.session.execute(query, params)
            result = []
            
            for row in rows:
                min_date = row.min_date.date() if isinstance(row.min_date, CassandraDate) else row.min_date
                max_date = row.max_date.date() if isinstance(row.max_date, CassandraDate) else row.max_date
                
                # Ensure proper ordering: start_date should be <= end_date
                start_date = min(min_date, max_date)
                end_date = max(min_date, max_date)
                
                result.append((row.asset_id, row.data_source_id, start_date, end_date))
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting assets with data: {str(e)}")
            return []

    def get_compatible_data_sources_for_asset(self, asset_id: int) -> List[int]:
        """Get data sources that are compatible with the given asset based on existing data or asset type."""
        try:
            # First, get data sources that already have data for this asset
            query = """
            SELECT DISTINCT data_source_id
            FROM data 
            WHERE asset_id = %s AND is_deleted = false
            ALLOW FILTERING
            """
            
            logger.debug(f"Checking compatible data sources for asset {asset_id}")
            rows = self.session.execute(query, (asset_id,))
            existing_data_source_ids = [row.data_source_id for row in rows]
            
            logger.debug(f"Found data source IDs for asset {asset_id}: {existing_data_source_ids}")
            return existing_data_source_ids
            
        except Exception as e:
            logger.error(f"Error getting compatible data sources for asset {asset_id}: {str(e)}")
            return []
    
    def batch_save_with_temporal_logic(self, data_list: List[Data], batch_size: int = DEFAULT_BATCH_SIZE) -> int:
        """
        Efficiently save multiple data records using batch operations with improved error handling.
        Returns number of successfully saved records.
        """
        if not data_list:
            return 0
            
        saved_count = 0
        now = datetime.now()
        
        # Pre-check existing data to optimize batch operations
        existing_data_map = self._build_existing_data_map(data_list)
        
        # Process in batches to avoid timeout
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            saved_count += self._process_batch(batch, existing_data_map, now)
            
            # Log progress for large datasets
            if len(data_list) > 1000 and saved_count % (batch_size * 10) == 0:
                logger.info(f"Batch progress: {saved_count}/{len(data_list)} records processed")
                    
        logger.info(f"Batch save completed: {saved_count}/{len(data_list)} records saved")
        return saved_count
    
    def _build_existing_data_map(self, data_list: List[Data]) -> dict:
        """Build a map of existing data for efficient lookup during batch processing."""
        existing_map = {}
        unique_keys = set()
        
        # Create unique keys to avoid duplicate checks
        for data in data_list:
            key = (data.asset_id, data.data_source_id, data.business_date)
            unique_keys.add(key)
        
        # Batch check existing data
        for asset_id, data_source_id, business_date in unique_keys:
            existing = self.get_existing_data_for_date(asset_id, data_source_id, business_date)
            if existing:
                existing_map[(asset_id, data_source_id, business_date)] = existing
                
        return existing_map
    
    def _process_batch(self, batch: List[Data], existing_data_map: dict, now: datetime) -> int:
        """Process a single batch of data with temporal logic."""
        batch_stmt = BatchStatement(batch_type=BatchType.LOGGED)
        
        try:
            for data in batch:
                self._add_to_batch(batch_stmt, data, existing_data_map, now)
            
            # Execute batch
            self.session.execute(batch_stmt)
            return len(batch)
            
        except Exception as e:
            logger.error(f"Batch operation failed: {str(e)}")
            # Fallback to individual processing
            return self._process_batch_individually(batch)
    
    def _add_to_batch(self, batch_stmt: BatchStatement, data: Data, existing_data_map: dict, now: datetime):
        """Add data operations to batch statement."""
        key = (data.asset_id, data.data_source_id, data.business_date)
        existing = existing_data_map.get(key)
        
        if existing:
            # Update existing record's valid_to
            batch_stmt.add(self.update_valid_to_stmt, 
                          (now, existing.asset_id, existing.data_source_id, 
                           existing.business_date.strftime('%Y-%m-%d'), existing.system_date))
        
        # Insert new record
        business_date_str = data.business_date.strftime('%Y-%m-%d') if isinstance(data.business_date, date) else data.business_date
        batch_stmt.add(self.insert_stmt, (
            data.asset_id, data.data_source_id, business_date_str, data.system_date,
            data.values_double, data.values_int, data.values_text,
            data.is_deleted, data.valid_from, data.valid_to
        ))
    
    def _process_batch_individually(self, batch: List[Data]) -> int:
        """Process batch items individually when batch operation fails."""
        saved_count = 0
        for data in batch:
            try:
                if self.save_with_temporal_logic(data):
                    saved_count += 1
            except Exception as individual_error:
                logger.error(f"Individual save failed for {data.asset_id}-{data.data_source_id}-{data.business_date}: {individual_error}")
        return saved_count