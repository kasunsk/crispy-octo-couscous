# AI Document Q&A Application

A comprehensive AI-powered document question-answering application that processes documents (PDF, Excel, Word) and answers questions using local LLM models. The application also supports general internet-based queries.

## Features

- 📄 **Document Processing**: Upload and process PDF, Excel, and Word documents
- 🤖 **Local AI**: Uses Ollama for local LLM inference (no external AI services)
- 🔍 **RAG Pipeline**: Retrieval-Augmented Generation for accurate document-based answers
- 🌐 **Internet Search**: Answer general questions using web search
- 💬 **Chat Interface**: Interactive chat UI similar to ChatGPT
- 🎨 **Modern UI**: Beautiful, responsive web interface built with React
- 🐳 **Docker Support**: Easy deployment with Docker Compose

## Architecture

```
Frontend (React) → Backend (FastAPI) → Services
                                      ├── Document Processor
                                      ├── Embedding Service (ChromaDB)
                                      ├── RAG Service
                                      ├── LLM Service (Ollama)
                                      └── Search Service (DuckDuckGo)
```

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Relational database for metadata
- **ChromaDB**: Vector database for document embeddings
- **Ollama**: Local LLM runtime
- **LangChain**: LLM orchestration
- **sentence-transformers**: Text embeddings

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Vite**: Build tool
- **Zustand**: State management
- **React Query**: Data fetching

## Prerequisites

1. **Docker & Docker Compose** (for containerized deployment)
2. **Ollama** installed and running locally
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull a model (recommended: llama3:8b or mistral:7b)
   ollama pull llama3:8b
   ```

3. **Python 3.11+** (for local development)
4. **Node.js 20+** (for frontend development)

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd crispy-octo-couscous
   ```

2. **Create environment file**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your configuration
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database** (first time only)
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Development

#### Backend Setup

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize database**
   ```bash
   # Make sure PostgreSQL is running
   alembic upgrade head
   ```

5. **Run the server**
   ```bash
   uvicorn app.api.main:app --reload
   ```

#### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Run development server**
   ```bash
   npm run dev
   ```

3. **Access the application**
   - Frontend: http://localhost:5173

## Configuration

### Environment Variables

**Backend (.env)**
```env
# Database
POSTGRES_USER=docqa_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=docqa_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b

# Application
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:5173

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Usage

### Uploading Documents

1. Click on the upload area or drag and drop a file
2. Supported formats: PDF, Word (.docx, .doc), Excel (.xlsx, .xls)
3. Wait for processing to complete (status indicator shows progress)

### Asking Questions

1. **Document-based questions:**
   - Select a document from the sidebar
   - Type your question in the chat interface
   - The AI will answer based on the document content

2. **General questions:**
   - Don't select any document
   - Type your question
   - The AI will search the internet and provide answers

### Example Questions

- "What degrees are mentioned in the resume?"
- "List all the work experience"
- "What is the total revenue for Q1?"
- "Explain quantum computing" (general question)

## API Endpoints

### Documents
- `POST /api/documents/upload` - Upload a document
- `GET /api/documents` - List all documents
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete a document

### Chat
- `POST /api/chat/question` - Ask a question
- `GET /api/chat/history/{session_id}` - Get chat history
- `DELETE /api/chat/history/{session_id}` - Delete chat history

### Health
- `GET /api/health` - Check system health

See full API documentation at `/docs` when the server is running.

## Project Structure

```
crispy-octo-couscous/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── documents.py
│   │   │   │   ├── chat.py
│   │   │   │   └── health.py
│   │   │   └── main.py
│   │   ├── services/
│   │   │   ├── document_processor.py
│   │   │   ├── embedding_service.py
│   │   │   ├── rag_service.py
│   │   │   ├── llm_service.py
│   │   │   └── search_service.py
│   │   ├── models/
│   │   │   └── database.py
│   │   └── utils/
│   │       └── chunking.py
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── store/
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Troubleshooting

### Ollama Connection Issues

1. **Check if Ollama is running:**
   ```bash
   ollama list
   ```

2. **Verify model is available:**
   ```bash
   ollama pull llama3:8b
   ```

3. **Check Ollama URL in .env:**
   - Default: `http://localhost:11434`
   - For Docker: `http://host.docker.internal:11434`

### Database Connection Issues

1. **Verify PostgreSQL is running:**
   ```bash
   docker-compose ps postgres
   ```

2. **Check connection string in .env**

3. **Reset database (if needed):**
   ```bash
   docker-compose down -v
   docker-compose up -d postgres
   ```

### Document Processing Fails

1. **Check file format is supported**
2. **Verify file is not corrupted**
3. **Check file size limits (default: 50MB)**
4. **Review backend logs for errors**

## Development

### Running Tests

```bash
# Backend tests (when implemented)
cd backend
pytest

# Frontend tests (when implemented)
cd frontend
npm test
```

### Code Formatting

```bash
# Backend
black .
isort .

# Frontend
npm run lint
```

## Production Deployment

1. **Update environment variables** for production
2. **Set secure passwords** and secrets
3. **Configure reverse proxy** (Nginx)
4. **Enable HTTPS** with SSL certificates
5. **Set up monitoring** and logging
6. **Configure backups** for database and uploads

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.


