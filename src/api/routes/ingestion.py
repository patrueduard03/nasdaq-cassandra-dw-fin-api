from fastapi import APIRouter, HTTPException
from datetime import date
import logging

from ..models import NasdaqIngestionRequest
from services.data_ingestion_service import DataIngestionService

router = APIRouter(prefix="/ingest", tags=["ingestion"])
data_ingestion = DataIngestionService()
logger = logging.getLogger(__name__)

@router.post("/nasdaq")
async def ingest_nasdaq_data(request: NasdaqIngestionRequest):
    """Ingest data from Nasdaq.
    
    Args:
        request: NasdaqIngestionRequest containing:
            - asset_id: ID of the asset to ingest data for
            - data_source_id: ID of the data source
            - start_date: Start date for data ingestion
            - end_date: End date for data ingestion
    
    Returns:
        dict: Message with number of data points ingested
    """
    logger.info(f"Starting Nasdaq data ingestion for asset {request.asset_id}, data source {request.data_source_id}, dates {request.start_date} to {request.end_date}")
    
    try:
        # Ingest data
        data_ingestion.ingest_nasdaq_data(
            request.asset_id,
            request.data_source_id,
            request.start_date,
            request.end_date
        )
        logger.info(f"Successfully completed Nasdaq data ingestion for asset {request.asset_id}")
        return {"message": "Successfully ingested data"}
    except ValueError as e:
        logger.error(f"Nasdaq ingestion validation error for asset {request.asset_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Nasdaq ingestion failed for asset {request.asset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest data: {str(e)}") 