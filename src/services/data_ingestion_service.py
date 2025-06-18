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
            valid_to=None
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
        end_date: date
    ) -> None:
        """
        Ingest data from Nasdaq Data Link for a specific asset.
        
        Args:
            asset_id: The ID of the asset to ingest data for
            data_source_id: The ID of the Nasdaq data source
            start_date: Start date for data ingestion
            end_date: End date for data ingestion
        """
        try:
            # Get asset and data source
            asset = self.asset_repository.get_asset_by_id(asset_id)
            if not asset:
                raise ValueError(f"Asset with ID {asset_id} not found")

            data_source = self.data_source_repository.get_data_source_by_id(data_source_id)
            if not data_source:
                raise ValueError(f"Data source with ID {data_source_id} not found")

            if data_source.provider != "Nasdaq":
                raise ValueError(f"Data source {data_source_id} is not a Nasdaq data source")

            # Get asset symbol from attributes
            asset_attrs = self._convert_attributes_to_dict(asset.attributes)
            symbol = asset_attrs.get('symbol')
            if not symbol:
                raise ValueError(f"Asset {asset_id} does not have a 'symbol' attribute")

            logger.info(f"Fetching Nasdaq data for {symbol} from {start_date} to {end_date}")

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
                logger.info(f"Starting to save {len(df)} records to Cassandra...")

                # Convert DataFrame to our data format and save with progress logging
                total_records = len(df)
                saved_count = 0
                batch_size = 100  # Log progress every 100 records
                
                for index, row in df.iterrows():
                    try:
                        business_date = self._ensure_date(row['date'])
                        now = datetime.now()
                        data = Data(
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
                            valid_to=None
                        )
                        self.data_repository.save(data)
                        saved_count += 1
                        
                        # Log progress every batch_size records
                        if saved_count % batch_size == 0 or saved_count == total_records:
                            progress_pct = (saved_count / total_records) * 100
                            logger.info(f"Cassandra save progress for {symbol}: {saved_count}/{total_records} records ({progress_pct:.1f}%) - Date: {business_date}")
                            
                    except Exception as e:
                        logger.error(f"Error processing row for date {row['date']}: {str(e)}")
                        continue

                logger.info(f"Successfully saved {saved_count} data points to Cassandra for {symbol}")
                logger.info(f"Successfully ingested {saved_count} data points for {symbol}")

            except nasdaqdatalink.AuthenticationError:
                raise ValueError("Invalid Nasdaq Data Link API key")
            except nasdaqdatalink.NotFoundError:
                raise ValueError(f"Dataset {dataset_code} not found")
            except Exception as e:
                raise ValueError(f"Error fetching data from Nasdaq: {str(e)}")

        except Exception as e:
            logger.error(f"Error ingesting Nasdaq data: {str(e)}")
            raise