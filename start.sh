#!/bin/bash

# AI Document Q&A Application Startup Script

echo "🚀 Starting AI Document Q&A Application..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Warning: Ollama doesn't seem to be running on localhost:11434"
    echo "   Please make sure Ollama is installed and running:"
    echo "   - Install: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "   - Pull model: ollama pull llama3:8b"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating .env file from template..."
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env - please review and update if needed"
    echo ""
fi

# Start services
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Initialize database
echo "🗄️  Initializing database..."
docker-compose exec -T backend alembic upgrade head 2>/dev/null || echo "⚠️  Database initialization skipped (may already be initialized)"

echo ""
echo "✅ Application is starting!"
echo ""
echo "📍 Access points:"
echo "   - Frontend: http://localhost:5173"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📊 Check status: docker-compose ps"
echo "📋 View logs: docker-compose logs -f"
echo "🛑 Stop: docker-compose down"
echo ""


