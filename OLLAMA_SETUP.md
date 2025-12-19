# Ollama Setup Guide

## Install Ollama on Windows

1. **Download Ollama:**
   - Visit: https://ollama.ai/download
   - Download the Windows installer
   - Run the installer and follow the setup wizard

2. **Verify Installation:**
   ```powershell
   ollama --version
   ```

3. **Pull a Model:**
   ```powershell
   # Recommended: Llama 3 8B (good balance)
   ollama pull llama3:8b
   
   # Or for faster inference (smaller model):
   ollama pull mistral:7b
   
   # Or for very fast inference (smallest):
   ollama pull phi3
   ```

4. **Start Ollama Service:**
   - Ollama runs as a service on Windows
   - It should start automatically after installation
   - If not running, start it from the Start Menu or run: `ollama serve`

5. **Verify Ollama is Running:**
   ```powershell
   # Check if it's accessible
   curl http://localhost:11434/api/tags
   ```

## Quick Start Commands

```powershell
# Check if Ollama is running
ollama list

# Pull a model (if not already pulled)
ollama pull llama3:8b

# Test Ollama
ollama run llama3:8b "Hello, how are you?"
```

## Troubleshooting

### Ollama not starting
- Check Windows Services: Search for "Services" → Look for "Ollama"
- Manually start: Open Command Prompt as Administrator → `ollama serve`

### Connection refused from Docker
- Make sure Ollama is running on the host machine
- The Docker container uses `host.docker.internal:11434` to reach the host
- If this doesn't work, you may need to:
  1. Check Windows Firewall settings
  2. Ensure Docker Desktop is configured to allow host access

### Model not found
- Pull the model first: `ollama pull llama3:8b`
- List available models: `ollama list`

## After Setup

Once Ollama is running:
1. Refresh the web application (http://localhost:5173)
2. The connection status should change from "Disconnected" to "Connected"
3. You can now ask questions and upload documents


