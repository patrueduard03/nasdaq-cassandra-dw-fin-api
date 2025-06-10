# Acme Ltd Financial Data Warehouse Project

## Table of Contents
1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Architecture](#architecture)
4. [Project Structure](#project-structure)
5. [Prerequisites](#prerequisites)
6. [Quick Setup](#quick-setup)
7. [Testing](#testing)
8. [Utilities](#utilities)
9. [Business Requirements Solved](#business-requirements-solved)
10. [Technical Implementation](#technical-implementation)
11. [Monitoring](#monitoring)
12. [Technical Architecture](#technical-architecture)
13. [Error Handling & Logging](#error-handling--logging)

## Overview
A financial data warehouse system designed to store, retrieve, and analyze financial data from multiple vendors. Built to meet the requirements for temporal data management and heterogeneous financial instruments.

## Academic Project for:

- **Institution**: West University of Timisoara
- **Course**: Big Data Data Warehouse Project
- **Author**: Patru Gheorghe Eduard
- **Year**: 2025

## Key Features
- **Data Management**: Manage financial assets, data sources, and time-series data.
- **Data Ingestion**: Ingest data from external providers like Nasdaq Data Link.
- **Scalability**: Built on Cassandra for high availability and scalability.
- **API-First Design**: RESTful APIs for seamless integration.

## Architecture
The project follows a 3-layer architecture:
1. **Presentation Layer**: FastAPI for exposing RESTful APIs.
2. **Business Logic Layer**: Services for handling business rules and data processing.
3. **Data Layer**: Cassandra database for storing and querying data.

## Project Structure
```
financial-data-warehouse/
├── src/
│   ├── api/                # API routes and models
│   ├── models/             # Data models and repositories
│   ├── services/           # Business logic services
│   ├── utils/              # Utility scripts (e.g., table creation, ingestion)
│   └── connect_database.py # Database connection setup
├── requirements.txt        # Python dependencies
├── setup_and_run.sh        # Setup and run script
├── README.md               # Project documentation
└── .env.example            # Environment variable template
```

## Prerequisites
- Python 3.9+
- Nasdaq Data Link account ([Sign up here](https://data.nasdaq.com/signup))
- DataStax Astra account ([Sign up here](https://www.datastax.com/astra))

## Quick Setup

### Clone & Install
```bash
git clone https://github.com/patrueduard03/nasdaq-cassandra-dw-fin-api
cd nasdaq-cassandra-dw-fin-api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Get Nasdaq API Key
1. Create an account at [Nasdaq Data Link](https://data.nasdaq.com/signup).
2. Copy the API key from account settings.

### Setup Cassandra Database
1. Create an account at [DataStax Astra](https://www.datastax.com/astra).
2. Create a database → choose AWS → region → keyspace: `lectures`.
3. Download the secure connect bundle (zip file).
4. Download the token file (JSON file).
5. Place both files in the `src/resources/` folder.

### Configure Environment
1. Create a `.env` file in the project root.
2. Add the Nasdaq API key, zip bundle and secure token:
   ```env
   NASDAQ_DATA_LINK_API_KEY=your_key_here
   SECURE_CONNECT_BUNDLE =src/resources/your-bundle.zip
   SECURE_TOKEN =src/resources/your-bundle-token.json
   ```

### Start Application
```bash
python src/main.py
```

### Alternative: Quick Setup & Run
```bash
sh setup_and_run.sh
```

## Testing

### Postman
- Import `financial-data-warehouse.postman_collection.json` into Postman to test API endpoints.

### API Docs
- Visit `http://localhost:8000/docs` (or your app's port) for interactive API documentation.

## Utilities
- **Table Management**: Scripts to create and drop Cassandra tables (`create_tables.py`, `drop_tables.py`).
- **Data Ingestion**: Scripts to test the Nasdaq Data Link (`test_nasdaq_datalink.py`).

## Business Requirements Solved

- Efficiently store and retrieve large financial datasets
- Temporal database: no updates/deletes, only new records with validity periods. Records marked as deleted are flagged with a special marker and remain in the database for historical tracking.
- Heterogeneous data: supports various financial instruments (stocks, bonds, currencies, etc.) with flexible schemas using attributes like `values_double`, `values_int`, and `values_text`.
- External API integration: aggregate data from financial vendors like Nasdaq Data Link. Data provenance is tracked by recording the source of each dataset.
- Data analytics pipeline: structured data for downstream analysis, with efficient data retrieval for analytics tools.

## Technical Implementation

- **FastAPI**: High-performance REST API with automatic documentation
- **Cassandra**: Distributed database for scalable time-series storage. Tables are designed to optimize queries for asset and time-series data retrieval.
- **Repository Pattern**: Clean data access layer with temporal support. Updates create new records, and deletions add marker records.
- **Flexible Schema**: Dynamic attributes for different financial instruments. Examples include equities with `open`, `close`, `high`, and `low` prices, or currencies with exchange rates.
- **Data Provenance**: Each dataset includes metadata about its source, ensuring traceability.

## Monitoring

- **Ingestion Logs**: `tail -f logs/ingestion.log` to monitor data ingestion processes.
- **Application Logs**: `tail -f logs/app.log` to track API and service operations.
- **Error Tracking**: Logs include detailed error messages and retry logic for external API failures.

## Technical Architecture

#### Cassandra Database:
- Horizontal scaling for large datasets
- Built-in temporal data support
- Excellent for time-series workloads
- No single point of failure

#### FastAPI Framework:
- High performance async API
- Automatic OpenAPI documentation
- Type safety with Pydantic
- Easy testing and development

#### Repository Pattern:
- Clean separation of concerns
- Database abstraction layer
- Easy to test and maintain
- Supports temporal data operations

#### Flexible Data Model:
- `values_double`, `values_int`, `values_text` maps
- Supports any financial instrument type
- No schema changes needed for new data types
- Efficient storage and retrieval

## Error Handling & Logging

### Comprehensive Error Management:
- HTTP status codes for API errors
- Detailed error messages with context
- Automatic retry logic for external APIs
- Rate limiting protection

### Logging Strategy:
- Structured logging with timestamps
- Separate logs for ingestion and application
- Progress tracking for bulk operations
- Error aggregation and reporting
