from typing import Dict, Any, List, Optional
from datetime import datetime, date
import logging
import os
import nasdaqdatalink
import pandas as pd
from models.asset import Asset
from models.data_source import DataSource
from models.data import Data
from connect_database import session
from models.data_repository import DataRepository
from models.data_source_repository import DataSourceRepository
from models.asset_repository import AssetRepository
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("data_ingestion")

# Temporal database constants
FAR_FUTURE_DATE = datetime(9999, 12, 31, 23, 59, 59)  # For current versions

class DataIngestionService:
    """Service for ingesting data from external sources"""
    
    def __init__(self):
        self.session = session
        self.data_repository = DataRepository()
        self.data_source_repository = DataSourceRepository()
        self.asset_repository = AssetRepository()
        
        # Set up Nasdaq Data Link API key
        api_key = os.getenv('NASDAQ_DATA_LINK_API_KEY')
        if not api_key:
            raise ValueError("NASDAQ_DATA_LINK_API_KEY environment variable not set")
        nasdaqdatalink.read_key(api_key)
        logger.info("Nasdaq API key configured successfully")
        
    def _get_data_source_id(self, provider: str) -> int:
        """Get or create data source ID for a provider"""
        data_source = self.data_source_repository.get_by_provider(provider)
        if data_source:
            return data_source.id
            
        # Create new data source
        data_source_id = self.data_source_repository.get_next_id()
        now = datetime.now()
        new_data_source = DataSource(
            id=data_source_id,
            name=f"{provider} Data Source",
            description=f"Data source for {provider}",
            system_date=now,
            provider=provider,
            attributes={},
            is_deleted=False,
            valid_from=now,
            valid_to=FAR_FUTURE_DATE  # Current version uses far-future date
        )
        self.data_source_repository.save_data_source(new_data_source)
        return data_source_id
        
    def _convert_attributes_to_dict(self, attributes: Any) -> Dict[str, Any]:
        """Convert attributes to dictionary if needed."""
        if isinstance(attributes, dict):
            return attributes
        if isinstance(attributes, set):
            return {k: True for k in attributes}
        if attributes is None:
            return {}
        try:
            return dict(attributes) if attributes else {}
        except (TypeError, ValueError):
            return {}

    def _ensure_date(self, value: Any) -> date:
        """Convert a value to a date object."""
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            return datetime.strptime(value, '%Y-%m-%d').date()
        raise ValueError(f"Cannot convert {value} to date")

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert a value to float, handling None/NaN values."""
        if value is None or pd.isna(value):
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def ingest_nasdaq_data(
        self,
        asset_id: int,
        data_source_id: int,
        start_date: date,
        end_date: date,
        force_refresh: bool = False
    ) -> None:
        """
        Ingest data from Nasdaq Data Link for a specific asset following temporal paradigm.
        
        Args:
            asset_id: The ID of the asset to ingest data for
            data_source_id: The ID of the Nasdaq data source
            start_date: Start date for data ingestion
            end_date: End date for data ingestion
            force_refresh: If True, creates new temporal versions for existing data
        """
        try:
            # Get asset and data source
            asset = self.asset_repository.get_asset_by_id(asset_id)
            if not asset:
                raise ValueError(f"Asset with ID {asset_id} not found")

            data_source = self.data_source_repository.get_data_source_by_id(data_source_id)
            if not data_source:
                raise ValueError(f"Data source with ID {data_source_id} not found")

            if "nasdaq" not in data_source.provider.lower():
                raise ValueError(f"Data source {data_source_id} is not a Nasdaq data source (provider: {data_source.provider})")

            # Get asset symbol from attributes
            asset_attrs = self._convert_attributes_to_dict(asset.attributes)
            symbol = asset_attrs.get('symbol')
            if not symbol:
                raise ValueError(f"Asset {asset_id} does not have a 'symbol' attribute")

            logger.info(f"Fetching Nasdaq data for {symbol} from {start_date} to {end_date} (force_refresh={force_refresh})")

            # Use WIKI/PRICES dataset for stock data
            dataset_code = "WIKI/PRICES"

            # Fetch data from Nasdaq
            try:
                # Fetch the data using get_table for WIKI/PRICES with proper date range
                df = nasdaqdatalink.get_table(
                    dataset_code,
                    ticker=symbol,
                    **{
                        'date.gte': start_date.strftime('%Y-%m-%d'),
                        'date.lte': end_date.strftime('%Y-%m-%d')
                    }
                )

                if df.empty:
                    logger.warning(f"No data found for {symbol} in the specified date range")
                    return

                logger.info(f"Successfully fetched {len(df)} records for {symbol}")
                
                # Check for existing data to determine ingestion strategy
                existing_data = self.data_repository.get_time_series_data(
                    asset_id=asset_id,
                    data_source_id=data_source_id,
                    start_date=start_date,
                    end_date=end_date
                )
                
                existing_dates = {data.business_date for data in existing_data}
                logger.info(f"Found {len(existing_dates)} existing data points in date range")
                
                # Convert DataFrame to our data format and save with temporal handling
                total_records = len(df)
                saved_count = 0
                updated_count = 0
                skipped_count = 0
                batch_size = 100  # Log progress every 100 records
                
                for index, row in df.iterrows():
                    try:
                        business_date = self._ensure_date(row['date'])
                        now = datetime.now()
                        
                        # Check if data exists for this date
                        date_exists = business_date in existing_dates
                        
                        if date_exists and not force_refresh:
                            # Skip existing data unless force_refresh is True
                            skipped_count += 1
                            logger.debug(f"Skipping existing data for {symbol} on {business_date}")
                            continue
                        
                        # Create new data point
                        new_data = Data(
                            asset_id=asset_id,
                            data_source_id=data_source_id,
                            business_date=business_date,
                            system_date=now,
                            values_double={
                                'open': self._safe_float(row['open']),
                                'high': self._safe_float(row['high']),
                                'low': self._safe_float(row['low']),
                                'close': self._safe_float(row['close']),
                                'volume': self._safe_float(row['volume']),
                                'split_ratio': self._safe_float(row['split_ratio'], 1.0),
                                'adj_open': self._safe_float(row['adj_open']),
                                'adj_high': self._safe_float(row['adj_high']),
                                'adj_low': self._safe_float(row['adj_low']),
                                'adj_close': self._safe_float(row['adj_close']),
                                'adj_volume': self._safe_float(row['adj_volume'])
                            },
                            values_int={},
                            values_text={},
                            is_deleted=False,
                            valid_from=now,
                            valid_to=FAR_FUTURE_DATE
                        )
                        
                        if date_exists and force_refresh:
                            # Temporal update: close existing version and create new one
                            success = self.data_repository.save_with_temporal_logic(new_data)
                            if success:
                                updated_count += 1
                            else:
                                logger.error(f"Failed to update data for {business_date}")
                        else:
                            # New data point - use temporal save logic to handle any existing data
                            success = self.data_repository.save_with_temporal_logic(new_data)
                            if success:
                                saved_count += 1
                            else:
                                logger.error(f"Failed to save data for {business_date}")
                        
                        # Log progress every batch_size records
                        total_processed = saved_count + updated_count + skipped_count
                        if total_processed % batch_size == 0 or total_processed == total_records:
                            progress_pct = (total_processed / total_records) * 100
                            logger.info(f"Progress for {symbol}: {total_processed}/{total_records} ({progress_pct:.1f}%) - New: {saved_count}, Updated: {updated_count}, Skipped: {skipped_count}")
                            
                    except Exception as e:
                        logger.error(f"Error processing row for date {row['date']}: {str(e)}")
                        continue

                logger.info(f"Ingestion completed for {symbol}: {saved_count} new, {updated_count} updated, {skipped_count} skipped")

            except nasdaqdatalink.AuthenticationError:
                raise ValueError("Invalid Nasdaq Data Link API key")
            except nasdaqdatalink.NotFoundError:
                raise ValueError(f"Dataset {dataset_code} not found")
            except Exception as e:
                raise ValueError(f"Error fetching data from Nasdaq: {str(e)}")

        except Exception as e:
            logger.error(f"Error ingesting Nasdaq data: {str(e)}")
            raise

    def get_data_coverage_info(
        self,
        asset_id: int,
        data_source_id: int
    ) -> Dict[str, Any]:
        """
        Get information about existing data coverage for an asset and data source.
        
        Returns:
            Dict with coverage info including date ranges, count, etc.
        """
        try:
            # Get all data for this asset/data_source combination
            all_data = self.data_repository.get_time_series_data(
                asset_id=asset_id,
                data_source_id=data_source_id
            )
            
            if not all_data:
                return {
                    'has_data': False,
                    'count': 0,
                    'start_date': None,
                    'end_date': None,
                    'last_updated': None
                }
            
            # Sort by business_date
            all_data.sort(key=lambda x: x.business_date)
            
            return {
                'has_data': True,
                'count': len(all_data),
                'start_date': all_data[0].business_date,
                'end_date': all_data[-1].business_date,
                'last_updated': max(data.system_date for data in all_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting data coverage info: {str(e)}")
            return {
                'has_data': False,
                'count': 0,
                'start_date': None,
                'end_date': None,
                'last_updated': None,
                'error': str(e)
            }

    def extend_data_coverage(
        self,
        asset_id: int,
        data_source_id: int,
        new_start_date: Optional[date] = None,
        new_end_date: Optional[date] = None
    ) -> None:
        """
        Extend data coverage for an existing asset by ingesting additional date ranges.
        
        Args:
            asset_id: Asset to extend coverage for
            data_source_id: Data source ID
            new_start_date: New start date (will ingest from this date to existing start)
            new_end_date: New end date (will ingest from existing end to this date)
        """
        coverage = self.get_data_coverage_info(asset_id, data_source_id)
        
        if not coverage['has_data']:
            raise ValueError(f"No existing data found for asset {asset_id} and data source {data_source_id}")
        
        existing_start = coverage['start_date']
        existing_end = coverage['end_date']
        
        # Determine what ranges to ingest
        ranges_to_ingest = []
        
        if new_start_date and new_start_date < existing_start:
            # Extend backwards
            extend_end = existing_start - pd.Timedelta(days=1)
            ranges_to_ingest.append((new_start_date, extend_end.date()))
            logger.info(f"Will extend coverage backwards from {new_start_date} to {extend_end.date()}")
        
        if new_end_date and new_end_date > existing_end:
            # Extend forwards
            extend_start = existing_end + pd.Timedelta(days=1)
            ranges_to_ingest.append((extend_start.date(), new_end_date))
            logger.info(f"Will extend coverage forwards from {extend_start.date()} to {new_end_date}")
        
        if not ranges_to_ingest:
            logger.info("No extension needed - requested dates are within existing coverage")
            return
        
        # Ingest each range
        for start_date, end_date in ranges_to_ingest:
            logger.info(f"Extending coverage from {start_date} to {end_date}")
            self.ingest_nasdaq_data(
                asset_id=asset_id,
                data_source_id=data_source_id,
                start_date=start_date,
                end_date=end_date,
                force_refresh=False  # Don't overwrite existing data during extension
            )

    def refresh_existing_data(
        self,
        asset_id: int,
        data_source_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> None:
        """
        Refresh existing data by re-ingesting with force_refresh=True.
        
        Args:
            asset_id: Asset to refresh
            data_source_id: Data source ID  
            start_date: Start date for refresh (defaults to existing coverage start)
            end_date: End date for refresh (defaults to existing coverage end)
        """
        coverage = self.get_data_coverage_info(asset_id, data_source_id)
        
        if not coverage['has_data']:
            raise ValueError(f"No existing data found for asset {asset_id} and data source {data_source_id}")
        
        # Use existing coverage if dates not specified
        refresh_start = start_date or coverage['start_date']
        refresh_end = end_date or coverage['end_date']
        
        logger.info(f"Refreshing data from {refresh_start} to {refresh_end}")
        
        self.ingest_nasdaq_data(
            asset_id=asset_id,
            data_source_id=data_source_id,
            start_date=refresh_start,
            end_date=refresh_end,
            force_refresh=True  # Force refresh creates new temporal versions
        )

    def get_ingestion_status(self, filter_asset_id: Optional[int] = None, filter_data_source_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get ingestion status for assets and data sources."""
        try:
            assets_with_data = self.data_repository.get_assets_with_data(filter_data_source_id)
            status_list = []
            
            for asset_id, ds_id, min_date, max_date in assets_with_data:
                # Skip if filtering by specific asset
                if filter_asset_id and asset_id != filter_asset_id:
                    continue
                    
                # Get asset details
                asset = self.asset_repository.get_asset_by_id(asset_id)
                data_source = self.data_source_repository.get_data_source_by_id(ds_id)
                
                if asset and data_source:
                    status_list.append({
                        'asset_id': asset_id,
                        'asset_symbol': asset.attributes.get('symbol', 'N/A'),
                        'asset_name': asset.name,
                        'data_source_id': ds_id,
                        'data_source_name': data_source.name,
                        'data_source_provider': data_source.provider,
                        'coverage_start': min_date.isoformat(),
                        'coverage_end': max_date.isoformat(),
                        'total_days': (max_date - min_date).days + 1,
                        'has_data': True
                    })
            
            return status_list
            
        except Exception as e:
            logger.error(f"Error getting ingestion status: {str(e)}")
            return []

    def check_data_availability(self, asset_id: int, data_source_id: int) -> Dict[str, Any]:
        """Check data availability for a specific asset and data source."""
        try:
            coverage_period = self.data_repository.get_data_coverage_period(asset_id, data_source_id)
            
            result = {
                'asset_id': asset_id,
                'data_source_id': data_source_id,
                'has_data': coverage_period is not None,
                'coverage_start': None,
                'coverage_end': None,
                'total_days': 0
            }
            
            if coverage_period:
                start_date, end_date = coverage_period
                result.update({
                    'coverage_start': start_date.isoformat(),
                    'coverage_end': end_date.isoformat(),
                    'total_days': (end_date - start_date).days + 1
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking data availability: {str(e)}")
            return {
                'asset_id': asset_id,
                'data_source_id': data_source_id,
                'has_data': False,
                'error': str(e)
            }