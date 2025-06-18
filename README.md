# 🏦 Acme Ltd Financial Data Warehouse Project

## 📋 Table of Contents
1. [Overview](#overview)
2. [🚀 Key Features](#key-features)
3. [🏗️ Architecture](#architecture)
4. [📁 Project Structure](#project-structure)
5. [⚡ Quick Setup](#quick-setup)
6. [🧪 Testing](#testing)
7. [🔧 Utilities](#utilities)
8. [💼 Business Requirements](#business-requirements)
9. [🔬 Technical Implementation](#technical-implementation)
10. [📊 Web Interface](#web-interface)
11. [🕒 Temporal Database Features](#temporal-database-features)
12. [📈 API Documentation](#api-documentation)

## Overview

A **state-of-the-art financial data warehouse system** designed### 📈 **Time Series API**
| ### 🛠️ **Utility Endpoin### 🔄 **Data Ingestion API**
| Method | Endpoint | Description | Features |
|--------|----------|-------------|----------|
| `POST` | `/ingest/nasdaq` | Import Nasdaq data | Bulk import, progress tracking |
| Method | - [ ] 🔑 **Get API Keys** - Nasdaq Data Link account and API key
- [ ] 🖥️ **Setup Database** - DataStax Astra account and connection filesdpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check and API info |
| `GET` | `/docs` | Interactive API documentation |
| `GET` | `/web/` | Web interface access |
| `GET` | `/health` | Database connectivity test |

### 🎯 **API Usage Best Practices**

#### 🔄 **Temporal Operations**
- **Standard Users**: Use regular endpoints (`/assets`, `/data-sources`) for current data
- **Admin Users**: Use admin endpoints (`/admin/all`) to view complete history and deleted records
- **Updates**: PUT operations create new versions while preserving history
- **Deletions**: DELETE operations create soft deletion markers (data never permanently lost)
- **Recovery**: Use resurrect endpoints to restore accidentally deleted entities

#### 📊 **Response Codes**
- **200 OK**: Successful operation
- **201 Created**: Resource created successfully
- **404 Not Found**: Resource doesn't exist or is deleted (standard endpoints)
- **409 Conflict**: Duplicate resource or invalid state transition
- **500 Internal Server Error**: Database or system error

#### ⚡ **Performance Tips**
- Use date range queries for time series data to limit result sets
- Admin endpoints return more data - use sparingly for operational queries
- Monitor logs for performance insights and error tracking

--- Endpoint | Description | Features |
|--------|----------|-------------|----------|
| `GET` | `/time-series/{asset_id}/{source_id}` | Get time series data | Date filtering, pagination |
| `GET` | `/time-series/{asset_id}/{source_id}?start_date=2024-01-01&end_date=2024-12-31` | Date range query | Optimized range queries |

### 🔄 **Data Ingestion API**
| Method | Endpoint | Description | Features |
|--------|----------|-------------|----------|
| `POST` | `/ingest/nasdaq` | Import Nasdaq data | Bulk import, progress tracking |

### 🛠️ **Utility Endpoints**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check and API info |
| `GET` | `/docs` | Interactive API documentation |
| `GET` | `/web/` | Web interface access |
| `GET` | `/health` | Database connectivity test |

### 🎓 Academic Project Details
- **Institution**: West University of Timisoara
- **Course**: Big Data Data Warehouse Project  
- **Author**: Patru Gheorghe Eduard
- **Year**: 2025

---

**🎯 Overview**: A comprehensive financial data warehouse system designed to store, retrieve, and analyze financial data from multiple vendors with full temporal database capabilities. Built to meet enterprise requirements for historical data tracking, audit trails, and heterogeneous financial instrument support.

## 🚀 Key Features

### 🏛️ **Temporal Database Architecture**
- **No Updates/Deletes**: All changes create new versioned records
- **Complete Audit Trail**: Full history of all data modifications
- **Point-in-Time Queries**: View data as it existed at any date
- **Soft Deletion**: Deleted records marked with temporal flags
- **Version Management**: Track multiple versions of assets and data sources

### 💰 **Financial Data Management**
- **Multi-Asset Support**: Stocks, bonds, currencies, derivatives
- **Flexible Schema**: Dynamic attributes for any financial instrument
- **Data Provenance**: Complete traceability of data sources
- **Real-time Ingestion**: Automated data import from external APIs
- **Time Series Analytics**: Optimized for financial time series data

### 🖥️ **Modern Web Interface**
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Interactive Charts**: Real-time financial visualizations
- **Asset Management**: Full CRUD operations with temporal support
- **Data Source Configuration**: Easy provider setup and management
- **Admin Mode**: View complete historical data and versions

### 🔧 **Technical Excellence**
- **High Performance**: FastAPI with async support
- **Horizontal Scaling**: Cassandra distributed database
- **Type Safety**: Full Pydantic model validation
- **Comprehensive Logging**: Detailed audit and error logs
- **API Documentation**: Auto-generated OpenAPI specs

## 🏗️ Architecture

The project follows a **modern 3-layer architecture** with temporal database patterns:

### 📊 **Presentation Layer**
- **FastAPI Framework**: High-performance async REST APIs
- **Web Interface**: Modern responsive UI with Bootstrap 5
- **Interactive Charts**: Real-time financial data visualizations
- **Admin Controls**: Temporal data management and version viewing

### 🔧 **Business Logic Layer**
- **Service Pattern**: Clean business logic separation
- **Temporal Operations**: Version-aware create, update, delete operations
- **Data Validation**: Comprehensive Pydantic model validation
- **External Integration**: Nasdaq Data Link API client

### 🗄️ **Data Layer**  
- **Cassandra Database**: Distributed, horizontally scalable
- **Repository Pattern**: Clean data access abstraction
- **Temporal Schema**: Built-in versioning and audit trails
- **Time Series Optimization**: Efficient financial data storage

## 📁 Project Structure
```
financial-data-warehouse/
├── 📂 src/
│   ├── 🌐 api/                    # API routes and models
│   │   ├── routes/                # API endpoint definitions
│   │   │   ├── assets.py         # Asset management endpoints
│   │   │   ├── data_sources.py   # Data source endpoints  
│   │   │   ├── time_series.py    # Time series data endpoints
│   │   │   └── ingestion.py      # Data ingestion endpoints
│   │   └── models.py             # Pydantic API models
│   ├── 📊 models/                 # Data models and repositories
│   │   ├── asset.py              # Asset domain model
│   │   ├── asset_repository.py   # Asset data access (temporal)
│   │   ├── data_source.py        # Data source domain model
│   │   ├── data_source_repository.py # Data source access (temporal)
│   │   ├── data.py               # Time series data model
│   │   └── data_repository.py    # Time series data access
│   ├── 🔧 services/               # Business logic services
│   │   ├── data_service.py       # Core data operations
│   │   └── data_ingestion_service.py # External data import
│   ├── 🛠️ utils/                  # Utility scripts
│   │   ├── create_tables.py      # Database table creation
│   │   ├── drop_tables.py        # Database cleanup
│   │   ├── truncate_tables.py    # Data cleanup
│   │   ├── ingest_nasdaq.py      # Nasdaq data import
│   │   └── test_nasdaq_datalink.py # API testing
│   ├── 📁 resources/             # Configuration files
│   │   ├── secure-connect-*.zip  # Cassandra connection bundle
│   │   └── *-token.json         # Database authentication
│   ├── connect_database.py      # Database connection setup
│   └── main.py                  # Application entry point
├── 🌐 web/                       # Modern web interface
│   ├── index.html               # Main application page
│   ├── styles.css               # Custom styling and themes
│   └── app.js                   # Frontend application logic
├── 📋 requirements.txt           # Python dependencies
├── 🚀 setup_and_run.sh          # Automated setup script
├── 📋 financial-data-warehouse.postman_collection.json # API testing
├── 📖 README.md                 # Project documentation
└── ⚙️ .env.example              # Environment template
```

## ⚡ Quick Setup

### 📋 Prerequisites
- **Python 3.9+** 🐍
- **Nasdaq Data Link Account** ([Sign up](https://data.nasdaq.com/signup)) 📈
- **DataStax Astra Account** ([Sign up](https://www.datastax.com/astra)) 🚀

### 🔧 Installation Steps

#### 1️⃣ Clone & Setup Environment
```bash
git clone https://github.com/patrueduard03/nasdaq-cassandra-dw-fin-api
cd nasdaq-cassandra-dw-fin-api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2️⃣ Get Nasdaq API Key  
1. Create account at [Nasdaq Data Link](https://data.nasdaq.com/signup)
2. Navigate to **Account Settings** → **API Key**
3. Copy your API key for configuration

#### 3️⃣ Setup Cassandra Database
1. Create account at [DataStax Astra](https://www.datastax.com/astra)
2. **Create Database**: 
   - Provider: **AWS** 
   - Region: **us-east-1** (recommended)
   - Keyspace: **`lectures`**
3. **Download Files**:
   - Secure Connect Bundle (ZIP file)
   - Database Token (JSON file)
4. **Place files** in `src/resources/` folder

#### 4️⃣ Configure Environment
Create `.env` file in project root:
```env
# Nasdaq Data Link API Configuration
NASDAQ_DATA_LINK_API_KEY=your_nasdaq_api_key_here

# Cassandra Database Configuration  
SECURE_CONNECT_BUNDLE=src/resources/secure-connect-your-db.zip
SECURE_TOKEN=src/resources/your-db-token.json
```

#### 5️⃣ Initialize Database Tables
```bash
python src/utils/create_tables.py
```

#### 6️⃣ Start the Application
```bash
python src/main.py
```

### 🌟 **Quick Start Alternative**
```bash
chmod +x setup_and_run.sh
./setup_and_run.sh
```

### 🌐 Access Points
Once running, access your application:

| Service | URL | Description |
|---------|-----|-------------|
| 🏠 **Web Interface** | `http://localhost:8000/web/` | Modern UI for data management |
| 📚 **API Documentation** | `http://localhost:8000/docs` | Interactive OpenAPI documentation |
| 🔗 **API Base** | `http://localhost:8000/` | REST API endpoints |

## 🧪 Testing

### 📮 **Postman Collection**
Import `financial-data-warehouse.postman_collection.json` for comprehensive API testing:
- ✅ **All CRUD Operations** - Create, Read, Update, Delete
- ✅ **Temporal Operations** - Asset resurrection, version management  
- ✅ **Admin Endpoints** - Access historical data and all versions
- ✅ **Data Ingestion** - Automated Nasdaq data import
- ✅ **Time Series Queries** - Date range filtering and analytics

### 🌐 **Interactive API Documentation**
Visit `http://localhost:8000/docs` for:
- **Live API Testing** - Execute requests directly from browser
- **Request/Response Examples** - See data formats and validation
- **Schema Documentation** - Understand all data models
- **Authentication Testing** - Verify API security

### 🔧 **Development Testing**
```bash
# Test database connection
python src/utils/test_nasdaq_datalink.py

# Verify table creation
python src/utils/create_tables.py

# Test data ingestion
python src/utils/ingest_nasdaq.py
```

## 🔧 Utilities

### 🗄️ **Database Management**
```bash
# Create all required Cassandra tables
python src/utils/create_tables.py

# Drop all tables (⚠️ destructive operation)
python src/utils/drop_tables.py

# Clear all data while keeping table structure
python src/utils/truncate_tables.py
```

### 📊 **Data Operations**
```bash
# Test Nasdaq Data Link API connection
python src/utils/test_nasdaq_datalink.py

# Bulk import historical data from Nasdaq
python src/utils/ingest_nasdaq.py
```

### 📋 **Monitoring & Logs**
```bash
# Monitor data ingestion processes
tail -f logs/ingestion.log

# Track API and service operations  
tail -f logs/app.log

# Check for errors and performance issues
grep "ERROR" logs/*.log
```

## 💼 Business Requirements

### 🎯 **Core Business Problems Solved**

#### 📈 **Scalable Financial Data Storage**
- Handle **millions of time series records** efficiently
- Support **multiple asset classes** (stocks, bonds, currencies, derivatives)
- **Horizontal scaling** with Cassandra's distributed architecture
- **High availability** with no single points of failure

#### 🕒 **Complete Temporal Data Management**
- **No Data Loss**: All historical versions preserved permanently
- **Audit Compliance**: Complete change tracking for regulatory requirements
- **Point-in-Time Analysis**: Query data as it existed at any historical date
- **Version Control**: Track who, what, when, and why of all changes

#### 🔗 **Heterogeneous Data Integration**
- **Flexible Schema**: Support any financial instrument without schema changes
- **Dynamic Attributes**: Store instrument-specific data (dividends, splits, etc.)
- **Multi-Source Data**: Aggregate from multiple financial data providers
- **Data Provenance**: Track the source and lineage of every data point

#### 🚀 **External API Integration**
- **Automated Ingestion**: Real-time data import from Nasdaq Data Link
- **Rate Limiting**: Respect API quotas and throttling
- **Error Recovery**: Automatic retry logic for failed requests
- **Data Validation**: Ensure data quality and consistency

#### 📊 **Analytics-Ready Pipeline**
- **Optimized Queries**: Fast retrieval for analytical workloads
- **Time Series Focus**: Specialized storage for financial time series
- **Batch Processing**: Efficient bulk data operations
- **Real-time Access**: Low-latency data retrieval for trading systems

## 🔬 Technical Implementation

### 🏛️ **Temporal Database Pattern**
```python
# Asset versioning example
class Asset:
    id: int                    # Immutable asset identifier
    valid_from: datetime      # Version start time
    valid_to: datetime        # Version end time (9999-12-31 for current)
    is_deleted: bool          # Soft deletion flag
    system_date: datetime     # Record creation timestamp
    
# Update creates new version, closes previous
def update_asset(asset_id, new_data):
    current = get_current_version(asset_id)
    close_version(current, now())
    create_new_version(asset_id, new_data, now(), FAR_FUTURE_DATE)
```

### 🗄️ **Cassandra Schema Design**
```sql
-- Optimized for time series queries
CREATE TABLE IF NOT EXISTS data (
    asset_id int,
    data_source_id int,
    business_date date,
    system_date timestamp,
    values_double map<text, double>,  -- OHLCV prices
    values_int map<text, int>,        -- Volume, shares
    values_text map<text, text>,      -- Symbols, notes
    valid_from timestamp,
    valid_to timestamp,
    is_deleted boolean,
    PRIMARY KEY ((asset_id, data_source_id), business_date)
) WITH CLUSTERING ORDER BY (business_date DESC);
```

### ⚡ **FastAPI Architecture**
```python
@router.get("/assets", response_model=List[AssetResponse])
async def get_assets(admin_mode: bool = False):
    """Get assets with temporal filtering"""
    if admin_mode:
        return asset_service.get_all_including_deleted()
    return asset_service.get_active_only()

@router.put("/assets/{asset_id}")
async def update_asset(asset_id: int, data: AssetUpdate):
    """Temporal update - creates new version"""
    return asset_service.create_new_version(asset_id, data)
```

### 🔧 **Repository Pattern**
```python
class AssetRepository:
    def update_asset(self, asset_id: int, data: dict) -> Asset:
        # 1. Close current version
        current = self.get_current_version(asset_id)
        self.close_version(current)
        
        # 2. Create new version
        return self.create_version(asset_id, data, valid_to=FAR_FUTURE_DATE)
    
    def soft_delete(self, asset_id: int) -> None:
        # Creates deletion marker, preserves history
        self.create_deletion_marker(asset_id)
```

## 📊 Web Interface

### ✨ **Modern User Experience**

#### 🏦 **Asset Management Dashboard**
- **📋 Asset Listing**: Sortable table with search and filtering
- **➕ Create Assets**: Intuitive form with dynamic attribute management
- **✏️ Edit Assets**: In-place editing with temporal version control
- **🗑️ Soft Delete**: Mark assets as deleted while preserving history
- **👁️ View Details**: Complete asset information with temporal metadata
- **⚙️ Admin Mode**: Toggle to view all versions and deleted assets

#### 📊 **Data Source Configuration**
- **🔗 Provider Setup**: Configure Nasdaq, Yahoo Finance, Bloomberg, etc.
- **📝 Attribute Management**: Custom key-value pairs for source metadata
- **🔄 Version Control**: Track changes to data source configurations
- **📈 Usage Analytics**: Monitor data source performance and reliability

#### 📈 **Interactive Time Series Visualization**
- **📊 Multi-Metric Charts**: Display OHLCV, volume, adjusted prices
- **🎨 Customizable Views**: Select metrics, date ranges, chart types
- **📱 Responsive Design**: Optimized for desktop, tablet, and mobile
- **⚡ Real-Time Updates**: Live data refresh and chart updates
- **📥 Export Options**: Download charts and data for analysis

#### 🔄 **Data Ingestion Management**
- **📥 Bulk Import**: Batch data import from Nasdaq Data Link
- **📅 Date Range Selection**: Flexible historical data retrieval
- **📊 Progress Tracking**: Real-time ingestion progress and status
- **❌ Error Handling**: Comprehensive error reporting and retry logic

### 🛠️ **Technical Features**

#### 🎨 **UI/UX Excellence**
- **Bootstrap 5**: Modern, responsive component library
- **Chart.js**: High-performance interactive charts
- **Font Awesome**: Professional icon library
- **Custom CSS**: Branded styling and themes
- **Progressive Enhancement**: Works without JavaScript (API access)

#### ⚡ **Performance Optimizations**
- **Async Loading**: Non-blocking API calls with loading indicators
- **Client-Side Caching**: Reduce redundant API requests
- **Lazy Loading**: Load data only when needed
- **Debounced Search**: Efficient search with automatic delays
- **Pagination Support**: Handle large datasets efficiently

## 🕒 Temporal Database Features

The system implements a **true temporal database** following industry best practices for financial data warehousing. All operations preserve complete historical records while ensuring data integrity and audit compliance.

### 🏛️ **Core Temporal Principles**

#### ❌ **No Updates or Deletes**
- **Immutable Records**: Once written, records are never modified
- **Version Creation**: All changes create new timestamped versions
- **Audit Trail**: Complete history of who, what, when, and why
- **Regulatory Compliance**: Meets financial audit requirements

#### 📅 **Temporal Dimensions**
- **`valid_from`**: When the data became valid in the real world
- **`valid_to`**: When the data stopped being valid (closed versions)
- **`system_date`**: When the record was created in the system
- **`is_deleted`**: Soft deletion flag for marking removed records

#### 🔮 **Far-Future Date Pattern**
```python
# Constant used throughout the system
FAR_FUTURE_DATE = datetime(9999, 12, 31, 23, 59, 59)

# Current/active records use far-future date for valid_to
current_asset = {
  "valid_from": "2025-01-15T10:00:00Z",
  "valid_to": "9999-12-31T23:59:59Z",  # Indicates current version
  "is_deleted": False
}
```

### 🔄 **Version Management Examples**

#### ✅ **Current Active Asset**
```json
{
  "id": 1,
  "name": "Apple Inc.",
  "description": "Apple Inc. Common Stock",
  "valid_from": "2025-01-15T10:00:00Z",
  "valid_to": "9999-12-31T23:59:59Z",
  "system_date": "2025-01-15T10:00:00Z",
  "is_deleted": false,
  "attributes": {
    "symbol": "AAPL",
    "type": "equity",
    "exchange": "NASDAQ",
    "sector": "Technology"
  }
}
```

#### 📜 **Historical Version (Closed)**
```json
{
  "id": 1,
  "name": "Apple Computer Inc.",
  "description": "Apple Computer Inc. Common Stock",
  "valid_from": "2025-01-01T00:00:00Z",
  "valid_to": "2025-01-15T10:00:00Z",    // Closed when updated
  "system_date": "2025-01-01T00:00:00Z",
  "is_deleted": false,
  "attributes": {
    "symbol": "AAPL",
    "type": "equity",
    "exchange": "NASDAQ",
    "sector": "Technology"
  }
}
```

#### 🗑️ **Deletion Marker**
```json
{
  "id": 1,
  "name": "Apple Inc.",
  "description": "Apple Inc. Common Stock",
  "valid_from": "2025-01-20T15:30:00Z",
  "valid_to": "9999-12-31T23:59:59Z",    // Current deletion state
  "system_date": "2025-01-20T15:30:00Z",
  "is_deleted": true,                     // Deletion marker
  "attributes": {
    "symbol": "AAPL",
    "type": "equity",
    "exchange": "NASDAQ",
    "sector": "Technology"
  }
}
```

### 🔧 **Temporal Operations**

#### 📝 **Create Operation**
```python
def create_asset(data: dict) -> Asset:
    """Creates first version of an asset"""
    now = datetime.now()
    return Asset(
        id=get_next_id(),
        valid_from=now,
        valid_to=FAR_FUTURE_DATE,  # Current version
        system_date=now,
        is_deleted=False,
        **data
    )
```

#### ✏️ **Update Operation**
```python
def update_asset(asset_id: int, data: dict) -> Asset:
    """Updates by creating new version and closing previous"""
    current = get_current_asset(asset_id)
    now = datetime.now()
    
    # Step 1: Close current version
    close_version(current, valid_to=now)
    
    # Step 2: Create new version
    return create_new_version(
        id=asset_id,
        valid_from=now,
        valid_to=FAR_FUTURE_DATE,
        system_date=now,
        is_deleted=False,
        **data
    )
```

#### 🗑️ **Delete Operation**
```python
def delete_asset(asset_id: int) -> None:
    """Creates deletion marker while preserving history"""
    current = get_current_asset(asset_id)
    now = datetime.now()
    
    # Step 1: Close current active version
    close_version(current, valid_to=now)
    
    # Step 2: Create deletion marker
    create_deletion_marker(
        id=asset_id,
        valid_from=now,
        valid_to=FAR_FUTURE_DATE,
        system_date=now,
        is_deleted=True,
        **current.data
    )
```

#### 🔄 **Resurrect Operation**
```python
def resurrect_asset(asset_id: int, data: dict) -> Asset:
    """Restores deleted asset with new data"""
    current = get_current_asset_including_deleted(asset_id)
    if not current or not current.is_deleted:
        raise ValueError("Asset not found or not deleted")
    
    now = datetime.now()
    
    # Step 1: Close deletion marker
    close_version(current, valid_to=now)
    
    # Step 2: Create new active version
    return create_new_version(
        id=asset_id,
        valid_from=now,
        valid_to=FAR_FUTURE_DATE,
        system_date=now,
        is_deleted=False,
        **data
    )
```

### 📅 **Temporal Queries**

#### 🔍 **Current State Query**
```sql
-- Get current active version
SELECT * FROM asset 
WHERE id = 1 
AND valid_to = '9999-12-31 23:59:59'
AND is_deleted = false
```

#### 🕒 **Point-in-Time Query**
```sql
-- Get asset state as of specific date
SELECT * FROM asset 
WHERE id = 1 
AND valid_from <= '2025-03-15T00:00:00Z'
AND valid_to > '2025-03-15T00:00:00Z'
```

#### 📚 **History Query**
```sql
-- Get all versions of an asset
SELECT * FROM asset 
WHERE id = 1 
ORDER BY valid_from DESC
```

#### � **Active Assets Only**
```sql
-- Get all currently active assets
SELECT * FROM asset 
WHERE valid_to = '9999-12-31 23:59:59'
AND is_deleted = false
```

### 🎯 **Benefits of Temporal Design**

- **🔒 Data Integrity**: Immutable records prevent accidental data loss
- **📊 Audit Compliance**: Complete change history for regulatory requirements
- **🕒 Time Travel**: Query data as it existed at any point in time
- **🔄 Reversibility**: Resurrect deleted assets with full history
- **📈 Analytics**: Temporal analysis of data changes over time
- **🛡️ Error Recovery**: Ability to recover from accidental changes
- **📝 Traceability**: Full lineage of all data modifications

## 📈 API Documentation

### 🏦 **Assets API**
| Method | Endpoint | Description | Temporal |
|--------|----------|-------------|----------|
| `GET` | `/assets` | List active assets | ✅ Latest versions only |
| `GET` | `/assets/admin/all` | List all versions | ✅ Complete history |
| `GET` | `/assets/{id}` | Get asset details | ✅ Current version |
| `POST` | `/assets` | Create new asset | ✅ Creates first version |
| `PUT` | `/assets/{id}` | Update asset | ✅ Creates new version |
| `DELETE` | `/assets/{id}` | Soft delete asset | ✅ Creates deletion marker |
| `POST` | `/assets/{id}/resurrect` | Restore deleted asset | ✅ Creates new active version |

### 📊 **Data Sources API**
| Method | Endpoint | Description | Temporal |
|--------|----------|-------------|----------|
| `GET` | `/data-sources` | List active sources | ✅ Latest versions only |
| `GET` | `/data-sources/admin/all` | List all versions | ✅ Complete history |
| `GET` | `/data-sources/{id}` | Get source details | ✅ Current version |
| `POST` | `/data-sources` | Create new source | ✅ Creates first version |
| `PUT` | `/data-sources/{id}` | Update source | ✅ Creates new version |
| `DELETE` | `/data-sources/{id}` | Soft delete source | ✅ Creates deletion marker |
| `POST` | `/data-sources/{id}/resurrect` | Restore deleted source | ✅ Creates new active version |
| `GET` | `/data-sources/provider/{name}` | Find by provider | ✅ Active versions only |

### 📈 **Time Series API**
| Method | Endpoint | Description | Features |
|--------|----------|-------------|----------|
| `GET` | `/time-series/{asset_id}/{source_id}` | Get time series data | Date filtering, pagination |
| `GET` | `/time-series/{asset_id}/{source_id}?start_date=2024-01-01&end_date=2024-12-31` | Date range query | Optimized range queries |

### � **Data Ingestion API**
| Method | Endpoint | Description | Features |
|--------|----------|-------------|----------|
| `POST` | `/ingest/nasdaq` | Import Nasdaq data | Bulk import, progress tracking |

### �️ **Utility Endpoints**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check and API info |
| `GET` | `/docs` | Interactive API documentation |
| `GET` | `/web/` | Web interface access |

---

## 🚀 **Getting Started Checklist**

- [ ] ✅ **Setup Environment** - Python 3.9+, virtual environment
- [ ] 🔑 **Get API Keys** - Nasdaq Data Link account and API key
- [ ] �️ **Setup Database** - DataStax Astra account and connection files
- [ ] ⚙️ **Configure Environment** - Create `.env` file with credentials
- [ ] 📊 **Initialize Tables** - Run `create_tables.py`
- [ ] 🚀 **Start Application** - Execute `python src/main.py`
- [ ] 🌐 **Access Web UI** - Open `http://localhost:8000/web/`
- [ ] 📚 **Explore API** - Visit `http://localhost:8000/docs`
- [ ] 📮 **Test with Postman** - Import collection and test endpoints
- [ ] 📈 **Import Sample Data** - Use Nasdaq ingestion to populate database

**🎉 Ready to build the future of financial data management!**
