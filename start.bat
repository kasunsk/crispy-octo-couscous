@echo off
REM AI Document Q&A Application Startup Script for Windows

echo 🚀 Starting AI Document Q&A Application...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker and try again.
    exit /b 1
)

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Warning: Ollama doesn't seem to be running on localhost:11434
    echo    Please make sure Ollama is installed and running:
    echo    - Install: Download from https://ollama.ai
    echo    - Pull model: ollama pull llama3:8b
    echo.
    set /p continue="Continue anyway? (y/n) "
    if /i not "%continue%"=="y" exit /b 1
)

REM Create .env file if it doesn't exist
if not exist backend\.env (
    echo 📝 Creating .env file from template...
    copy backend\.env.example backend\.env
    echo ✅ Created backend\.env - please review and update if needed
    echo.
)

REM Start services
echo 🐳 Starting Docker containers...
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 5 /nobreak >nul

REM Initialize database
echo 🗄️  Initializing database...
docker-compose exec -T backend alembic upgrade head 2>nul || echo ⚠️  Database initialization skipped (may already be initialized)

echo.
echo ✅ Application is starting!
echo.
echo 📍 Access points:
echo    - Frontend: http://localhost:5173
echo    - Backend API: http://localhost:8000
echo    - API Docs: http://localhost:8000/docs
echo.
echo 📊 Check status: docker-compose ps
echo 📋 View logs: docker-compose logs -f
echo 🛑 Stop: docker-compose down
echo.

pause


