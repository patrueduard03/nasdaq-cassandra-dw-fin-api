import argparse
import logging
import os
from datetime import date
from typing import List, Optional
from services.data_ingestion_service import DataIngestionService
from services.data_service import DataService
from models.asset import Asset

# Configure logging - ensure we use the same log file as the service
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
log_dir = os.path.join(root_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'ingestion.log')

# Configure logging - ensure we use the same log file as the service
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
log_dir = os.path.join(root_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'ingestion.log')

# Get logger for this module (don't reconfigure if already done)
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)

def parse_args():
    parser = argparse.ArgumentParser(description='Bulk ingest Nasdaq data for multiple assets')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--asset-ids', type=str, help='Comma-separated list of asset IDs to ingest')
    return parser.parse_args()

def parse_date(date_str: str) -> date:
    try:
        return date.fromisoformat(date_str)
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD format.") from e

def get_assets_to_ingest(data_service: DataService, asset_ids: Optional[str] = None) -> List[Asset]:
    """Get list of assets to ingest data for."""
    if asset_ids:
        # Ingest specific assets
        asset_id_list = [int(id.strip()) for id in asset_ids.split(',')]
        assets = []
        for asset_id in asset_id_list:
            asset = data_service.get_asset_by_id(asset_id)
            if asset:
                assets.append(asset)
            else:
                logger.warning(f"Asset with ID {asset_id} not found")
        return assets
    else:
        # Ingest all assets
        return data_service.get_all_assets()

def ingest_data_for_assets(
    ingestion_service: DataIngestionService,
    data_service: DataService,
    assets: List[Asset],
    start_date: date,
    end_date: date
) -> None:
    """Ingest data for multiple assets."""
    # Get Nasdaq data source
    data_source = data_service.get_data_source_by_provider("Nasdaq")
    if not data_source:
        raise ValueError("Nasdaq data source not found")

    total_assets = len(assets)
    successful = 0
    failed = 0

    for i, asset in enumerate(assets, 1):
        try:
            logger.info(f"Processing asset {i}/{total_assets}: {asset.name} (ID: {asset.id})")
            
            ingestion_service.ingest_nasdaq_data(
                asset_id=asset.id,
                data_source_id=data_source.id,
                start_date=start_date,
                end_date=end_date
            )
            
            successful += 1
            logger.info(f"Successfully ingested data for {asset.name}")
            
        except Exception as e:
            failed += 1
            logger.error(f"Failed to ingest data for {asset.name}: {str(e)}")
            continue

    logger.info(f"Ingestion completed. Successful: {successful}, Failed: {failed}")

def main():
    try:
        args = parse_args()
        
        # Parse dates
        start_date = parse_date(args.start_date) if args.start_date else date(2020, 1, 1)
        end_date = parse_date(args.end_date) if args.end_date else date(2023, 12, 31)
        
        if start_date > end_date:
            raise ValueError("Start date must be before end date")

        # Initialize services
        ingestion_service = DataIngestionService()
        data_service = DataService()

        # Get assets to ingest
        assets = get_assets_to_ingest(data_service, args.asset_ids)
        if not assets:
            raise ValueError("No assets found to ingest data for")

        logger.info(f"Starting bulk ingestion for {len(assets)} assets")
        logger.info(f"Date range: {start_date} to {end_date}")

        # Ingest data for all assets
        ingest_data_for_assets(
            ingestion_service=ingestion_service,
            data_service=data_service,
            assets=assets,
            start_date=start_date,
            end_date=end_date
        )

    except Exception as e:
        logger.error(f"Bulk ingestion failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()