# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Set Django settings (optional, since asgi.py does it)
$env:DJANGO_SETTINGS_MODULE = "studyroom.settings"

# Start Redis in background (if not already running)
Start-Process -FilePath "C:\redis\redis-server.exe" -WindowStyle Hidden

# Start Uvicorn
uvicorn studyroom.asgi:application --host 0.0.0.0 --port 8000 --reload