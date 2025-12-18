# Quick Start Guide

## Step 1: Install Ollama (Required for AI Features)

### Windows:
1. **Download Ollama:**
   - Visit: https://ollama.ai/download/windows
   - Download and run the installer
   - Ollama will install and start automatically

2. **Or use the installation script:**
   ```powershell
   .\install_ollama.ps1
   ```

3. **Pull a model:**
   ```powershell
   # Recommended: Good balance of quality and speed
   ollama pull llama3:8b
   
   # OR for faster responses:
   ollama pull mistral:7b
   
   # OR for very fast responses (smallest):
   ollama pull phi3
   ```

4. **Verify it's working:**
   ```powershell
   ollama list
   ollama run llama3:8b "Hello"
   ```

## Step 2: Start the Application

```powershell
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

## Step 3: Access the Application

- **Web UI**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Step 4: Use the Application

1. **Upload a Document:**
   - Drag and drop a PDF, Word, or Excel file
   - Wait for processing to complete

2. **Ask Questions:**
   - **With Document**: Select a document, then ask questions about it
   - **General Questions**: Don't select a document, ask any question (uses internet search)

## Troubleshooting

### "Connection refused" Error
- **Solution**: Install and start Ollama (see Step 1)
- Run: `.\install_ollama.ps1` to check setup

### Ollama not accessible from Docker
- Make sure Ollama is running on Windows
- Check: `curl http://localhost:11434/api/tags`
- If using Docker Desktop, `host.docker.internal` should work automatically

### Database Errors
- Reset database: `docker-compose exec postgres psql -U docqa_user -d docqa_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"`
- Re-run migrations: `docker-compose exec backend alembic upgrade head`

## Features

✅ **Document Q&A**: Upload PDF/Word/Excel and ask questions  
✅ **General Q&A**: Ask any question (uses internet search)  
✅ **100% Local**: No external AI APIs, all processing local  
✅ **Privacy**: All data stays on your machine  
✅ **Free**: No API costs, completely free to use  

## Next Steps

- See `README.md` for detailed documentation
- See `SETUP.md` for manual setup instructions
- See `OLLAMA_SETUP.md` for detailed Ollama setup

