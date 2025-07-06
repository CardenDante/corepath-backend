@echo off
echo ?? Setting up CorePath Impact Backend Development Environment

echo ?? Creating virtual environment...
python -m venv venv

echo ?? Activating virtual environment...
call venv\Scripts\activate.bat

echo ?? Installing dependencies...
pip install -r requirements/dev.txt

echo ??? Setting up database...
copy .env.example .env
echo Please edit .env file with your configuration

echo ? Setup complete!
echo To run the server: uvicorn app.main:app --reload
pause
