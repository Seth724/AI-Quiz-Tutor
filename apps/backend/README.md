# AI Quiz Tutor - Backend

FastAPI backend service for document processing, RAG-powered Q&A, and LLM-based quiz generation.

## ✅ What's Fixed

Recent production deployment identified and fixed critical issues:

1. **PDF Processing Hangs** → Added Docling watchdog timeout (180s) with heartbeat progress updates
2. **Out-of-Memory Kills** → Reduced OCR memory footprint (DPI: 150, max dims: 1400) + added swap setup
3. **Stale Processing Jobs** → Auto-mark failed after 20 minutes of no progress
4. **Status Display Issues** → Fixed UTC timezone handling in frontend
5. **Auth Redirect Loops** → Service worker now bypasses Clerk auth routes
6. **Missing Dependencies** → Docling added to production requirements

## 📁 Project Structure

```
apps/backend/
├── src/
│   ├── main.py                      # FastAPI application
│   ├── config.py                    # Environment settings with memory tuning
│   ├── api/
│   │   ├── routes.py               # REST endpoints
│   │   ├── schemas.py              # Pydantic models
│   │   └── document_utils.py       # Utilities
│   ├── services/
│   │   ├── document_service.py     # Smart PDF/OCR processing
│   │   ├── quiz_service.py         # LLM quiz generation
│   │   ├── vision_service.py       # Image understanding
│   │   └── background_processor.py # Async job queue
│   ├── chatbot/
│   │   └── service.py              # Chat RAG service
│   └── data/                        # Document storage
│
├── requirements.txt                 # Python dependencies (Docling now included)
├── Dockerfile                       # Production image (1.5GB RAM optimized)
├── docker-compose.yml              # Local dev setup
├── .env.example                    # Environment template
├── test_backend.py                 # Integration tests
├── QUICK_START.md                  # 5-minute local setup
├── SETUP.md                        # Full setup + production guide
└── README.md                       # This file
```

## 🏗️ Architecture

### Smart Document Processing Pipeline

```
PDF/Image Upload
  ↓
[Mode Detection]
  • Analyze: page count, text density, image ratio
  ↓
[Select Strategy]
  ├─ simple_text (text-only) → Direct PyMuPDF
  ├─ docling_batch (complex) → Docling with watchdog timeout
  ├─ ocr_hybrid (mixed) → Docling + EasyOCR fallback
  └─ ocr_full (scanned) → EasyOCR only
  ↓
[Extract with Progress Tracking]
  • Docling: 180s timeout + 15s heartbeat updates
  • OCR: Memory-aware preprocessing (DPI, dimensions)
  • Fallback: Auto-downgrade on failure
  ↓
[Vectorization]
  • Split into chunks (300-500 tokens)
  • Embed with HuggingFace API
  • Store in MongoDB with metadata
  ↓
[Status Changes]
  processing → ready
  (or: processing → failed after 20 min timeout)
```

### RAG Pipeline

```
User Query
  ↓
[Retrieve]
  • MongoDB vector search (top-3 chunks)
  ↓
[Augment]
  • Combine query + retrieved context
  ↓
[Generate]
  • Groq LLM: Chat or quiz questions
  ↓
Response
```

## 🚀 Quick Start

See [QUICK_START.md](QUICK_START.md) for 5-minute local setup.

## 📊 API Endpoints

### Documents

```
POST /api/documents/upload
  Upload PDF/image for processing
  
GET /api/documents
  List all documents
  
GET /api/documents/{id}
  Get document details + status
  
GET /api/documents/{id}/status
  Poll processing progress (elapsed time)
  
DELETE /api/documents/{id}
  Delete document and vectors
  
POST /api/documents/{id}/reprocess
  Force reprocess with new settings
```

### Quizzes

```
POST /api/quizzes/generate
  Generate quiz from document
  
GET /api/quizzes/{id}
  Get quiz questions
  
POST /api/quizzes/{id}/submit
  Submit answers → Get results
```

