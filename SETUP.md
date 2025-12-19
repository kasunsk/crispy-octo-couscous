# Setup Guide

## Quick Start (5 minutes)

### Prerequisites

1. **Install Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop
   - Start Docker Desktop

2. **Install Ollama**
   ```bash
   # Linux/Mac
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows: Download from https://ollama.ai
   ```

3. **Pull a Model**
   ```bash
   ollama pull llama3:8b
   # Or for faster inference:
   ollama pull mistral:7b
   ```

### Start the Application

**Windows:**
```cmd
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**Or manually:**
```bash
# Copy environment file
cp backend/.env.example backend/.env

# Start services
docker-compose up -d

# Initialize database (first time only)
docker-compose exec backend alembic upgrade head
```

### Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Manual Setup (Development)

### Backend Setup

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Set up PostgreSQL**
   - Install PostgreSQL 15+
   - Create database: `docqa_db`
   - Update `.env` with credentials

5. **Initialize database**
   ```bash
   alembic upgrade head
   ```

6. **Run server**
   ```bash
   uvicorn app.api.main:app --reload
   ```

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Run development server**
   ```bash
   npm run dev
   ```

3. **Access**: http://localhost:5173

## Troubleshooting

### Ollama Not Connecting

1. **Check Ollama is running:**
   ```bash
   ollama list
   ```

2. **Verify model exists:**
   ```bash
   ollama pull llama3:8b
   ```

3. **Check URL in `.env`:**
   - Local: `http://localhost:11434`
   - Docker: `http://host.docker.internal:11434`

### Database Connection Issues

1. **Check PostgreSQL is running:**
   ```bash
   docker-compose ps postgres
   ```

2. **Reset database:**
   ```bash
   docker-compose down -v
   docker-compose up -d postgres
   docker-compose exec backend alembic upgrade head
   ```

### Port Conflicts

If ports 5173, 8000, or 5432 are in use:

1. **Edit `docker-compose.yml`** to change ports
2. **Update `.env`** with new port numbers
3. **Restart services:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Document Processing Fails

1. **Check file format** (PDF, DOCX, XLSX only)
2. **Verify file size** (max 50MB default)
3. **Check backend logs:**
   ```bash
   docker-compose logs backend
   ```

## Next Steps

1. **Upload a document** (PDF, Word, or Excel)
2. **Wait for processing** (status indicator shows progress)
3. **Select the document** from the sidebar
4. **Ask questions** about the document
5. **Try general questions** without selecting a document

## Production Deployment

See `README.md` for production deployment instructions.


