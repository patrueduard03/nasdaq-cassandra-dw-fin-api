# 🏦 Financial Data Warehouse

A modern financial data warehouse built with **FastAPI** and **Cassandra**, featuring temporal database capabilities for complete audit trails and historical data tracking.

**Academic Project - West University of Timisoara**  
*Big Data Data Warehouse Course | Author: Patru Gheorghe Eduard | 2025*

## 🚀 Features

- **🕒 Temporal Database**: Complete audit trail with versioned records (no data loss)
- **📈 Multi-Asset Support**: Stocks, bonds, currencies, derivatives  
- **⚡ Real-time Data**: Automated Nasdaq data ingestion with coverage tracking
- **🎨 Modern Web UI**: Responsive interface with interactive charts
- **🚀 High Performance**: FastAPI + Cassandra scaling
- **🔒 Type Safety**: Full Pydantic validation and auto-generated docs
- **📊 Smart Ingestion**: Automatic data source filtering and coverage extension
- **🔄 Data Refresh**: Temporal versioning for data updates without loss

## 📁 Project Structure

```
├── src/
│   ├── api/          # FastAPI routes and models
│   ├── models/       # Data models and repositories  
│   ├── services/     # Business logic
│   ├── utils/        # Database utilities
│   └── resources/    # Connection files
├── web/              # Frontend interface
├── requirements.txt  # Dependencies
└── setup_and_run.sh # Automated setup
```

## ⚡ Quick Start

### Prerequisites
- Python 3.9+
- [Nasdaq Data Link API Key](https://data.nasdaq.com/signup) (free)
- [DataStax Astra Database](https://www.datastax.com/astra) (free)

### 🚀 Automated Setup
```bash
git clone https://github.com/patrueduard03/nasdaq-cassandra-dw-fin-api
cd nasdaq-cassandra-dw-fin-api
chmod +x setup_and_run.sh
./setup_and_run.sh
```

### 🔧 Manual Setup
```bash
git clone https://github.com/patrueduard03/nasdaq-cassandra-dw-fin-api
cd nasdaq-cassandra-dw-fin-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## ⚙️ Configuration

### 1. Get Nasdaq API Key
- Sign up at [Nasdaq Data Link](https://data.nasdaq.com/signup)
- Account Settings → API Key → Copy

### 2. Setup Cassandra Database  
- Create account at [DataStax Astra](https://www.datastax.com/astra)
- Create database with keyspace `lectures`
- Download: secure connect bundle (ZIP) + token file (JSON)
- Place files in `src/resources/`

### 3. Environment Variables
Create `.env` file in project root:
```bash
NASDAQ_DATA_LINK_API_KEY=your_api_key_here
SECURE_CONNECT_BUNDLE=src/resources/secure-connect-your-db.zip
SECURE_TOKEN=src/resources/your-db-token.json
```

### 4. Initialize & Start
```bash
python src/utils/create_tables.py  # Create database tables
python src/main.py                 # Start application
```

## 🌐 Access Points
- **📱 Web Interface**: http://localhost:8000/web/
- **📚 API Documentation**: http://localhost:8000/docs  
- **🔗 API Base**: http://localhost:8000/

## 🧪 Testing

### API Testing
- Import `financial-data-warehouse.postman_collection.json` into Postman
- Or use interactive docs at http://localhost:8000/docs

### Database Utilities
```bash
python src/utils/create_tables.py      # Initialize tables
python src/utils/test_nasdaq_datalink.py  # Test API connection  
python src/utils/ingest_nasdaq.py      # Import sample data
python src/utils/truncate_tables.py    # Clear data
```

### Monitoring
```bash
tail -f logs/app.log        # Application logs
tail -f logs/ingestion.log  # Data ingestion logs
```

## 📋 API Endpoints

### 🏦 Assets
- `GET /assets` - List active assets
- `POST /assets` - Create asset
- `PUT /assets/{id}` - Update asset (creates version)
- `DELETE /assets/{id}` - Soft delete
- `GET /admin/assets/all` - All versions + deleted

### 📊 Data Sources  
- `GET /data-sources` - List active sources
- `POST /data-sources` - Create source
- `PUT /data-sources/{id}` - Update source
- `DELETE /data-sources/{id}` - Soft delete

### 📈 Time Series
- `GET /time-series/{asset_id}/{source_id}` - Get data
- `GET /time-series/{asset_id}/{source_id}?start_date=2024-01-01&end_date=2024-12-31` - Date range

### 📥 Data Ingestion
- `POST /ingest/nasdaq` - Import Nasdaq data

### 🛠️ Utilities
- `GET /` - Health check
- `GET /docs` - API documentation  
- `GET /web/` - Web interface

## 🏛️ Temporal Database

This system implements a **temporal database** with:

### Core Principles
- **❌ No Data Loss**: Changes create new versions, never overwrite
- **📅 Complete History**: Track who, what, when, and why  
- **🕒 Point-in-Time**: Query data as it existed at any date
- **🗑️ Soft Deletion**: Mark deleted but preserve records
- **🔄 Version Control**: Multiple versions of each entity

### Key Fields
- `valid_from/valid_to` - Business time (real-world validity)
- `system_date` - System time (record creation)
- `is_deleted` - Soft deletion flag
- `9999-12-31` - Far-future date for current records

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Database**: Apache Cassandra (DataStax Astra)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js
- **Data Source**: Nasdaq Data Link API

### Key Libraries
- `fastapi` - Modern web framework
- `cassandra-driver` - Database connectivity
- `pydantic` - Data validation
- `nasdaq-data-link` - Financial data API
- `uvicorn` - ASGI server