### Chat

```
POST /api/chat
  Query document with RAG
  (Returns error if document not ready)
```

### Health

```
GET /
  Health check
  
GET /docs
  Swagger API docs
```

## 🔧 Configuration

### Environment Variables

**Required:**
```env
GROQ_API_KEY=gsk_...                    # https://console.groq.com/keys
HF_TOKEN=hf_...                          # https://huggingface.co/settings/tokens
MONGODB_URI=mongodb+srv://...            # https://cloud.mongodb.com
```

**Optional but Recommended:**
```env
ENVIRONMENT=development|production       # Default: development
MONGODB_DATABASE=quiz_tutor             # Default: quiz_tutor
FRONTEND_ORIGINS=https://yourdomain.com # For CORS
PROCESSING_TIMEOUT_MINUTES=20           # Default: 20
```

**Memory Tuning (for VPS/low-resource):**
```env
OCR_PDF_DPI=150                          # Default: 170, Lower = less RAM
OCR_MAX_IMAGE_DIM=1400                   # Default: 1800, Lower = less RAM
```

**Docling Settings:**
```env
DOCLING_BATCH_TIMEOUT_SECONDS=120       # Timeout before fallback to OCR
DOCLING_PROGRESS_HEARTBEAT_SECONDS=10   # Progress update frequency
```

**Force Mode (for testing):**
```env
FORCE_PROCESSING_MODE=docling_batch     # Override auto-detection
```

See [`.env.example`](.env.example) for all options.

## 🛠️ Development

### Local Setup

```bash
cd apps/backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
copy .env.example .env
notepad .env  # Add your API keys
python test_backend.py  # Test connections
python src/main.py      # Start dev server
```

### Running Tests

```bash
# Full integration test
python test_backend.py

# Test specific backend component
python -m pytest src/tests/ -v

# Test document processing
python -c "from src.services.document_service import DocumentService; print('✅ Imports OK')"
```

### API Documentation

Visit: http://localhost:8000/docs

## 🚀 Production Deployment (VPS)

### Infrastructure

Tested on: **DigitalOcean $12/mo basic VPS**
- OS: Ubuntu 22.04
- CPU: 1 core
- RAM: 1.5GB
- Disk: 25GB SSD

### Prerequisites on VPS

```bash
sudo apt update
sudo apt install -y docker.io docker-compose git certbot nginx
sudo usermod -aG docker $USER  # Avoid typing sudo
exit  # Log out and back in for changes
```

### Deployment Steps

1. **Clone and prepare**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-quiz-tutor
   cd ai-quiz-tutor
   
   # Create environment file
   cp deploy/.env.example .env.backend
   # Edit with your API keys
   nano .env.backend
   ```

2. **Add 4GB Swap** (prevents OOM kills)
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

3. **Memory Tune OCR** (in `.env.backend`)
   ```env
   OCR_PDF_DPI=150
   OCR_MAX_IMAGE_DIM=1400
   DOCLING_BATCH_TIMEOUT_SECONDS=120
   ```

4. **Build Docker image**
   ```bash
   docker build -t quiz-tutor-backend -f apps/backend/Dockerfile apps/backend
   ```

5. **Start services**
   ```bash
   docker compose --env-file .env.backend -f deploy/docker-compose.prod.yml up -d

   # Verify running
   docker logs -f quiz-tutor-backend
   ```

6. **Point domain and get HTTPS**
   ```bash
   # Update DNS to VPS IP: A record api.yourdomain.com → IP
   
   # Configure Nginx (see deploy/nginx.conf)
   sudo cp deploy/nginx.conf /etc/nginx/sites-available/quiz-tutor
   sudo ln -s /etc/nginx/sites-available/quiz-tutor /etc/nginx/sites-enabled/
   sudo certbot certonly --nginx -d api.yourdomain.com
   sudo systemctl restart nginx
   ```

7. **Verify accessible**
   ```bash
   curl https://api.yourdomain.com/
   ```

### Memory Tuning Explained

The default 1.5GB VPS gets killed by OOM when:
- Docling loads (200MB) + EasyOCR loads (300MB) = 500MB base
- Processing a large PDF (400-500MB temporary buffers)
- MongoDB writes vectors in parallel

**Solutions:**
- **Gunicorn single worker**: Only 1 OCR model in RAM at a time
- **Reduced DPI**: 170 → 150 cuts memory ~30%
- **Smaller max dims**: 1800 → 1400 cuts memory ~30%
- **4GB Swap**: Lets OS page out to disk (slower but survives)

Combined: Should handle PDFs up to 100-150MB on $12 VPS.

### Monitoring Production

```bash
# Watch real-time logs
docker logs -f quiz-tutor-backend

