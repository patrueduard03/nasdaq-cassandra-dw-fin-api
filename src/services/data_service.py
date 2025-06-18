from typing import List, Optional, Dict, Any
from datetime import datetime, date
from models.asset import Asset
from models.data_source import DataSource
from models.data import Data
from models.asset_repository import AssetRepository
from models.data_source_repository import DataSourceRepository
from models.data_repository import DataRepository
from api.models import DataSourceCreate
import logging

logger = logging.getLogger(__name__)

class DataService:
    """High-level service for managing financial data"""
    
    def __init__(self):
        self.asset_repo = AssetRepository()
        self.data_source_repo = DataSourceRepository()
        self.data_repo = DataRepository()

    def get_all_assets(self) -> List[Asset]:
        """Get all financial assets"""
        return self.asset_repo.get_all_assets()

    def get_asset_by_id(self, asset_id: int) -> Optional[Asset]:
        """Get asset by ID"""
        return self.asset_repo.get_asset_by_id(asset_id)

    def get_all_data_sources(self) -> List[DataSource]:
        """Get all data sources"""
        return self.data_source_repo.get_all_data_sources()

    def get_data_source_by_id(self, data_source_id: int) -> Optional[DataSource]:
        """Get data source by ID"""
        return self.data_source_repo.get_data_source_by_id(data_source_id)

    def get_data_source_by_provider(self, provider: str) -> Optional[DataSource]:
        """Get data source by provider"""
        return self.data_source_repo.get_by_provider(provider)

    def create_data_source(self, data_source: DataSourceCreate) -> DataSource:
        """Create a new data source"""
        data_source_id = self.data_source_repo.get_next_id()
        # Ensure attributes is always a dictionary, never None
        attributes = data_source.attributes if data_source.attributes is not None else {}
        
        now = datetime.now()
        new_data_source = DataSource(
            id=data_source_id,
            name=data_source.name,
            description=data_source.description or "",
            system_date=now,
            provider=data_source.provider,
            attributes=attributes,
            is_deleted=False,
            valid_from=now,
            valid_to=None
        )
        self.data_source_repo.save_data_source(new_data_source)
        logger.info(f"Created new data source: {new_data_source.name} (Provider: {new_data_source.provider})")
        return new_data_source

    def get_time_series_data(
        self,
        asset_id: int,
        data_source_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Data]:
        """Get time series data"""
        return self.data_repo.get_time_series_data(
            asset_id,
            data_source_id,
            start_date,
            end_date
        )

    def create_asset(self, asset_data: Dict[str, Any]) -> Asset:
        """Create a new asset or resurrect a previously deleted one with the same symbol"""
        symbol = asset_data.get('attributes', {}).get('symbol', '').upper()
        
        # Check if there's already an active asset with the same symbol
        if symbol:
            existing_active = self.asset_repo.get_active_asset_by_symbol(symbol)
            if existing_active:
                logger.warning(f"Cannot create asset - active asset with symbol {symbol} already exists (ID: {existing_active.id})")
                raise ValueError(f"Asset with symbol '{symbol}' already exists and is active")
            
            # Check if there's a deleted asset with the same symbol for resurrection
            deleted_asset = self.asset_repo.get_deleted_asset_by_symbol(symbol)
            if deleted_asset:
                logger.info(f"Found deleted asset with symbol {symbol} (ID: {deleted_asset.id}). Resurrecting instead of creating new.")
                return self.asset_repo.resurrect_asset(deleted_asset.id, asset_data)
        
        # No existing or deleted asset found, create new one
        now = datetime.now()
        asset_id = self.asset_repo.get_next_id()
        asset = Asset(
            id=asset_id,
            name=asset_data['name'],
            description=asset_data['description'],
            system_date=now,
            is_deleted=False,
            valid_from=now,
            valid_to=None,
            attributes=asset_data.get('attributes', {})
        )
        self.asset_repo.save_asset(asset)
        logger.info(f"Created new asset: {asset.name} (ID: {asset_id})")
        return asset

    def get_asset_by_id_including_deleted(self, asset_id: int) -> Optional[Asset]:
        """Get asset by ID including deleted ones"""
        return self.asset_repo.get_asset_by_id_including_deleted(asset_id)

    def mark_asset_deleted(self, asset_id: int) -> None:
        """Mark an asset as deleted"""
        asset = self.asset_repo.get_asset_by_id(asset_id)
        if not asset:
            raise ValueError(f"Asset with ID {asset_id} not found")
        if asset.is_deleted:
            raise ValueError(f"Asset with ID {asset_id} is already deleted")
        self.asset_repo.mark_deleted(asset_id)

    def mark_data_source_deleted(self, data_source_id: int) -> None:
        """Mark a data source as deleted"""
        data_source = self.data_source_repo.get_data_source_by_id(data_source_id)
        if not data_source:
            raise ValueError(f"Data source with ID {data_source_id} not found")
        if data_source.is_deleted:
            raise ValueError(f"Data source with ID {data_source_id} is already deleted")
        self.data_source_repo.mark_deleted(data_source_id)