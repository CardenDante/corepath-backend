# CorePath Impact Backend API

## Setup

### Windows
Run setup.bat or:
`ash
python -m venv venv
venv\Scripts\activate
pip install -r requirements/dev.txt
copy .env.example .env
# Edit .env file with your settings
uvicorn app.main:app --reload
`

### Linux/Mac
Run setup.sh or:
`ash
python -m venv venv
source venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env
# Edit .env file with your settings
uvicorn app.main:app --reload
`

## Development

1. Edit .env file with your configuration
2. Run migrations: lembic upgrade head
3. Start server: uvicorn app.main:app --reload
4. Visit: http://localhost:8000/docs

## Project Structure

- pp/ - Main application code
- pp/core/ - Core configuration and utilities
- pp/models/ - Database models
- pp/schemas/ - Pydantic schemas
- pp/api/ - API endpoints
- pp/services/ - Business logic
- uploads/ - Local file storage
- equirements/ - Dependencies

## Features

- User authentication and management
- Product catalog
- Order processing
- Merchant referral system (500 points per referral)
- Course management
- Local file storage
- Admin panel
- Blog integration

## API Documentation

When running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