# Search for errors
docker logs quiz-tutor-backend | grep ERROR

# Monitor for OOM kills
docker logs quiz-tutor-backend | grep SIGKILL  # Bad sign!

# Check memory usage
docker stats quiz-tutor-backend

# Restart if stuck
docker restart quiz-tutor-backend
```

## 🐛 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `Worker was sent SIGKILL` | Out of memory | Add swap (see above) |
| `PDF stuck on processing` | Timeout didn't trigger | Check logs, restart |
| `Docling not found` | Dependency missing | Rebuild Docker: `docker build -t quiz-tutor-backend .` |
| `MongoDB connection refused` | Bad URI or IP whitelist | Check `.env` and MongoDB Atlas Network Access |
| `Port 8000 in use` | Another process running | Kill it: `lsof -ti:8000 \| xargs kill` |
| `PDF processing takes 5+ min` | Likely OCR phase | Normal for large/scanned PDFs |

## 🔐 Security

- ✅ CORS restricted to frontend origins
- ✅ No hardcoded secrets (use environment variables)
- ✅ Input validation on all endpoints
- ✅ HTTPS enforced in production (Nginx + Let's Encrypt)
- ✅ No API keys logged (sanitized in debug output)
- `GET /api/progress` - Get user progress
- `GET /api/progress/weak-areas` - Get weak areas
- `POST /api/reminders` - Schedule review reminder

### Chat
- `POST /api/chat` - Chat with AI tutor (RAG)

## 🧪 Test with Tutorial-3 Files

This backend uses the working code from `tutorial-3-mongodb`:
- `pdf_rag_simple.py` - Simple PDF processing
- `pdf_rag_batch.py` - Batch processing
- `demo_retrieval_methods.py` - MongoDB retrieval

## 📊 MongoDB Collections

### documents
```json
{
  "_id": "uuid",
  "user_id": "clerk_user_id",
  "title": "Three.js Tutorial",
  "local_file_path": "apps/backend/src/data/<doc_id>_filename.pdf",
  "chunks": [...],
  "created_at": "timestamp"
}
```

### quizzes
```json
{
  "_id": "uuid",
  "document_id": "doc_uuid",
  "questions": [
    {
      "id": "q1",
      "question": "What is Three.js?",
      "options": ["A", "B", "C", "D"],
      "correct": "A",
      "explanation": "..."
    }
  ],
  "created_at": "timestamp"
}
```

### attempts
```json
{
  "_id": "uuid",
  "user_id": "clerk_user_id",
  "quiz_id": "quiz_uuid",
  "answers": [...],
  "score": 0.85,
  "weak_areas": ["topic1", "topic2"],
  "completed_at": "timestamp"
}
```

## 🔧 Development

### Run in Development Mode
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Specific Module
```bash
# Test document service
python src/services/document_service.py

# Test quiz generation
python src/services/quiz_service.py
```

## 📝 Notes

- Uses working code from `tutorial-3-mongodb` for MongoDB RAG
- Docling for OCR (when needed)
- Groq for fast LLM inference
- HuggingFace API for embeddings (no local models)
