#!/bin/bash
echo "?? Setting up CorePath Impact Backend Development Environment"

echo "?? Creating virtual environment..."
python -m venv venv

echo "?? Activating virtual environment..."
# For Windows
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
# For Unix/Mac
else
    source venv/bin/activate
fi

echo "?? Installing dependencies..."
pip install -r requirements/dev.txt

echo "??? Setting up database..."
# Copy example env file
cp .env.example .env
echo "Please edit .env file with your configuration"

echo "????? Initialize database..."
alembic upgrade head

echo "? Setup complete!"
echo "To run the server: uvicorn app.main:app --reload"
