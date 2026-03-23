# AI Quiz Tutor - Backend (ML Service)

FastAPI backend for document processing, RAG, and quiz generation.

## ✅ Reliability Updates

- Chat endpoint now gates document Q&A until the document status is `ready`
- Async-safe chat retrieval path prevents `asyncio.run() cannot be called from a running event loop`
- Background processor now stores accurate page counts from page labels instead of chunk totals
- Estimated table indicators are saved as `tables_count` in document metadata

## 📁 Structure

```
backend/
├── src/
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Configuration
│   ├── models/                 # MongoDB schemas
│   ├── services/               # Business logic
│   │   ├── document_service.py     # PDF processing
│   │   ├── quiz_service.py         # Quiz generation
│   │   ├── rag_service.py          # RAG pipeline
│   │   └── ocr_service.py          # OCR with Docling
│   ├── api/                    # API routes
│   │   ├── routes.py
│   │   └── schemas.py
│   └── utils/                  # Utilities
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
```bash
copy .env.example .env  # Windows
# or
cp .env.example .env  # macOS/Linux
```

Edit `.env` with your API keys:
```env
# API Keys
GROQ_API_KEY=your_groq_key
HF_TOKEN=your_huggingface_token

# MongoDB Atlas
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/

# Clerk (auth - for later)
CLERK_SECRET_KEY=your_clerk_key

# Optional: SMTP email reminders
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_USE_TLS=true
```

### 4. Run the Server
```bash
python src/main.py
```

Server will start at: `http://localhost:8000`

API Docs: `http://localhost:8000/docs`

## 📚 API Endpoints

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List user's documents
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete document

### Quizzes
- `POST /api/quizzes/generate` - Generate quiz from document
- `GET /api/quizzes/{id}` - Get quiz
- `POST /api/quizzes/{id}/submit` - Submit quiz answers
- `GET /api/quizzes/{id}/results` - Get quiz results

### Progress
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
